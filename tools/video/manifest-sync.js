#!/usr/bin/env node
/**
 * manifest-sync.js — Sincronizza il manifest con i file su disco
 *
 * Scansiona VO (.mp3) e clip (.webm), misura durate reali con FFprobe,
 * aggiorna manifest.json. Da eseguire OGNI VOLTA che:
 *   - Rigeneri un VO (durata cambiata)
 *   - Ri-registri un clip
 *   - Prima di lanciare il montaggio
 *
 * Uso:
 *   node tools/video/manifest-sync.js data/videos/01-primo-cliente
 *
 * Senza argomento: usa la directory corrente.
 */

const { getDurationRounded, readManifest, writeManifest, validateForMontage } = require("./lib");
const path = require("path");
const fs = require("fs");

function main() {
  const videoDir = path.resolve(process.argv[2] || ".");

  if (!fs.existsSync(path.join(videoDir, "manifest.json"))) {
    console.error(`Manifest non trovato in: ${videoDir}`);
    console.error("Crea un manifest.json prima di eseguire manifest-sync.");
    process.exit(1);
  }

  const manifest = readManifest(videoDir);
  console.log(`=== Manifest Sync: ${manifest.video.title || path.basename(videoDir)} ===\n`);

  let changes = 0;

  for (const scene of manifest.scenes) {
    // ── Sync VO duration ──
    const voPath = path.join(videoDir, scene.vo.file);
    if (fs.existsSync(voPath)) {
      const measured = getDurationRounded(voPath);
      if (scene.vo.duration !== measured) {
        const old = scene.vo.duration !== null ? scene.vo.duration.toFixed(3) : "null";
        console.log(`  ${scene.name} VO: ${old} -> ${measured.toFixed(3)}s`);
        scene.vo.duration = measured;
        changes++;
      }
    } else {
      console.log(`  !! ${scene.name} VO: file mancante (${scene.vo.file})`);
    }

    // ── Sync clip duration ──
    if (scene.recording.file) {
      const clipPath = path.join(videoDir, scene.recording.file);
      if (fs.existsSync(clipPath)) {
        const measured = getDurationRounded(clipPath);
        if (scene.recording.clip_duration !== measured) {
          const old = scene.recording.clip_duration !== null
            ? scene.recording.clip_duration.toFixed(3) : "null";
          console.log(`  ${scene.name} clip: ${old} -> ${measured.toFixed(3)}s`);
          scene.recording.clip_duration = measured;
          changes++;
        }
      } else {
        console.log(`  !! ${scene.name} clip: file mancante (${scene.recording.file})`);
      }
    }
  }

  // ── Salva se ci sono cambiamenti ──
  if (changes > 0) {
    writeManifest(videoDir, manifest);
    console.log(`\n  ${changes} valori aggiornati -> manifest.json salvato`);
  } else {
    console.log(`\n  Manifest gia' sincronizzato, nessun cambiamento.`);
  }

  // ═══════════════════════════════════════════════════════
  // Report stato completo
  // ═══════════════════════════════════════════════════════
  console.log("\n  STATO SCENE:");
  console.log("  " + "-".repeat(90));
  console.log(
    "  " +
    "Scena".padEnd(18) +
    "VO".padEnd(8) +
    "Gap".padEnd(6) +
    "Serve".padEnd(8) +
    "Clip".padEnd(8) +
    "Trim".padEnd(8) +
    "Usabile".padEnd(9) +
    "Stato"
  );
  console.log("  " + "-".repeat(90));

  for (const scene of manifest.scenes) {
    const voDur = scene.vo.duration;
    const gap = scene.gap;
    const needed = voDur !== null ? voDur + gap : null;
    const clipDur = scene.recording.clip_duration;
    const trim = scene.recording.trim_start;
    const usable = (clipDur !== null && trim !== null) ? clipDur - trim : null;

    const col = (v, w) => (v !== null ? v.toFixed(1) + "s" : "--").padEnd(w);
    const stato =
      voDur === null ? "VO mancante" :
      clipDur === null ? "Clip mancante" :
      trim === null ? "Trim mancante" :
      usable < needed - 0.15 ? `CORTO ${(needed - usable).toFixed(1)}s` :
      "OK";
    const icon = stato === "OK" ? "+" : "!";

    console.log(
      `  ${icon} ${scene.name.padEnd(16)}` +
      col(voDur, 8) +
      col(gap, 6) +
      col(needed, 8) +
      col(clipDur, 8) +
      col(trim, 8) +
      col(usable, 9) +
      stato
    );
  }
  console.log("  " + "-".repeat(90));

  // ── Totali ──
  const totalVO = manifest.scenes.reduce((s, sc) => s + (sc.vo.duration || 0), 0);
  const totalNeeded = manifest.scenes.reduce((s, sc) => s + (sc.vo.duration || 0) + sc.gap, 0);
  const xfade = manifest.video.crossfade_duration || 0.4;
  const transitions = manifest.scenes.length - 1;
  const estimatedFinal = totalNeeded - xfade * transitions;
  console.log(`\n  Totale VO: ${totalVO.toFixed(1)}s`);
  console.log(`  Totale necessario (VO+gap): ${totalNeeded.toFixed(1)}s`);
  console.log(`  Stima finale (con ${transitions} crossfade ${xfade}s): ~${estimatedFinal.toFixed(1)}s`);

  // ── Validazione montaggio ──
  const errors = validateForMontage(manifest, videoDir);
  if (errors.length > 0) {
    console.log(`\n  BLOCCHI MONTAGGIO (${errors.length}):`);
    errors.forEach((e) => console.log(`    - ${e}`));
  } else {
    console.log("\n  Pronto per montaggio.");
  }
}

main();
