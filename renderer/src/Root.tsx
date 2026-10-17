import React from "react";
import { CalculateMetadataFunction, Composition, staticFile } from "remotion";
import { getAudioDurationInSeconds } from "@remotion/media-utils";
import { JourneyVideo } from "./JourneyVideo";
import { Scene, VideoProps } from "./types";

const FPS = 30;

/** With a voiceover, each scene is stretched (or cut to markers) so pictures line up with the audio. */
export const fitScenesToAudio = (scenes: Scene[], audioSeconds: number, markers: number[] | null): Scene[] => {
  const spoken = scenes.filter((s) => s.text);
  if (markers && markers.length === spoken.length) {
    return scenes.map((s) => {
      const i = spoken.indexOf(s);
      if (i < 0) return s;
      const start = i === 0 ? 0 : markers[i];
      const end = i + 1 < markers.length ? markers[i + 1] : audioSeconds;
      return { ...s, seconds: Math.max(0.5, end - start) };
    });
  }
  const estimated = spoken.reduce((a, s) => a + s.seconds, 0);
  const k = audioSeconds / estimated;
  return scenes.map((s) => (s.text ? { ...s, seconds: s.seconds * k } : s));
};

const calculateMetadata: CalculateMetadataFunction<VideoProps> = async ({ props }) => {
  let scenes = props.scenes;
  if (props.audio) {
    const seconds = await getAudioDurationInSeconds(staticFile(props.audio));
    scenes = fitScenesToAudio(scenes, seconds, props.markers);
  }
  const durationInFrames = scenes.reduce((a, s) => a + Math.max(1, Math.round(s.seconds * FPS)), 0);
  return { durationInFrames, props: { ...props, scenes } };
};

const demo: VideoProps = {
  style: "vector",
  title: "Demo track",
  subtitle: "",
  label: "Demo",
  species: "white stork",
  points: [
    { t: Date.parse("2013-08-20T00:00:00Z"), lat: 52, lon: 13, km: 0, place: "Germany" },
    { t: Date.parse("2013-09-20T00:00:00Z"), lat: 36, lon: -5.5, km: 2000, place: "Spain" },
  ],
  scenes: [
    { id: "s1", kind: "leg", text: "Run `wildtracks render` to load a real track.", t0: "2013-08-20T00:00:00Z", t1: "2013-09-20T00:00:00Z", camera: "follow", seconds: 6 },
  ],
  credits: { data: "", license: "", doi: "" },
  audio: null,
  markers: null,
  maptilerKey: null,
};

export const Root: React.FC = () => (
  <>
    <Composition id="Short" component={JourneyVideo} width={1080} height={1920} fps={FPS} durationInFrames={180} defaultProps={demo} calculateMetadata={calculateMetadata} />
    <Composition id="Long" component={JourneyVideo} width={1920} height={1080} fps={FPS} durationInFrames={180} defaultProps={demo} calculateMetadata={calculateMetadata} />
  </>
);
