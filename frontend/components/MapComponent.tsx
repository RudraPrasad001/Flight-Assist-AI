// Map types that match your backend map_data payload
"use client";
import 'leaflet/dist/leaflet.css'; 
type MapAirport = {
  code?: string | null;
  iata?: string | null;
  icao?: string | null;
  name: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
};

type DirectRoute = {
  route_id: number;
  src: string;
  dst: string;
  src_city: string;
  src_country: string;
  dst_city: string;
  dst_country: string;
  airline: string;
  airline_code: string;
  equipment: string;
  stops: number;
  type: 'direct';
};

type LayoverRoute = {
  src: string;
  hub: string;
  dst: string;
  hub_name: string;
  hub_city: string;
  hub_country: string;
  hub_latitude: number | null;
  hub_longitude: number | null;
  leg1_airline: string;
  leg2_airline: string;
  leg1_equipment: string;
  leg2_equipment: string;
  leg1_rid: number;
  leg2_rid: number;
  stops: number;
  type: 'layover';
};

type MapData = {
  airports: MapAirport[];
  direct_routes: DirectRoute[];
  layover_routes: LayoverRoute[];
};

// ------------- Map widget -------------
import { MapContainer, TileLayer, Polyline, Popup, useMap, Marker } from 'react-leaflet';
import L, { LatLngBoundsExpression } from 'leaflet';
import { useMemo, useEffect } from 'react';

// Use a simple DivIcon so we don’t need Leaflet’s image assets
const airportIcon = (label: string) =>
  L.divIcon({
    className: 'airport-icon',
    html: `<div style="background:#0ea5e9;color:#fff;padding:3px 6px;border-radius:6px;font-size:11px;font-weight:700">${label}</div>`,
    iconSize: [40, 18],
    iconAnchor: [20, 9],
  });

// Fit map to all airport coordinates after layers mount
const FitBounds: React.FC<{ airports: MapAirport[] }> = ({ airports }) => {
  const map = useMap();
  useEffect(() => {
    if (!airports || airports.length === 0) return;
    const pts = airports
      .filter(a => a.latitude != null && a.longitude != null)
      .map(a => [a.latitude, a.longitude]) as [number, number][];
    if (pts.length === 0) return;
    const bounds = L.latLngBounds(pts);
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [airports, map]);
  return null;
};

export const MapWidget: React.FC<{ mapData: MapData }> = ({ mapData }) => {
  const airports = mapData?.airports ?? [];
  const directs = mapData?.direct_routes ?? [];
  const layovers = mapData?.layover_routes ?? [];

  // Fast lookup for airport coords by code (IATA preferred; fallback ICAO)
  const byCode = useMemo(() => {
    const m = new Map<string, { lat: number; lon: number; label: string }>();
    for (const a of airports) {
      const code = (a.code || a.iata || a.icao) as string;
      if (!code) continue;
      m.set(code, {
        lat: a.latitude,
        lon: a.longitude,
        label: a.iata || a.icao || code,
      });
    }
    return m;
  }, [airports]);

  // Default center if nothing to show
  const defaultCenter: [number, number] = [20, 0];

  return (
    <div className="w-full h-[520px] rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
      <MapContainer center={defaultCenter} zoom={2} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitBounds airports={airports} />

        {/* Airport markers */}
        {airports.map((a, idx) => {
          const code = (a.code || a.iata || a.icao) as string;
          if (a.latitude == null || a.longitude == null || !code) return null;
          return (
            <Marker key={`ap-${code}-${idx}`} position={[a.latitude, a.longitude]} icon={airportIcon(code)}>
              <Popup>
                <div style={{ minWidth: 180 }}>
                  <div style={{ fontWeight: 700 }}>{a.name}</div>
                  <div>{a.city}, {a.country}</div>
                  <div>Code: {code}{a.iata ? ` | IATA: ${a.iata}` : ''}{a.icao ? ` | ICAO: ${a.icao}` : ''}</div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Direct routes (solid red) */}
        {directs.map((r, idx) => {
          const s = byCode.get(r.src);
          const d = byCode.get(r.dst);
          if (!s || !d) return null;
          return (
            <Polyline
              key={`dr-${r.route_id}-${idx}`}
              positions={[
                [s.lat, s.lon],
                [d.lat, d.lon],
              ]}
              pathOptions={{ color: 'red', weight: 3, opacity: 0.7 }}
            >
              <Popup>
                <div style={{ minWidth: 200 }}>
                  <div style={{ fontWeight: 700 }}>{r.airline} ({r.airline_code})</div>
                  <div>{r.src} → {r.dst}</div>
                  <div>Equipment: {r.equipment.replace('\r', '')}</div>
                  <div>{r.src_city}, {r.src_country} → {r.dst_city}, {r.dst_country}</div>
                </div>
              </Popup>
            </Polyline>
          );
        })}

        {/* Layover routes (dashed green) */}
        {layovers.map((l, idx) => {
          const s = byCode.get(l.src);
          const h = byCode.get(l.hub);
          const d = byCode.get(l.dst);
          if (!s || !h || !d) return null;
          return (
            <>
              <Polyline
                key={`lr1-${idx}`}
                positions={[
                  [s.lat, s.lon],
                  [h.lat, h.lon],
                ]}
                pathOptions={{ color: 'green', weight: 2, opacity: 0.6, dashArray: '6 8' }}
              >
                <Popup>
                  <div style={{ minWidth: 200 }}>
                    <div style={{ fontWeight: 700 }}>Leg 1: {l.leg1_airline}</div>
                    <div>{l.src} → {l.hub}</div>
                    <div>Equipment: {l.leg1_equipment.replace('\r', '')}</div>
                    <div>Hub: {l.hub_name} ({l.hub_city}, {l.hub_country})</div>
                  </div>
                </Popup>
              </Polyline>
              <Polyline
                key={`lr2-${idx}`}
                positions={[
                  [h.lat, h.lon],
                  [d.lat, d.lon],
                ]}
                pathOptions={{ color: 'green', weight: 2, opacity: 0.6, dashArray: '6 8' }}
              >
                <Popup>
                  <div style={{ minWidth: 200 }}>
                    <div style={{ fontWeight: 700 }}>Leg 2: {l.leg2_airline}</div>
                    <div>{l.hub} → {l.dst}</div>
                    <div>Equipment: {l.leg2_equipment.replace('\r', '')}</div>
                  </div>
                </Popup>
              </Polyline>
            </>
          );
        })}
      </MapContainer>
    </div>
  );
};
