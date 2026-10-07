import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

const features = [
  ["01", "A plan that fits you", "Shape each trip around your dates, interests and the way you like to travel."],
  ["02", "A budget with breathing room", "See estimated costs and what is left, before and during your trip."],
  ["03", "Days that flow", "Keep nearby stops together and leave time between the places you love."],
];

export default function Landing() {
  const { token } = useAuth();
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    let active = true;
    api.get("/health")
      .then(() => active && setApiStatus("connected"))
      .catch(() => active && setApiStatus("unavailable"));
    return () => { active = false; };
  }, []);

  return (
    <div className="landing">
      <header className="landing-nav">
        <Link className="brand" to="/"><span className="brand-mark">T</span><span>tripwise</span></Link>
        <nav aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#features">Features</a>
          <Link className="nav-signin" to={token ? "/dashboard" : "/login"}>{token ? "My workspace" : "Sign in"}</Link>
          <Link className="button button-primary nav-cta" to={token ? "/trips/new" : "/register"}>Plan a trip <span>↗</span></Link>
        </nav>
      </header>
      <section className="hero">
        <div className="hero-copy">
          <div className="hero-kicker"><span className="sparkle">✳</span> A little more wonder, a lot less planning</div>
          <h1>Plan smarter.<br /><span>Travel better.</span></h1>
          <p>Thoughtful itineraries, a budget that makes sense, and more time for the moments you came for.</p>
          <div className="hero-actions">
            <Link className="button button-primary button-large" to={token ? "/trips/new" : "/register"}>Plan my trip <span>→</span></Link>
            <a className="button button-quiet button-large" href="#how-it-works">See how it works <span>↓</span></a>
          </div>
          <div className="hero-proof"><span className="proof-dot">✓</span> Your trips, your choices <span className="proof-separator">·</span> No guesswork on live data</div>
        </div>
        <div className="hero-visual" aria-label="An illustrated travel itinerary">
          <div className="sun-disc" />
          <div className="hill hill-back" />
          <div className="hill hill-front" />
          <div className="hero-stamp">GO<br />SOMEWHERE<br /><span>lovely</span></div>
          <div className="itinerary-float">
            <div className="float-heading"><span>YOUR WEEKEND, WELL SPENT</span><b>•••</b></div>
            <div className="float-place"><span className="float-icon">01</span><span><strong>Old town wander</strong><small>09:30 · Culture</small></span><span className="float-check">✓</span></div>
            <div className="float-place"><span className="float-icon float-icon-peach">02</span><span><strong>A long lunch</strong><small>12:00 · Food</small></span><span className="float-check">✓</span></div>
            <div className="float-budget"><span>TRIP BUDGET</span><strong>Looking good</strong><div className="budget-line"><i /></div><small>Thoughtful spending, room to spare</small></div>
          </div>
          <div className="hero-note"><span>✳</span> Leave space for the unexpected.</div>
        </div>
      </section>
      <div className="trust-strip"><span>MADE FOR THE WAY YOU WANDER</span><span>✳ Your pace</span><span>✳ Your budget</span><span>✳ Your kind of trip</span></div>
      <section className="section-how" id="how-it-works">
        <div className="section-heading"><span className="eyebrow">SIMPLE BY DESIGN</span><h2>From “we should go”<br />to “remember when…”</h2><p>One easy place to turn the idea of a trip into a plan you can actually use.</p></div>
        <div className="steps-grid">
          {[["01", "Tell us what you love", "Choose your destination, dates, budget and the things you want to see."], ["02", "Get a thoughtful starting point", "TripWise groups sample places into a day-by-day plan. Make it your own."], ["03", "Go, with a little more ease", "Keep plans and expenses together, and adjust whenever you need."]].map(([number, title, body]) => (
            <article className="step-card" key={number}><span>{number}</span><h3>{title}</h3><p>{body}</p></article>
          ))}
        </div>
      </section>
      <section className="section-features" id="features">
        <div className="feature-intro"><span className="eyebrow">GOOD PLANS, NOT MORE TABS</span><h2>Everything you need.<br />Nothing you don’t.</h2><p>Just the useful pieces, brought together so you can spend less time coordinating and more time looking forward to it.</p><Link className="inline-link" to={token ? "/trips/new" : "/register"}>Make a plan of your own <span>→</span></Link></div>
        <div className="feature-list">{features.map(([number, title, body]) => <article className="feature-row" key={number}><span>{number}</span><div><h3>{title}</h3><p>{body}</p></div><span className="feature-arrow">↗</span></article>)}</div>
      </section>
      <section className="landing-cta"><span className="eyebrow">THE WORLD IS STILL OUT THERE</span><h2>Start with somewhere<br />you’ve been dreaming of.</h2><Link className="button button-dark button-large" to={token ? "/trips/new" : "/register"}>Let’s plan it <span>→</span></Link><span className="cta-doodle">✳</span></section>
      <footer className="landing-footer"><Link className="brand" to="/"><span className="brand-mark">T</span><span>tripwise</span></Link><span>Thoughtful plans. Unplanned magic.</span><Link to={token ? "/dashboard" : "/register"}>Get started ↗</Link></footer>
      <div className={`health-badge health-${apiStatus}`} role="status" aria-live="polite">
        <span className="health-dot" /> API {apiStatus === "checking" ? "checking" : apiStatus}
      </div>
    </div>
  );
}
