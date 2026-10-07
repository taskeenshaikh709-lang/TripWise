import { useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function TripMap({ days }) {
  const [selectedDay, setSelectedDay] = useState("all");
  const allItems = days.flatMap((day) => day.items.map((item) => ({ ...item, day_number: day.day_number })));
  const items = selectedDay === "all" ? allItems : allItems.filter((item) => item.day_number === Number(selectedDay));
  const center = useMemo(() => {
    const located = items.filter((item) => item.latitude != null && item.longitude != null);
    if (!located.length) return [20, 0];
    return [
      located.reduce((sum, item) => sum + item.latitude, 0) / located.length,
      located.reduce((sum, item) => sum + item.longitude, 0) / located.length,
    ];
  }, [items]);

  if (allItems.every((item) => item.latitude == null || item.longitude == null)) {
    return <div className="empty-inline">There are no mapped coordinates in this itinerary yet.</div>;
  }

  return (
    <div className="map-wrap">
      <div className="map-toolbar"><div><strong>Places on your plan</strong><small>Locations from the sample place catalog</small></div>
        <label className="map-filter">Show<select value={selectedDay} onChange={(event) => setSelectedDay(event.target.value)}><option value="all">All days</option>{days.map((day) => <option value={day.day_number} key={day.id}>Day {day.day_number}</option>)}</select></label></div>
      <MapContainer center={center} zoom={12} scrollWheelZoom={false} className="leaflet-map" key={`${selectedDay}-${center.join(",")}`}>
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {items.filter((item) => item.latitude != null && item.longitude != null).map((item, index) => (
          <CircleMarker key={`${item.id}-${item.day_number}`} center={[item.latitude, item.longitude]} radius={9} pathOptions={{ color: "#595be8", fillColor: index % 2 ? "#ffc477" : "#6569f0", fillOpacity: 0.92 }}>
            <Popup><strong>{item.place}</strong><br />Day {item.day_number} · {item.start_time}<br />{item.category}</Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      <p className="map-disclaimer">Map pins show place coordinates. This is not a routed navigation map; the displayed travel times are estimates.</p>
    </div>
  );
}
