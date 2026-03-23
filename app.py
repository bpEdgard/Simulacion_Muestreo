import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Simulador de Muestreo",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilo ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0a0e17; }
    .stApp { background-color: #0a0e17; color: #e2e8f0; }
    div[data-testid="stSidebar"] { background-color: #111827; }
    .metric-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
        font-family: 'Courier New', monospace;
    }
    .badge-ok {
        background: #10b98118;
        border: 1px solid #10b98144;
        border-radius: 8px;
        padding: 10px 14px;
        color: #10b981;
        font-family: 'Courier New', monospace;
    }
    .badge-warn {
        background: #f59e0b18;
        border: 1px solid #f59e0b44;
        border-radius: 8px;
        padding: 10px 14px;
        color: #f59e0b;
        font-family: 'Courier New', monospace;
    }
    .badge-danger {
        background: #ef444418;
        border: 1px solid #ef444444;
        border-radius: 8px;
        padding: 10px 14px;
        color: #ef4444;
        font-family: 'Courier New', monospace;
    }
    .activities-box {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# ─── Definición de señales ────────────────────────────────────────────────────
SIGNALS = {
    "Senoidal": {
        "desc": "Señal pura de una frecuencia",
        "bandwidth": lambda f: f,
        "fn": lambda t, f: np.sin(2 * np.pi * f * t),
        "spectrum": lambda f: [(f, 1.0)],
    },
    "Cuadrada": {
        "desc": "Armónicos impares hasta el 15°",
        "bandwidth": lambda f: 15 * f,
        "fn": lambda t, f: sum(
            np.sin(2 * np.pi * k * f * t) / k for k in range(1, 16, 2)
        ) * (4 / np.pi),
        "spectrum": lambda f: [(k * f, 4 / (np.pi * k)) for k in range(1, 16, 2)],
    },
    "Triangular": {
        "desc": "Armónicos impares, decaen como 1/n²",
        "bandwidth": lambda f: 15 * f,
        "fn": lambda t, f: sum(
            ((-1) ** k * np.sin(2 * np.pi * (2 * k + 1) * f * t)) / (2 * k + 1) ** 2
            for k in range(8)
        ) * (8 / np.pi**2),
        "spectrum": lambda f: [
            ((2 * k + 1) * f, 8 / (np.pi**2 * (2 * k + 1) ** 2)) for k in range(8)
        ],
    },
    "Multitono": {
        "desc": "Suma de 3 senoidales: f, 2.5f, 4f",
        "bandwidth": lambda f: 4 * f,
        "fn": lambda t, f: (
            0.5 * np.sin(2 * np.pi * f * t)
            + 0.3 * np.sin(2 * np.pi * 2.5 * f * t)
            + 0.2 * np.sin(2 * np.pi * 4 * f * t)
        ),
        "spectrum": lambda f: [(f, 0.5), (2.5 * f, 0.3), (4 * f, 0.2)],
    },
}

# ─── Reconstrucción por interpolación sinc ────────────────────────────────────
def sinc_reconstruct(t_samples, y_samples, fs, t_cont):
    result = np.zeros_like(t_cont, dtype=float)
    for ti, yi in zip(t_samples, y_samples):
        x = fs * (t_cont - ti)
        with np.errstate(invalid="ignore", divide="ignore"):
            sinc = np.where(np.abs(x) < 1e-9, 1.0, np.sin(np.pi * x) / (np.pi * x))
        result += yi * sinc
    return result

# ─── Badge de Nyquist ─────────────────────────────────────────────────────────
def nyquist_badge(fs, bw):
    ratio = fs / (2 * bw)
    if ratio >= 2:
        label = "SOBREMUESTREO"
        css = "badge-ok"
        msg = f"fs = {ratio * 2:.1f}× BW — Reconstrucción excelente"
    elif ratio >= 1:
        label = "NYQUIST OK"
        css = "badge-ok"
        msg = f"fs ≥ 2·BW — Se cumple el criterio de Nyquist"
    elif ratio >= 0.7:
        label = "SUBMUESTREO LEVE"
        css = "badge-warn"
        msg = f"fs < 2·BW — Aparece aliasing parcial"
    else:
        label = "⚠ ALIASING SEVERO"
        css = "badge-danger"
        msg = f"fs << 2·BW — Señal irrecuperable"
    st.markdown(
        f'<div class="{css}"><strong>{label}</strong><br><span style="font-size:11px">{msg}</span></div>',
        unsafe_allow_html=True,
    )

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("FaIn UNCo fondo transparente.png", use_container_width=True)
    st.markdown("## ⚙️ Parámetros")

    signal_name = st.selectbox("Tipo de señal", list(SIGNALS.keys()))
    sig = SIGNALS[signal_name]

    st.caption(f"_{sig['desc']}_")
    st.divider()

    f0 = st.slider("Frecuencia de señal  f₀ (Hz)", 1, 100, 10, 1)
    fs = st.slider("Frecuencia de muestreo  fs (Hz)", 2, 500, 25, 1)
    show_rec = st.toggle("Mostrar reconstrucción sinc", value=True)
    st.divider()

    bw = sig["bandwidth"](f0)
    nyquist_badge(fs, bw)

    st.divider()
    st.markdown(f"""
    <div style="font-family:'Courier New',monospace; font-size:12px; color:#64748b; line-height:1.8">
    <b style="color:#e2e8f0">📐 Parámetros</b><br>
    Ancho de banda: <span style="color:#22d3ee">{bw:.0f} Hz</span><br>
    Nyquist mínimo: <span style="color:#ef4444">fs ≥ {2*bw:.0f} Hz</span><br>
    Frec. de muestreo: <span style="color:#f59e0b">{fs} Hz</span><br>
    Muestras/período: <span style="color:#e2e8f0">{fs/f0:.1f}</span>
    </div>
    """, unsafe_allow_html=True)

# ─── Cuerpo principal ─────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='text-align:center; font-family:sans-serif; "
    "background:linear-gradient(135deg,#22d3ee,#a78bfa); "
    "-webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:2px'>"
    "Simulador de Muestreo</h1>"
    "<p style='text-align:center; color:#64748b; font-family:monospace; font-size:13px; margin-top:0'>"
    "Teorema de Nyquist-Shannon · Aliasing · Reconstrucción</p>",
    unsafe_allow_html=True,
)

# ─── Generación de señal ──────────────────────────────────────────────────────
duration = 3 / max(f0, 0.5)
t_cont = np.linspace(0, duration, 2000)
t_samp = np.arange(0, duration + 1 / fs, 1 / fs)
t_samp = t_samp[t_samp <= duration]

y_cont = sig["fn"](t_cont, f0)
y_samp = sig["fn"](t_samp, f0)
y_rec = sinc_reconstruct(t_samp, y_samp, fs, t_cont) if show_rec else None

# ─── Paleta ───────────────────────────────────────────────────────────────────
C = {
    "bg": "#0a0e17",
    "grid": "#1e2d4a",
    "signal": "#22d3ee",
    "sampled": "#f59e0b",
    "rec": "#a78bfa",
    "alias": "#ef4444",
    "nyquist": "#ef4444",
    "paper": "#0f172a",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=C["paper"],
    plot_bgcolor=C["bg"],
    font=dict(color="#e2e8f0", family="Courier New, monospace"),
    margin=dict(l=50, r=20, t=40, b=40),
    hovermode="x unified",
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e293b"),
)
AXIS_STYLE = dict(gridcolor=C["grid"], zerolinecolor=C["grid"])

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Dominio del tiempo", "📊 Espectro de frecuencia", "🔬 Interpolación sinc", "🔁 Espectro replicado", "🎛️ Señal reconstruida"])

# ─── Tab 1: Tiempo ────────────────────────────────────────────────────────────
with tab1:
    fig = go.Figure()

    # Señal original
    fig.add_trace(go.Scatter(
        x=t_cont * 1000, y=y_cont,
        name="Original",
        line=dict(color=C["signal"], width=2),
    ))

    # Reconstrucción sinc
    if show_rec and y_rec is not None:
        fig.add_trace(go.Scatter(
            x=t_cont * 1000, y=y_rec,
            name="Reconstruida (sinc)",
            line=dict(color=C["rec"], width=2, dash="dash"),
        ))

    # Stems
    stem_x, stem_y = [], []
    for ti, yi in zip(t_samp, y_samp):
        stem_x += [ti * 1000, ti * 1000, None]
        stem_y += [0, yi, None]

    fig.add_trace(go.Scatter(
        x=stem_x, y=stem_y,
        name="Stems",
        mode="lines",
        line=dict(color=C["sampled"], width=1.2),
        showlegend=False,
    ))

    # Puntos de muestra
    fig.add_trace(go.Scatter(
        x=t_samp * 1000, y=y_samp,
        name="Muestras",
        mode="markers",
        marker=dict(color=C["sampled"], size=8, line=dict(color=C["bg"], width=1.5)),
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Señal original, muestras y reconstrucción", font=dict(size=14)),
        height=380,
    )
    fig.update_xaxes(title_text="Tiempo (ms)", **AXIS_STYLE)
    fig.update_yaxes(title_text="Amplitud", **AXIS_STYLE)
    st.plotly_chart(fig, width="stretch", key="chart_tab1")

# ─── Tab 2: Espectro ──────────────────────────────────────────────────────────
with tab2:
    components = sig["spectrum"](f0)
    nyquist_freq = fs / 2
    max_freq = max(nyquist_freq * 1.5, bw * 1.3, f0 * 2)

    fig2 = go.Figure()

    for freq, amp in components:
        aliased = freq > nyquist_freq
        color = C["alias"] if aliased else C["signal"]
        label = f"{freq:.1f} Hz {'⚠ ALIAS' if aliased else ''}"

        fig2.add_trace(go.Scatter(
            x=[freq, freq], y=[0, amp],
            mode="lines",
            line=dict(color=color, width=4),
            name=label,
            hovertemplate=f"f = {freq:.1f} Hz<br>Amp = {amp:.3f}<extra></extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=[freq], y=[amp],
            mode="markers",
            marker=dict(color=color, size=10),
            showlegend=False,
        ))

    # Línea de Nyquist
    fig2.add_vline(
        x=nyquist_freq,
        line_dash="dash",
        line_color=C["nyquist"],
        line_width=1.5,
        annotation_text=f"Nyquist: {nyquist_freq:.0f} Hz",
        annotation_font_color=C["nyquist"],
        annotation_position="top right",
    )

    fig2.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Espectro analítico de la señal — componentes vs. frecuencia de Nyquist", font=dict(size=14)),
        height=380,
        showlegend=True,
    )
    fig2.update_xaxes(title_text="Frecuencia (Hz)", range=[0, max_freq], **AXIS_STYLE)
    fig2.update_yaxes(title_text="Amplitud normalizada", range=[0, 1.15], **AXIS_STYLE)
    st.plotly_chart(fig2, width="stretch", key="chart_tab2")

    # Tabla de componentes
    st.markdown("**Componentes espectrales:**")
    rows = []
    for freq, amp in components:
        aliased = freq > nyquist_freq
        rows.append({
            "Frecuencia (Hz)": f"{freq:.1f}",
            "Amplitud": f"{amp:.4f}",
            "Estado": "⚠️ Aliasing" if aliased else "✅ OK",
        })
    st.dataframe(rows, width="stretch", hide_index=True)

# ─── Tab 3: Interpolación sinc ────────────────────────────────────────────────
with tab3:
    fig3 = go.Figure()

    MAX_SINCS = 30
    samples_to_plot = list(zip(t_samp, y_samp))[:MAX_SINCS]

    for ti, yi in samples_to_plot:
        x = fs * (t_cont - ti)
        sinc_i = np.where(np.abs(x) < 1e-9, 1.0, np.sin(np.pi * x) / (np.pi * x))
        sinc_scaled = yi * sinc_i

        fig3.add_trace(go.Scatter(
            x=t_cont * 1000, y=sinc_scaled,
            mode="lines",
            line=dict(color="#22d3ee", width=1, dash="dot"),
            opacity=0.35,
            showlegend=False,
        ))

    if y_rec is not None:
        fig3.add_trace(go.Scatter(
            x=t_cont * 1000, y=y_rec,
            name="Reconstruida (suma sinc)",
            line=dict(color="#a78bfa", width=2.5),
        ))

    fig3.add_trace(go.Scatter(
        x=t_samp * 1000, y=y_samp,
        name="Muestras",
        mode="markers",
        marker=dict(color=C["sampled"], size=8),
    ))

    fig3.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Reconstrucción sinc — suma de funciones interpolantes", font=dict(size=14)),
        height=380,
    )
    fig3.update_xaxes(title_text="Tiempo (ms)", **AXIS_STYLE)
    fig3.update_yaxes(title_text="Amplitud", **AXIS_STYLE)

    if len(t_samp) > MAX_SINCS:
        st.caption(f"⚠️ Se muestran las primeras {MAX_SINCS} sincs de {len(t_samp)} muestras para no saturar el gráfico.")

    st.plotly_chart(fig3, width="stretch", key="chart_sinc")

# ─── Tab 4: Espectro replicado ────────────────────────────────────────────────
with tab4:
    nyquist_freq = fs / 2
    max_disp = 2.5 * fs

    fig4 = go.Figure()

    # Bandas de fondo alternadas: base (cyan), espejo (rojo), réplica, ...
    zone_bounds = [0, nyquist_freq, fs, 1.5 * fs, 2 * fs, 2.5 * fs]
    zone_colors = [
        "rgba(34,211,238,0.08)",
        "rgba(239,68,68,0.07)",
        "rgba(34,211,238,0.04)",
        "rgba(239,68,68,0.04)",
        "rgba(34,211,238,0.02)",
    ]
    zone_names = ["Banda base", "Zona espejo", "Réplica 1", "Zona espejo", "Réplica 2"]
    for i in range(len(zone_colors)):
        lo = zone_bounds[i]
        hi = min(zone_bounds[i + 1], max_disp)
        fig4.add_vrect(x0=lo, x1=hi, fillcolor=zone_colors[i], line_width=0, layer="below")
        fig4.add_annotation(
            x=(lo + hi) / 2, y=1.20,
            text=zone_names[i],
            showarrow=False,
            font=dict(size=9, color="#64748b"),
            xref="x", yref="y",
        )

    # Líneas verticales en múltiplos de fs/2
    k = 1
    while k * nyquist_freq <= max_disp:
        x = k * nyquist_freq
        label = {1: f"fs/2={nyquist_freq:.0f}Hz", 2: f"fs={fs:.0f}Hz"}.get(k, f"{k}·fs/2" if k % 2 else f"{k//2}·fs")
        fig4.add_vline(
            x=x,
            line_dash="dash",
            line_color="#ef4444" if k == 1 else "#334155",
            line_width=1.5 if k == 1 else 0.8,
            annotation_text=label,
            annotation_font_color="#ef4444" if k == 1 else "#475569",
            annotation_font_size=9,
            annotation_position="top left",
        )
        k += 1

    # Réplicas espectrales
    # Para una señal real con componente en f_orig, las copias en frecuencias positivas son:
    #   f_orig + k*fs  (copia directa)
    #   k*fs - f_orig  (copia espejo de la frecuencia negativa)
    already_labeled = {}
    legend_names = {
        "alias":   "⚠ Alias en banda base",
        "original": "Original (banda base)",
        "replica":  "Réplica (fuera de banda base)",
    }

    for orig_f, amp in components:
        copies = set()
        for k in range(-2, 5):
            for c in [orig_f + k * fs, k * fs - orig_f]:
                if 1e-3 < c <= max_disp + 1e-3:
                    copies.add(round(c, 4))
        copies = sorted(copies)

        for copy_f in copies:
            in_baseband = copy_f <= nyquist_freq + 1e-4
            is_original = (orig_f <= nyquist_freq) and (abs(copy_f - orig_f) < 0.1)
            is_alias = in_baseband and not is_original

            if is_alias:
                color, kind = "#ef4444", "alias"
            elif is_original:
                color, kind = C["signal"], "original"
            else:
                color, kind = "#475569", "replica"

            show_leg = kind not in already_labeled
            already_labeled[kind] = True

            hover = (
                f"f = {copy_f:.1f} Hz<br>Amp = {amp:.3f}<br>"
                + (f"⚠ Alias de {orig_f:.1f} Hz" if is_alias
                   else "Original" if is_original
                   else f"Réplica de {orig_f:.1f} Hz")
                + "<extra></extra>"
            )

            fig4.add_trace(go.Scatter(
                x=[copy_f, copy_f], y=[0, amp],
                mode="lines",
                line=dict(color=color, width=3),
                name=legend_names[kind] if show_leg else "",
                showlegend=show_leg,
                hovertemplate=hover,
            ))
            fig4.add_trace(go.Scatter(
                x=[copy_f], y=[amp],
                mode="markers",
                marker=dict(color=color, size=9),
                showlegend=False,
            ))

            # Flecha desde el componente fuera de banda hacia su alias en banda base
            if is_alias and orig_f > nyquist_freq and orig_f <= max_disp:
                fig4.add_annotation(
                    ax=orig_f, ay=amp + 0.12,
                    x=copy_f,  y=amp + 0.12,
                    xref="x", yref="y",
                    axref="x", ayref="y",
                    text="",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=1.5,
                    arrowcolor="#ef4444",
                )

    fig4.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Espectro replicado del muestreo — réplicas periódicas en múltiplos de fs", font=dict(size=14)),
        height=440,
        showlegend=True,
    )
    fig4.update_xaxes(title_text="Frecuencia (Hz)", range=[0, max_disp], **AXIS_STYLE)
    fig4.update_yaxes(title_text="Amplitud normalizada", range=[0, 1.3], **AXIS_STYLE)
    st.plotly_chart(fig4, width="stretch", key="chart_tab4")

    st.markdown("""
    <div style="font-family:'Courier New',monospace; font-size:12px; color:#64748b;
                line-height:1.8; padding:12px; background:#111827;
                border:1px solid #1e293b; border-radius:8px;">
    <b style="color:#e2e8f0">¿Qué muestra este gráfico?</b><br>
    Al muestrear a fs, el espectro de la señal discreta es la suma infinita de
    <b style="color:#22d3ee">réplicas periódicas</b> del espectro original,
    desplazadas en múltiplos de fs (y sus espejos).<br>
    Cuando fs &lt; 2·BW, alguna réplica <b style="color:#ef4444">cae dentro de la
    banda base [0, fs/2]</b>: el filtro reconstructor no puede distinguirla de una
    componente legítima → <b style="color:#ef4444">aliasing</b>.<br>
    Las flechas rojas muestran qué componente fuera de banda genera cada alias.
    Es un fenómeno <b style="color:#e2e8f0">lineal</b> de superposición de espectros solapados.
    </div>
    """, unsafe_allow_html=True)

    # Tabla de aliases
    alias_rows = []
    for orig_f, amp in components:
        if orig_f > nyquist_freq:
            f_red = orig_f % fs
            f_alias = fs - f_red if f_red > nyquist_freq else f_red
            clash = next((f"{f:.1f}" for f, _ in components if abs(f - f_alias) < 0.5 and f <= nyquist_freq), "—")
            alias_rows.append({
                "Componente original (Hz)": f"{orig_f:.1f}",
                "Alias en banda base (Hz)": f"{f_alias:.1f}",
                "Amplitud": f"{amp:.4f}",
                "Interfiere con (Hz)": clash,
            })
    if alias_rows:
        st.markdown("**Tabla de aliases:**")
        st.dataframe(alias_rows, width="stretch", hide_index=True)

# ─── Tab 5: Señal reconstruida analítica ──────────────────────────────────────
with tab5:
    nyquist_freq = fs / 2

    # Para cada componente, calcular la frecuencia efectiva en [0, fs/2] y el signo.
    # Cuando f mod fs > fs/2, el alias tiene signo negativo (reflexión espectral).
    # Esto es consistente con la reconstrucción sinc.
    baseband_components = {}   # f_eff -> amplitud acumulada (con signo)
    comp_detail = []           # para la tabla explicativa

    for orig_f, amp in components:
        f_red = orig_f % fs
        if f_red <= nyquist_freq:
            f_eff, sign = f_red, +1.0
            es_alias = (orig_f > nyquist_freq)   # componente que "se copió" sin doblar
        else:
            f_eff, sign = fs - f_red, -1.0
            es_alias = True

        baseband_components[f_eff] = baseband_components.get(f_eff, 0.0) + sign * amp
        comp_detail.append({
            "f original (Hz)": f"{orig_f:.1f}",
            "f en banda base (Hz)": f"{f_eff:.1f}",
            "Amplitud efectiva": f"{sign * amp:+.4f}",
            "Tipo": "⚠ Alias" if es_alias else "✅ Original",
        })

    # Señal filtrada ideal: solo componentes originales que ya estaban en [0, fs/2]
    y_filtered = np.zeros_like(t_cont)
    for orig_f, amp in components:
        if orig_f <= nyquist_freq:
            y_filtered += amp * np.sin(2 * np.pi * orig_f * t_cont)

    # Señal reconstruida con aliases: suma de todas las componentes en banda base
    y_reconstructed = np.zeros_like(t_cont)
    for f_eff, a_eff in baseband_components.items():
        y_reconstructed += a_eff * np.sin(2 * np.pi * f_eff * t_cont)

    # Distorsión pura generada por el aliasing
    y_distortion = y_reconstructed - y_filtered

    fig5 = go.Figure()

    fig5.add_trace(go.Scatter(
        x=t_cont * 1000, y=y_cont,
        name="Señal original (completa)",
        line=dict(color=C["signal"], width=2),
    ))
    fig5.add_trace(go.Scatter(
        x=t_cont * 1000, y=y_filtered,
        name="Filtrada ideal (solo f ≤ fs/2)",
        line=dict(color="#10b981", width=2, dash="dash"),
    ))
    fig5.add_trace(go.Scatter(
        x=t_cont * 1000, y=y_reconstructed,
        name="Reconstruida (con aliases)",
        line=dict(color=C["rec"], width=2.5),
    ))
    fig5.add_trace(go.Scatter(
        x=t_cont * 1000, y=y_distortion,
        name="Distorsión por aliasing",
        line=dict(color=C["alias"], width=1.5, dash="dot"),
        visible="legendonly",
    ))

    fig5.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Señal reconstruida — componentes en banda base incluyendo aliases", font=dict(size=14)),
        height=400,
    )
    fig5.update_xaxes(title_text="Tiempo (ms)", **AXIS_STYLE)
    fig5.update_yaxes(title_text="Amplitud", **AXIS_STYLE)
    st.plotly_chart(fig5, width="stretch", key="chart_tab5")

    st.markdown("""
    <div style="font-family:'Courier New',monospace; font-size:12px; color:#64748b;
                line-height:1.8; padding:12px; background:#111827;
                border:1px solid #1e293b; border-radius:8px;">
    <b style="color:#e2e8f0">¿Cómo se construye la señal reconstruida?</b><br>
    El filtro pasabajos del reconstructor toma <b style="color:#e2e8f0">todo</b> lo que cae en
    [0, fs/2] y lo trata como frecuencia legítima.<br>
    • Las componentes originales que ya estaban en banda base pasan sin cambio
    (<b style="color:#10b981">verde</b>).<br>
    • Los alias entran a la banda base con <b style="color:#ef4444">signo invertido</b>
    cuando se doblan alrededor de fs/2 (reflexión espectral).<br>
    • La suma de ambas forma la señal reconstruida (<b style="color:#a78bfa">violeta</b>):
    diferente a la original cuando hay aliasing.<br>
    • Activar "Distorsión" en la leyenda muestra únicamente la componente espuria agregada.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Componentes en banda base usadas para la reconstrucción:**")
    st.dataframe(comp_detail, width="stretch", hide_index=True)

# ─── Actividades sugeridas ────────────────────────────────────────────────────
#st.divider()
#with st.expander("🧪 Actividades sugeridas para la clase", expanded=False):
#    st.markdown("""
#    <div class="activities-box">
#    <b style="color:#22d3ee">1.</b> Con señal senoidal de 10 Hz, encontrá la fs mínima para evitar aliasing. ¿Qué pasa con fs = 19 Hz?<br><br>
#    <b style="color:#22d3ee">2.</b> Comparar señal cuadrada vs senoidal a 10 Hz. ¿Por qué la cuadrada necesita mayor fs?<br><br>
#    <b style="color:#22d3ee">3.</b> Con señal multitono, hallá fs tal que solo la componente de 4f tenga aliasing.<br><br>
#    <b style="color:#22d3ee">4.</b> Activá la reconstrucción y observá cómo se degrada al bajar fs por debajo de Nyquist.<br><br>
#    <b style="color:#22d3ee">5.</b> Para cada tipo de señal, determiná el ancho de banda y verificá el criterio de Nyquist.
#    </div>
#    """, unsafe_allow_html=True)
#
st.markdown(
    "<p style='text-align:center; color:#334155; font-size:11px; font-family:monospace; margin-top:8px'>"
    "Ingeniería Electrónica · Sistemas de Comunicaciones I</p>",
    unsafe_allow_html=True,
)
