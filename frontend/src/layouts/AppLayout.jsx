import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AppLayout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const logout = () => {
    signOut();
    navigate("/");
  };

  return (
    <div className="workspace">
      <aside className="sidebar">
        <NavLink className="brand" to="/dashboard">
          <span className="brand-mark">T</span>
          <span>tripwise</span>
        </NavLink>
        <p className="sidebar-label">WORKSPACE</p>
        <nav className="side-nav" aria-label="Main navigation">
          <NavLink to="/dashboard">Overview</NavLink>
          <NavLink to="/trips">My trips</NavLink>
          <NavLink to="/trips/new" className="new-trip-link">＋ Plan a trip</NavLink>
        </nav>
        <div className="sidebar-bottom">
          <div className="user-chip">
            <span className="avatar">{user?.name?.[0]?.toUpperCase() || "T"}</span>
            <span className="user-info"><strong>{user?.name}</strong><small>Traveler</small></span>
          </div>
          <NavLink to="/profile" className="mobile-profile-link">Profile</NavLink>
          <button className="text-button signout-button" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <div className="workspace-main">
        <header className="topbar">
          <span className="topbar-caption">YOUR PERSONAL TRAVEL STUDIO</span>
          <NavLink to="/profile" className="profile-link">Profile</NavLink>
        </header>
        <main className="page-content"><Outlet /></main>
      </div>
    </div>
  );
}
