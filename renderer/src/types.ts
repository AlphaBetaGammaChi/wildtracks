export type MapStyle = "vector" | "street" | "satellite";

export type TrackPoint = {
  t: number; // epoch ms
  lat: number;
  lon: number;
  km: number;
  place: string;
};

export type Camera = "follow" | "start" | "overview";

export type Scene = {
  id: string;
  kind: "hook" | "intro" | "leg" | "arrival" | "after" | "outcome" | "credits";
  text: string;
  t0: string;
  t1: string;
  camera: Camera;
  seconds: number;
};

export type VideoProps = {
  style: MapStyle;
  title: string;
  subtitle: string;
  label: string;
  species: string;
  points: TrackPoint[];
  scenes: Scene[];
  credits: { data: string; license: string; doi: string };
  audio: string | null;
  markers: number[] | null;
  maptilerKey: string | null;
};
