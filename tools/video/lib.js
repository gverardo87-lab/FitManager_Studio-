/**
 * lib.js — Fondamenta pipeline video FitManager
 *
 * SSoT per: percorsi FFmpeg, misurazione durate, manifest I/O,
 * validazione pre-montaggio, helper registrazione Playwright.
 *
 * NESSUN valore hardcodato altrove. Tutto passa da qui.
 */

const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

// ═══════════════════════════════════════════════════════════
// Percorsi fissi (Windows, verificati)
// ═══════════════════════════════════════════════════════════

const FF =
  "C:\\Users\\gvera\\AppData\\Local\\Microsoft\\WinGet\\Packages\\" +
  "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\" +
  "ffmpeg-8.1-full_build\\bin\\ffmpeg.exe";

const PROBE =
  "C:\\Users\\gvera\\AppData\\Local\\Microsoft\\WinGet\\Packages\\" +
  "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\" +
  "ffmpeg-8.1-full_build\\bin\\ffprobe.exe";

const VIDEOS_DIR = path.resolve(__dirname, "../../data/videos");

// ═══════════════════════════════════════════════════════════
// FFprobe — misurazione durate
// ═══════════════════════════════════════════════════════════

/**
 * Ritorna la durata in secondi di un file audio/video.
 * @param {string} filePath - percorso assoluto al file
 * @returns {number} durata in secondi (es. 7.337)
 * @throws se il file non esiste o FFprobe fallisce
 */
function getDuration(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File non trovato: ${filePath}`);
  }
  const raw = execSync(
    `"${PROBE}" -v quiet -show_entries format=duration -of csv=p=0 "${filePath}"`
  )
    .toString()
    .trim();
  const dur = parseFloat(raw);
  if (isNaN(dur)) {
    throw new Error(`FFprobe ha ritornato un valore non numerico per ${filePath}: "${raw}"`);
  }
  return dur;
}

/**
 * Ritorna la durata arrotondata a 3 decimali (millisecondo).
 */
function getDurationRounded(filePath) {
  return parseFloat(getDuration(filePath).toFixed(3));
}

// ═══════════════════════════════════════════════════════════
// FFmpeg — esecuzione comandi
// ═══════════════════════════════════════════════════════════

/**
 * Esegue un comando FFmpeg completo (senza il path di ffmpeg).
 * @param {string} args - argomenti FFmpeg (es. "-y -i input.mp4 ...")
 * @param {object} opts - { quiet: bool, label: string }
 */
function ff(args, opts = {}) {
  const cmd = `"${FF}" ${args}`;
  if (!opts.quiet) {
    const label = opts.label || args.substring(0, 100) + "...";
    console.log(`  > ${label}`);
  }
  execSync(cmd, { stdio: "pipe" });
}

// ═══════════════════════════════════════════════════════════
// Manifest I/O
// ═══════════════════════════════════════════════════════════

/**
 * Legge il manifest.json dalla directory video.
 * @param {string} videoDir - directory video (es. data/videos/01-primo-cliente)
 * @returns {object} manifest parsed
 */
function readManifest(videoDir) {
  const p = path.join(videoDir, "manifest.json");
  if (!fs.existsSync(p)) {
    throw new Error(`Manifest non trovato: ${p}\nEsegui manifest-sync.js per crearlo.`);
  }
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

/**
 * Scrive il manifest.json nella directory video.
 */
function writeManifest(videoDir, manifest) {
  const p = path.join(videoDir, "manifest.json");
  manifest.updated_at = new Date().toISOString();
  fs.writeFileSync(p, JSON.stringify(manifest, null, 2) + "\n");
}

// ═══════════════════════════════════════════════════════════
// Validazione pre-montaggio
// ═══════════════════════════════════════════════════════════

/**
 * Valida il manifest per il montaggio.
 * Ritorna un array di errori (vuoto = tutto OK).
 *
 * Controlli:
 * 1. Ogni scena ha VO duration misurata
 * 2. Ogni scena ha clip file con duration misurata
 * 3. Ogni scena ha trim_start misurato
 * 4. Clip usabile (clip_duration - trim_start) >= VO + gap
 * 5. File VO e clip esistono su disco
 */
function validateForMontage(manifest, videoDir) {
  const errors = [];

  if (!manifest.video) errors.push("Sezione 'video' mancante nel manifest");
  if (!manifest.scenes || manifest.scenes.length === 0) {
    errors.push("Nessuna scena nel manifest");
    return errors;
  }

  for (const scene of manifest.scenes) {
    const prefix = `${scene.name}:`;

    // VO checks
    if (!scene.vo || !scene.vo.file) {
      errors.push(`${prefix} vo.file mancante`);
    } else {
      const voPath = path.join(videoDir, scene.vo.file);
      if (!fs.existsSync(voPath)) {
        errors.push(`${prefix} file VO non trovato su disco (${scene.vo.file})`);
      }
    }
    if (!scene.vo || scene.vo.duration === null || scene.vo.duration === undefined) {
      errors.push(`${prefix} vo.duration non misurata — esegui manifest-sync.js`);
    }

    // Recording checks
    if (!scene.recording || !scene.recording.file) {
      errors.push(`${prefix} recording.file mancante`);
    } else {
      const clipPath = path.join(videoDir, scene.recording.file);
      if (!fs.existsSync(clipPath)) {
        errors.push(`${prefix} file clip non trovato su disco (${scene.recording.file})`);
      }
    }
    if (!scene.recording || scene.recording.clip_duration === null || scene.recording.clip_duration === undefined) {
      errors.push(`${prefix} clip_duration non misurata — esegui manifest-sync.js`);
    }
    if (!scene.recording || scene.recording.trim_start === null || scene.recording.trim_start === undefined) {
      errors.push(`${prefix} trim_start non impostato`);
    }

    // Usability check: clip usabile >= VO + gap
    if (
      scene.vo && scene.vo.duration &&
      scene.recording && scene.recording.clip_duration &&
      scene.recording.trim_start !== null && scene.recording.trim_start !== undefined
    ) {
      const usable = scene.recording.clip_duration - scene.recording.trim_start;
      const needed = scene.vo.duration + scene.gap;
      if (usable < needed - 0.15) {
        errors.push(
          `${prefix} clip usabile ${usable.toFixed(2)}s < necessario ${needed.toFixed(2)}s ` +
          `(mancano ${(needed - usable).toFixed(2)}s — ri-registrare o ridurre trim)`
        );
      }
    }
  }

  // Music check
  if (manifest.video && manifest.video.music && manifest.video.music.file) {
    const musicPath = path.join(videoDir, manifest.video.music.file);
    if (!fs.existsSync(musicPath)) {
      errors.push(`Musica non trovata su disco (${manifest.video.music.file})`);
    }
  }

  return errors;
}

// ═══════════════════════════════════════════════════════════
// Helper registrazione Playwright
// ═══════════════════════════════════════════════════════════

/**
 * Legge il timing necessario per registrare una scena.
 * Il recording script usa questo per sapere quanto aspettare.
 *
 * @param {string} videoDir - directory video
 * @param {string} sceneName - es. "04_anamnesi"
 * @returns {{ minDuration: number, voDuration: number, gap: number }}
 */
function getSceneTiming(videoDir, sceneName) {
  const manifest = readManifest(videoDir);
  const scene = manifest.scenes.find((s) => s.name === sceneName);
  if (!scene) {
    throw new Error(
      `Scena "${sceneName}" non trovata nel manifest.\n` +
      `Scene disponibili: ${manifest.scenes.map((s) => s.name).join(", ")}`
    );
  }
  if (!scene.vo || !scene.vo.duration) {
    throw new Error(
      `Scena "${sceneName}": vo.duration non misurata. Esegui manifest-sync.js prima.`
    );
  }
  return {
    minDuration: scene.vo.duration + scene.gap + 0.5, // +0.5s buffer sicurezza
    voDuration: scene.vo.duration,
    gap: scene.gap,
  };
}

/**
 * Aggiorna il manifest dopo una registrazione Playwright.
 * Misura la durata reale del clip e salva trim_start.
 *
 * Uso tipico nel recording script:
 *   const recordingStart = Date.now();
 *   // ... naviga, waitForSelector ...
 *   const pageReady = Date.now();
 *   // ... azioni ...
 *   // ... wait VO-locked ...
 *   // ... chiudi context (video salvato) ...
 *   updateRecording(videoDir, "04_anamnesi", {
 *     trimStart: (pageReady - recordingStart) / 1000,
 *     clipFile: "clips/04_anamnesi.webm"  // opzionale se gia' nel manifest
 *   });
 *
 * @param {string} videoDir
 * @param {string} sceneName
 * @param {{ trimStart: number, clipFile?: string }} data
 */
function updateRecording(videoDir, sceneName, data) {
  const manifest = readManifest(videoDir);
  const scene = manifest.scenes.find((s) => s.name === sceneName);
  if (!scene) {
    throw new Error(`Scena "${sceneName}" non trovata nel manifest.`);
  }

  if (data.clipFile) {
    scene.recording.file = data.clipFile;
  }

  const clipPath = path.join(videoDir, scene.recording.file);
  if (!fs.existsSync(clipPath)) {
    throw new Error(`Clip non trovato: ${clipPath}`);
  }

  scene.recording.trim_start = parseFloat(data.trimStart.toFixed(3));
  scene.recording.clip_duration = getDurationRounded(clipPath);
  scene.recording.recorded_at = new Date().toISOString();

  writeManifest(videoDir, manifest);

  // Report
  const usable = scene.recording.clip_duration - scene.recording.trim_start;
  const needed = scene.vo.duration + scene.gap;
  const ok = usable >= needed - 0.15;
  console.log(
    `  ${ok ? "OK" : "ATTENZIONE"} ${scene.name}: clip ${scene.recording.clip_duration.toFixed(1)}s ` +
    `- trim ${scene.recording.trim_start.toFixed(1)}s = ${usable.toFixed(1)}s usabili ` +
    `(servono ${needed.toFixed(1)}s)${ok ? "" : " — RI-REGISTRARE"}`
  );

  return scene;
}

// ═══════════════════════════════════════════════════════════
// Exports
// ═══════════════════════════════════════════════════════════

module.exports = {
  // Percorsi
  FF,
  PROBE,
  VIDEOS_DIR,
  // FFprobe
  getDuration,
  getDurationRounded,
  // FFmpeg
  ff,
  // Manifest
  readManifest,
  writeManifest,
  // Validazione
  validateForMontage,
  // Recording helpers
  getSceneTiming,
  updateRecording,
};
