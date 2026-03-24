/**
 * Ricostruzione FASE 4 — Montaggio + Musica migliorata
 * Usa clip e VO già generati, ricostruisce solo video + audio mix.
 *
 * Fix: fade-in 0.3s per clip + xfade 0.6s + musica con progressione accordi
 *
 * Usage: node tools/scripts/rebuild-montaggio.js
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "../..");
const OUT = path.join(ROOT, "data/videos/primi-10-minuti");
const FF = "C:/Users/gvera/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1-full_build/bin/ffmpeg.exe";
const FFP = FF.replace("ffmpeg.exe", "ffprobe.exe");

function run(cmd) {
  const s = cmd.length > 160 ? cmd.substring(0, 157) + "..." : cmd;
  console.log(`  $ ${s}`);
  return execSync(cmd, { encoding: "utf8", stdio: "pipe", maxBuffer: 20 * 1024 * 1024 });
}
function dur(f) { return parseFloat(run(`"${FFP}" -v quiet -show_entries format=duration -of csv=p=0 "${f}"`).trim()); }

// Scene con durate reali dei clip
const SCENES = [
  { id: "01_hook",       dur: 10.70 },
  { id: "02_soluzione",  dur: 5.57 },
  { id: "03_cliente",    dur: 8.67 },
  { id: "04_anamnesi",   dur: 9.97 },
  { id: "05_contratto",  dur: 8.37 },
  { id: "06_cassa",      dur: 7.27 },
  { id: "07_safety",     dur: 10.87 },
  { id: "08_esercizi",   dur: 5.07 },
  { id: "09_nutrizione", dur: 7.97 },
  { id: "10_cta",        dur: 12.20 },
];

const XFADE = 0.6;   // crossfade più lungo = transizione più morbida
const FADE_IN = 0.3;  // fade-in su ogni clip = elimina flash residuo
const N = SCENES.length;
const mDir = path.join(OUT, "music");

async function main() {
  console.log("\n══ REBUILD MONTAGGIO ══\n");

  // ────────────────────────────────────────────
  // 1. MUSICA — progressione Am→F→C→G con build
  // ────────────────────────────────────────────
  console.log("🎵 Musica v2 — progressione accordi + build dinamico\n");

  const totalDur = SCENES.reduce((s, sc) => s + sc.dur, 0) - (N - 1) * XFADE;
  const MDUR = Math.ceil(totalDur) + 6;
  const BPM = 118;
  const beat = 60 / BPM;
  const bar = beat * 4; // 4/4

  // Accordi: Am(A2=110, C4=261.6, E4=329.6) → F(F2=87.3, A3=220, C4=261.6)
  //          → C(C3=130.8, E3=164.8, G3=196) → G(G2=98, B3=246.9, D4=293.7)
  // Ciclo di 4 battute, ripetuto
  const chords = [
    { root: 110,   third: 261.6, fifth: 329.6 }, // Am
    { root: 87.3,  third: 220,   fifth: 261.6 }, // F
    { root: 130.8, third: 164.8, fifth: 196   }, // C
    { root: 98,    third: 246.9, fifth: 293.7 }, // G
  ];

  // Pad — progressione accordi con evoluzione timbrica
  // Ogni battuta cambia accordo, ciclo di 4 battute
  const padExpr = chords.map((ch, i) => {
    const tStart = `(t/${bar}-floor(t/${bar}))`;  // posizione nella battuta corrente
    const chordIdx = `mod(floor(t/${bar}),4)`;     // indice accordo (0-3)
    return `if(eq(${chordIdx},${i}),` +
      `0.22*sin(2*PI*${ch.root}*t)+0.18*sin(2*PI*${ch.third}*t)+0.15*sin(2*PI*${ch.fifth}*t)+0.06*sin(2*PI*${ch.root*2}*t)` +
      `,0)`;
  }).join("+");

  run(`"${FF}" -y -f lavfi -i "aevalsrc='(${padExpr})*(0.12+0.28*sin(PI*t/${MDUR}))':s=44100:d=${MDUR}" -af "lowpass=f=4000,highpass=f=60,afade=t=in:st=0:d=3,afade=t=out:st=${MDUR - 4}:d=4" "${mDir}/pad2.wav"`);
  console.log("  ✓ Pad (progressione Am→F→C→G)");

  // Arpeggio — note singole in sequenza 16th note sulla progressione
  const arpExpr = chords.map((ch, i) => {
    const chordIdx = `mod(floor(t/${bar}),4)`;
    const noteInBar = `mod(floor(t/${beat}*4),4)`; // 4 note per battuta (16th=4 per beat... actually 16th = 1 per beat at this expression)
    // Arpeggio: root → third → fifth → octave
    const notes = [ch.root * 2, ch.third, ch.fifth, ch.root * 4];
    return `if(eq(${chordIdx},${i}),` +
      notes.map((n, j) => `if(eq(${noteInBar},${j}),0.12*sin(2*PI*${n}*t)*exp(-4*mod(t,${beat})),0)`).join("+") +
      `,0)`;
  }).join("+");

  run(`"${FF}" -y -f lavfi -i "aevalsrc='(${arpExpr})*min(1,max(0,(t-4)/4))':s=44100:d=${MDUR}" -af "highpass=f=200,lowpass=f=6000,volume=0.6,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/arp.wav"`);
  console.log("  ✓ Arpeggio (16th note arpeggiate)");

  // Sub-bass — segue la root della progressione
  const bassExpr = chords.map((ch, i) => {
    const chordIdx = `mod(floor(t/${bar}),4)`;
    return `if(eq(${chordIdx},${i}),0.35*sin(2*PI*${ch.root / 2}*t),0)`;
  }).join("+");

  run(`"${FF}" -y -f lavfi -i "aevalsrc='(${bassExpr})*(0.4+0.3*sin(2*PI*${(1/beat).toFixed(4)}*t))*min(1,max(0,(t-3)/3))':s=44100:d=${MDUR}" -af "lowpass=f=140,volume=0.5,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/bass2.wav"`);
  console.log("  ✓ Sub-bass (root della progressione)");

  // Kick — entra a 6s, più presente
  run(`"${FF}" -y -f lavfi -i "aevalsrc='0.8*sin(2*PI*(200-170*mod(t,${beat.toFixed(6)})/${beat.toFixed(6)})*t)*exp(-12*mod(t,${beat.toFixed(6)}))':s=44100:d=${MDUR}" -af "lowpass=f=200,volume='if(lt(t,6),0,min(1,(t-6)/2))':eval=frame,volume=0.5,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/kick2.wav"`);
  console.log("  ✓ Kick (punchier, entra a 6s)");

  // Clap/snare — ogni 2° e 4° beat
  const clapBeat = beat * 2;
  run(`"${FF}" -y -f lavfi -i "anoisesrc=d=0.08:c=white:a=0.3" -af "bandpass=f=1200:w=800,volume='exp(-25*t)':eval=frame,aloop=loop=${Math.ceil(MDUR / clapBeat)}:size=${Math.floor(clapBeat * 44100)},atrim=0:${MDUR},adelay=${Math.round(beat * 1000)}|${Math.round(beat * 1000)},volume='if(lt(t,8),0,min(1,(t-8)/3))':eval=frame,volume=0.35,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/clap.wav"`);
  console.log("  ✓ Clap (beat 2 & 4, entra a 8s)");

  // Hihat — 8th note, leggero
  const hh = beat / 2;
  run(`"${FF}" -y -f lavfi -i "anoisesrc=d=${hh.toFixed(4)}:c=white:a=0.12" -af "highpass=f=10000,lowpass=f=16000,volume='exp(-25*mod(t,${hh.toFixed(6)}))':eval=frame,aloop=loop=${Math.ceil(MDUR / hh)}:size=${Math.floor(hh * 44100)},atrim=0:${MDUR},volume='if(lt(t,10),0,min(1,(t-10)/4))':eval=frame,volume=0.12,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/hh2.wav"`);
  console.log("  ✓ Hihat (8th note, entra a 10s)");

  // Riser/shimmer — ultimi 15s, build verso il CTA
  const riserStart = MDUR - 15;
  run(`"${FF}" -y -f lavfi -i "aevalsrc='(0.08*sin(2*PI*880*t)*sin(2*PI*0.4*t)+0.06*sin(2*PI*1320*t)*sin(2*PI*0.25*t)+0.04*sin(2*PI*1760*t)*sin(2*PI*0.15*t))':s=44100:d=${MDUR}" -af "volume='if(lt(t,${riserStart}),0,min(1,(t-${riserStart})/4)*min(1,max(0,(${MDUR}-t)/3)))':eval=frame,highpass=f=800,lowpass=f=8000" "${mDir}/riser.wav"`);
  console.log("  ✓ Riser (build finale ultimi 15s)");

  // Mix 7 layer
  const bgMusic = path.join(OUT, "music-v2.wav");
  run(`"${FF}" -y ` +
    `-i "${mDir}/pad2.wav" -i "${mDir}/arp.wav" -i "${mDir}/bass2.wav" ` +
    `-i "${mDir}/kick2.wav" -i "${mDir}/clap.wav" -i "${mDir}/hh2.wav" -i "${mDir}/riser.wav" ` +
    `-filter_complex "` +
    `[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[p];` +
    `[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a];` +
    `[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[b];` +
    `[3:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[k];` +
    `[4:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[c];` +
    `[5:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[h];` +
    `[6:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[r];` +
    `[p][a][b][k][c][h][r]amix=inputs=7:duration=first:normalize=0,` +
    `alimiter=limit=0.9,` +
    `equalizer=f=80:t=q:w=1:g=3,` +    // boost sub
    `equalizer=f=3000:t=q:w=1.5:g=2,` + // boost presence
    `equalizer=f=10000:t=q:w=2:g=1.5` +  // boost air
    `" -c:a pcm_f32le "${bgMusic}"`);
  console.log(`\n  ✓ Mix musicale: ${dur(bgMusic).toFixed(1)}s (7 layer, Am→F→C→G)\n`);

  // ────────────────────────────────────────────
  // 2. VIDEO — xfade con fade-in per clip
  // ────────────────────────────────────────────
  console.log("🎞️  Video crossfade v2 (fade-in + xfade 0.6s)\n");

  const clips = SCENES.map(s => `${path.join(OUT, "clips", s.id + ".mp4").replace(/\\/g, "/")}`);

  // Fase pre: ogni input ottiene fade-in 0.3s per eliminare flash residuo
  const inputs = clips.map((f, i) => `-i "${f}"`).join(" ");
  const preFade = SCENES.map((s, i) =>
    `[${i}:v]fade=t=in:st=0:d=${FADE_IN}:color=black,fade=t=out:st=${(s.dur - FADE_IN).toFixed(2)}:d=${FADE_IN}:color=black[f${i}]`
  );

  // Catena xfade sugli output pre-faded
  const xfadeParts = [];
  let offset = SCENES[0].dur - XFADE;
  for (let i = 1; i < N; i++) {
    const inL = i === 1 ? "[f0]" : `[xf${i}]`;
    const inR = `[f${i}]`;
    const outLabel = i === N - 1 ? "[xfraw]" : `[xf${i + 1}]`;
    xfadeParts.push(`${inL}${inR}xfade=transition=fade:duration=${XFADE}:offset=${offset.toFixed(2)}${outLabel}`);
    offset += SCENES[i].dur - XFADE;
  }

  const fullFilter = [...preFade, ...xfadeParts, `[xfraw]format=yuv420p[vout]`].join(";");

  const silentVideo = path.join(OUT, "silent.mp4");
  run(`"${FF}" -y ${inputs} -filter_complex "${fullFilter}" -map "[vout]" -c:v libx264 -preset medium -crf 20 -movflags +faststart "${silentVideo}"`);
  const vidDur = dur(silentVideo);
  console.log(`\n  ✓ Video: ${vidDur.toFixed(1)}s (xfade=${XFADE}s, fade-in=${FADE_IN}s)\n`);

  // ────────────────────────────────────────────
  // 3. VO GAPPED — ricalcolo offset con xfade
  // ────────────────────────────────────────────
  console.log("🎙️  VO gapped (offset compensati)\n");

  const voInputs = SCENES.map((s, i) => `-i "${path.join(OUT, "scenes", s.id + ".mp3")}"`).join(" ");
  const voFmt = SCENES.map((_, i) => `[${i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[v${i}]`);

  let cumMs = 0;
  const voDelay = SCENES.map((s, i) => {
    const part = cumMs > 0
      ? `[v${i}]adelay=${Math.round(cumMs)}|${Math.round(cumMs)}[d${i}]`
      : `[v${i}]acopy[d${i}]`;
    cumMs += (s.dur - (i < N - 1 ? XFADE : 0)) * 1000;
    return part;
  });

  const voMix = SCENES.map((_, i) => `[d${i}]`).join("");
  const voFilter = [...voFmt, ...voDelay, `${voMix}amix=inputs=${N}:duration=longest:normalize=0[out]`].join(";");

  const voGapped = path.join(OUT, "voiceover-gapped.mp3");
  run(`"${FF}" -y ${voInputs} -filter_complex "${voFilter}" -map "[out]" -c:a libmp3lame -b:a 192k "${voGapped}"`);
  console.log(`  ✓ VO gapped: ${dur(voGapped).toFixed(1)}s\n`);

  // ────────────────────────────────────────────
  // 4. MIX FINALE
  // ────────────────────────────────────────────
  console.log("🎬 Mix finale\n");

  const fadeSt = (vidDur - 3).toFixed(1);
  const final = path.join(OUT, "primi-10-minuti.mp4");
  run(
    `"${FF}" -y -i "${silentVideo}" -i "${voGapped}" -i "${bgMusic}" ` +
    `-filter_complex "` +
    `[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=1.0[voice];` +
    `[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,atrim=0:${vidDur.toFixed(1)},asetpts=PTS-STARTPTS,volume=0.22,afade=t=out:st=${fadeSt}:d=3[music];` +
    `[voice][music]sidechaincompress=threshold=0.02:ratio=4:attack=50:release=300[aout]" ` +
    `-map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "${final}"`
  );

  const finalDur = dur(final);
  const finalSize = (fs.statSync(final).size / 1024 / 1024).toFixed(1);

  console.log(`\n${"═".repeat(50)}`);
  console.log(`  ✅ REBUILD COMPLETATO`);
  console.log(`${"═".repeat(50)}`);
  console.log(`  File:    primi-10-minuti.mp4`);
  console.log(`  Durata:  ${finalDur.toFixed(1)}s`);
  console.log(`  Peso:    ${finalSize} MB`);
  console.log(`  Video:   H.264 High yuv420p, xfade 0.6s`);
  console.log(`  Audio:   VO + musica 7-layer (Am→F→C→G)`);
  console.log(`${"═".repeat(50)}`);
}

main().catch(err => { console.error("FATAL:", err); process.exit(1); });
