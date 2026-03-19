import { useState, useMemo, useCallback, useRef, useEffect } from "react";

const TAU = 2 * Math.PI;

// --- Color Palette: "Oscilloscope" aesthetic ---
const C = {
  bg: "#0a0e17",
  panel: "#111827",
  panelBorder: "#1e293b",
  grid: "#1a2236",
  gridLine: "#1e2d4a",
  signal: "#22d3ee",
  signalGlow: "#22d3ee44",
  sampled: "#f59e0b",
  sampledGlow: "#f59e0b44",
  reconstructed: "#a78bfa",
  reconstructedGlow: "#a78bfa33",
  alias: "#ef4444",
  aliasGlow: "#ef444444",
  text: "#e2e8f0",
  textDim: "#64748b",
  accent: "#22d3ee",
  accentWarm: "#f59e0b",
  sliderTrack: "#1e293b",
  sliderThumb: "#22d3ee",
  nyquistLine: "#ef4444",
  ok: "#10b981",
  warn: "#f59e0b",
  danger: "#ef4444",
};

// --- Signal generators ---
const signals = {
  senoidal: {
    label: "Senoidal",
    fn: (t, f) => Math.sin(TAU * f * t),
    bandwidth: (f) => f,
    desc: "Señal pura de una frecuencia",
    spectrum: (f) => [{ freq: f, amp: 1 }],
  },
  cuadrada: {
    label: "Cuadrada",
    fn: (t, f) => {
      let s = 0;
      for (let k = 1; k <= 15; k += 2) s += Math.sin(TAU * k * f * t) / k;
      return s * (4 / Math.PI);
    },
    bandwidth: (f) => f * 15,
    desc: "Armónicos impares hasta 15°",
    spectrum: (f) => {
      const r = [];
      for (let k = 1; k <= 15; k += 2) r.push({ freq: k * f, amp: 4 / (Math.PI * k) });
      return r;
    },
  },
  triangular: {
    label: "Triangular",
    fn: (t, f) => {
      let s = 0;
      for (let k = 0; k < 8; k++) {
        const n = 2 * k + 1;
        s += ((-1) ** k * Math.sin(TAU * n * f * t)) / (n * n);
      }
      return s * (8 / (Math.PI * Math.PI));
    },
    bandwidth: (f) => f * 15,
    desc: "Armónicos impares, decaen como 1/n²",
    spectrum: (f) => {
      const r = [];
      for (let k = 0; k < 8; k++) {
        const n = 2 * k + 1;
        r.push({ freq: n * f, amp: 8 / (Math.PI * Math.PI * n * n) });
      }
      return r;
    },
  },
  multitono: {
    label: "Multitono",
    fn: (t, f) => 0.5 * Math.sin(TAU * f * t) + 0.3 * Math.sin(TAU * 2.5 * f * t) + 0.2 * Math.sin(TAU * 4 * f * t),
    bandwidth: (f) => f * 4,
    desc: "Suma de 3 senoidales: f, 2.5f, 4f",
    spectrum: (f) => [
      { freq: f, amp: 0.5 },
      { freq: 2.5 * f, amp: 0.3 },
      { freq: 4 * f, amp: 0.2 },
    ],
  },
};

// --- Sinc reconstruction ---
function reconstruct(sampleTimes, sampleValues, fs, t) {
  let val = 0;
  for (let i = 0; i < sampleTimes.length; i++) {
    const x = fs * (t - sampleTimes[i]);
    const sinc = Math.abs(x) < 1e-9 ? 1 : Math.sin(Math.PI * x) / (Math.PI * x);
    val += sampleValues[i] * sinc;
  }
  return val;
}

// --- SVG Chart component ---
function Chart({ signalFn, fSignal, fs, signalType, showReconstructed }) {
  const W = 800, H = 260, pad = { l: 48, r: 16, t: 16, b: 32 };
  const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;
  const duration = 3 / Math.max(fSignal, 0.5);
  const N = 500;

  const data = useMemo(() => {
    const pts = [];
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * duration;
      pts.push({ t, y: signalFn(t, fSignal) });
    }
    return pts;
  }, [signalFn, fSignal, duration]);

  const samples = useMemo(() => {
    if (fs <= 0) return [];
    const s = [];
    const dt = 1 / fs;
    for (let t = 0; t <= duration + dt; t += dt) {
      if (t <= duration) s.push({ t, y: signalFn(t, fSignal) });
    }
    return s;
  }, [signalFn, fSignal, fs, duration]);

  const reconstructedPts = useMemo(() => {
    if (!showReconstructed || samples.length < 2) return [];
    const times = samples.map((s) => s.t);
    const vals = samples.map((s) => s.y);
    const pts = [];
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * duration;
      pts.push({ t, y: reconstruct(times, vals, fs, t) });
    }
    return pts;
  }, [showReconstructed, samples, fs, duration]);

  const yMax = 1.3;
  const tx = (t) => pad.l + (t / duration) * pw;
  const ty = (y) => pad.t + ph / 2 - (y / yMax) * (ph / 2);

  const toPath = (pts) =>
    pts.map((p, i) => `${i === 0 ? "M" : "L"}${tx(p.t).toFixed(1)},${ty(p.y).toFixed(1)}`).join(" ");

  const gridLinesY = [-1, -0.5, 0, 0.5, 1];
  const gridLinesX = [];
  const step = duration / 6;
  for (let i = 0; i <= 6; i++) gridLinesX.push(i * step);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }}>
      <rect width={W} height={H} fill={C.bg} rx="8" />
      {/* Grid */}
      {gridLinesY.map((v) => (
        <line key={v} x1={pad.l} x2={W - pad.r} y1={ty(v)} y2={ty(v)} stroke={C.gridLine} strokeWidth="0.5" />
      ))}
      {gridLinesX.map((v, i) => (
        <line key={i} x1={tx(v)} x2={tx(v)} y1={pad.t} y2={H - pad.b} stroke={C.gridLine} strokeWidth="0.5" />
      ))}
      {/* Y axis labels */}
      {gridLinesY.map((v) => (
        <text key={v} x={pad.l - 6} y={ty(v) + 4} fill={C.textDim} fontSize="10" textAnchor="end" fontFamily="monospace">
          {v.toFixed(1)}
        </text>
      ))}
      {/* X axis labels */}
      {gridLinesX.map((v, i) => (
        <text key={i} x={tx(v)} y={H - pad.b + 16} fill={C.textDim} fontSize="9" textAnchor="middle" fontFamily="monospace">
          {(v * 1000).toFixed(0)}ms
        </text>
      ))}
      {/* Original signal glow + line */}
      <path d={toPath(data)} fill="none" stroke={C.signalGlow} strokeWidth="6" />
      <path d={toPath(data)} fill="none" stroke={C.signal} strokeWidth="1.5" strokeLinejoin="round" />
      {/* Reconstructed */}
      {showReconstructed && reconstructedPts.length > 0 && (
        <>
          <path d={toPath(reconstructedPts)} fill="none" stroke={C.reconstructedGlow} strokeWidth="5" />
          <path d={toPath(reconstructedPts)} fill="none" stroke={C.reconstructed} strokeWidth="1.5" strokeDasharray="6 3" />
        </>
      )}
      {/* Sample stems */}
      {samples.map((s, i) => (
        <g key={i}>
          <line x1={tx(s.t)} x2={tx(s.t)} y1={ty(0)} y2={ty(s.y)} stroke={C.sampled} strokeWidth="1" opacity="0.5" />
          <circle cx={tx(s.t)} cy={ty(s.y)} r="3.5" fill={C.bg} stroke={C.sampled} strokeWidth="1.5" />
          <circle cx={tx(s.t)} cy={ty(s.y)} r="1.5" fill={C.sampled} />
        </g>
      ))}
    </svg>
  );
}

// --- Spectrum chart ---
function Spectrum({ signalType, fSignal, fs }) {
  const W = 800, H = 180, pad = { l: 48, r: 16, t: 20, b: 36 };
  const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;

  const sig = signals[signalType];
  const components = sig.spectrum(fSignal);
  const nyquist = fs / 2;
  const maxFreq = Math.max(nyquist * 1.5, sig.bandwidth(fSignal) * 1.3, fSignal * 2);

  const tx = (f) => pad.l + (f / maxFreq) * pw;
  const ty = (a) => pad.t + ph - a * ph;

  const freqTicks = [];
  const tickStep = maxFreq < 50 ? 5 : maxFreq < 200 ? 20 : maxFreq < 500 ? 50 : 100;
  for (let f = 0; f <= maxFreq; f += tickStep) freqTicks.push(f);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }}>
      <rect width={W} height={H} fill={C.bg} rx="8" />
      {/* Grid */}
      <line x1={pad.l} x2={W - pad.r} y1={ty(0)} y2={ty(0)} stroke={C.gridLine} strokeWidth="0.5" />
      {freqTicks.map((f, i) => (
        <g key={i}>
          <line x1={tx(f)} x2={tx(f)} y1={pad.t} y2={ty(0)} stroke={C.gridLine} strokeWidth="0.5" />
          <text x={tx(f)} y={ty(0) + 14} fill={C.textDim} fontSize="9" textAnchor="middle" fontFamily="monospace">
            {f}
          </text>
        </g>
      ))}
      <text x={W / 2} y={H - 2} fill={C.textDim} fontSize="10" textAnchor="middle" fontFamily="monospace">
        Frecuencia (Hz)
      </text>
      {/* Nyquist line */}
      <line x1={tx(nyquist)} x2={tx(nyquist)} y1={pad.t} y2={ty(0)} stroke={C.nyquistLine} strokeWidth="1.5" strokeDasharray="6 4" />
      <text x={tx(nyquist)} y={pad.t - 4} fill={C.nyquistLine} fontSize="9" textAnchor="middle" fontFamily="monospace" fontWeight="bold">
        f_N = {nyquist.toFixed(0)} Hz
      </text>
      {/* Spectral lines */}
      {components.map((c, i) => {
        const isAliased = c.freq > nyquist;
        const color = isAliased ? C.alias : C.signal;
        return (
          <g key={i}>
            <line x1={tx(c.freq)} x2={tx(c.freq)} y1={ty(0)} y2={ty(c.amp)} stroke={color} strokeWidth="2.5" />
            <circle cx={tx(c.freq)} cy={ty(c.amp)} r="3" fill={color} />
            {isAliased && (
              <text x={tx(c.freq)} y={ty(c.amp) - 8} fill={C.alias} fontSize="8" textAnchor="middle" fontFamily="monospace">
                ALIAS
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

// --- Slider ---
function Slider({ label, value, min, max, step, onChange, unit, color }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ color: C.textDim, fontSize: 12, fontFamily: "'JetBrains Mono', monospace" }}>{label}</span>
        <span style={{ color: color || C.accent, fontSize: 13, fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
          {value} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          width: "100%",
          accentColor: color || C.accent,
          height: 6,
          cursor: "pointer",
        }}
      />
    </div>
  );
}

// --- Status badge ---
function NyquistBadge({ fs, bw }) {
  const ratio = fs / (2 * bw);
  let status, color, label, explanation;
  if (ratio >= 2) {
    status = "ok";
    color = C.ok;
    label = "SOBREMUESTREO";
    explanation = `fs = ${(ratio * 2).toFixed(1)}× BW — Reconstrucción excelente`;
  } else if (ratio >= 1) {
    status = "ok";
    color = C.ok;
    label = "NYQUIST OK";
    explanation = `fs ≥ 2·BW — Se cumple el criterio de Nyquist`;
  } else if (ratio >= 0.7) {
    status = "warn";
    color = C.warn;
    label = "SUBMUESTREO LEVE";
    explanation = `fs < 2·BW — Aparece aliasing parcial`;
  } else {
    status = "danger";
    color = C.danger;
    label = "ALIASING SEVERO";
    explanation = `fs << 2·BW — Señal irrecuperable`;
  }

  return (
    <div
      style={{
        background: `${color}11`,
        border: `1px solid ${color}44`,
        borderRadius: 8,
        padding: "10px 14px",
        marginBottom: 12,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: color,
            boxShadow: `0 0 8px ${color}`,
            animation: status === "danger" ? "pulse 1s infinite" : "none",
          }}
        />
        <span style={{ color, fontSize: 12, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", letterSpacing: 1 }}>
          {label}
        </span>
      </div>
      <div style={{ color: C.textDim, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }}>{explanation}</div>
    </div>
  );
}

// --- Info panel ---
function InfoPanel({ fSignal, fs, signalType }) {
  const sig = signals[signalType];
  const bw = sig.bandwidth(fSignal);
  const nyq = 2 * bw;

  return (
    <div
      style={{
        background: C.panel,
        border: `1px solid ${C.panelBorder}`,
        borderRadius: 8,
        padding: 14,
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
        color: C.textDim,
        lineHeight: 1.7,
      }}
    >
      <div style={{ color: C.text, fontWeight: 700, marginBottom: 6, fontSize: 12 }}>📐 Parámetros</div>
      <div>
        Ancho de banda: <span style={{ color: C.signal }}>{bw.toFixed(0)} Hz</span>
      </div>
      <div>
        Nyquist mínimo: <span style={{ color: C.nyquistLine }}>fs ≥ {nyq.toFixed(0)} Hz</span>
      </div>
      <div>
        Frecuencia de muestreo: <span style={{ color: C.accentWarm }}>{fs} Hz</span>
      </div>
      <div>
        Muestras/período:{" "}
        <span style={{ color: C.text }}>{fSignal > 0 ? (fs / fSignal).toFixed(1) : "∞"}</span>
      </div>
      <div style={{ marginTop: 8, borderTop: `1px solid ${C.panelBorder}`, paddingTop: 8 }}>
        <span style={{ color: C.text, fontWeight: 600 }}>Teorema de Nyquist-Shannon:</span>
        <br />
        Para reconstruir una señal de ancho de banda B sin aliasing, se requiere fs ≥ 2B.
      </div>
    </div>
  );
}

// --- Main ---
export default function SamplingSimulator() {
  const [signalType, setSignalType] = useState("senoidal");
  const [fSignal, setFSignal] = useState(10);
  const [fs, setFs] = useState(25);
  const [showReconstructed, setShowReconstructed] = useState(true);

  const sig = signals[signalType];
  const bw = sig.bandwidth(fSignal);

  return (
    <div
      style={{
        background: C.bg,
        minHeight: "100vh",
        color: C.text,
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        padding: "20px 16px",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;500;700&display=swap');
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        input[type=range] {
          -webkit-appearance: none;
          appearance: none;
          background: ${C.sliderTrack};
          border-radius: 4px;
          outline: none;
        }
        input[type=range]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 16px; height: 16px;
          border-radius: 50%;
          background: var(--thumb, ${C.accent});
          cursor: pointer;
          border: 2px solid ${C.bg};
        }
        .signal-btn {
          background: ${C.panel};
          border: 1px solid ${C.panelBorder};
          color: ${C.textDim};
          padding: 6px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          font-family: 'JetBrains Mono', monospace;
          transition: all 0.2s;
        }
        .signal-btn:hover { border-color: ${C.accent}66; color: ${C.text}; }
        .signal-btn.active {
          background: ${C.accent}18;
          border-color: ${C.accent};
          color: ${C.accent};
        }
        .toggle-btn {
          background: ${C.panel};
          border: 1px solid ${C.panelBorder};
          color: ${C.textDim};
          padding: 6px 14px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 11px;
          font-family: 'JetBrains Mono', monospace;
          transition: all 0.2s;
        }
        .toggle-btn.active {
          background: ${C.reconstructed}18;
          border-color: ${C.reconstructed};
          color: ${C.reconstructed};
        }
      `}</style>

      <div style={{ maxWidth: 860, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <h1
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontWeight: 700,
              fontSize: 26,
              letterSpacing: -0.5,
              margin: 0,
              background: `linear-gradient(135deg, ${C.signal}, ${C.reconstructed})`,
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Simulador de Muestreo
          </h1>
          <p style={{ color: C.textDim, fontSize: 13, margin: "4px 0 0", fontFamily: "'JetBrains Mono', monospace" }}>
            Teorema de Nyquist-Shannon · Aliasing · Reconstrucción
          </p>
        </div>

        {/* Signal selector */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16, justifyContent: "center" }}>
          {Object.entries(signals).map(([key, s]) => (
            <button key={key} className={`signal-btn ${signalType === key ? "active" : ""}`} onClick={() => setSignalType(key)}>
              {s.label}
            </button>
          ))}
        </div>
        <div style={{ textAlign: "center", color: C.textDim, fontSize: 11, marginBottom: 16, fontFamily: "'JetBrains Mono', monospace" }}>
          {sig.desc}
        </div>

        {/* Charts */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: C.textDim, fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
              DOMINIO TEMPORAL
            </span>
            <div style={{ flex: 1, height: 1, background: C.panelBorder }} />
            <button
              className={`toggle-btn ${showReconstructed ? "active" : ""}`}
              onClick={() => setShowReconstructed(!showReconstructed)}
            >
              {showReconstructed ? "◉" : "○"} Reconstrucción
            </button>
          </div>
          <Chart signalFn={sig.fn} fSignal={fSignal} fs={fs} signalType={signalType} showReconstructed={showReconstructed} />
          <div style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 6, fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }}>
            <span>
              <span style={{ color: C.signal }}>━━</span> Original
            </span>
            <span>
              <span style={{ color: C.sampled }}>●</span> Muestras
            </span>
            {showReconstructed && (
              <span>
                <span style={{ color: C.reconstructed }}>╌╌</span> Reconstruida
              </span>
            )}
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: C.textDim, fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
              ESPECTRO DE FRECUENCIA
            </span>
            <div style={{ flex: 1, height: 1, background: C.panelBorder }} />
          </div>
          <Spectrum signalType={signalType} fSignal={fSignal} fs={fs} />
          <div style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 6, fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }}>
            <span>
              <span style={{ color: C.signal }}>|</span> Componente
            </span>
            <span>
              <span style={{ color: C.alias }}>|</span> Aliased
            </span>
            <span>
              <span style={{ color: C.nyquistLine }}>┊</span> Nyquist (fs/2)
            </span>
          </div>
        </div>

        {/* Controls + Info */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div style={{ background: C.panel, border: `1px solid ${C.panelBorder}`, borderRadius: 8, padding: 16 }}>
            <Slider
              label="Frecuencia de señal (f)"
              value={fSignal}
              min={1}
              max={100}
              step={1}
              onChange={setFSignal}
              unit="Hz"
              color={C.signal}
            />
            <Slider
              label="Frecuencia de muestreo (fs)"
              value={fs}
              min={2}
              max={500}
              step={1}
              onChange={setFs}
              unit="Hz"
              color={C.accentWarm}
            />
            <div style={{ marginTop: 8 }}>
              <NyquistBadge fs={fs} bw={bw} />
            </div>
          </div>
          <InfoPanel fSignal={fSignal} fs={fs} signalType={signalType} />
        </div>

        {/* Exercises */}
        <div
          style={{
            marginTop: 20,
            background: C.panel,
            border: `1px solid ${C.panelBorder}`,
            borderRadius: 8,
            padding: 16,
          }}
        >
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: 12, marginBottom: 10, color: C.accent }}>
            🧪 ACTIVIDADES SUGERIDAS
          </div>
          <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.8, fontFamily: "'JetBrains Mono', monospace" }}>
            <div>
              <strong style={{ color: C.text }}>1.</strong> Con señal senoidal de 10 Hz, encuentre la fs mínima para evitar aliasing. ¿Qué pasa con fs = 19 Hz?
            </div>
            <div>
              <strong style={{ color: C.text }}>2.</strong> Compare la señal cuadrada vs senoidal a 10 Hz. ¿Por qué la cuadrada necesita mayor fs?
            </div>
            <div>
              <strong style={{ color: C.text }}>3.</strong> Con la señal multitono, halle fs tal que solo la componente de 4f tenga aliasing.
            </div>
            <div>
              <strong style={{ color: C.text }}>4.</strong> Active la reconstrucción y observe cómo se degrada al bajar fs por debajo de Nyquist.
            </div>
            <div>
              <strong style={{ color: C.text }}>5.</strong> Para cada tipo de señal, determine el ancho de banda y verifique el criterio de Nyquist.
            </div>
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: 16, fontSize: 10, color: C.textDim, fontFamily: "'JetBrains Mono', monospace" }}>
          Ingeniería Electrónica · Sistemas de Comunicaciones & Control
        </div>
      </div>
    </div>
  );
}
