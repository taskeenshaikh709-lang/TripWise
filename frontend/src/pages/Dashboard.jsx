import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

function formatMoney(value, currency = "INR") {
  return new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 0 }).format(value || 0);
}

export default function Dashboard() {
  const { user } = useAuth();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/trips")
      .then(({ data }) => setTrips(data.trips))
      .catch((requestError) => setError(requestError.response?.data?.message || "Your trips could not be loaded. Please try again."))
      .finally(() => setLoading(false));
  }, []);

  const nextTrip = [...trips].sort((a, b) => (a.start_date || "").localeCompare(b.start_date || "")).find((trip) => trip.start_date && trip.start_date >= new Date().toISOString().slice(0, 10));
  const totalBudget = trips.reduce((sum, trip) => sum + trip.budget, 0);

  return (
    <div className="dashboard-page">
      <div className="page-heading">
        <div><span className="eyebrow">YOUR TRAVEL STUDIO</span><h1>Good to see you, {user?.name?.split(" ")[0]}.</h1><p>Every great trip starts somewhere. What are you dreaming about?</p></div>
        <Link className="button button-primary" to="/trips/new">＋ Plan a trip</Link>
      </div>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      <section className="stat-grid">
        <article className="stat-card"><span>PLANNED TRIPS</span><strong>{trips.length}</strong><small>A little something to look forward to</small></article>
        <article className="stat-card stat-card-accent"><span>NEXT ADVENTURE</span><strong>{nextTrip?.destination || "Still dreaming"}</strong><small>{nextTrip?.start_date || "Your next trip could start here"}</small></article>
        <article className="stat-card"><span>TRIP BUDGETS</span><strong>{formatMoney(totalBudget)}</strong><small>Across all your planned trips</small></article>
      </section>
      <div className="section-title-row"><div><span className="eyebrow">YOUR COLLECTION</span><h2>Trips on your mind</h2></div><Link className="inline-link" to="/trips">See all trips <span>→</span></Link></div>
      {loading ? <div className="loading-card">Gathering your plans…</div> : trips.length === 0 ? (
        <section className="empty-state">
          <span className="empty-illustration">✳</span><span className="eyebrow">A BLANK PAGE, IN THE BEST WAY</span>
          <h2>Somewhere is calling.</h2><p>Start with a destination and a few things you love. We’ll help you shape the rest.</p>
          <Link className="button button-primary" to="/trips/new">Plan your first trip <span>→</span></Link>
        </section>
      ) : (
        <div className="trip-grid">{trips.map((trip, index) => (
          <Link className={`trip-card trip-card-${index % 3}`} to={`/trips/${trip.id}`} key={trip.id}>
            <div className="trip-card-art"><span>{trip.destination.slice(0, 1).toUpperCase()}</span><small>{trip.days}-DAY TRIP</small></div>
            <div className="trip-card-body"><div className="trip-card-title"><h3>{trip.destination}</h3><span>↗</span></div>
              <p>{trip.start_date} — {trip.end_date}</p>
              <div className="trip-card-meta"><span>{trip.travelers} {trip.travelers === 1 ? "traveler" : "travelers"}</span><span>{formatMoney(trip.budget, trip.currency)}</span></div>
            </div>
          </Link>
        ))}</div>
      )}
      <section className="dashboard-note"><span>✳</span><div><strong>Plans are a starting point, not a promise.</strong><p>Place suggestions and travel times are estimates. Always check current opening hours and routes before heading out.</p></div></section>
    </div>
  );
}
