import { useRef } from "react";
import { Link } from "react-router-dom";
import { Package, ChevronLeft, ChevronRight } from "./icons";

function CarouselCard({ p }) {
  const src =
    p.thumbnail_url ||
    (p.listings &&
      p.listings[0] &&
      p.listings[0].photo_urls &&
      p.listings[0].photo_urls[0]) ||
    p.image_url;
  return (
    <Link className="carousel-card sheen" to={`/p/${p.id}`}>
      <div className="carousel-thumb">
        {src ? (
          <img
            src={src}
            alt={p.title}
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : (
          <div className="media-fallback">
            <Package size={36} />
          </div>
        )}
      </div>
      <div className="carousel-meta">
        <h4>{p.title}</h4>
        <span className="price">₹{p.mrp}</span>
      </div>
    </Link>
  );
}

/**
 * Horizontal, scrollable product carousel with arrow controls.
 * Used on the product page to surface more items from the same category.
 */
export default function ProductCarousel({ items = [], title }) {
  const trackRef = useRef(null);

  const scrollBy = (dir) => {
    const track = trackRef.current;
    if (!track) return;
    // Scroll by roughly the visible width so paging feels natural.
    track.scrollBy({ left: dir * track.clientWidth * 0.9, behavior: "smooth" });
  };

  if (!items.length) return null;

  return (
    <div className="carousel">
      {title && <div className="carousel-head">{title}</div>}
      <div className="carousel-viewport">
        <button
          type="button"
          className="carousel-arrow left secondary"
          aria-label="Scroll left"
          onClick={() => scrollBy(-1)}
        >
          <ChevronLeft size={18} />
        </button>
        <div className="carousel-track" ref={trackRef}>
          {items.map((p) => (
            <CarouselCard key={p.id} p={p} />
          ))}
        </div>
        <button
          type="button"
          className="carousel-arrow right secondary"
          aria-label="Scroll right"
          onClick={() => scrollBy(1)}
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}
