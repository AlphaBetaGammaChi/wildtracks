import { Box, View, fitZoom, toWorld, KM_PER_WORLD_PX } from "./mercator";
import { Scene, TrackPoint } from "./types";

export type SceneSpan = { scene: Scene; f0: number; f1: number; t0: number; t1: number; i0: number; i1: number; warp: number[] };

const lowerBound = (pts: TrackPoint[], t: number) => {
  let lo = 0, hi = pts.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (pts[mid].t < t) lo = mid + 1; else hi = mid;
  }
  return lo;
};

export const sampleAt = (pts: TrackPoint[], t: number) => {
  const i = Math.min(Math.max(lowerBound(pts, t), 1), pts.length - 1);
  const a = pts[i - 1], b = pts[i];
  const k = b.t === a.t ? 0 : Math.max(0, Math.min(1, (t - a.t) / (b.t - a.t)));
  return {
    lat: a.lat + (b.lat - a.lat) * k,
    lon: a.lon + (b.lon - a.lon) * k,
    km: a.km + (b.km - a.km) * k,
    place: k < 0.5 ? a.place : b.place,
    index: i,
  };
};

export const buildSpans = (scenes: Scene[], pts: TrackPoint[], fps: number): SceneSpan[] => {
  let f = 0;
  return scenes.map((scene) => {
    const frames = Math.max(1, Math.round(scene.seconds * fps));
    const t0 = Date.parse(scene.t0), t1 = Date.parse(scene.t1);
    const i0 = Math.max(0, lowerBound(pts, t0) - 1), i1 = Math.min(pts.length - 1, lowerBound(pts, t1));
    // Screen time follows distance (80%) more than clock time (20%), so long stopovers don't stall the video.
    const dkm = pts[i1].km - pts[i0].km, dt = pts[i1].t - pts[i0].t;
    const warp: number[] = [];
    for (let i = i0; i <= i1; i++) {
      const byKm = dkm > 0 ? (pts[i].km - pts[i0].km) / dkm : 0;
      const byT = dt > 0 ? (pts[i].t - pts[i0].t) / dt : 0;
      warp.push(dkm > 0 ? 0.8 * byKm + 0.2 * byT : byT);
    }
    const span = { scene, f0: f, f1: f + frames, t0, t1, i0, i1, warp };
    f += frames;
    return span;
  });
};

export const totalFrames = (spans: SceneSpan[]) => (spans.length ? spans[spans.length - 1].f1 : 1);

export const spanAt = (spans: SceneSpan[], frame: number) =>
  spans.find((s) => frame >= s.f0 && frame < s.f1) ?? spans[spans.length - 1];

const ease = (u: number) => (u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2);

/** Track time (ms) shown at a given frame. */
export const timeAt = (spans: SceneSpan[], pts: TrackPoint[], frame: number): number => {
  const s = spanAt(spans, frame);
  if (s.t1 <= s.t0) return s.t0;
  const raw = Math.max(0, Math.min(1, (frame - s.f0) / (s.f1 - s.f0)));
  const u = 0.15 * ease(raw) + 0.85 * raw;
  const w = s.warp;
  let k = 0;
  while (k < w.length - 2 && w[k + 1] < u) k++;
  const a = pts[s.i0 + k], b = pts[Math.min(s.i0 + k + 1, s.i1)];
  const wa = w[k], wb = w[Math.min(k + 1, w.length - 1)];
  const frac = wb > wa ? (u - wa) / (wb - wa) : 0;
  return Math.max(s.t0, Math.min(s.t1, a.t + (b.t - a.t) * Math.max(0, Math.min(1, frac))));
};

const boxOf = (pts: TrackPoint[], from: number, to: number): Box => {
  const b = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
  for (let i = Math.max(0, from); i <= Math.min(pts.length - 1, to); i++) {
    const [x, y] = toWorld(pts[i].lat, pts[i].lon);
    b.minX = Math.min(b.minX, x); b.maxX = Math.max(b.maxX, x);
    b.minY = Math.min(b.minY, y); b.maxY = Math.max(b.maxY, y);
  }
  return b;
};

const viewFor = (b: Box, w: number, h: number, minKm: number, maxZoom: number): View => {
  const pad = Math.min(w, h) * 0.12;
  const zoom = Math.min(maxZoom, Math.max(1.2, fitZoom(b, w, h, pad, minKm / KM_PER_WORLD_PX)));
  return { x: (b.minX + b.maxX) / 2, y: (b.minY + b.maxY) / 2, zoom };
};

const rawView = (spans: SceneSpan[], pts: TrackPoint[], frame: number, w: number, h: number, journey: [number, number]): View => {
  const s = spanAt(spans, frame);
  const t = timeAt(spans, pts, frame);
  const here = sampleAt(pts, t);
  const cam = s.scene.kind === "hook" ? "overview" : s.scene.camera;
  if (cam === "overview") {
    const from = s.scene.kind === "hook" ? lowerBound(pts, journey[0]) : 0;
    const to = s.scene.kind === "hook" ? lowerBound(pts, journey[1]) : here.index;
    return viewFor(boxOf(pts, from, to), w, h, 400, 6);
  }
  if (cam === "start") {
    return viewFor(boxOf(pts, s.i0, Math.max(s.i0, here.index)), w, h, 250, 8);
  }
  // follow: frame the stretch of route around the bird (where it has just been and where it is going next)
  const u = s.f1 > s.f0 ? (frame - s.f0) / (s.f1 - s.f0) : 0;
  const lo = s.warp.findIndex((x) => x >= u - 0.3);
  let hi = s.warp.findIndex((x) => x > u + 0.3);
  if (hi < 0) hi = s.warp.length - 1;
  const box = boxOf(pts, s.i0 + Math.max(0, lo), s.i0 + hi);
  const [bx, by] = toWorld(here.lat, here.lon);
  box.minX = Math.min(box.minX, bx); box.maxX = Math.max(box.maxX, bx);
  box.minY = Math.min(box.minY, by); box.maxY = Math.max(box.maxY, by);
  const v = viewFor(box, w, h, 500, 7);
  return { x: 0.6 * v.x + 0.4 * bx, y: 0.6 * v.y + 0.4 * by, zoom: v.zoom };
};

/** Camera with a moving average so cuts between scenes become smooth glides. */
export const viewAt = (spans: SceneSpan[], pts: TrackPoint[], frame: number, w: number, h: number, journey: [number, number], fps: number): View => {
  const k = Math.round(fps * 0.8);
  const last = totalFrames(spans) - 1;
  let x = 0, y = 0, z = 0, n = 0;
  for (let f = frame - k; f <= frame + k; f += 2) {
    const v = rawView(spans, pts, Math.max(0, Math.min(last, f)), w, h, journey);
    x += v.x; y += v.y; z += v.zoom; n++;
  }
  return { x: x / n, y: y / n, zoom: z / n };
};

export const sentenceAt = (text: string, u: number): string => {
  const sentences = text.match(/[^.!?:]+[.!?:]+(\s|$)/g)?.map((s) => s.trim()) ?? [text];
  const words = sentences.map((s) => s.split(/\s+/).length);
  const total = words.reduce((a, b) => a + b, 0);
  let acc = 0;
  for (let i = 0; i < sentences.length; i++) {
    acc += words[i] / total;
    if (u <= acc) return sentences[i];
  }
  return sentences[sentences.length - 1];
};
