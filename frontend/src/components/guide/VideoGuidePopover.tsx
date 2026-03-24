// components/guide/VideoGuidePopover.tsx
"use client";

/**
 * VideoGuidePopover — bussola (?) contestuale per gli header delle pagine.
 *
 * Mostra un popover con il video-pillola della sezione corrente.
 * Click sull'icona → popover con player inline.
 * Se il video non è pronto, mostra link alla guida.
 */

import { useState } from "react";
import { HelpCircle, Play, Clock, BookOpen } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { VideoGuide } from "@/lib/video-guides";

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m}:${s.toString().padStart(2, "0")}` : `0:${s}`;
}

export function VideoGuidePopover({ video }: { video: VideoGuide }) {
  const [playing, setPlaying] = useState(false);
  const [open, setOpen] = useState(false);

  // Reset player quando si chiude il popover
  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) setPlaying(false);
  };

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-primary"
          title="Video guida"
        >
          <HelpCircle className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        side="bottom"
        align="end"
        className="w-80 p-0"
      >
        <div className="space-y-2 p-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">{video.title}</p>
            {video.ready && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {formatDuration(video.durationSec)}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">{video.description}</p>
        </div>

        {video.ready ? (
          <div className="border-t">
            {playing ? (
              <div className="bg-black">
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
                className="group relative w-full bg-black"
              >
                <div className="aspect-video w-full bg-muted/20" />
                <div className="absolute inset-0 flex items-center justify-center bg-black/30 transition-colors group-hover:bg-black/40">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-lg transition-transform group-hover:scale-110">
                    <Play className="h-4 w-4 text-zinc-900 ml-0.5" />
                  </div>
                </div>
              </button>
            )}
          </div>
        ) : (
          <div className="border-t px-3 py-2">
            <Button asChild variant="ghost" size="sm" className="h-7 w-full gap-1 text-xs">
              <Link href="/guida">
                <BookOpen className="h-3 w-3" />
                Vai alla guida completa
              </Link>
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
