import { Navigate, NavLink, Route, Routes, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "./auth";
import { GiSeedling } from "react-icons/gi";
import Shop from "./pages/Shop";
import ProductPage from "./pages/ProductPage";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Orders from "./pages/Orders";
import Resell from "./pages/Resell";
import SellerPortal from "./pages/SellerPortal";
import FacilityPortal from "./pages/FacilityPortal";
import HealthCard from "./pages/HealthCard";
import PreLoved from "./pages/PreLoved";
import Rewards from "./pages/Rewards";

function Guard({ need, children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page muted">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (need && user.role !== need) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  return (
    <>
      <nav className="nav">
        <div className="brand">
          <img
            src="/logo.png"
            alt="Loop"
            style={{ height: 28, marginRight: 8 }}
          />
          <span
            style={{
              fontWeight: 800,
              fontSize: 18,
              color: "var(--accent)",
            }}
          >
            Loop
          </span>
        </div>
        <button
          className={loc.pathname === "/" ? "active" : ""}
          onClick={() => nav("/")}
        >
          Shop
        </button>
        {user && (
          <button
            className={
              loc.pathname.startsWith("/orders") ? "active" : ""
            }
            onClick={() => nav("/orders")}
          >
            Orders
          </button>
        )}
        {user && (
          <button
            className={loc.pathname.startsWith("/resell") ? "active" : ""}
            onClick={() => nav("/resell")}
          >
            Resell
          </button>
        )}
        {user?.role === "SELLER" && (
          <button
            className={loc.pathname.startsWith("/seller") ? "active" : ""}
            onClick={() => nav("/seller")}
          >
            Seller
          </button>
        )}
        {user?.role === "FACILITY" && (
          <button
            className={loc.pathname.startsWith("/facility") ? "active" : ""}
            onClick={() => nav("/facility")}
          >
            Facility
          </button>
        )}
        <button
          className={loc.pathname.startsWith("/preloved") ? "active" : ""}
          onClick={() => nav("/preloved")}
        >
          Pre-Loved
        </button>
        <span className="spacer" />
        {user ? (
          <>
            <button className="muted nav-user" onClick={() => window.location.assign('/profile')}>
              {user.username} · {user.role}
            </button>
            <NavLink to="/rewards" className="muted">
              <GiSeedling style={{ marginRight: 6 }} />{" "}
              {user.green_credits?.balance ?? 0}
            </NavLink>
            <button className="secondary" onClick={logout}>
              Logout
            </button>
          </>
        ) : (
          <button onClick={() => nav("/login")}>Login</button>
        )}
      </nav>
      <Routes>
        <Route path="/" element={<Shop />} />
        <Route path="/p/:id" element={<ProductPage />} />
        <Route path="/preloved" element={<PreLoved />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/unit/:id" element={<HealthCard />} />
        <Route
          path="/orders"
          element={
            <Guard>
              <Orders />
            </Guard>
          }
        />
        <Route
          path="/resell"
          element={
            <Guard>
              <Resell />
            </Guard>
          }
        />
        <Route
          path="/seller/*"
          element={
            <Guard need="SELLER">
              <SellerPortal />
            </Guard>
          }
        />
        <Route
          path="/facility/*"
          element={
            <Guard need="FACILITY">
              <FacilityPortal />
            </Guard>
          }
        />
        <Route
          path="/rewards"
          element={
            <Guard>
              <Rewards />
            </Guard>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
