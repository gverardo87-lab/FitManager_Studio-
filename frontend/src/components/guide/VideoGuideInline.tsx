// components/guide/VideoGuideInline.tsx
"use client";

/**
 * VideoGuideInline — video embed per empty state delle pagine.
 *
 * Appare quando una lista è vuota (0 clienti, 0 contratti, ecc.).
 * Mostra il video contestuale con CTA "Guarda come fare" + poster.
 * Compatto, non invasivo: il trainer può ignorarlo e creare direttamente.
 */

import { useState } from "react";
import { Play, Clock } from "lucide-react";

import type { VideoGuide } from "@/lib/video-guides";

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m}:${s.toString().padStart(2, "0")}` : `0:${s}`;
}

export function VideoGuideInline({ video }: { video: VideoGuide }) {
  const [playing, setPlaying] = useState(false);

  if (!video.ready) return null;

  return (
    <div className="mx-auto w-full max-w-lg space-y-2">
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <Play className="h-3 w-3" />
        <span>{video.title}</span>
        <span className="flex items-center gap-0.5">
          <Clock className="h-3 w-3" />
          {formatDuration(video.durationSec)}
        </span>
      </div>

      {playing ? (
        <div className="overflow-hidden rounded-lg border border-border/50 bg-black shadow-sm">
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <video
            className="w-full"
            controls
            autoPlay
            preload="metadata"
          >
            <source src={video.src} type="video/mp4" />
          </video>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setPlaying(true)}
          className="group relative mx-auto block w-full overflow-hidden rounded-lg border border-border/50 bg-black shadow-sm"
        >
          <div className="aspect-video w-full bg-muted/20" />
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/30 transition-colors group-hover:bg-black/40">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-lg transition-transform group-hover:scale-110">
              <Play className="h-4 w-4 text-zinc-900 ml-0.5" />
            </div>
            <span className="text-xs font-medium text-white/80">
              Guarda come fare
            </span>
          </div>
        </button>
      )}
    </div>
  );
}
