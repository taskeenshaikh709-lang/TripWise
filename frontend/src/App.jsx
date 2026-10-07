import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import TripDetail from "./pages/TripDetail";
import TripWizard from "./pages/TripWizard";
import ProtectedRoute from "./routes/ProtectedRoute";

function NotFound() {
  return <main className="not-found"><span className="eyebrow">OFF THE MAP</span><h1>This page took a detour.</h1><p>The link may be old, or the page may have moved.</p><a className="button button-primary" href="/">Go to TripWise</a></main>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/trips" element={<Dashboard />} />
          <Route path="/trips/new" element={<TripWizard />} />
          <Route path="/trips/:tripId" element={<TripDetail />} />
          <Route path="/trips/:tripId/:section" element={<TripDetail />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
