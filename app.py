"""
app.py  –  Dash 3.x web app for Nortek Signature 55 ADCP data
------------------------------------------------------------------
• Parses PNORI / PNORS / PNORC strings (Signature 55 “String Signature.txt”)
• Computes depth for each cell (pressure + blanking + cell size)
• Interactive dashboard with 8 plots:
      – Correlation  Beams 1‑3
      – Amplitude    Beams 1‑3
      – Correlation MEAN (three beams)
      – Amplitude  MEAN (three beams)
• Global RangeSlider filters any time interval (Time HHMMSS)
• Line x = 50 on all correlation plots (quality threshold)
• Designed for free Render deploy →  gunicorn app:app
------------------------------------------------------------------
"""

# ------------------------------------------------------------------
# 0) PATH TO RAW STRING FILE
# ------------------------------------------------------------------

DATA_FILE = Path(__file__).resolve().parent / "data" / "String Signature.txt"

# ------------------------------------------------------------------
# 1) BUILD DATAFRAME
# ------------------------------------------------------------------
import numpy as np, pandas as pd
from pathlib import Path

def f2(x): return float(x) if x not in ("", None) else np.nan
def i2(x): return int(x)   if x not in ("", None) else np.nan

recs, blanking, cell_size, press_m, profile = [], np.nan, np.nan, np.nan, None

with Path(DATA_FILE).open(encoding="utf-8") as f:
    for line in f:
        if line.startswith("$PNORI"):
            b = line.split("*")[0].split(",")
            blanking, cell_size = f2(b[5]), f2(b[6])
            continue
        if line.startswith("$PNORS"):
            s = line.split("*")[0].split(",")
            profile, press_m = s[2], f2(s[10])      # Time HHMMSS & pressure
            continue
        if line.startswith("$PNORC"):
            c = line.split("*")[0].split(",")
            cell = i2(c[3])
            if np.isnan(cell) or np.isnan(cell_size):
                continue
            depth = press_m + blanking + cell_size*(cell-0.5)  # down‑looking
            recs.append(dict(
                profile=profile, depth=depth,
                corr1=i2(c[15]), corr2=i2(c[16]), corr3=i2(c[17]),
                amp1=f2(c[11]),  amp2=f2(c[12]),  amp3=f2(c[13]),
            ))

df = (pd.DataFrame(recs)
        .dropna(subset=["depth"])
        .sort_values(["profile","depth"]))

# Averages across the three beams
df["corr_mean"] = df[["corr1","corr2","corr3"]].mean(axis=1, skipna=True)
df["amp_mean"]  = df[["amp1","amp2","amp3"]].mean(axis=1, skipna=True)

perfis = sorted(df.profile.unique())            # ascending HHMMSS
df["idx"] = df.profile.map({p:i for i,p in enumerate(perfis)})

# ------------------------------------------------------------------
# 2) DASH APP
# ------------------------------------------------------------------
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

def make_fig(sub, col, title, is_corr):
    fig = go.Figure()
    for p, dsub in sub.groupby("profile"):
        fig.add_trace(go.Scatter(
            x=dsub[col], y=dsub.depth,
            mode="lines+markers", name=p,
            hovertemplate="Time=%{name}<br>Depth=%{y:.2f} m<br>%{x}<extra></extra>"
        ))
    fig.update_yaxes(autorange="reversed", title="Depth (m)")
    fig.update_xaxes(title="Correlation (counts)" if is_corr else "Amplitude (counts)")
    fig.update_layout(
        title=title, legend_title="Profile (HHMMSS)",
        margin=dict(l=55,r=40,t=50,b=40)
    )
    if is_corr:
        fig.add_vline(x=50, line_dash="dash", line_color="black",
                      annotation_text="50", annotation_position="top")
    return fig

app = Dash(__name__)
server = app.server                     # for gunicorn on Render

app.layout = html.Div(
    style={"width":"95%","margin":"auto"},
    children=[
        html.H3("Signature 55 Profiles – Interactive Dashboard"),
        dcc.RangeSlider(
            id="slider", min=0, max=len(perfis)-1,
            value=[0, len(perfis)-1], step=1, allowCross=False,
            marks={i:p for i,p in enumerate(perfis)},
            tooltip={"placement":"bottom","always_visible":True},
        ),
        html.P("Move the handles to select a time interval (HHMMSS)."),
        html.Div(children=[
            dcc.Graph(id="corr1"), dcc.Graph(id="corr2"), dcc.Graph(id="corr3"),
            dcc.Graph(id="corrM"),   # mean correlation
            dcc.Graph(id="amp1"),  dcc.Graph(id="amp2"),  dcc.Graph(id="amp3"),
            dcc.Graph(id="ampM"),    # mean amplitude
        ])
    ]
)

@app.callback(
    Output("corr1","figure"), Output("corr2","figure"), Output("corr3","figure"),
    Output("corrM","figure"),
    Output("amp1","figure"),  Output("amp2","figure"),  Output("amp3","figure"),
    Output("ampM","figure"),
    Input("slider","value")
)
def update_figs(range_idx):
    s,e = range_idx
    sub = df[(df.idx>=s)&(df.idx<=e)]
    return (
        make_fig(sub,"corr1","Correlation – Beam 1", True),
        make_fig(sub,"corr2","Correlation – Beam 2", True),
        make_fig(sub,"corr3","Correlation – Beam 3", True),
        make_fig(sub,"corr_mean","Correlation MEAN (Beams 1‑3)", True),
        make_fig(sub,"amp1","Amplitude – Beam 1", False),
        make_fig(sub,"amp2","Amplitude – Beam 2", False),
        make_fig(sub,"amp3","Amplitude – Beam 3", False),
        make_fig(sub,"amp_mean","Amplitude MEAN (Beams 1‑3)", False),
    )

# ------------------------------------------------------------------
# 3) RUN LOCALLY (optional).  Render uses gunicorn app:app
# ------------------------------------------------------------------
if __name__ == "__main__":
    import os, webbrowser, threading
    port = int(os.environ.get("PORT", 8050))     # Render injects PORT
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}/")).start()
    app.run_server(debug=False, host="0.0.0.0", port=port)
