import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { user, signOut } = useAuth();
  return <section className="profile-page">
    <span className="eyebrow">YOUR DETAILS</span><h1>A little about you.</h1><p className="muted">Your account details stay private to your TripWise account.</p>
    <div className="content-card profile-card"><span className="profile-avatar">{user?.name?.[0]?.toUpperCase()}</span><div><small>NAME</small><strong>{user?.name}</strong></div><div><small>EMAIL ADDRESS</small><strong>{user?.email}</strong></div><div><small>ACCOUNT</small><strong>Traveler</strong></div></div>
    <button className="button button-light" onClick={signOut}>Sign out of TripWise</button>
  </section>;
}
