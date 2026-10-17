import React from "react";
import { TrackPoint } from "./types";

const FONT = "Avenir Next, Helvetica Neue, Arial, sans-serif";

export const Route: React.FC<{
  pts: TrackPoint[];
  fromIndex: number;
  upToIndex: number;
  head: [number, number] | null;
  proj: (lat: number, lon: number) => [number, number];
  width: number;
  height: number;
  color: string;
  strokeWidth: number;
  opacity?: number;
}> = ({ pts, fromIndex, upToIndex, head, proj, width, height, color, strokeWidth, opacity = 1 }) => {
  const coords: string[] = [];
  for (let i = fromIndex; i < upToIndex && i < pts.length; i++) {
    const [x, y] = proj(pts[i].lat, pts[i].lon);
    coords.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  if (head) coords.push(`${head[0].toFixed(1)},${head[1].toFixed(1)}`);
  if (coords.length < 2) return null;
  const d = `M${coords.join("L")}`;
  return (
    <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
      <path d={d} fill="none" stroke={color} strokeOpacity={0.25 * opacity} strokeWidth={strokeWidth * 3.2} strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} fill="none" stroke={color} strokeOpacity={opacity} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

export const Marker: React.FC<{ at: [number, number]; label: string; color: string; scale: number; below?: boolean }> = ({ at, label, color, scale, below }) => (
  <div style={{ position: "absolute", left: at[0], top: at[1], transform: "translate(-50%, -50%)" }}>
    <div style={{ width: 18 * scale, height: 18 * scale, borderRadius: "50%", background: color, border: `${3 * scale}px solid white`, boxShadow: "0 0 12px rgba(0,0,0,0.6)" }} />
    <div style={{
      position: "absolute", left: "50%", top: below ? 26 * scale : -38 * scale, transform: "translateX(-50%)", whiteSpace: "nowrap",
      color: "white", fontFamily: FONT, fontWeight: 700, fontSize: 22 * scale, textShadow: "0 2px 6px rgba(0,0,0,0.9)",
    }}>{label}</div>
  </div>
);

// Top-down bird silhouette with long broad wings (stork-like), pointing up (north) before rotation.
const BIRD_PATH =
  "M0,-34 C3,-30 4,-24 4,-16 L4,-8 C14,-10 30,-6 46,2 C50,4 50,8 46,8 C32,6 18,6 6,8 L5,18 C10,22 12,26 12,28 L0,25 L-12,28 C-12,26 -10,22 -5,18 L-6,8 C-18,6 -32,6 -46,8 C-50,8 -50,4 -46,2 C-30,-6 -14,-10 -4,-8 L-4,-16 C-4,-24 -3,-30 0,-34 Z";

export const Animal: React.FC<{ at: [number, number]; headingDeg: number; scale: number; flap: number }> = ({ at, headingDeg, scale, flap }) => (
  <svg width={140 * scale} height={140 * scale} viewBox="-70 -70 140 140"
    style={{ position: "absolute", left: at[0] - 70 * scale, top: at[1] - 70 * scale, overflow: "visible" }}>
    <circle r={34} fill="#ffb347" fillOpacity={0.18} />
    <g transform={`rotate(${headingDeg}) scale(${1 + 0.04 * flap}, ${1 - 0.04 * flap})`}>
      <path d={BIRD_PATH} fill="white" stroke="#1b1b1b" strokeWidth={2.5} strokeLinejoin="round" />
      <path d="M0,-34 L0,-46" stroke="#ff8a3d" strokeWidth={4} strokeLinecap="round" />
    </g>
  </svg>
);

export const Hud: React.FC<{ title: string; date: string; day: number; km: number; place: string; scale: number; vertical: boolean; opacity: number }> = ({ title, date, day, km, place, scale, vertical, opacity }) => {
  const box: React.CSSProperties = {
    background: "rgba(8, 16, 26, 0.72)", borderRadius: 18 * scale, padding: `${14 * scale}px ${22 * scale}px`,
    border: "1px solid rgba(255,255,255,0.12)", color: "white", fontFamily: FONT,
  };
  const stat = (k: string, v: string) => (
    <div style={{ display: "flex", flexDirection: "column", minWidth: 150 * scale }}>
      <span style={{ fontSize: 18 * scale, letterSpacing: 2, opacity: 0.7, textTransform: "uppercase" }}>{k}</span>
      <span style={{ fontSize: 40 * scale, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{v}</span>
    </div>
  );
  return (
    <div style={{ position: "absolute", top: (vertical ? 120 : 36) * scale, left: 36 * scale, right: vertical ? 36 * scale : undefined, opacity, display: "flex", flexDirection: "column", gap: 12 * scale }}>
      <div style={{ ...box, fontSize: 30 * scale, fontWeight: 700 }}>{title}</div>
      <div style={{ ...box, display: "flex", gap: 28 * scale, justifyContent: "space-between" }}>
        {stat("Date", date)}
        {stat("Day", String(day))}
        {stat("Distance", `${Math.round(km).toLocaleString("en-GB")} km`)}
      </div>
      <div style={{ ...box, fontSize: 26 * scale, fontWeight: 600, alignSelf: "flex-start", display: "flex", alignItems: "center", gap: 12 * scale }}>
        <span style={{ width: 14 * scale, height: 14 * scale, borderRadius: "50%", background: "#ffb347", display: "inline-block" }} />
        {place}
      </div>
    </div>
  );
};

export const Caption: React.FC<{ text: string; scale: number; vertical: boolean; opacity: number }> = ({ text, scale, vertical, opacity }) =>
  text ? (
    <div style={{ position: "absolute", left: 60 * scale, right: 60 * scale, bottom: (vertical ? 330 : 70) * scale, display: "flex", justifyContent: "center", opacity }}>
      <div style={{
        background: "rgba(0,0,0,0.68)", color: "white", fontFamily: FONT, fontWeight: 700, fontSize: (vertical ? 46 : 40) * scale,
        lineHeight: 1.25, padding: `${14 * scale}px ${26 * scale}px`, borderRadius: 16 * scale, textAlign: "center", maxWidth: vertical ? "100%" : "75%",
      }}>{text}</div>
    </div>
  ) : null;

export const TitleCard: React.FC<{ title: string; subtitle: string; scale: number; opacity: number }> = ({ title, subtitle, scale, opacity }) => (
  <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", opacity, fontFamily: FONT, color: "white", textAlign: "center", textShadow: "0 4px 18px rgba(0,0,0,0.85)" }}>
    <div style={{ fontSize: 30 * scale, letterSpacing: 6, textTransform: "uppercase", opacity: 0.85 }}>Real GPS track</div>
    <div style={{ fontSize: 92 * scale, fontWeight: 800, lineHeight: 1.05, padding: `0 ${40 * scale}px` }}>{title}</div>
    {subtitle ? <div style={{ fontSize: 44 * scale, fontWeight: 600, marginTop: 14 * scale, color: "#ffcf8a" }}>{subtitle}</div> : null}
  </div>
);

export const Credits: React.FC<{ data: string; license: string; mapCredit: string; scale: number; opacity: number }> = ({ data, license, mapCredit, scale, opacity }) => (
  <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", opacity, background: "rgba(5,10,18,0.78)" }}>
    <div style={{ maxWidth: "80%", color: "white", fontFamily: FONT, textAlign: "center" }}>
      <div style={{ fontSize: 44 * scale, fontWeight: 800, marginBottom: 24 * scale }}>Data & credits</div>
      <div style={{ fontSize: 26 * scale, lineHeight: 1.4, opacity: 0.92 }}>{data}</div>
      <div style={{ fontSize: 24 * scale, marginTop: 18 * scale, opacity: 0.8 }}>Licence: {license} · Distances are straight lines between nightly roosts, so the real figure is higher.</div>
      <div style={{ fontSize: 24 * scale, marginTop: 12 * scale, opacity: 0.8 }}>{mapCredit}</div>
    </div>
  </div>
);

export const Attribution: React.FC<{ text: string; scale: number }> = ({ text, scale }) => (
  <div style={{ position: "absolute", right: 14 * scale, bottom: 10 * scale, color: "white", opacity: 0.7, fontFamily: FONT, fontSize: 16 * scale, textShadow: "0 1px 3px black" }}>{text}</div>
);
