import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, NavLink, useLocation, useNavigate, useParams } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import TripMap from "../components/TripMap";
import api from "../services/api";

const CATEGORIES = ["food", "transport", "hotel", "activities", "shopping", "other"];
const PALETTE = ["#6265e9", "#ffbd68", "#8ac9ad", "#ed9380", "#989be7", "#c6c7d2"];

function money(amount, currency) {
  try {
    return new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount || 0);
  } catch {
    return `${currency} ${Number(amount || 0).toLocaleString()}`;
  }
}

function Overview({ trip, refresh, setNotice }) {
  const [busy, setBusy] = useState("");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    start_location: trip.start_location || "",
    start_date: trip.start_date,
    end_date: trip.end_date,
    travelers: trip.travelers,
    budget: trip.budget,
  });
  const navigate = useNavigate();

  const generate = async (path, label) => {
    setBusy(label);
    setNotice("");
    try {
      await api.post(`/trips/${trip.id}/${path}`);
      await refresh();
      setNotice("Your plan is ready. Take a look at the day-by-day itinerary.");
      navigate(`/trips/${trip.id}/itinerary`);
    } catch (error) {
      setNotice(error.response?.data?.message || "The itinerary could not be created.");
    } finally {
      setBusy("");
    }
  };

  const updateTrip = async (event) => {
    event.preventDefault();
    setBusy("save");
    setNotice("");
    try {
      const { data } = await api.put(`/trips/${trip.id}`, form);
      setEditing(false);
      await refresh();
      setNotice(data.message || "Trip details saved.");
    } catch (error) {
      setNotice(error.response?.data?.message || "Trip details could not be saved.");
    } finally {
      setBusy("");
    }
  };

  const duplicate = async () => {
    setBusy("duplicate");
    try {
      const { data } = await api.post(`/trips/${trip.id}/duplicate`);
      navigate(`/trips/${data.trip.id}`);
    } catch (error) {
      setNotice(error.response?.data?.message || "The trip could not be duplicated.");
    } finally {
      setBusy("");
    }
  };

  const removeTrip = async () => {
    if (!window.confirm(`Delete your ${trip.destination} trip and its expenses? This cannot be undone.`)) return;
    setBusy("delete");
    try {
      await api.delete(`/trips/${trip.id}`);
      navigate("/trips");
    } catch (error) {
      setNotice(error.response?.data?.message || "The trip could not be deleted.");
      setBusy("");
    }
  };

  const downloadPdf = async () => {
    setBusy("pdf");
    try {
      const response = await api.get(`/trips/${trip.id}/export.pdf`, { responseType: "blob" });
      const href = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.download = `tripwise-${trip.id}.pdf`;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(href), 1000);
      setNotice("Your trip plan has been downloaded.");
    } catch (error) {
      setNotice(error.response?.data?.message || "Your PDF could not be downloaded.");
    } finally {
      setBusy("");
    }
  };

  return (
    <>
      <section className="trip-overview-hero">
        <div><span className="eyebrow">YOUR NEXT CHAPTER</span><h2>{trip.destination}</h2><p>{trip.start_date} — {trip.end_date} <span>·</span> {trip.travelers} {trip.travelers === 1 ? "traveler" : "travelers"}</p><span className="trip-hero-budget">Your budget <strong>{money(trip.budget, trip.currency)}</strong></span></div>
        <div className="overview-actions"><button className="button button-primary" onClick={() => generate(trip.itinerary?.length ? "reoptimize" : "generate", trip.itinerary?.length ? "optimizing" : "generating")} disabled={Boolean(busy)}>{busy === "generating" ? "Planning…" : busy === "optimizing" ? "Reworking…" : trip.itinerary?.length ? "↻ Re-optimize" : "✳ Build my itinerary"}</button>
          <button className="button button-light" onClick={downloadPdf} disabled={Boolean(busy)}>{busy === "pdf" ? "Preparing…" : "↓ Download plan"}</button></div>
      </section>
      {trip.budget_summary?.over_budget && <div className="alert alert-warning">This starter estimate is above your budget. Review the category breakdown and adjust your plan.</div>}
      <div className="overview-stat-grid">
        <article className="overview-stat"><span>TRIP LENGTH</span><strong>{trip.days} days</strong><small>With room to explore</small></article>
        <article className="overview-stat"><span>ESTIMATED SPEND</span><strong>{money(trip.budget_summary?.estimated_total, trip.currency)}</strong><small>Planning estimate</small></article>
        <article className="overview-stat"><span>SPENT SO FAR</span><strong>{money(trip.budget_summary?.actual_total, trip.currency)}</strong><small>{money(trip.budget_summary?.remaining, trip.currency)} remaining</small></article>
        <article className="overview-stat"><span>PLACES PLANNED</span><strong>{trip.itinerary?.reduce((sum, day) => sum + day.items.length, 0) || 0}</strong><small>Across your itinerary</small></article>
      </div>
      <div className="section-title-row trip-section-title"><div><span className="eyebrow">YOUR TRIP, AT A GLANCE</span><h2>Make it yours</h2></div><button className="text-button" onClick={() => setEditing((current) => !current)}>{editing ? "Close editor" : "Edit trip details →"}</button></div>
      {editing && <form className="card form-grid edit-trip-form" onSubmit={updateTrip}>
        <label className="field">Starting from<input value={form.start_location} onChange={(event) => setForm({ ...form, start_location: event.target.value })} /></label>
        <label className="field">Travelers<input type="number" min="1" max="20" value={form.travelers} onChange={(event) => setForm({ ...form, travelers: event.target.value })} /></label>
        <label className="field">Start date<input type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} /></label>
        <label className="field">End date<input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} /></label>
        <label className="field">Budget ({trip.currency})<input type="number" min="1" value={form.budget} onChange={(event) => setForm({ ...form, budget: event.target.value })} /></label>
        <div className="form-submit"><button className="button button-primary" disabled={Boolean(busy)}>{busy === "save" ? "Saving…" : "Save trip details"}</button></div>
      </form>}
      <div className="quick-links">
        <Link to={`/trips/${trip.id}/itinerary`}><span>↗</span><strong>Day-by-day plan</strong><small>See where each day takes you</small></Link>
        <Link to={`/trips/${trip.id}/budget`}><span>◎</span><strong>Budget & insights</strong><small>See estimates and spending</small></Link>
        <Link to={`/trips/${trip.id}/map`}><span>⌖</span><strong>Places on a map</strong><small>Find your stops around town</small></Link>
        <Link to={`/trips/${trip.id}/expenses`}><span>＋</span><strong>Track expenses</strong><small>Keep your spending together</small></Link>
      </div>
      <section className="planning-card"><div><span className="eyebrow">A FEW HELPFUL THINGS</span><h3>Make a good plan even better.</h3><p>Confirm opening hours and admission directly with venues. Map distances are straight-line estimates, not turn-by-turn routes.</p></div><div className="planning-actions"><Link className="text-button" to={`/trips/${trip.id}/hotels`}>Sample hotel ideas →</Link><Link className="text-button" to={`/trips/${trip.id}/weather`}>Weather availability →</Link></div></section>
      <div className="danger-zone"><button className="text-button" onClick={duplicate} disabled={Boolean(busy)}>{busy === "duplicate" ? "Duplicating…" : "Duplicate this trip"}</button><button className="text-button danger-text" onClick={removeTrip} disabled={Boolean(busy)}>{busy === "delete" ? "Deleting…" : "Delete trip"}</button></div>
    </>
  );
}

function Itinerary({ trip, refresh, setNotice }) {
  const [busy, setBusy] = useState(false);
  const generate = async () => {
    setBusy(true);
    try {
      await api.post(`/trips/${trip.id}/generate`);
      await refresh();
      setNotice("Your itinerary has been generated from the available sample catalog.");
    } catch (error) {
      setNotice(error.response?.data?.message || "The itinerary could not be generated.");
    } finally {
      setBusy(false);
    }
  };

  return <section className="content-card">
    <div className="section-title-row"><div><span className="eyebrow">A THOUGHTFUL STARTING POINT</span><h2>Your day-by-day plan</h2></div><button className="button button-primary" onClick={generate} disabled={busy}>{busy ? "Working…" : trip.itinerary?.length ? "↻ Re-optimize" : "Build itinerary"}</button></div>
    {!trip.itinerary?.length ? <div className="empty-inline"><strong>No itinerary yet.</strong><p>Build a plan from our sample place catalog for this destination.</p></div> : <>
      {trip.itinerary.some((day) => day.items.some((item) => item.sample_data)) && <div className="sample-note">Place details and admission costs are sample planning data. Check live opening times and prices with the venue.</div>}
      <div className="itinerary-days">{trip.itinerary.map((day) => <article className="itinerary-day" key={day.id}><div className="day-label"><span>DAY {String(day.day_number).padStart(2, "0")}</span><strong>{day.date}</strong></div>
        {day.items.length === 0 ? <p className="empty-inline">Leave this day open for your own discoveries.</p> : <div className="timeline">{day.items.map((item) => <div className="timeline-item" key={item.id}><div className="timeline-time">{item.start_time}<small>{item.end_time}</small></div><span className="timeline-dot" /><div className="timeline-copy"><div className="timeline-title"><strong>{item.place}</strong><span>{item.category}</span></div><p>{item.description}</p><small>{item.travel_time ? `About ${item.travel_time} min estimated travel · ${item.distance} km straight-line` : "First stop of the day"}{item.estimated_cost ? ` · Est. ${money(item.estimated_cost, item.currency)}` : ""}</small></div></div>)}</div>}</article>)}</div>
      <div className="sample-note">Estimated travel time is derived from straight-line distance and a typical mode speed; actual route and traffic may differ.</div>
    </>}
  </section>;
}

function Budget({ trip }) {
  const summary = trip.budget_summary || { categories: [], estimated_total: 0, actual_total: 0, remaining: trip.budget, percentage_used: 0, over_budget: false };
  const colors = summary.categories.map((entry, index) => ({ ...entry, fill: PALETTE[index % PALETTE.length] }));
  const categories = summary.categories;
  const spentByCategory = trip.expenses.reduce((totals, expense) => {
    totals[expense.category] = (totals[expense.category] || 0) + expense.amount;
    return totals;
  }, {});
  const largestCategory = [...categories].sort((a, b) => b.estimated - a.estimated)[0];
  const daysTravel = trip.itinerary?.map((day) => ({ day: day.day_number, minutes: day.items.reduce((sum, item) => sum + item.travel_time, 0) })) || [];
  const longestTravelDay = [...daysTravel].sort((a, b) => b.minutes - a.minutes)[0];
  const insights = [
    `You have used ${summary.percentage_used}% of your budget on recorded expenses.`,
    largestCategory ? `${largestCategory.name} is your largest current estimate at ${money(largestCategory.estimated, trip.currency)}.` : "Generate an itinerary to add activity estimates to this breakdown.",
    longestTravelDay?.minutes ? `Day ${longestTravelDay.day} has the most estimated travel time (${longestTravelDay.minutes} min).` : "Travel-time insights appear after you create an itinerary.",
  ];
  return <div className="budget-page"><section className="budget-summary-card">
    <div><span className="eyebrow">YOUR TRIP BUDGET</span><h2>{money(trip.budget, trip.currency)}</h2><p>Total amount set aside</p></div>
    <div className="budget-summary-stats"><div><small>Estimated plan</small><strong>{money(summary.estimated_total, trip.currency)}</strong></div><div><small>Recorded spending</small><strong>{money(summary.actual_total, trip.currency)}</strong></div><div><small>Budget left</small><strong>{money(summary.remaining, trip.currency)}</strong></div></div>
    <div className="spending-track"><span style={{ width: `${Math.min(summary.percentage_used, 100)}%` }} /></div><small>{summary.percentage_used}% of your budget recorded as spent</small>
  </section>
    {summary.over_budget && <div className="alert alert-warning">Your current estimates are above your trip budget. Consider adjusting your stay or activities.</div>}
    <div className="budget-content-grid"><section className="content-card"><div className="card-heading"><span className="eyebrow">THE BREAKDOWN</span><h3>Estimated by category</h3></div>
      {categories.length ? <><div className="chart-layout"><div className="budget-chart"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={colors} dataKey="estimated" nameKey="name" innerRadius="64%" outerRadius="92%" paddingAngle={3} stroke="none">{colors.map((item, index) => <Cell key={item.name} fill={item.fill} />)}</Pie><Tooltip formatter={(value) => money(value, trip.currency)} /></PieChart></ResponsiveContainer><div className="chart-center"><strong>{money(summary.estimated_total, trip.currency)}</strong><small>estimated</small></div></div>
        <div className="category-legend">{colors.map((category) => <div className="category-row" key={category.name}><span className="category-dot" style={{ background: category.fill }} /><span>{category.name}</span><strong>{money(category.estimated, trip.currency)}</strong></div>)}</div></div>
      <p className="chart-footnote">Starting estimates reflect your accommodation and transport preferences plus planned sample activities. Recorded expenses determine actual spending.</p></> : <div className="empty-inline">Budget estimates will show here.</div>}
    </section><section className="content-card"><div className="card-heading"><span className="eyebrow">A QUICK READ</span><h3>Useful things to know</h3></div>{insights.map((insight) => <div className="insight-row" key={insight}><span>✳</span><p>{insight}</p></div>)}
      <Link className="inline-link" to={`/trips/${trip.id}/expenses`}>Review your expenses →</Link>
    </section></div>
    <section className="content-card expense-categories-card"><div className="card-heading"><span className="eyebrow">WHAT YOU’VE SPENT</span><h3>Recorded by category</h3></div>
      {CATEGORIES.some((category) => spentByCategory[category]) ? <div className="category-legend expense-category-list">{CATEGORIES.filter((category) => spentByCategory[category]).map((category, index) => <div className="category-row" key={category}><span className="category-dot" style={{ background: PALETTE[index % PALETTE.length] }} /><span>{category[0].toUpperCase() + category.slice(1)}</span><strong>{money(spentByCategory[category], trip.currency)}</strong></div>)}</div> : <p className="muted">Add your first expense to see where your spending goes.</p>}
    </section>
  </div>;
}

function Expenses({ trip, refresh, setNotice }) {
  const [form, setForm] = useState({ category: "food", description: "", amount: "", date: new Date().toISOString().slice(0, 10), notes: "" });
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const entries = trip.expenses || [];

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      const route = `/trips/${trip.id}/expenses${editing ? `/${editing}` : ""}`;
      if (editing) await api.put(route, form);
      else await api.post(route, form);
      setForm({ category: "food", description: "", amount: "", date: new Date().toISOString().slice(0, 10), notes: "" });
      setEditing(null);
      await refresh();
      setNotice(editing ? "Expense updated." : "Expense added.");
    } catch (error) {
      setNotice(error.response?.data?.message || "The expense could not be saved.");
    } finally {
      setBusy(false);
    }
  };

  const edit = (expense) => {
    setEditing(expense.id);
    setForm({ category: expense.category, description: expense.description, amount: expense.amount, date: expense.date, notes: expense.notes || "" });
  };

  const remove = async (id) => {
    setBusy(true);
    try {
      await api.delete(`/trips/${trip.id}/expenses/${id}`);
      await refresh();
      setNotice("Expense removed.");
    } catch (error) {
      setNotice(error.response?.data?.message || "The expense could not be removed.");
    } finally {
      setBusy(false);
    }
  };

  return <div className="expenses-layout"><section className="content-card expenses-list-card"><div className="section-title-row"><div><span className="eyebrow">KEEP THE LITTLE THINGS TOGETHER</span><h2>Trip expenses</h2></div><strong className="expense-total">{money(trip.budget_summary?.actual_total, trip.currency)}</strong></div>
    {!entries.length ? <div className="empty-inline"><strong>No expenses recorded yet.</strong><p>Add a meal, ticket or ride to start keeping track.</p></div> : <div className="expense-table-wrap"><table className="expense-table"><thead><tr><th>Expense</th><th>Category</th><th>Date</th><th>Amount</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{entries.map((expense) => <tr key={expense.id}><td><strong>{expense.description}</strong>{expense.notes && <small>{expense.notes}</small>}</td><td><span className="category-pill">{expense.category}</span></td><td>{expense.date}</td><td className="expense-amount">{money(expense.amount, trip.currency)}</td><td><button className="row-action" onClick={() => edit(expense)}>Edit</button><button className="row-action danger-text" onClick={() => remove(expense.id)} disabled={busy}>Delete</button></td></tr>)}</tbody></table></div>}
  </section>
    <form className="content-card expense-form" onSubmit={submit}><span className="eyebrow">{editing ? "MAKE AN UPDATE" : "LOG A PURCHASE"}</span><h3>{editing ? "Edit expense" : "Add an expense"}</h3>
      <label className="field">What was it for?<input required maxLength={200} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Dinner with a view" /></label>
      <label className="field">Category<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>{CATEGORIES.map((category) => <option key={category} value={category}>{category[0].toUpperCase() + category.slice(1)}</option>)}</select></label>
      <div className="form-grid"><label className="field">Amount ({trip.currency})<input required type="number" min="0.01" step="0.01" value={form.amount} onChange={(event) => setForm({ ...form, amount: event.target.value })} /></label><label className="field">Date<input required type="date" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} /></label></div>
      <label className="field">Note <span className="optional-text">optional</span><input maxLength={500} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="A detail to remember" /></label>
      <button className="button button-primary button-wide" disabled={busy}>{busy ? "Saving…" : editing ? "Save changes" : "Add expense"} <span>→</span></button>
      {editing && <button type="button" className="text-button cancel-edit" onClick={() => { setEditing(null); setForm({ category: "food", description: "", amount: "", date: new Date().toISOString().slice(0, 10), notes: "" }); }}>Cancel editing</button>}
    </form>
  </div>;
}

function Hotels({ trip, refresh, setNotice }) {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api.get(`/trips/${trip.id}/hotels`).then(({ data }) => setHotels(data.hotels))
      .catch((requestError) => setError(requestError.response?.data?.message || "Hotel ideas could not be loaded."))
      .finally(() => setLoading(false));
  }, [trip.id]);

  const select = async (hotel) => {
    try {
      await api.post(`/trips/${trip.id}/hotels/${hotel.id}`);
      await refresh();
      setNotice(`${hotel.name} selected. The accommodation estimate has been updated.`);
    } catch (requestError) {
      setNotice(requestError.response?.data?.message || "This hotel could not be selected.");
    }
  };
  const removeSelected = async () => {
    try {
      await api.delete(`/trips/${trip.id}/hotels`);
      await refresh();
      setNotice("Selected sample hotel removed. Accommodation estimates now use the preference-based allowance.");
    } catch (requestError) {
      setNotice(requestError.response?.data?.message || "The selected hotel could not be removed.");
    }
  };
  return <section className="content-card"><div className="section-title-row"><div><span className="eyebrow">A PLACE TO COME BACK TO</span><h2>Sample hotel ideas</h2></div></div>
    {trip.selected_hotel && <p className="selected-hotel-note">Selected: {trip.selected_hotel.name} · <button className="text-button" onClick={removeSelected}>Remove selection</button></p>}
    <div className="sample-note">These are structured sample listings for planning demonstrations—not live availability or booking offers. Check directly with providers.</div>
    {error && <div className="alert alert-error">{error}</div>}
    {loading ? <div className="loading-card">Gathering sample stays…</div> : !hotels.length ? <div className="empty-inline">No sample hotel data is available for {trip.destination} yet.</div> :
      <div className="hotel-grid">{hotels.map((hotel) => <article className={`hotel-card ${trip.selected_hotel?.id === hotel.id ? "hotel-selected" : ""}`} key={hotel.id}>
        <div className="hotel-art"><span>⌂</span><small>{hotel.rating.toFixed(1)} ★</small></div>
        <div className="hotel-card-body"><span className="eyebrow">{trip.selected_hotel?.id === hotel.id ? "YOUR SELECTED STAY" : "SAMPLE IDEA"}</span><h3>{hotel.name}</h3><p>{hotel.amenities.join(" · ")}</p>
          <strong>{money(hotel.price_per_night, hotel.currency)} <small>/ night · approx. {money(hotel.estimated_stay, hotel.currency)} total</small></strong>
          {trip.currency !== hotel.currency && <small className="currency-warning">Trip currency is {trip.currency}. No exchange rate is assumed.</small>}
          <button className={`button ${trip.selected_hotel?.id === hotel.id ? "button-light" : "button-primary"} button-wide`} disabled={trip.selected_hotel?.id === hotel.id || trip.currency !== hotel.currency} onClick={() => select(hotel)}>{trip.selected_hotel?.id === hotel.id ? "Selected" : trip.currency !== hotel.currency ? `Requires ${hotel.currency} trip currency` : "Choose this sample"}</button></div>
      </article>)}</div>}
  </section>;
}

function Weather({ trip }) {
  const [weather, setWeather] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api.get(`/trips/${trip.id}/weather`).then(({ data }) => setWeather(data))
      .catch((requestError) => setError(requestError.response?.data?.message || "Weather availability could not be checked."));
  }, [trip.id]);
  return <section className="content-card weather-card"><span className="weather-icon">☼</span><span className="eyebrow">A NOTE ABOUT THE SKY</span><h2>Weather, when it’s real.</h2>
    {error ? <div className="alert alert-error">{error}</div> : weather ? <><p className="weather-message">{weather.message}</p><div className="sample-note">TripWise does not invent forecasts. Check a trusted weather provider closer to your dates.</div></> : <p className="muted">Checking provider availability…</p>}
  </section>;
}

export default function TripDetail() {
  const { tripId, section } = useParams();
  const location = useLocation();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(location.state?.created ? "Your trip is ready. Build an itinerary when you’re ready." : "");
  const refresh = useCallback(async () => {
    const [tripResponse, expensesResponse] = await Promise.all([
      api.get(`/trips/${tripId}`),
      api.get(`/trips/${tripId}/expenses`),
    ]);
    setTrip({ ...tripResponse.data.trip, expenses: expensesResponse.data.expenses });
  }, [tripId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setTrip(null);
    Promise.all([api.get(`/trips/${tripId}`), api.get(`/trips/${tripId}/expenses`)])
      .then(([tripResponse, expensesResponse]) => {
        if (active) setTrip({ ...tripResponse.data.trip, expenses: expensesResponse.data.expenses });
      })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.message || "Trip details could not be loaded.");
      })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [tripId]);

  const reload = refresh;

  const tab = useMemo(() => section || "overview", [section]);
  if (loading) return <div className="loading-card">Opening your trip…</div>;
  if (error) return <div className="alert alert-error" role="alert">{error} <Link to="/trips">Back to trips</Link></div>;
  if (!trip) return null;

  const titleMap = { overview: "Overview", itinerary: "Itinerary", budget: "Budget", expenses: "Expenses", map: "Map", hotels: "Hotels", weather: "Weather" };
  return <div className="trip-detail-page">
    <Link className="back-link" to="/trips">← All trips</Link>
    <div className="trip-detail-heading"><div><span className="eyebrow">{trip.destination.toUpperCase()} · {trip.start_date}</span><h1>{titleMap[tab] || "Your trip"}</h1></div><span className="trip-detail-destination">{trip.destination}</span></div>
    <nav className="trip-tabs" aria-label="Trip sections">
      {[["", "Overview"], ["itinerary", "Itinerary"], ["budget", "Budget"], ["expenses", "Expenses"], ["map", "Map"], ["hotels", "Hotels"], ["weather", "Weather"]].map(([path, label]) => <NavLink end={!path} className={({ isActive }) => isActive ? "active" : ""} to={`/trips/${trip.id}${path ? `/${path}` : ""}`} key={label}>{label}</NavLink>)}
    </nav>
    {notice && <div className="notice-banner" role="status"><span>✳</span><p>{notice}</p><button aria-label="Dismiss notice" onClick={() => setNotice("")}>×</button></div>}
    {tab === "overview" && <Overview trip={trip} refresh={reload} setNotice={setNotice} />}
    {tab === "itinerary" && <Itinerary trip={trip} refresh={reload} setNotice={setNotice} />}
    {tab === "budget" && <Budget trip={trip} />}
    {tab === "expenses" && <Expenses trip={trip} refresh={reload} setNotice={setNotice} />}
    {tab === "map" && <section className="content-card"><div className="section-title-row"><div><span className="eyebrow">OPENSTREETMAP</span><h2>Your trip, on the map</h2></div></div>{trip.itinerary?.length ? <TripMap days={trip.itinerary} /> : <div className="empty-inline"><strong>Build an itinerary to see places on your map.</strong><p>Place coordinates come from the sample catalog and are not live navigation guidance.</p><Link className="inline-link" to={`/trips/${trip.id}/itinerary`}>Go to itinerary →</Link></div>}</section>}
    {tab === "hotels" && <Hotels trip={trip} refresh={reload} setNotice={setNotice} />}
    {tab === "weather" && <Weather trip={trip} />}
  </div>;
}
