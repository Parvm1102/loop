import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useToast } from "../components/Toast";
import { useTilt } from "../lib/motion";
import ProductCarousel from "../components/ProductCarousel";
import {
  ShieldCheck,
  Sparkles,
  Package,
  Activity,
  ShoppingCart,
  CheckCircle,
} from "../components/icons";

export default function ProductPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const { reload } = useAuth();
  const nav = useNavigate();
  const [p, setP] = useState(null);
  const [related, setRelated] = useState([]);
  const [fitHint, setFitHint] = useState("");
  const { push } = useToast();
  const tilt = useTilt(5);

  const load = () => api.get(`/products/${id}`).then(setP);
  useEffect(() => {
    load();
    // load fit-check hint
    api
      .get(`/products/${id}/fitcheck`)
      .then((res) => {
        if (res && res.hint) setFitHint(res.hint);
      })
      .catch(() => {});
    // load same-category products for the carousel
    api
      .get(`/products/${id}/related`)
      .then((res) => setRelated(res || []))
      .catch(() => setRelated([]));
  }, [id]);

  const buy = async (listingId) => {
    if (!user) return nav("/login");
    const prevBal = user?.green_credits?.balance || 0;
    try {
      await api.post("/orders/place", { listing_id: listingId });
      push("Order placed — check Orders tab", "success");
      load();
      // refresh auth payload to update green credits counter in header
      try {
        await reload();
      } catch (e) {
        /* ignore */
      }
      try {
        const me = await api.get("/auth/me");
        const newBal = me.user?.green_credits?.balance || 0;
        if (newBal > prevBal)
          push(`+${newBal - prevBal} green credits added`, "success");
      } catch (e) {}
    } catch (e) {
      push(e.message || "Order failed", "error");
    }
  };

  if (!p) return <div className="page muted">Loading…</div>;

  const newListings = p.listings.filter((l) => l.source === "NEW");
  const preLoved = p.listings.filter((l) => l.source !== "NEW");

  return (
    <div className="page">
      <div
        className="row enter"
        style={{ alignItems: "stretch", gap: 24, marginBottom: 8 }}
      >
        <div
          ref={tilt.ref}
          {...tilt.bind}
          className="media-card"
          style={{
            width: 320,
            maxWidth: "100%",
            aspectRatio: "1 / 1",
            flex: "0 0 auto",
          }}
        >
          {p.image_url ? (
            <img className="media-img" src={p.image_url} alt={p.title} />
          ) : (
            <div className="media-fallback">
              <Package size={56} />
            </div>
          )}
        </div>

        <div className="glass" style={{ flex: 1, minWidth: 260, padding: 20 }}>
          <span className="badge">{p.category}</span>
          <h2 style={{ marginTop: 8 }}>{p.title}</h2>
          <p className="muted">{p.description}</p>
          {p.attributes && Object.keys(p.attributes).length > 0 && (
            <div style={{ marginTop: 14 }}>
              <strong style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Package size={15} /> Specifications
              </strong>
              <dl className="spec-list">
                {Object.entries(p.attributes).map(([k, v]) => (
                  <div className="spec-row" key={k}>
                    <dt>{k.replaceAll("_", " ")}</dt>
                    <dd>{String(v)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
          {fitHint && (
            <div
              className="disposition"
              style={{
                marginTop: 12,
                display: "flex",
                alignItems: "flex-start",
                gap: 8,
              }}
            >
              <Sparkles
                size={16}
                style={{
                  flexShrink: 0,
                  marginTop: 2,
                  color: "var(--brand-orange-deep)",
                }}
              />
              <div>
                <strong>Fit hint</strong> {fitHint}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="product-lower">
        <div className="product-listings">
          <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <ShoppingCart size={18} /> Buy new
          </h3>
          {newListings.length === 0 && (
            <div className="muted">Out of stock.</div>
          )}
          <div className="grid preloved-grid stagger">
            {newListings.map((l) => (
              <div className="card preloved-buy buynew" key={l.id}>
                <div className="preloved-info">
                  <div className="price">₹{l.price}</div>
                </div>
                <div className="preloved-actions">
                  <button
                    className="buy"
                    onClick={() => buy(l.id)}
                    aria-label="Buy this item"
                  >
                    <ShoppingCart size={16} /> Buy
                  </button>
                </div>
              </div>
            ))}
          </div>

          <h3
            style={{
              marginTop: 28,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <ShieldCheck size={18} style={{ color: "var(--success)" }} />{" "}
            Pre-loved
            <span
              className="muted"
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              (graded &amp; verified by
              <img
                src="/logo.png"
                alt="Orbit"
                style={{ height: 14, verticalAlign: "middle" }}
              />
              Orbit)
            </span>
          </h3>
          {preLoved.length === 0 && (
            <div className="muted">No pre-loved offers right now.</div>
          )}
          <div className="grid preloved-grid stagger">
            {preLoved.map((l) => (
              <div className="card no-hover preloved-buy" key={l.id}>
                <div className="preloved-info">
                  <div className="row" style={{ gap: 4 }}>
                    <span className={`badge grade-${l.grade}`}>
                      Grade {l.grade ?? "?"}
                    </span>
                    <span className="badge src">
                      {l.source.replaceAll("_", " ")}
                    </span>
                    {l.untouched && (
                      <span className="badge success">
                        <CheckCircle size={12} /> UNOPENED
                      </span>
                    )}
                  </div>
                  {l.photo_urls?.length > 0 && (
                    <div className="row" style={{ marginTop: 10, gap: 6 }}>
                      {l.photo_urls.slice(0, 3).map((ph) => (
                        <img
                          key={ph}
                          src={ph}
                          alt="condition"
                          className="photo-tile"
                        />
                      ))}
                    </div>
                  )}
                  <div style={{ marginTop: 10 }}>
                    <span className="price">₹{l.price}</span>
                    <span className="mrp">₹{p.mrp}</span>
                  </div>
                </div>
                <div className="preloved-actions">
                  <button
                    className="buy"
                    onClick={() => buy(l.id)}
                    aria-label="Buy this item"
                  >
                    <ShoppingCart size={16} /> Buy
                  </button>
                  <Link
                    to={`/unit/${l.unit_id}`}
                    className="button green"
                    aria-label="View Health Card"
                  >
                    <Activity size={16} /> View Health Card
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {related.length > 0 && (
          <aside className="product-aside">
            <ProductCarousel
              items={related}
              title={
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <Package size={16} /> More in {p.category}
                </span>
              }
            />
          </aside>
        )}
      </div>
    </div>
  );
}
