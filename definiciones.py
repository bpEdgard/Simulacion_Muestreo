# ─── Paletas de color para el área de gráficos (Plotly) ──────────────────────
# Para cambiar el tema de los gráficos, editar app.py y asignar:
#   C = DARK   →  tema oscuro  (osciloscopio)
#   C = LIGHT  →  tema claro   (presentación / impresión)

DARK = {
    "bg":            "#0a0e17",        # fondo del área de trazado
    "paper":         "#0f172a",        # fondo del paper (fuera de ejes)
    "grid":          "#1e2d4a",        # grilla y línea de cero
    "font":          "#e2e8f0",        # texto de ejes, leyenda y títulos
    "legend_border": "#1e293b",        # borde del cuadro de leyenda
    "signal":        "#22d3ee",        # señal original (cyan)
    "sampled":       "#f59e0b",        # muestras y stems (amber)
    "rec":           "#a78bfa",        # señal reconstruida (violeta)
    "alias":         "#ef4444",        # componentes aliasadas (rojo)
    "nyquist":       "#ef4444",        # línea de Nyquist (rojo)
    "filtered":      "#10b981",        # señal filtrada ideal (verde)
    "replica":       "#475569",        # réplicas fuera de banda base (gris)
    "zone_base":     "rgba(34,211,238,0.08)",   # banda base (cyan tenue)
    "zone_mirror":   "rgba(239,68,68,0.07)",    # zona espejo (rojo tenue)
    "zone_rep1":     "rgba(34,211,238,0.04)",   # réplica 1
    "zone_rep2":     "rgba(239,68,68,0.04)",    # zona espejo 2
    "zone_rep3":     "rgba(34,211,238,0.02)",   # réplica 2
    "vline_mid":     "#334155",        # líneas verticales intermedias (fs, 3fs/2…)
    "ann_mid":       "#475569",        # anotaciones de líneas intermedias
    "zone_label":    "#64748b",        # etiquetas de zonas espectrales
}

LIGHT = {
    "bg":            "#ffffff",        # fondo del área de trazado
    "paper":         "#f8fafc",        # fondo del paper
    "grid":          "#e2e8f0",        # grilla y línea de cero
    "font":          "#1e293b",        # texto de ejes, leyenda y títulos
    "legend_border": "#cbd5e1",        # borde del cuadro de leyenda
    "signal":        "#0891b2",        # señal original (cyan oscuro)
    "sampled":       "#d97706",        # muestras y stems (amber oscuro)
    "rec":           "#7c3aed",        # señal reconstruida (violeta oscuro)
    "alias":         "#dc2626",        # componentes aliasadas (rojo oscuro)
    "nyquist":       "#dc2626",        # línea de Nyquist (rojo oscuro)
    "filtered":      "#059669",        # señal filtrada ideal (verde oscuro)
    "replica":       "#94a3b8",        # réplicas fuera de banda base (gris)
    "zone_base":     "rgba(8,145,178,0.10)",    # banda base (cyan tenue)
    "zone_mirror":   "rgba(220,38,38,0.08)",    # zona espejo (rojo tenue)
    "zone_rep1":     "rgba(8,145,178,0.05)",    # réplica 1
    "zone_rep2":     "rgba(220,38,38,0.05)",    # zona espejo 2
    "zone_rep3":     "rgba(8,145,178,0.02)",    # réplica 2
    "vline_mid":     "#94a3b8",        # líneas verticales intermedias
    "ann_mid":       "#64748b",        # anotaciones de líneas intermedias
    "zone_label":    "#475569",        # etiquetas de zonas espectrales
}
