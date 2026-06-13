import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { useToast } from "../components/Toast";
import { Link } from "react-router-dom";
import { Activity, ShoppingCart, Package, Recycle } from "../components/icons";

export default function PreLoved() {
  const [listings, setListings] = useState([]);
  const { user, reload } = useAuth();
  const { push } = useToast();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get("/listings/preloved")
      .then((res) => setListings(res))
      .finally(() => setLoading(false));
  }, []);

  const buy = async (listingId) => {
    if (!user) return window.location.assign("/login");
    const prevBal = user?.green_credits?.balance || 0;
    try {
      await api.post("/orders/place", { listing_id: listingId });
      push("Order placed", "success");
      try {
        const me = await reload();
        const newBal = me?.green_credits?.balance || 0;
        if (newBal > prevBal)
          push(`+${newBal - prevBal} green credits`, "success");
      } catch (e) {}
    } catch (e) {
      push(e.message || "Order failed", "error");
    }
  };

  return (
    <div className="page">
      <h2 style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span className="brand-hero" style={{ padding: 4 }}>
          <img src="/logo.png" alt="Orbit" style={{ height: 22 }} />
        </span>
        Pre-Loved Shop
      </h2>

      {!loading && listings.length === 0 ? (
        <div className="empty">
          <span className="medallion">
            <Recycle size={28} />
          </span>
          <div>No pre-loved listings yet — check back soon.</div>
        </div>
      ) : (
        <div className="grid stagger">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="media-card skel">
                  <div className="media-img skeleton" />
                  <div className="panel">
                    <div className="line skeleton" />
                    <div className="line short skeleton" />
                  </div>
                </div>
              ))
            : listings.map((l) => {
                const src =
                  (l.photo_urls && l.photo_urls[0]) ||
                  l.product.image_url ||
                  l.product.thumbnail_url;
                const save = Math.round(100 - (l.price * 100) / l.product.mrp);
                return (
                  <div key={l.id} className="media-card sheen">
                    <Link
                      to={`/p/${l.product.id}`}
                      style={{ position: "absolute", inset: 0, zIndex: 1 }}
                      aria-label={l.product.title}
                    />
                    {src ? (
                      <img
                        className="media-img"
                        src={src}
                        alt={l.product.title}
                        loading="lazy"
                      />
                    ) : (
                      <div className="media-fallback">
                        <Package size={48} />
                      </div>
                    )}
                    <div className="corner left">
                      <span className={`badge grade-${l.grade} float`}>
                        Grade {l.grade}
                      </span>
                      {save > 0 && (
                        <span className="badge success float">
                          Save {save}%
                        </span>
                      )}
                    </div>
                    <div className="panel" style={{ zIndex: 2 }}>
                      <h3>{l.product.title}</h3>
                      <div
                        className="row"
                        style={{ gap: 8, justifyContent: "space-between" }}
                      >
                        <span>
                          <span className="price">₹{l.price}</span>
                          <span className="mrp">₹{l.product.mrp}</span>
                        </span>
                        <span className="badge src" style={{ margin: 0 }}>
                          {l.source}
                        </span>
                      </div>
                      <div className="card-actions" style={{ marginTop: 10 }}>
                        <button
                          className="buy"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            buy(l.id);
                          }}
                        >
                          <ShoppingCart size={15} /> Buy
                        </button>
                        <a
                          className="button green"
                          href={`/unit/${l.unit_id}`}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Activity size={15} /> Health
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}
        </div>
      )}
    </div>
  );
}
