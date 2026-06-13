import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { AlertCircle } from "../components/icons";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      const u = await login(username, password);
      nav(
        u.role === "SELLER"
          ? "/seller"
          : u.role === "FACILITY"
            ? "/facility"
            : "/",
      );
    } catch (e2) {
      setErr(e2.message);
    }
  };

  return (
    <form
      className="form glass enter"
      onSubmit={submit}
      style={{ padding: 26 }}
    >
      <div style={{ textAlign: "center", marginBottom: 8 }}>
        <span className="brand-hero">
          <img src="/logo.png" alt="Orbit" style={{ height: 48 }} />
        </span>
        <h2 style={{ margin: "8px 0 0" }}>Welcome to Orbit</h2>
        <p className="muted" style={{ marginTop: 2 }}>
          Sign in to continue
        </p>
      </div>
      <label>Username</label>
      <input
        value={username}
        onChange={(e) => setU(e.target.value)}
        autoFocus
      />
      <label>Password</label>
      <input
        type="password"
        value={password}
        onChange={(e) => setP(e.target.value)}
      />
      {err && (
        <div className="error">
          <AlertCircle size={14} /> {err}
        </div>
      )}
      <button style={{ marginTop: 16, width: "100%" }}>Login</button>
      <p className="muted" style={{ marginTop: 12, textAlign: "center" }}>
        No account? <Link to="/register">Register</Link>
        <br />
        Demo: buyer1 / rahul / seller1 / facility1 · password{" "}
        <code>demo1234</code>
      </p>
    </form>
  );
}
