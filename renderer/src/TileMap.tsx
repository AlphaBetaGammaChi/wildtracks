import React, { useEffect, useRef, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";
import * as maplibregl from "maplibre-gl";
import type { StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { View, fromWorld } from "./mercator";
import { MapStyle } from "./types";

export const STREET_STYLE = "https://tiles.openfreemap.org/styles/liberty";

const satelliteStyle = (key: string): StyleSpecification => ({
  version: 8,
  sources: {
    sat: {
      type: "raster",
      tiles: [`https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=${key}`],
      tileSize: 512,
      maxzoom: 20,
    },
  },
  layers: [{ id: "sat", type: "raster", source: "sat" }],
});

export const attributionFor = (style: MapStyle) =>
  style === "street"
    ? "Map: OpenFreeMap · © OpenMapTiles · Data © OpenStreetMap contributors"
    : style === "satellite"
      ? "Imagery © MapTiler · © OpenStreetMap contributors"
      : "Map: Natural Earth (public domain)";

export const TileMap: React.FC<{ style: "street" | "satellite"; view: View; width: number; height: number; maptilerKey: string | null }> = ({ style, view, width, height, maptilerKey }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [loadHandle] = useState(() => delayRender("Loading map style", { timeoutInMilliseconds: 120000 }));

  useEffect(() => {
    if (!ref.current) return;
    if (style === "satellite" && !maptilerKey) throw new Error("Satellite style needs MAPTILER_KEY");
    maplibregl.setWorkerUrl(staticFile("maplibre-gl-worker.mjs"));
    const [lat, lon] = fromWorld(view.x, view.y);
    const m = new maplibregl.Map({
      container: ref.current,
      style: style === "street" ? STREET_STYLE : satelliteStyle(maptilerKey as string),
      center: [lon, lat],
      zoom: view.zoom,
      interactive: false,
      attributionControl: false,
      fadeDuration: 0,
      canvasContextAttributes: { preserveDrawingBuffer: true, antialias: true },
    });
    m.on("error", (e) => console.error("MapLibre error:", e.error?.message ?? e));
    m.once("idle", () => {
      setMap(m);
      continueRender(loadHandle);
    });
    return () => m.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!map) return;
    const handle = delayRender("Rendering map frame", { timeoutInMilliseconds: 60000 });
    const [lat, lon] = fromWorld(view.x, view.y);
    let done = false;
    const finish = () => {
      if (!done) {
        done = true;
        continueRender(handle);
      }
    };
    map.once("idle", finish);
    map.jumpTo({ center: [lon, lat], zoom: view.zoom });
    map.triggerRepaint();
    const fallback = setTimeout(finish, 20000);
    return () => clearTimeout(fallback);
  }, [map, view.x, view.y, view.zoom]);

  return <div ref={ref} style={{ position: "absolute", inset: 0, width, height }} />;
};
