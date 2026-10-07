import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function AuthForm({ mode }) {
  const isRegister = mode === "register";
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post(`/auth/${mode}`, form);
      signIn(data);
      navigate("/dashboard", { replace: true });
    } catch (requestError) {
      setError(requestError.response?.data?.message || "We couldn't reach the server. Check that the API is running and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-aside">
        <Link className="brand brand-light" to="/"><span className="brand-mark">T</span><span>tripwise</span></Link>
        <div className="auth-aside-copy">
          <span className="eyebrow">MORE THAN A MAP</span>
          <h1>Make room for the moments that matter.</h1>
          <p>Bring your ideas, itinerary and travel budget together in one calm place.</p>
          <div className="auth-trip-card">
            <span className="trip-card-top">YOUR NEXT CHAPTER</span>
            <strong>Somewhere new.</strong>
            <span>Thoughtful plans. Unplanned magic.</span>
          </div>
        </div>
        <span className="auth-aside-foot">Plan thoughtfully. Go freely.</span>
      </div>
      <section className="auth-panel">
        <div className="auth-form-wrap">
          <span className="eyebrow">{isRegister ? "START YOUR JOURNEY" : "WELCOME BACK"}</span>
          <h2>{isRegister ? "Create your account" : "Good to see you again"}</h2>
          <p className="muted">{isRegister ? "A little planning goes a long way." : "Pick up right where you left off."}</p>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <form className="form-stack" onSubmit={submit}>
            {isRegister && (
              <label className="field">Your name
                <input required maxLength={100} autoComplete="name" value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Alex Morgan" />
              </label>
            )}
            <label className="field">Email address
              <input required type="email" autoComplete="email" value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder="you@example.com" />
            </label>
            <label className="field">Password
              <input required type="password" minLength={isRegister ? 8 : undefined} maxLength={128}
                autoComplete={isRegister ? "new-password" : "current-password"} value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
                placeholder={isRegister ? "At least 8 characters" : "Enter your password"} />
            </label>
            <button className="button button-primary button-wide" disabled={loading}>
              {loading ? "Please wait…" : isRegister ? "Create account" : "Sign in"}
              {!loading && <span aria-hidden="true">→</span>}
            </button>
          </form>
          <p className="auth-switch">
            {isRegister ? "Already have an account?" : "New to TripWise?"}{" "}
            <Link to={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create an account"}</Link>
          </p>
          <Link className="back-link" to="/">← Back to TripWise</Link>
        </div>
      </section>
    </main>
  );
}
