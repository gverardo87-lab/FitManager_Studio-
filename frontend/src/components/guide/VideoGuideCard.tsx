// components/guide/VideoGuideCard.tsx
"use client";

/**
 * VideoGuideCard — card video per la pagina /guida.
 *
 * Mostra poster + overlay play + titolo + durata.
 * Click → espande il player HTML5 inline (no modal).
 * Nessun autoplay, nessun preload pesante.
 */

import { useState } from "react";
import { Play, Clock } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { VideoGuide } from "@/lib/video-guides";

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m}:${s.toString().padStart(2, "0")}` : `0:${s}`;
}

export function VideoGuideCard({ video }: { video: VideoGuide }) {
  const [playing, setPlaying] = useState(false);

  if (!video.ready) {
    return (
      <Card className="border-border/50 opacity-60">
        <CardHeader className="space-y-1 pb-2">
          <CardTitle className="text-sm">{video.title}</CardTitle>
          <CardDescription className="text-xs">{video.description}</CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex aspect-video items-center justify-center rounded-lg bg-muted/40 text-xs text-muted-foreground">
            In arrivo
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden border-border/70 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <CardHeader className="space-y-1 pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">{video.title}</CardTitle>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatDuration(video.durationSec)}
          </div>
        </div>
        <CardDescription className="text-xs">{video.description}</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        {playing ? (
          <div className="overflow-hidden rounded-lg border border-border/50 bg-black">
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <video
              className="w-full"
              controls
              autoPlay
              preload="metadata"
              poster={video.poster}
            >
              <source src={video.src} type="video/mp4" />
            </video>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setPlaying(true)}
            className="group relative w-full overflow-hidden rounded-lg border border-border/50 bg-black"
          >
            <div className="aspect-video w-full bg-muted/20" />
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 transition-colors group-hover:bg-black/40">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/90 shadow-lg transition-transform group-hover:scale-110">
                <Play className="h-5 w-5 text-zinc-900 ml-0.5" />
              </div>
            </div>
          </button>
        )}
      </CardContent>
    </Card>
  );
}
