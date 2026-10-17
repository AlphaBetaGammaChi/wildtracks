// Web Mercator in MapLibre's convention: the world is 512px wide at zoom 0.
export const TILE = 512;

export type View = { x: number; y: number; zoom: number }; // x/y are zoom-0 world pixels of the centre

export const toWorld = (lat: number, lon: number): [number, number] => {
  const clamped = Math.max(-85, Math.min(85, lat));
  const phi = (clamped * Math.PI) / 180;
  const x = ((lon + 180) / 360) * TILE;
  const y = ((Math.PI - Math.log(Math.tan(Math.PI / 4 + phi / 2))) / (2 * Math.PI)) * TILE;
  return [x, y];
};

export const fromWorld = (x: number, y: number): [number, number] => {
  const lon = (x / TILE) * 360 - 180;
  const n = Math.PI - (2 * Math.PI * y) / TILE;
  const lat = (180 / Math.PI) * Math.atan(Math.sinh(n));
  return [lat, lon];
};

export const project = (view: View, w: number, h: number) => {
  const s = 2 ** view.zoom;
  return (lat: number, lon: number): [number, number] => {
    const [x, y] = toWorld(lat, lon);
    return [(x - view.x) * s + w / 2, (y - view.y) * s + h / 2];
  };
};

export type Box = { minX: number; maxX: number; minY: number; maxY: number };

export const fitZoom = (b: Box, w: number, h: number, pad: number, minSpanWorld: number): number => {
  const dx = Math.max(b.maxX - b.minX, minSpanWorld);
  const dy = Math.max(b.maxY - b.minY, minSpanWorld);
  return Math.log2(Math.min((w - 2 * pad) / dx, (h - 2 * pad) / dy));
};

// ~km per zoom-0 world pixel at the equator (40075 km / 512 px)
export const KM_PER_WORLD_PX = 40075 / TILE;
