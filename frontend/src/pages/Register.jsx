import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { AlertCircle } from "../components/icons";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [role, setRole] = useState("BUYER");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      const u = await register(username, password, role);
      nav(u.role === "SELLER" ? "/seller" : "/");
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
        <h2 style={{ margin: "8px 0 0" }}>Join Orbit</h2>
        <p className="muted" style={{ marginTop: 2 }}>
          Every product finds its next owner
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
      <label>I am a…</label>
      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="BUYER">Buyer (can also resell)</option>
        <option value="SELLER">Seller</option>
      </select>
      {err && (
        <div className="error">
          <AlertCircle size={14} /> {err}
        </div>
      )}
      <button style={{ marginTop: 16, width: "100%" }}>Create account</button>
      <p className="muted" style={{ marginTop: 12, textAlign: "center" }}>
        Have an account? <Link to="/login">Login</Link>
      </p>
    </form>
  );
}
