import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

const INTERESTS = ["Nature", "Adventure", "Historical", "Food", "Shopping", "Culture", "Beaches", "Photography"];
const STEPS = ["Destination", "When & where", "Your budget", "Your style", "Review"];

function defaultDate(offset) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.toISOString().slice(0, 10);
}

const INITIAL = {
  destination: "",
  start_location: "",
  start_date: defaultDate(21),
  end_date: defaultDate(24),
  travelers: 2,
  budget: 30000,
  currency: "INR",
  interests: ["Culture"],
  travel_style: "balanced",
  transport_preference: "public transport",
  accommodation_preference: "hotel",
};

export default function TripWizard() {
  const [form, setForm] = useState(INITIAL);
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const toggleInterest = (interest) => update("interests", form.interests.includes(interest)
    ? form.interests.filter((item) => item !== interest)
    : [...form.interests, interest]);

  const goNext = () => {
    if (step === 0 && !form.destination.trim()) return setError("Add a destination to continue.");
    if (step === 1) {
      if (!form.start_date || !form.end_date || form.start_date > form.end_date) return setError("Choose valid trip dates.");
      const days = Math.floor((new Date(`${form.end_date}T00:00:00`) - new Date(`${form.start_date}T00:00:00`)) / 86400000) + 1;
      if (days > 30) return setError("Trips can be up to 30 days long.");
    }
    setError("");
    setStep((current) => Math.min(current + 1, STEPS.length - 1));
  };

  const createTrip = async () => {
    setSaving(true);
    setError("");
    try {
      const { data } = await api.post("/trips", form);
      navigate(`/trips/${data.trip.id}`, { state: { created: true } });
    } catch (requestError) {
      setError(requestError.response?.data?.message || "Your trip could not be saved. Please try again.");
      setSaving(false);
    }
  };

  return (
    <div className="wizard-page">
      <Link className="back-link" to="/dashboard">← Back to your trips</Link>
      <div className="wizard-heading"><span className="eyebrow">YOUR NEXT ADVENTURE</span><h1>Let’s make a plan.</h1><p>A few thoughtful details are all we need to get started.</p></div>
      <div className="wizard-progress" aria-label={`Step ${step + 1} of ${STEPS.length}`}>
        {STEPS.map((label, index) => <div className={`wizard-step ${index === step ? "active" : ""} ${index < step ? "complete" : ""}`} key={label}><span>{index < step ? "✓" : `0${index + 1}`}</span><small>{label}</small></div>)}
      </div>
      <section className="wizard-card">
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {step === 0 && <div className="wizard-step-content"><span className="step-icon">⌖</span><span className="eyebrow">FIRST THINGS FIRST</span><h2>Where would you like to go?</h2><p>Start with a city. Place suggestions are available for Jaipur and Paris.</p>
          <label className="field">Destination<input autoFocus value={form.destination} onChange={(event) => update("destination", event.target.value)} placeholder="Try Jaipur or Paris" maxLength={150} /></label></div>}
        {step === 1 && <div className="wizard-step-content"><span className="step-icon">◷</span><span className="eyebrow">THE DETAILS</span><h2>When are you heading out?</h2><div className="form-grid">
          <label className="field">Starting from<input value={form.start_location} onChange={(event) => update("start_location", event.target.value)} placeholder="Your city (optional)" maxLength={150} /></label>
          <label className="field">Travelers<input type="number" min="1" max="20" value={form.travelers} onChange={(event) => update("travelers", event.target.value)} /></label>
          <label className="field">Start date<input type="date" value={form.start_date} onChange={(event) => update("start_date", event.target.value)} /></label>
          <label className="field">End date<input type="date" min={form.start_date} value={form.end_date} onChange={(event) => update("end_date", event.target.value)} /></label>
        </div></div>}
        {step === 2 && <div className="wizard-step-content"><span className="step-icon">◎</span><span className="eyebrow">SPEND WITH INTENTION</span><h2>What feels comfortable?</h2><p>We’ll make a starter estimate you can change whenever you like.</p>
          <div className="form-grid"><label className="field">Total trip budget<input type="number" min="1" value={form.budget} onChange={(event) => update("budget", event.target.value)} /></label><label className="field">Currency<select value={form.currency} onChange={(event) => update("currency", event.target.value)}>{["INR", "USD", "EUR", "GBP", "JPY"].map((currency) => <option key={currency}>{currency}</option>)}</select></label></div></div>}
        {step === 3 && <div className="wizard-step-content"><span className="step-icon">✳</span><span className="eyebrow">YOUR KIND OF TRIP</span><h2>What do you love doing?</h2><p>Choose as many as you like. It helps rank the sample place suggestions.</p>
          <div className="interest-list">{INTERESTS.map((interest) => <button type="button" key={interest} className={`interest-chip ${form.interests.includes(interest) ? "selected" : ""}`} aria-pressed={form.interests.includes(interest)} onClick={() => toggleInterest(interest)}>{interest}</button>)}</div>
          <div className="form-grid preference-grid"><label className="field">Travel style<select value={form.travel_style} onChange={(event) => update("travel_style", event.target.value)}>{["budget", "balanced", "comfort", "luxury"].map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}</select></label>
            <label className="field">Getting around<select value={form.transport_preference} onChange={(event) => update("transport_preference", event.target.value)}>{["walking", "public transport", "car", "cab"].map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}</select></label>
            <label className="field">Stay preference<select value={form.accommodation_preference} onChange={(event) => update("accommodation_preference", event.target.value)}>{["hostel", "budget hotel", "hotel", "luxury hotel"].map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}</select></label></div></div>}
        {step === 4 && <div className="wizard-step-content"><span className="step-icon">✈</span><span className="eyebrow">LOOKING GOOD</span><h2>Your trip at a glance.</h2><p>Everything here can be edited later.</p><div className="review-grid">
          {[["Destination", form.destination], ["Starting from", form.start_location || "Not specified"], ["Dates", `${form.start_date} — ${form.end_date}`], ["Travelers", form.travelers], ["Budget", `${form.currency} ${Number(form.budget).toLocaleString()}`], ["Interests", form.interests.join(", ") || "Open to anything"], ["Travel style", form.travel_style], ["Transport", form.transport_preference], ["Accommodation", form.accommodation_preference]].map(([label, value]) => <div className="review-item" key={label}><small>{label}</small><strong>{value}</strong></div>)}</div>
          <div className="sample-note">Place suggestions and estimated costs are sample planning data, not live listings or quotes.</div></div>}
        <div className="wizard-actions">{step > 0 ? <button className="button button-quiet" onClick={() => { setError(""); setStep(step - 1); }}>← Back</button> : <span />}
          {step < STEPS.length - 1 ? <button className="button button-primary" onClick={goNext}>Continue <span>→</span></button> : <button className="button button-primary" onClick={createTrip} disabled={saving}>{saving ? "Saving your trip…" : "Create my trip"} {!saving && <span>→</span>}</button>}</div>
      </section>
    </div>
  );
}
