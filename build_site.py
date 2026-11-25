"""Builds index.html: keeps the existing <head> styles, adds diagram styles, writes every section.
Diagrams are inline SVG line art; figures come from make_site_figs.py and make_site_maps.py."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
old = (ROOT / "index.html").read_text(encoding="utf-8")
head = old.split("</style>")[0]
if "svg.dg" not in head:
    head = head.replace('''  figure img { width: 100%; display: block; border: 1px solid var(--ink); border-radius: 3px; background: #fff; }''',
'''  figure img { width: 100%; display: block; }
  figure img.boxed { border: 1px solid var(--ink); border-radius: 3px; background: #fff; }
  svg.dg { width: 100%; height: auto; display: block; margin: 12px 0 4px; }
  svg.dg text { font-family: var(--mono); fill: var(--ink); }
  svg.dg .t { font-size: 12.5px; } svg.dg .s { font-size: 10.5px; fill: var(--muted); }
  svg.dg rect, svg.dg path, svg.dg line, svg.dg circle, svg.dg polyline { fill: none; stroke: var(--ink); stroke-width: 1.2; }
  svg.dg .dash { stroke-dasharray: 4 3; } svg.dg .bold { stroke-width: 2.2; }
  .step { font-size: 11.5px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin-top: 40px; }
  .sec-label.tight { margin-top: 6px; }
  .dgwrap { overflow-x: auto; }
  @media (max-width: 620px) { svg.dg { min-width: 680px; } }''')

ARROW = ('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0 L10,5 L0,10" style="fill:none;stroke:#1a1a1a;stroke-width:1.4"/></marker></defs>')


def box(x, y, w, h, title, sub="", cls=""):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" class="{cls}"/>'
    s += f'<text x="{x + 10}" y="{y + 20}" class="t">{title}</text>'
    for i, line in enumerate(sub.split("|") if sub else []):
        s += f'<text x="{x + 10}" y="{y + 37 + 14 * i}" class="s">{line}</text>'
    return s


def arrow(x1, y1, x2, y2, cls=""):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" marker-end="url(#ar)"/>'


def svg(h, label, inner):
    return f'<div class="dgwrap"><svg class="dg" viewBox="0 0 800 {h}" role="img" aria-label="{label}">{ARROW}{inner}</svg></div>'


# D1 architecture
i = box(10, 10, 780, 60, "Data", "PJM public queue (8,190 requests);  MATPOWER grids, 30 to 2,000 buses;|seasons and NERC-style outage sets;  public cost and time data")
i += arrow(400, 70, 400, 92)
i += box(10, 95, 780, 66, "Step 1  Physics engine (grid-engine, on Power Grid Model)",
         "batch AC power flow over every outage case, three seasons, generator reactive limits, a DC baseline|checked against PYPOWER (MATPOWER) on 19,041 cases", "bold")
i += arrow(200, 161, 200, 183) + arrow(600, 161, 600, 183)
i += box(10, 186, 380, 80, "Step 2  Capacity", "each bus, each request alone, the cluster|together, the exact best cluster decision,|and what limits it (outage and element)")
i += box(410, 186, 380, 80, "Step 3  Ways to make room", "flexible load, batteries, tripping|generation after an outage, one switch,|partial MW, all re-checked in AC")
i += arrow(200, 266, 200, 288) + arrow(600, 266, 600, 288)
i += box(10, 291, 380, 66, "Step 4  Time and cost", "PJM's own timelines; upgrade cost|ranges with a source on every number")
i += box(410, 291, 380, 66, "Step 5  Certify or defer", "trust a fast answer only with a tested|error bound; otherwise run the full study", "bold")
i += arrow(200, 357, 320, 383) + arrow(560, 357, 480, 383)
i += box(220, 386, 320, 74, "Product", "a queue file in; per-project and cluster|answers, options, cost and time ranges,|and which answers are certified")
i += ('<rect x="560" y="386" width="230" height="74" rx="3" class="dash"/><text x="570" y="406" class="t">AI layer (proposes)</text>'
      '<text x="570" y="423" class="s">Set Transformer, operator graph,</text><text x="570" y="437" class="s">GENCO / OpenGridFM predictions;</text>'
      '<text x="570" y="451" class="s">never makes the safe call alone</text>')
i += arrow(700, 386, 700, 360, "dash")
D1 = svg(470, "Architecture: data feeds the physics engine; capacity, options, cost and certify-or-defer build on it; an AI layer proposes and the guarantee layer decides.", i)

# D2 integration
i = box(280, 122, 240, 90, "grid-engine", "MATPOWER cases to PGM input,|seasons, outage sets, capacity,|reactive-limit outer loop", "bold")
i += box(10, 20, 250, 92, "Power Grid Model (LF Energy)", "the C++ solver European grid|operators use; batch Newton-|Raphson over all outage cases")
i += box(540, 20, 250, 92, "OpenGridFM / GENCO", "grid foundation-model predictions:|certify or reject each answer,|then warm-start the exact solver")
i += box(10, 228, 250, 92, "Contributed back to PGM", "PR #1720: IEEE 118 validation case|issue #1609: warm-start benchmarks|re-run on the maintainers' branch")
i += box(540, 228, 250, 92, "Independent referees", "PYPOWER (MATPOWER's algorithm):|19,041 cases; PGM's own IEEE 300|reference: 1.1e-13 pu")
i += arrow(260, 80, 292, 126) + arrow(540, 80, 508, 126) + arrow(292, 208, 258, 242) + arrow(508, 208, 542, 242, "dash")
D2 = svg(330, "Integration: Power Grid Model is the solver; OpenGridFM and GENCO predictions are checked and used as warm starts; PYPOWER is the independent referee; contributions flow back upstream.", i)

# D3 Set Transformer
i = ""
for k, lab in enumerate(["request 1", "request 2", "request 3", "...", "request K"]):
    y = 20 + 52 * k
    i += f'<rect x="10" y="{y}" width="160" height="40" rx="3"/><text x="20" y="{y + 18}" class="t">{lab}</text>'
    if lab != "...":
        i += f'<text x="20" y="{y + 33}" class="s">bus, MW, DC sensitivities</text>'
    i += arrow(170, y + 20, 213, 150)
i += box(218, 100, 165, 100, "self-attention", "every pair of requests|interacts: who crowds|or helps whom; then a|feed-forward block", "bold")
i += arrow(383, 150, 413, 150)
i += box(418, 100, 140, 100, "pool", "mean + max over|requests: order|doesn't matter; the|worst one stands out")
i += box(418, 225, 140, 60, "grid state", "load, season,|base flows")
i += arrow(558, 150, 588, 150) + arrow(500, 225, 600, 180)
i += box(593, 100, 197, 100, "correction z", "z = log(AC capacity /|DC capacity); starts at|0, so the untrained|model is exactly DC")
D3 = svg(300, "Set Transformer: each request is a token; self-attention lets every pair interact; mean and max pooling plus grid-state context give a correction to the linear answer that starts at zero.", i)

# D4 certify or defer
i = box(10, 80, 150, 80, "cluster", "requests at|nearby buses")
i += arrow(160, 120, 190, 120)
i += box(195, 80, 150, 80, "fast pick", "linear (DC) best|subset, exact")
i += arrow(345, 120, 375, 120)
i += box(380, 70, 175, 100, "screened AC score", "AC on the base case|and the 10 outages DC|ranks riskiest: 11|solves, not 178", "bold")
i += arrow(555, 105, 600, 50) + arrow(555, 135, 600, 192)
i += box(605, 10, 185, 70, "certify", "score >= threshold;|failure rate bounded")
i += box(605, 165, 185, 75, "defer", "full AC study and|exact best subset")
i += ('<text x="380" y="205" class="s">threshold: fixed-sequence testing on</text><text x="380" y="219" class="s">calibration picks, valid for the picks</text>'
      '<text x="380" y="233" class="s">the screen actually makes</text>')
D4 = svg(250, "Certify or defer: the fast linear pick is scored by AC on its ten riskiest outages; above a tested threshold it is certified, otherwise it goes to the full study.", i)

# D5 cluster study
i = box(10, 20, 240, 160, "1. each request alone", "largest MW that keeps every|case within limits; the|binding outage and element;|no outages vs every single|outage vs common-tower pairs")
i += box(280, 20, 240, 160, "2. all together", "the cluster scaled together:|usually far below the sum of|its parts; some requests fit|only next to a partner (a|load beside a generator)")
i += box(550, 20, 240, 160, "3. which to admit", "first come vs largest first vs|the exact best subset, every|answer checked in full AC;|then options to make room|for the rest", "bold")
i += arrow(250, 100, 278, 100) + arrow(520, 100, 548, 100)
D5 = svg(200, "Three questions per cluster: each request alone, all together, and which subset to admit.", i)


def fig(src, alt, cap):
    return f'<figure><img src="assets/{src}" alt="{alt}" loading="lazy"><figcaption>{cap}</figcaption></figure>'


GH = "https://github.com/certified-interconnection"
body = (ROOT / "site_body.html").read_text(encoding="utf-8")
for k, v in dict(D1=D1, D2=D2, D3=D3, D4=D4, D5=D5).items():
    body = body.replace("{{" + k + "}}", v)
import re
body = re.sub(r'\{\{fig ([^|]+)\|([^|]+)\|([^}]+)\}\}', lambda m: fig(m.group(1).strip(), m.group(2).strip(), m.group(3).strip()), body)
(ROOT / "index.html").write_text(head + "</style>\n</head>\n" + body, encoding="utf-8", newline="\n")
print("built index.html", len(head + body))
