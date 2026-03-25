#!/usr/bin/env node
/**
 * Montaggio video 01 — "Il Primo Cliente"
 *
 * Input: 6 clip .webm + 6 VO .mp3 + 1 musica .mp3
 * Output: 01-primo-cliente.mp4 (H.264 + AAC)
 *
 * Strategia:
 * - Ogni clip viene tagliato alla durata del VO + gap (0.3-0.5s)
 * - I clip vengono concatenati in sequenza
 * - Il VO viene allineato all'inizio di ogni clip
 * - La musica corre sotto a volume 20%, con fade in/out
 */

const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const FF = "C:\\Users\\gvera\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1-full_build\\bin\\ffmpeg.exe";
const PROBE = "C:\\Users\\gvera\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1-full_build\\bin\\ffprobe.exe";

const VIDEO_DIR = path.resolve(__dirname, "../../data/videos/01-primo-cliente");
const CLIPS_DIR = path.join(VIDEO_DIR, "clips");
const SCENES_DIR = path.join(VIDEO_DIR, "scenes");
const MUSIC_FILE = path.join(VIDEO_DIR, "music", "background.mp3");
const OUTPUT = path.join(VIDEO_DIR, "primo-cliente.mp4");
const TEMP_DIR = path.join(VIDEO_DIR, "temp");

function getDuration(file) {
  return parseFloat(execSync(`"${PROBE}" -v quiet -show_entries format=duration -of csv=p=0 "${file}"`).toString().trim());
}

function run(cmd) {
  console.log(`  > ${cmd.substring(0, 120)}...`);
  execSync(cmd, { stdio: "pipe" });
}

function main() {
  console.log("=== Montaggio Video 01: Il Primo Cliente ===\n");

  // Crea temp dir
  if (fs.existsSync(TEMP_DIR)) fs.rmSync(TEMP_DIR, { recursive: true });
  fs.mkdirSync(TEMP_DIR, { recursive: true });

  const scenes = [
    { name: "01_hook",      gap: 0.3, trimStart: 0.0 },  // Prima scena, nessun trim
    { name: "02_cliente",   gap: 0.3, trimStart: 1.5 },  // Navigazione a /clienti
    { name: "03_contratto", gap: 0.5, trimStart: 1.5 },  // Navigazione a /contratti/ID
    { name: "04_anamnesi",  gap: 0.5, trimStart: 0.5 },  // Trim ridotto: clip corto (14.1s), VO lungo (12.9s)
    { name: "05_profilo",   gap: 0.3, trimStart: 1.5 },  // Navigazione a /clienti + profilo
    { name: "06_cta",       gap: 1.5, trimStart: 1.0 },  // Navigazione a /guida
  ];

  // ── Step 1: Calcola durate e taglia clip ──
  console.log("[1/4] Taglio clip alla durata VO + gap...");
  let totalDur = 0;
  const concatEntries = [];

  for (const scene of scenes) {
    const clipFile = path.join(CLIPS_DIR, `${scene.name}.webm`);
    const voFile = path.join(SCENES_DIR, `${scene.name}.mp3`);
    const voDur = getDuration(voFile);
    const targetDur = voDur + scene.gap;
    scene.voDur = voDur;
    scene.targetDur = targetDur;
    scene.offset = totalDur;
    totalDur += targetDur;

    // Taglia clip: skip bianchi iniziali (trimStart) + durata target
    const trimmedFile = path.join(TEMP_DIR, `${scene.name}.mp4`);
    const ss = scene.trimStart || 0;
    run(`"${FF}" -y -ss ${ss.toFixed(3)} -i "${clipFile}" -t ${targetDur.toFixed(3)} -vf "scale=1440:900:force_original_aspect_ratio=decrease,pad=1440:900:(ow-iw)/2:(oh-ih)/2,fps=30" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -an "${trimmedFile}"`);

    const actualDur = getDuration(trimmedFile);
    scene.actualDur = actualDur;  // Durata reale per xfade robusto
    const trimNote = ss > 0 ? ` (trim ${ss}s)` : "";
    if (actualDur < targetDur - 0.2) {
      console.log(`  ⚠ ${scene.name}: VO ${voDur.toFixed(1)}s + gap ${scene.gap}s = ${targetDur.toFixed(1)}s (actual: ${actualDur.toFixed(1)}s — CLIP CORTO!)${trimNote}`);
    } else {
      console.log(`  ${scene.name}: VO ${voDur.toFixed(1)}s + gap ${scene.gap}s = ${targetDur.toFixed(1)}s (actual: ${actualDur.toFixed(1)}s)${trimNote}`);
    }

    concatEntries.push(`file '${scene.name}.mp4'`);
  }

  console.log(`  TOTALE VIDEO: ${totalDur.toFixed(1)}s\n`);

  // ── Step 2: Concatena clip video con crossfade ──
  console.log("[2/4] Concateno clip video con crossfade 0.4s...");
  const XFADE = 0.4; // secondi di crossfade tra scene

  // Costruisci filtro xfade a catena: clip0 xfade clip1 → result xfade clip2 → ...
  const clipInputs = scenes.map((s) => `-i "${path.join(TEMP_DIR, s.name + ".mp4")}"`).join(" ");
  let xfadeFilter = "";
  let lastLabel = "[0:v]";
  let cumulativeOffset = 0;

  for (let i = 1; i < scenes.length; i++) {
    cumulativeOffset += scenes[i - 1].actualDur - XFADE;  // actualDur, non targetDur
    const outLabel = i < scenes.length - 1 ? `[xf${i}]` : "[vout]";
    xfadeFilter += `${lastLabel}[${i}:v]xfade=transition=fade:duration=${XFADE}:offset=${cumulativeOffset.toFixed(3)}${outLabel}`;
    if (i < scenes.length - 1) xfadeFilter += "; ";
    lastLabel = outLabel;
  }

  const videoOnly = path.join(TEMP_DIR, "video_concat.mp4");
  run(`"${FF}" -y ${clipInputs} -filter_complex "${xfadeFilter}" -map "[vout]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p "${videoOnly}"`);

  // Ricalcola durata totale basata su actualDur
  const totalActual = scenes.reduce((sum, s) => sum + s.actualDur, 0) - XFADE * (scenes.length - 1);
  console.log(`  video_concat.mp4: ${getDuration(videoOnly).toFixed(1)}s (atteso: ${totalActual.toFixed(1)}s)\n`);

  // ── Step 3: Costruisci traccia VO con timing esatto ──
  console.log("[3/4] Costruisco traccia VO sincronizzata...");

  // Ricalcola offset con crossfade: ogni scena dopo la prima inizia XFADE prima
  let voOffset = 0;
  for (let i = 0; i < scenes.length; i++) {
    scenes[i].offset = voOffset;
    if (i < scenes.length - 1) {
      voOffset += scenes[i].actualDur - XFADE;  // actualDur, non targetDur
    }
  }

  // Crea filtro complex per posizionare ogni VO al suo offset
  const inputOffset = scenes.length; // Gli input video occupano indici 0..N-1
  const voInputs = scenes.map((s) => `-i "${path.join(SCENES_DIR, s.name + ".mp3")}"`).join(" ");
  const voDelays = scenes.map((s, i) => {
    const delayMs = Math.round(s.offset * 1000);
    return `[${i}:a]adelay=${delayMs}|${delayMs}[vo${i}]`;
  }).join("; ");
  const voMix = scenes.map((_, i) => `[vo${i}]`).join("");
  const voTrack = path.join(TEMP_DIR, "voiceover.mp3");

  run(`"${FF}" -y ${voInputs} -filter_complex "${voDelays}; ${voMix}amix=inputs=${scenes.length}:duration=longest:dropout_transition=0" -c:a libmp3lame -b:a 192k "${voTrack}"`);
  console.log(`  voiceover.mp3: ${getDuration(voTrack).toFixed(1)}s\n`);

  // ── Step 4: Mix finale — video + VO + musica ──
  console.log("[4/4] Mix finale: video + VO + musica...");

  const videoDur = getDuration(videoOnly);
  const musicFadeOut = videoDur - 3;
  const mixCmd = `"${FF}" -y -i "${videoOnly}" -i "${voTrack}" -i "${MUSIC_FILE}" -filter_complex "[2:a]volume=0.18,afade=t=in:st=0:d=2,afade=t=out:st=${musicFadeOut.toFixed(1)}:d=3[music]; [1:a][music]amix=inputs=2:duration=first:dropout_transition=0[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest "${OUTPUT}"`;

  run(mixCmd);

  const finalDur = getDuration(OUTPUT);
  const finalSize = (fs.statSync(OUTPUT).size / 1024 / 1024).toFixed(1);

  console.log(`\n=== MONTAGGIO COMPLETATO ===`);
  console.log(`  Output: ${OUTPUT}`);
  console.log(`  Durata: ${finalDur.toFixed(1)}s`);
  console.log(`  Dimensione: ${finalSize} MB`);
  console.log(`\n  Timing per scena:`);
  for (const s of scenes) {
    console.log(`    ${s.name}: offset ${s.offset.toFixed(1)}s → VO ${s.voDur.toFixed(1)}s → fine ${(s.offset + s.targetDur).toFixed(1)}s`);
  }

  // Cleanup temp
  fs.rmSync(TEMP_DIR, { recursive: true });
  console.log("\n  Temp files rimossi.");
}

main();
