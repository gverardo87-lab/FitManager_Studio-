#!/usr/bin/env node
/**
 * montage.js — Montaggio deterministico da manifest
 *
 * Due modalita':
 *   - "continuous": clip unico con scene markers → sovrapponi VO + musica
 *   - "clips": clip separati per scena → trim + xfade + VO + musica
 *
 * Uso:
 *   node tools/video/montage.js data/videos/01-primo-cliente
 */

const { FF, PROBE, getDuration, readManifest, validateForMontage } = require("./lib");
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

function run(cmd, label) {
  console.log(`  > ${label || cmd.substring(0, 120) + "..."}`);
  execSync(cmd, { stdio: "pipe" });
}

// ═══════════════════════════════════════════════════════════
// Modalita' CONTINUOUS — clip unico, VO sovrapposto
// ═══════════════════════════════════════════════════════════

function montageContinuous(manifest, videoDir) {
  const { video, scenes } = manifest;
  const AUDIO_BR = video.codec.audio_bitrate;
  const [W, H] = video.resolution;
  const CRF = video.codec.crf;
  const XFADE = video.crossfade_duration;

  const clipPath = path.join(videoDir, manifest.recording_file);
  if (!fs.existsSync(clipPath)) {
    console.error(`  Clip non trovato: ${clipPath}`);
    process.exit(1);
  }

  const clipDur = getDuration(clipPath);
  console.log(`  Clip continuo: ${clipPath} (${clipDur.toFixed(1)}s)\n`);

  const TEMP_DIR = path.join(videoDir, "temp");
  if (fs.existsSync(TEMP_DIR)) fs.rmSync(TEMP_DIR, { recursive: true });
  fs.mkdirSync(TEMP_DIR, { recursive: true });

  // ── Step 1: Converti clip + intro/outro ──
  console.log("[1/4] Converti clip + intro/outro...");

  // Trim iniziale: salta il flash bianco di caricamento pagina
  // Crop basso: rimuovi taskbar Windows catturata nella registrazione
  const trimStart = manifest.recording_trim_start || 0;
  const cropBottom = manifest.recording_crop_bottom || 0;
  const cropH = H - cropBottom;

  let vfFilter = `fps=${video.fps}`;
  if (cropBottom > 0) {
    // Crop la taskbar, poi pad con colore sfondo app (no stretching)
    const padColor = manifest.recording_pad_color || "f0f4f8";
    vfFilter = `crop=${W}:${cropH}:0:0,pad=${W}:${H}:0:0:color=0x${padColor},${vfFilter}`;
  } else {
    vfFilter = `scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,${vfFilter}`;
  }

  const mainClip = path.join(TEMP_DIR, "main.mp4");
  const ssArg = trimStart > 0 ? `-ss ${trimStart.toFixed(1)} ` : "";
  run(
    `"${FF}" -y ${ssArg}-i "${clipPath}" ` +
    `-vf "${vfFilter}" ` +
    `-c:v libx264 -preset medium -crf ${CRF} -pix_fmt yuv420p -an "${mainClip}"`,
    `convert (trim=${trimStart}s, crop_bottom=${cropBottom}px)`
  );

  if (trimStart > 0) {
    console.log(`  + trim iniziale: ${trimStart}s (flash bianco rimosso)`);
  }
  if (cropBottom > 0) {
    console.log(`  + crop basso: ${cropBottom}px (taskbar rimossa)`);
  }

  // Intro e Outro (se presenti in cards/)
  const introPath = path.join(videoDir, "cards", "intro.mp4");
  const outroPath = path.join(videoDir, "cards", "outro.mp4");
  const hasIntro = fs.existsSync(introPath);
  const hasOutro = fs.existsSync(outroPath);

  let videoOnly;
  if (hasIntro || hasOutro) {
    // Concatena: intro + main + outro con crossfade
    const parts = [];
    if (hasIntro) parts.push(introPath);
    parts.push(mainClip);
    if (hasOutro) parts.push(outroPath);

    if (parts.length === 1) {
      videoOnly = mainClip;
    } else {
      // Xfade chain
      const inputs = parts.map((p) => `-i "${p}"`).join(" ");
      let filter = "", lastLabel = "[0:v]", cumOffset = 0;
      const durations = parts.map((p) => getDuration(p));

      for (let i = 1; i < parts.length; i++) {
        cumOffset += durations[i - 1] - XFADE;
        const outLabel = i < parts.length - 1 ? `[xf${i}]` : "[vout]";
        filter += `${lastLabel}[${i}:v]xfade=transition=fade:duration=${XFADE}:offset=${cumOffset.toFixed(3)}${outLabel}`;
        if (i < parts.length - 1) filter += "; ";
        lastLabel = outLabel;
      }

      videoOnly = path.join(TEMP_DIR, "video_full.mp4");
      run(
        `"${FF}" -y ${inputs} -filter_complex "${filter}" -map "[vout]" -c:v libx264 -preset medium -crf ${CRF} -pix_fmt yuv420p "${videoOnly}"`,
        `xfade ${hasIntro ? "intro + " : ""}main${hasOutro ? " + outro" : ""}`
      );
    }
    const introDur = hasIntro ? getDuration(introPath) : 0;
    const outroDur = hasOutro ? getDuration(outroPath) : 0;
    console.log(`  + intro: ${introDur.toFixed(1)}s, main: ${getDuration(mainClip).toFixed(1)}s, outro: ${outroDur.toFixed(1)}s`);
  } else {
    videoOnly = mainClip;
  }

  const videoDur = getDuration(videoOnly);
  console.log(`  + video finale: ${videoDur.toFixed(1)}s\n`);

  // Calcola offset intro per sincronizzare VO (il VO parte DOPO l'intro)
  const introOffset = hasIntro ? getDuration(introPath) - XFADE : 0;

  // ── Step 2: Traccia VO sincronizzata ──
  console.log("[2/4] Traccia VO sincronizzata...");
  const voInputs = scenes
    .map((s) => `-i "${path.join(videoDir, s.vo.file)}"`)
    .join(" ");

  const voDelays = scenes
    .map((s, i) => {
      // Offset = intro duration + (scene_start - trim iniziale)
      const sceneStart = Math.max(0, (s.recording.scene_start || 0) - trimStart);
      const delayMs = Math.round((sceneStart + introOffset) * 1000);
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
  const drift = Math.abs(videoDur - voDur);
  console.log(`  + Drift video/VO: ${drift.toFixed(1)}s${drift > 3 ? " (ATTENZIONE)" : " (OK)"}\n`);

  // ── Step 3: Musica con compressor + volume ridotto ──
  console.log("[3/4] Musica (compressor + volume)...");
  const musicPath = path.join(videoDir, video.music.file);
  const musicVol = video.music.volume;
  const fadeIn = video.music.fade_in;
  const fadeOut = video.music.fade_out;
  const fadeOutStart = videoDur - fadeOut;

  // Compressor per appiattire i picchi PRIMA di ridurre il volume
  // Poi volume + fade in/out
  const musicProcessed = path.join(TEMP_DIR, "music.mp3");
  run(
    `"${FF}" -y -i "${musicPath}" -af "acompressor=threshold=-20dB:ratio=4:attack=5:release=50,volume=${musicVol},afade=t=in:st=0:d=${fadeIn},afade=t=out:st=${fadeOutStart.toFixed(1)}:d=${fadeOut}" -c:a libmp3lame -b:a ${AUDIO_BR} "${musicProcessed}"`,
    `compress + volume ${musicVol} + fade`
  );
  console.log(`  + music.mp3: processata\n`);

  // ── Step 4: Mix finale ──
  console.log("[4/4] Mix finale...");
  const outputPath = path.join(videoDir, video.output);

  run(
    `"${FF}" -y -i "${videoOnly}" -i "${voTrack}" -i "${musicProcessed}" ` +
    `-filter_complex "[1:a]apad=whole_dur=${videoDur.toFixed(1)}[vopad]; [vopad][2:a]amix=inputs=2:duration=first:dropout_transition=0[aout]" ` +
    `-map 0:v -map "[aout]" -c:v copy -c:a aac -b:a ${AUDIO_BR} ` +
    `-movflags +faststart -t ${videoDur.toFixed(1)} "${outputPath}"`,
    "final mix (video + VO + music)"
  );

  reportFinal(outputPath, scenes, videoDur, drift, TEMP_DIR);
}

// ═══════════════════════════════════════════════════════════
// Modalita' CLIPS — clip separati, trim + xfade
// ═══════════════════════════════════════════════════════════

function montageClips(manifest, videoDir) {
  const { video, scenes } = manifest;
  const AUDIO_BR = video.codec.audio_bitrate;
  const [W, H] = video.resolution;
  const CRF = video.codec.crf;
  const XFADE = video.crossfade_duration;

  const TEMP_DIR = path.join(videoDir, "temp");
  if (fs.existsSync(TEMP_DIR)) fs.rmSync(TEMP_DIR, { recursive: true });
  fs.mkdirSync(TEMP_DIR, { recursive: true });

  // Step 1: Trim
  console.log("[1/4] Trim clip...");
  for (const scene of scenes) {
    const clipPath = path.join(videoDir, scene.recording.file);
    const trimmedPath = path.join(TEMP_DIR, `${scene.name}.mp4`);
    const ss = scene.recording.trim_start;
    const targetDur = scene.vo.duration + scene.gap;

    run(
      `"${FF}" -y -ss ${ss.toFixed(3)} -i "${clipPath}" -t ${targetDur.toFixed(3)} ` +
      `-vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,fps=${video.fps}" ` +
      `-c:v libx264 -preset medium -crf ${CRF} -pix_fmt yuv420p -an "${trimmedPath}"`,
      `trim ${scene.name}`
    );
    scene._trimmedDur = getDuration(trimmedPath);
    console.log(`  + ${scene.name}: ${scene._trimmedDur.toFixed(1)}s`);
  }

  // Step 2: Xfade
  console.log(`\n[2/4] Crossfade ${XFADE}s...`);
  const clipInputs = scenes.map((s) => `-i "${path.join(TEMP_DIR, s.name + ".mp4")}"`).join(" ");
  let xfadeFilter = "", lastLabel = "[0:v]", cumOffset = 0;

  for (let i = 1; i < scenes.length; i++) {
    cumOffset += scenes[i - 1]._trimmedDur - XFADE;
    const outLabel = i < scenes.length - 1 ? `[xf${i}]` : "[vout]";
    xfadeFilter += `${lastLabel}[${i}:v]xfade=transition=fade:duration=${XFADE}:offset=${cumOffset.toFixed(3)}${outLabel}`;
    if (i < scenes.length - 1) xfadeFilter += "; ";
    lastLabel = outLabel;
  }

  const videoOnly = path.join(TEMP_DIR, "video_concat.mp4");
  run(`"${FF}" -y ${clipInputs} -filter_complex "${xfadeFilter}" -map "[vout]" -c:v libx264 -preset medium -crf ${CRF} -pix_fmt yuv420p "${videoOnly}"`, "xfade");

  const videoDur = getDuration(videoOnly);
  console.log(`  + video_concat.mp4: ${videoDur.toFixed(1)}s\n`);

  // Step 3: VO
  console.log("[3/4] VO sync...");
  let voOffset = 0;
  for (let i = 0; i < scenes.length; i++) {
    scenes[i]._offset = voOffset;
    if (i < scenes.length - 1) voOffset += scenes[i]._trimmedDur - XFADE;
  }

  const voInputs = scenes.map((s) => `-i "${path.join(videoDir, s.vo.file)}"`).join(" ");
  const voDelays = scenes.map((s, i) => `[${i}:a]adelay=${Math.round(s._offset * 1000)}|${Math.round(s._offset * 1000)}[vo${i}]`).join("; ");
  const voMixLabels = scenes.map((_, i) => `[vo${i}]`).join("");
  const voTrack = path.join(TEMP_DIR, "voiceover.mp3");

  run(`"${FF}" -y ${voInputs} -filter_complex "${voDelays}; ${voMixLabels}amix=inputs=${scenes.length}:duration=longest:dropout_transition=0" -c:a libmp3lame -b:a ${AUDIO_BR} "${voTrack}"`, "vo sync");

  const voDur = getDuration(voTrack);
  const drift = Math.abs(videoDur - voDur);
  console.log(`  + voiceover.mp3: ${voDur.toFixed(1)}s (drift: ${drift.toFixed(1)}s)\n`);

  // Step 4: Mix
  console.log("[4/4] Mix finale...");
  const musicPath = path.join(videoDir, video.music.file);
  const fadeOutStart = videoDur - video.music.fade_out;
  const outputPath = path.join(videoDir, video.output);

  run(
    `"${FF}" -y -i "${videoOnly}" -i "${voTrack}" -i "${musicPath}" ` +
    `-filter_complex "[2:a]volume=${video.music.volume},afade=t=in:st=0:d=${video.music.fade_in},afade=t=out:st=${fadeOutStart.toFixed(1)}:d=${video.music.fade_out}[music]; ` +
    `[1:a][music]amix=inputs=2:duration=first:dropout_transition=0[aout]" ` +
    `-map 0:v -map "[aout]" -c:v copy -c:a aac -b:a ${AUDIO_BR} -movflags +faststart -shortest "${outputPath}"`,
    "final mix"
  );

  reportFinal(outputPath, scenes, videoDur, drift, TEMP_DIR);
}

// ═══════════════════════════════════════════════════════════
// Report + cleanup
// ═══════════════════════════════════════════════════════════

function reportFinal(outputPath, scenes, videoDur, drift, tempDir) {
  const finalDur = getDuration(outputPath);
  const finalSize = (fs.statSync(outputPath).size / 1024 / 1024).toFixed(1);

  console.log(`\n${"=".repeat(50)}`);
  console.log("  MONTAGGIO COMPLETATO");
  console.log(`${"=".repeat(50)}`);
  console.log(`  Output:     ${outputPath}`);
  console.log(`  Durata:     ${finalDur.toFixed(1)}s`);
  console.log(`  Dimensione: ${finalSize} MB`);
  console.log(`  Drift V/A:  ${drift.toFixed(1)}s`);

  console.log("\n  Scene:");
  for (const s of scenes) {
    const offset = s._offset !== undefined ? s._offset : (s.recording.scene_start || 0);
    console.log(`    ${s.name}: @${offset.toFixed(1)}s — VO ${s.vo.duration.toFixed(1)}s`);
  }

  fs.rmSync(tempDir, { recursive: true });
  console.log("\n  Temp rimossi.\n");
}

// ═══════════════════════════════════════════════════════════
// Main
// ═══════════════════════════════════════════════════════════

function main() {
  const videoDir = path.resolve(process.argv[2] || ".");
  const manifest = readManifest(videoDir);

  console.log(`\n${"=".repeat(60)}`);
  console.log(`  MONTAGGIO: ${manifest.video.title}`);
  console.log(`  Modalita': ${manifest.recording_mode || "clips"}`);
  console.log(`${"=".repeat(60)}\n`);

  if (manifest.recording_mode === "continuous") {
    montageContinuous(manifest, videoDir);
  } else {
    // Validazione solo per modalita' clips (continuous non usa trim/clip separati)
    const errors = validateForMontage(manifest, videoDir);
    if (errors.length > 0) {
      console.error("  MONTAGGIO BLOCCATO:\n");
      errors.forEach((e) => console.error(`    - ${e}`));
      process.exit(1);
    }
    montageClips(manifest, videoDir);
  }
}

main();
