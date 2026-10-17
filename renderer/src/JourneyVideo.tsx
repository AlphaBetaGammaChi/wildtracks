import React, { useMemo } from "react";
import { AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { buildSpans, sampleAt, sentenceAt, spanAt, timeAt, viewAt } from "./timeline";
import { project, toWorld } from "./mercator";
import { VectorMap } from "./VectorMap";
import { TileMap, attributionFor } from "./TileMap";
import { Animal, Attribution, Caption, Credits, Hud, Marker, Route, TitleCard } from "./Overlay";
import { VideoProps } from "./types";

const DAY = 86400000;
const fmtDate = (t: number) =>
  new Date(t).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });

export const JourneyVideo: React.FC<VideoProps> = (props) => {
  const { points: pts, scenes, style } = props;
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const vertical = height > width;
  const scale = Math.min(width, height) / 1080;

  const spans = useMemo(() => buildSpans(scenes, pts, fps), [scenes, pts, fps]);
  const journey = useMemo<[number, number]>(() => {
    const hook = scenes.find((s) => s.kind === "hook");
    const legs = scenes.filter((s) => s.kind === "leg");
    if (hook) return [Date.parse(hook.t0), Date.parse(hook.t1)];
    if (legs.length) return [Date.parse(legs[0].t0), Date.parse(legs[legs.length - 1].t1)];
    return [pts[0].t, pts[pts.length - 1].t];
  }, [scenes, pts]);

  const span = spanAt(spans, frame);
  const kind = span.scene.kind;
  const u = (frame - span.f0) / Math.max(1, span.f1 - span.f0);
  const t = timeAt(spans, pts, frame);
  const here = sampleAt(pts, t);
  const view = viewAt(spans, pts, frame, width, height, journey, fps);
  const proj = project(view, width, height);
  const head = proj(here.lat, here.lon);

  const ahead = sampleAt(pts, timeAt(spans, pts, frame + 5));
  const behind = sampleAt(pts, timeAt(spans, pts, frame - 5));
  const [ax, ay] = toWorld(ahead.lat, ahead.lon), [bx, by] = toWorld(behind.lat, behind.lon);
  const moving = Math.hypot(ax - bx, ay - by) > 1e-6;
  const heading = moving ? (Math.atan2(ax - bx, -(ay - by)) * 180) / Math.PI : 180;

  const visited = useMemo(() => {
    const seen: string[] = [];
    for (let i = 0; i < here.index && i < pts.length; i++) if (!seen.includes(pts[i].place)) seen.push(pts[i].place);
    return seen;
  }, [here.index, pts]);

  const isHook = kind === "hook";
  const isCredits = kind === "credits";
  const fadeIn = (f0: number, len = 12) => interpolate(frame, [f0, f0 + len], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const hudOpacity = isHook ? 0 : isCredits ? 0 : fadeIn(spans.find((s) => s.scene.kind !== "hook")?.f0 ?? 0);
  const titleOpacity = isHook ? interpolate(u, [0, 0.08, 0.85, 1], [0, 1, 1, 0]) : 0;
  const captionOpacity = interpolate(u, [0, 0.04, 0.97, 1], [0, 1, 1, 0.6]);
  const startIdx = 0;
  const hookStart = pts.findIndex((p) => p.t >= journey[0]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#07131f" }}>
      {style === "vector" ? (
        <VectorMap view={view} width={width} height={height} visited={isHook ? [] : visited} labelScale={scale} />
      ) : (
        <TileMap style={style} view={view} width={width} height={height} maptilerKey={props.maptilerKey} />
      )}

      {isHook ? (
        <Route pts={pts} fromIndex={Math.max(0, hookStart)} upToIndex={here.index} head={head} proj={proj} width={width} height={height} color="#ffffff" strokeWidth={5 * scale} opacity={0.85} />
      ) : (
        <Route pts={pts} fromIndex={startIdx} upToIndex={here.index} head={head} proj={proj} width={width} height={height} color="#ffb347" strokeWidth={6 * scale} />
      )}

      {!isHook ? <Marker at={proj(pts[0].lat, pts[0].lon)} label="Tagged here" color="#4ade80" scale={scale} below /> : null}
      {!isHook && !isCredits ? <Animal at={head} headingDeg={heading} scale={scale} flap={moving ? Math.sin(frame / 2.2) : 0} /> : null}

      <Hud title={props.title} date={fmtDate(t)} day={Math.max(1, Math.floor((t - pts[0].t) / DAY) + 1)} km={here.km} place={here.place} scale={scale} vertical={vertical} opacity={hudOpacity} />
      {isHook ? <TitleCard title={props.title} subtitle={props.subtitle} scale={scale} opacity={titleOpacity} /> : null}
      {!isCredits ? <Caption text={sentenceAt(span.scene.text, u)} scale={scale} vertical={vertical} opacity={captionOpacity} /> : null}
      {isCredits ? <Credits data={props.credits.data} license={props.credits.license} mapCredit={attributionFor(style)} scale={scale} opacity={fadeIn(span.f0, 10)} /> : null}
      <Attribution text={attributionFor(style)} scale={scale} />
      {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
    </AbsoluteFill>
  );
};
