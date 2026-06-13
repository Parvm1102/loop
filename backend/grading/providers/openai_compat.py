"""VLM provider backed by any OpenAI-compatible endpoint.

One client serves Gemini (Google's OpenAI-compatibility endpoint), OpenAI, and
self-hosted Modal/vLLM — the difference is only base_url + api_key + model, which
the registry pulls from settings.LLM_PROVIDERS. Images are sent as standard
`image_url` base64 data URIs and we request a JSON object response.

The caller is responsible for falling back to the mock on failure (see
orchestrator.run_vlm); we keep this provider thin.
"""

import logging

from openai import BadRequestError, OpenAI

from .. import jsonio, prompts
from . import base

log = logging.getLogger(__name__)

# Models that rejected `reasoning_effort` once (e.g. Gemma served via the Gemini
# OpenAI-compat endpoint answers 400 "Thinking level is not supported"). We
# remember them per worker process so we only pay the failed round-trip once and
# skip the knob thereafter. Module-level so it survives provider re-creation.
_NO_REASONING_MODELS: set[str] = set()
# Likewise for models whose endpoint rejects response_format json_schema: we
# degrade that model to json_object (still constrained) rather than to the mock.
_NO_JSON_SCHEMA_MODELS: set[str] = set()


class OpenAICompatVLM(base.VLMProvider):
    def __init__(self, name, base_url, api_key, model, timeout=30.0, reasoning_effort=""):
        self.name = name
        self.model = model
        self.reasoning_effort = reasoning_effort or ""
        self._client = OpenAI(
            base_url=base_url or None,
            api_key=api_key or "missing",
            timeout=timeout,
            max_retries=1,
        )

    def grade(self, req: base.VLMRequest) -> dict:
        messages = prompts.build_vlm_messages(req)
        content = self._complete(messages)
        data = jsonio.extract_json(content)
        data["source"] = self.name
        return prompts.normalize_vlm_output(data, n_uploaded=len(req.uploaded or []))

    def _response_format(self) -> dict:
        """json_schema (strongest) unless this model has rejected it before."""
        if self.model in _NO_JSON_SCHEMA_MODELS:
            return {"type": "json_object"}
        return {"type": "json_schema", "json_schema": prompts.grade_schema()}

    def _complete(self, messages) -> str:
        """Call the model and return raw text.

        Two output knobs can be rejected per-model: `reasoning_effort` (Gemma)
        and `response_format: json_schema`. We degrade each independently,
        remember it for the process, and retry — so a knob the endpoint dislikes
        costs one round-trip, never a fall back to the mock. A BadRequestError
        that is *not* a knob rejection is re-raised for the caller to handle.
        """
        last_exc = None
        for _ in range(3):  # at most: drop one knob, drop the other, then settle
            kwargs = {
                "model": self.model,
                "messages": messages,
                "response_format": self._response_format(),
                "temperature": 0.1,
            }
            if self.reasoning_effort and self.model not in _NO_REASONING_MODELS:
                kwargs["extra_body"] = {"reasoning_effort": self.reasoning_effort}
            try:
                resp = self._client.chat.completions.create(**kwargs)
                return (resp.choices[0].message.content or "").strip()
            except BadRequestError as exc:
                last_exc = exc
                used_effort = "extra_body" in kwargs
                used_schema = kwargs["response_format"].get("type") == "json_schema"
                if used_effort and _is_reasoning_rejection(exc):
                    _NO_REASONING_MODELS.add(self.model)
                elif used_schema:
                    # json_schema is the fragile path; drop to json_object and
                    # retry before ever giving up, to stay off the mock.
                    _NO_JSON_SCHEMA_MODELS.add(self.model)
                else:
                    raise
                log.info("VLM model %r rejected an output knob; retrying degraded", self.model)
        raise last_exc


def _is_reasoning_rejection(exc: BadRequestError) -> bool:
    """True when a 400 is specifically about an unsupported thinking/reasoning knob."""
    msg = str(getattr(exc, "message", "") or exc).lower()
    return "thinking" in msg or "reasoning" in msg
