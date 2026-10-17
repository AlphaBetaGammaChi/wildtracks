import React, { useMemo } from "react";
import { geoMercator, geoPath, geoCentroid } from "d3-geo";
import { feature, mesh } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";
import world from "world-atlas/countries-50m.json";
import { TILE, View } from "./mercator";

const topo = world as unknown as Topology<{ countries: GeometryCollection<{ name: string }>; land: GeometryCollection }>;
const countries = feature(topo, topo.objects.countries).features;
const land = feature(topo, topo.objects.land);
const borders = mesh(topo, topo.objects.countries, (a, b) => a !== b);
const centroids = new Map(countries.map((c) => [c.properties.name, geoCentroid(c)]));

export const VectorMap: React.FC<{ view: View; width: number; height: number; visited: string[]; labelScale: number }> = ({ view, width, height, visited, labelScale }) => {
  const s = 2 ** view.zoom;
  const k = (TILE * s) / (2 * Math.PI);
  const projection = geoMercator()
    .scale(k)
    .translate([k * Math.PI - view.x * s + width / 2, k * Math.PI - view.y * s + height / 2])
    .clipExtent([[-50, -50], [width + 50, height + 50]]);
  const path = geoPath(projection);
  const visitedSet = useMemo(() => new Set(visited), [visited]);

  return (
    <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <radialGradient id="sea" cx="50%" cy="40%" r="75%">
          <stop offset="0%" stopColor="#123049" />
          <stop offset="100%" stopColor="#07131f" />
        </radialGradient>
      </defs>
      <rect width={width} height={height} fill="url(#sea)" />
      <path d={path(land) ?? ""} fill="#26323a" stroke="#4d6a7a" strokeWidth={1.2} />
      {countries
        .filter((c) => visitedSet.has(c.properties.name))
        .map((c) => (
          <path key={c.properties.name} d={path(c) ?? ""} fill="#2f4a3f" />
        ))}
      <path d={path(borders) ?? ""} fill="none" stroke="#5b7486" strokeOpacity={0.55} strokeWidth={1} />
      {visited.map((name) => {
        const c = centroids.get(name);
        const p = c && projection(c);
        if (!p || p[0] < 0 || p[0] > width || p[1] < 0 || p[1] > height) return null;
        return (
          <text key={name} x={p[0]} y={p[1]} textAnchor="middle" fill="#cfe3d6" fillOpacity={0.55}
            fontSize={22 * labelScale} fontWeight={600} letterSpacing={2}
            style={{ fontFamily: "Avenir Next, Helvetica Neue, Arial, sans-serif", textTransform: "uppercase" }}>
            {name}
          </text>
        );
      })}
    </svg>
  );
};
