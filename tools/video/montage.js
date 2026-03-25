#!/usr/bin/env node
/**
 * montage.js — Montaggio deterministico da manifest
 *
 * ZERO valori hardcodati. TUTTO dal manifest.json.
 * Se il manifest non e' completo o i clip sono insufficienti → RIFIUTA.
 *
 * Pipeline:
 *   1. GATE   — validazione manifest (blocca se incompleto)
 *   2. TRIM   — taglia ogni clip a trim_start + (vo_duration + gap)
 *   3. XFADE  — concatena con crossfade (offset da durate REALI trimmate)
 *   4. VO     — traccia voiceover sincronizzata (offset da durate REALI)
 *   5. MIX    — video + VO + musica con fade in/out
 *
 * Uso:
 *   node tools/video/montage.js data/videos/01-primo-cliente
 */

const { FF, PROBE, getDuration, readManifest, validateForMontage } = require("./lib");
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

function run(cmd, label) {
  if (label) {
    console.log(`  > ${label}`);
  } else {
    console.log(`  > ${cmd.substring(0, 120)}...`);
  }
  execSync(cmd, { stdio: "pipe" });
}

function main() {
  const videoDir = path.resolve(process.argv[2] || ".");
  const manifest = readManifest(videoDir);
  const { video, scenes } = manifest;

  console.log(`\n${"=".repeat(60)}`);
  console.log(`  MONTAGGIO: ${video.title}`);
  console.log(`${"=".repeat(60)}\n`);

  // ═══════════════════════════════════════════════════════
  // GATE — Validazione
  // ═══════════════════════════════════════════════════════
  console.log("[GATE] Validazione manifest...");
  const errors = validateForMontage(manifest, videoDir);
  if (errors.length > 0) {
    console.error("\n  MONTAGGIO BLOCCATO:\n");
    errors.forEach((e) => console.error(`    - ${e}`));
    console.error("\n  Correggi e riesegui manifest-sync.js prima di riprovare.\n");
    process.exit(1);
  }
  console.log("  Manifest valido — procedo.\n");

  // Temp directory
  const TEMP_DIR = path.join(videoDir, "temp");
  if (fs.existsSync(TEMP_DIR)) fs.rmSync(TEMP_DIR, { recursive: true });
  fs.mkdirSync(TEMP_DIR, { recursive: true });

  const [W, H] = video.resolution;
  const FPS = video.fps;
  const CRF = video.codec.crf;
  const AUDIO_BR = video.codec.audio_bitrate;
  const XFADE = video.crossfade_duration;

  // ═══════════════════════════════════════════════════════
  // STEP 1 — Trim clip
  // ═══════════════════════════════════════════════════════
  console.log("[1/4] Trim clip alla durata esatta VO + gap...");

  for (const scene of scenes) {
    const clipPath = path.join(videoDir, scene.recording.file);
    const trimmedPath = path.join(TEMP_DIR, `${scene.name}.mp4`);
    const ss = scene.recording.trim_start;
    const targetDur = scene.vo.duration + scene.gap;

    run(
      `"${FF}" -y -ss ${ss.toFixed(3)} -i "${clipPath}" ` +
      `-t ${targetDur.toFixed(3)} ` +
      `-vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,fps=${FPS}" ` +
      `-c:v libx264 -preset medium -crf ${CRF} -pix_fmt yuv420p -an "${trimmedPath}"`,
      `trim ${scene.name} (ss=${ss.toFixed(1)}s, t=${targetDur.toFixed(1)}s)`
    );

    const actualDur = getDuration(trimmedPath);
    scene._trimmedDur = actualDur;

    const delta = Math.abs(actualDur - targetDur);
    const icon = delta < 0.2 ? "+" : "!";
    console.log(
      `  ${icon} ${scene.name}: ` +
      `VO ${scene.vo.duration.toFixed(1)}s + gap ${scene.gap}s = ${targetDur.toFixed(1)}s ` +
      `(trim ${ss.toFixed(1)}s -> actual ${actualDur.toFixed(1)}s)`
    );
  }

  const totalTrimmed = scenes.reduce((s, sc) => s + sc._trimmedDur, 0);
  const totalAfterXfade = totalTrimmed - XFADE * (scenes.length - 1);
  console.log(`\n  Totale dopo trim: ${totalTrimmed.toFixed(1)}s`);
  console.log(`  Stima dopo crossfade: ~${totalAfterXfade.toFixed(1)}s\n`);

  // ═══════════════════════════════════════════════════════
  // STEP 2 — Crossfade video
  // ═══════════════════════════════════════════════════════
  console.log(`[2/4] Crossfade ${XFADE}s tra ${scenes.length} scene...`);

  const clipInputs = scenes
    .map((s) => `-i "${path.join(TEMP_DIR, s.name + ".mp4")}"`)
    .join(" ");

  let xfadeFilter = "";
  let lastLabel = "[0:v]";
  let cumulativeOffset = 0;

  for (let i = 1; i < scenes.length; i++) {
    // Offset basato su durata REALE trimmata — MAI su target stimato
    cumulativeOffset += scenes[i - 1]._trimmedDur - XFADE;
    const outLabel = i < scenes.length - 1 ? `[xf${i}]` : "[vout]";
    xfadeFilter +=
      `${lastLabel}[${i}:v]xfade=transition=fade:duration=${XFADE}` +
      `:offset=${cumulativeOffset.toFixed(3)}${outLabel}`;
    if (i < scenes.length - 1) xfadeFilter += "; ";
    lastLabel = outLabel;
  }

  const videoOnly = path.join(TEMP_DIR, "video_concat.mp4");
  run(
    `"${FF}" -y ${clipInputs} -filter_complex "${xfadeFilter}" ` +
    `-map "[vout]" -c:v libx264 -preset medium -crf ${CRF} -pix_fmt yuv420p "${videoOnly}"`,
    "xfade concatenation"
  );

  const videoDur = getDuration(videoOnly);
  console.log(`  + video_concat.mp4: ${videoDur.toFixed(1)}s\n`);

  // ═══════════════════════════════════════════════════════
  // STEP 3 — Traccia VO sincronizzata
  // ═══════════════════════════════════════════════════════
  console.log("[3/4] Traccia VO sincronizzata...");

  // Ricalcola offset per ogni scena basandosi su durate REALI trimmate
  let voOffset = 0;
  for (let i = 0; i < scenes.length; i++) {
    scenes[i]._offset = voOffset;
    if (i < scenes.length - 1) {
      voOffset += scenes[i]._trimmedDur - XFADE;
    }
  }

  const voInputs = scenes
    .map((s) => `-i "${path.join(videoDir, s.vo.file)}"`)
    .join(" ");

  const voDelays = scenes
    .map((s, i) => {
      const delayMs = Math.round(s._offset * 1000);
      return `[${i}:a]adelay=${delayMs}|${delayMs}[vo${i}]`;
    })
    .join("; ");

  const voMixLabels = scenes.map((_, i) => `[vo${i}]`).join("");
  const voTrack = path.join(TEMP_DIR, "voiceover.mp3");

  run(
    `"${FF}" -y ${voInputs} -filter_complex ` +
    `"${voDelays}; ${voMixLabels}amix=inputs=${scenes.length}:duration=longest:dropout_transition=0" ` +
    `-c:a libmp3lame -b:a ${AUDIO_BR} "${voTrack}"`,
    "vo sync + mix"
  );

  const voDur = getDuration(voTrack);
  console.log(`  + voiceover.mp3: ${voDur.toFixed(1)}s`);

  // Drift check
  const drift = Math.abs(videoDur - voDur);
  if (drift > 2.0) {
    console.log(`  ! DRIFT video/VO: ${drift.toFixed(1)}s — verificare sync`);
  } else {
    console.log(`  + Drift video/VO: ${drift.toFixed(1)}s (OK)`);
  }
  console.log();

  // ═══════════════════════════════════════════════════════
  // STEP 4 — Mix finale
  // ═══════════════════════════════════════════════════════
  console.log("[4/4] Mix finale: video + VO + musica...");

  const musicPath = path.join(videoDir, video.music.file);
  const musicVol = video.music.volume;
  const fadeIn = video.music.fade_in;
  const fadeOut = video.music.fade_out;
  const fadeOutStart = videoDur - fadeOut;
  const outputPath = path.join(videoDir, video.output);

  run(
    `"${FF}" -y -i "${videoOnly}" -i "${voTrack}" -i "${musicPath}" ` +
    `-filter_complex ` +
    `"[2:a]volume=${musicVol},afade=t=in:st=0:d=${fadeIn},afade=t=out:st=${fadeOutStart.toFixed(1)}:d=${fadeOut}[music]; ` +
    `[1:a][music]amix=inputs=2:duration=first:dropout_transition=0[aout]" ` +
    `-map 0:v -map "[aout]" -c:v copy -c:a aac -b:a ${AUDIO_BR} ` +
    `-movflags +faststart -shortest "${outputPath}"`,
    "final mix (video + VO + music)"
  );

  // ═══════════════════════════════════════════════════════
  // Report finale
  // ═══════════════════════════════════════════════════════
  const finalDur = getDuration(outputPath);
  const finalSize = (fs.statSync(outputPath).size / 1024 / 1024).toFixed(1);

  console.log(`\n${"=".repeat(60)}`);
  console.log("  MONTAGGIO COMPLETATO");
  console.log(`${"=".repeat(60)}`);
  console.log(`  Output:     ${outputPath}`);
  console.log(`  Durata:     ${finalDur.toFixed(1)}s`);
  console.log(`  Dimensione: ${finalSize} MB`);
  console.log(`  Drift V/A:  ${drift.toFixed(1)}s`);
  console.log();
  console.log("  Scene:");
  console.log("  " + "-".repeat(55));
  console.log(
    "  " +
    "Scena".padEnd(18) +
    "Offset".padEnd(10) +
    "VO".padEnd(8) +
    "Clip".padEnd(8) +
    "Fine".padEnd(8)
  );
  console.log("  " + "-".repeat(55));
  for (const s of scenes) {
    const fine = s._offset + s._trimmedDur;
    console.log(
      "  " +
      s.name.padEnd(18) +
      `${s._offset.toFixed(1)}s`.padEnd(10) +
      `${s.vo.duration.toFixed(1)}s`.padEnd(8) +
      `${s._trimmedDur.toFixed(1)}s`.padEnd(8) +
      `${fine.toFixed(1)}s`
    );
  }
  console.log("  " + "-".repeat(55));

  // Cleanup
  fs.rmSync(TEMP_DIR, { recursive: true });
  console.log("\n  Temp rimossi.\n");
}

main();
