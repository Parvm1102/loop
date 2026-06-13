import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { useToast } from "../components/Toast";
import { useCountUp } from "../lib/motion";
import { Sprout, Gift, Leaf, Recycle } from "../components/icons";

export default function Rewards() {
  const { reload } = useAuth();
  const [balance, setBalance] = useState(0);
  const [impact, setImpact] = useState({});
  const [rewards, setRewards] = useState([]);
  const [loading, setLoading] = useState(true);
  const { push } = useToast();
  const shownBalance = useCountUp(balance);

  useEffect(() => {
    setLoading(true);
    Promise.all([api.get("/credits"), api.get("/rewards")])
      .then(([c, r]) => {
        setBalance(c.balance);
        setImpact(c.impact || {});
        setRewards(r);
      })
      .finally(() => setLoading(false));
  }, []);

  const claim = async (id) => {
    try {
      const res = await api.post(`/rewards/${id}/claim`);
      setBalance(res.new_balance);
      reload();
      push("Reward claimed", "success");
    } catch (e) {
      push(e.response?.data?.message || "Claim failed", "error");
    }
  };

  return (
    <div className="page">
      <h2 style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span className="brand-hero" style={{ padding: 4 }}>
          <Sprout size={24} style={{ color: "var(--success)" }} />
        </span>
        Green Credits
      </h2>

      {loading ? (
        <div className="card skeleton">
          <div className="thumb skeleton" />
          <div className="line skeleton" />
          <div className="line short skeleton" />
        </div>
      ) : (
        <div className="glass" style={{ padding: 22 }}>
          <div className="row" style={{ alignItems: "baseline", gap: 10 }}>
            <span
              style={{
                fontSize: 40,
                fontWeight: 800,
                fontFeatureSettings: '"tnum" 1',
              }}
            >
              {shownBalance}
            </span>
            <span
              className="muted"
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <Sprout size={16} style={{ color: "var(--success)" }} /> credits
              available
            </span>
          </div>
          <div className="stat-grid">
            <div className="stat-tile">
              <div
                className="v"
                style={{ display: "flex", alignItems: "center", gap: 6 }}
              >
                <Recycle size={18} /> {impact.items_saved_from_landfill ?? 0}
              </div>
              <div className="k">Items saved from landfill</div>
            </div>
            <div className="stat-tile">
              <div
                className="v"
                style={{ display: "flex", alignItems: "center", gap: 6 }}
              >
                <Leaf size={18} style={{ color: "var(--success)" }} />{" "}
                {impact.co2_avoided_kg ?? 0} kg
              </div>
              <div className="k">CO₂ avoided</div>
            </div>
          </div>
        </div>
      )}

      <h3
        style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 22 }}
      >
        <Gift size={18} /> Rewards Store
      </h3>
      <div className="grid stagger">
        {rewards.map((r) => (
          <div key={r.id} className="card no-hover">
            <span className="medallion" style={{ width: 48, height: 48 }}>
              <Gift size={22} />
            </span>
            <h3 style={{ marginTop: 10 }}>{r.title}</h3>
            <div className="muted">{r.description}</div>
            <div
              className="price"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                color: "var(--success)",
              }}
            >
              <Sprout size={16} /> {r.cost}
            </div>
            <button
              onClick={() => claim(r.id)}
              disabled={balance < r.cost}
              style={{ marginTop: 10, width: "100%" }}
            >
              <Gift size={15} /> Claim
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
