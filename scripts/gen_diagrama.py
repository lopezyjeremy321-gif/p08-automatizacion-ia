"""Genera docs/diagrama-flujo.html (estilo diagram-design: flowchart, tokens por defecto del skill)."""
import pathlib

CX, W, DW, DH, RH = 400, 190, 230, 84, 44
seq = [("oval", "Correo o formulario de prueba", ""),
       ("dia", "¿Firma HMAC o token válidos?", ("NO", "401, no se procesa")),
       ("dia", "¿Esquema válido y sin CR/LF?", ("NO", "422, rechazado")),
       ("dia", "¿Message-ID ya visto?", ("SÍ", "Duplicado: sin tarea ni aviso nuevo")),
       ("rect", "Clasificar (Groq, respaldo Ollama)", "salida validada contra enum cerrado"),
       ("dia", "¿Ventas o soporte, sin inyección?", ("NO", "Spam o revisión manual: sin borrador ni botón")),
       ("rect", "Borrador + tarea en la hoja", "tono fijo, humanizer, sin precios ni fechas"),
       ("rect", "Aviso Telegram con botón Aprobar", "muestra destinatario, asunto y cuerpo exactos"),
       ("dia", "¿Clic válido?", ("NO", "Nada se envía")),
       ("end", "Buzón simulado: 1 envío", "hash + chat en allowlist + un solo uso")]
GAP = 34
y = 36
out, arrows, nodes = [], [], []
prev_bottom = None
for i, (kind, label, extra) in enumerate(seq):
    h = DH if kind == "dia" else (RH + (12 if kind == "end" else 0))
    top = y
    cy = top + h / 2
    if prev_bottom is not None:
        accent = (kind == "end")
        col, mk = ("#bf4520", "arrow-accent") if accent else ("#4f5d75", "arrow")
        arrows.append(f'<line x1="{CX}" y1="{prev_bottom}" x2="{CX}" y2="{top}" stroke="{col}" stroke-width="1.3" marker-end="url(#{mk})"/>')
        if seq[i - 1][0] == "dia":
            arrows.append(f'<rect x="{CX+8}" y="{prev_bottom+8}" width="30" height="12" rx="2" fill="#f5f5f5"/><text x="{CX+23}" y="{prev_bottom+17}" fill="{"#bf4520" if accent else "#4f5d75"}" font-size="8" font-family="monospace" text-anchor="middle" letter-spacing="0.1em">{"SÍ" if seq[i-1][2][0]=="NO" else "NO"}</text>')
    if kind in ("oval", "end"):
        acc = kind == "end"
        fill, stroke = ("rgba(191,69,32,0.08)", "#bf4520") if acc else ("rgba(45,49,66,0.03)", "rgba(45,49,66,0.30)")
        nodes.append(f'<rect x="{CX-W/2-20}" y="{top}" width="{W+40}" height="{h}" rx="20" fill="{fill}" stroke="{stroke}"/>')
        nodes.append(f'<text x="{CX}" y="{cy-(4 if extra else -4)}" fill="#2d3142" font-size="12.5" font-weight="600" text-anchor="middle">{label}</text>')
        if extra:
            nodes.append(f'<text x="{CX}" y="{cy+12}" fill="#4f5d75" font-size="9" font-family="monospace" text-anchor="middle">{extra}</text>')
    elif kind == "rect":
        nodes.append(f'<rect x="{CX-W/2-40}" y="{top}" width="{W+80}" height="{h}" rx="6" fill="#ffffff" stroke="#2d3142"/>')
        nodes.append(f'<text x="{CX}" y="{cy-3}" fill="#2d3142" font-size="12.5" font-weight="600" text-anchor="middle">{label}</text>')
        nodes.append(f'<text x="{CX}" y="{cy+11}" fill="#4f5d75" font-size="9" font-family="monospace" text-anchor="middle">{extra}</text>')
    else:
        hw = DW / 2
        nodes.append(f'<polygon points="{CX},{top} {CX+hw},{cy} {CX},{top+h} {CX-hw},{cy}" fill="#ffffff" stroke="#2d3142"/>')
        words = label.split(" ")
        mid = len(words) // 2 + (1 if len(words) > 3 else 0)
        l1, l2 = " ".join(words[:mid]), " ".join(words[mid:])
        nodes.append(f'<text x="{CX}" y="{cy-2}" fill="#2d3142" font-size="11.5" font-weight="600" text-anchor="middle">{l1}</text>')
        nodes.append(f'<text x="{CX}" y="{cy+12}" fill="#2d3142" font-size="11.5" font-weight="600" text-anchor="middle">{l2}</text>')
        tag, side = extra
        x1, x2 = CX + hw, CX + hw + 90
        arrows.append(f'<line x1="{x1}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="#4f5d75" stroke-width="1.3" marker-end="url(#arrow)"/>')
        arrows.append(f'<rect x="{x1+24}" y="{cy-17}" width="30" height="12" rx="2" fill="#f5f5f5"/><text x="{x1+39}" y="{cy-8}" fill="#4f5d75" font-size="8" font-family="monospace" text-anchor="middle" letter-spacing="0.1em">{tag}</text>')
        nodes.append(f'<rect x="{x2}" y="{cy-24}" width="236" height="48" rx="20" fill="rgba(45,49,66,0.03)" stroke="rgba(45,49,66,0.30)"/>')
        sw = side.split(": ")
        if len(sw) == 2:
            nodes.append(f'<text x="{x2+118}" y="{cy-3}" fill="#2d3142" font-size="11" font-weight="600" text-anchor="middle">{sw[0]}</text><text x="{x2+118}" y="{cy+12}" fill="#4f5d75" font-size="9" font-family="monospace" text-anchor="middle">{sw[1]}</text>')
        else:
            nodes.append(f'<text x="{x2+118}" y="{cy+4}" fill="#2d3142" font-size="11" font-weight="600" text-anchor="middle">{side}</text>')
    prev_bottom = top + h
    y = top + h + GAP
H = y + 70
legend_y = y - GAP + 24
svg = f'''<svg viewBox="0 0 1000 {H:.0f}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d">
<title id="t">Flujo de correo a tareas con aprobación obligatoria</title>
<desc id="d">Un correo de prueba pasa por firma, esquema, deduplicación y clasificación. Solo ventas y soporte sin inyección generan borrador y aviso; el único camino a un envío es un clic válido en Aprobar.</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#4f5d75"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#bf4520"/></marker>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.9" fill="rgba(45,49,66,0.10)"/></pattern></defs>
<rect width="100%" height="100%" fill="#f5f5f5"/><rect width="100%" height="100%" fill="url(#dots)" opacity="0.55"/>
{chr(10).join(arrows)}
{chr(10).join(nodes)}
<line x1="40" y1="{legend_y}" x2="960" y2="{legend_y}" stroke="rgba(45,49,66,0.10)"/>
<text x="40" y="{legend_y+18}" fill="#4f5d75" font-size="8.5" font-family="monospace" letter-spacing="0.16em">LEYENDA · LA FORMA INDICA EL TIPO · CORAL = ÚNICO CAMINO A UN ENVÍO</text>
</svg>'''
html = f'''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>P08 flujo de correo a tareas</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}:root{{--paper:#f5f5f5;--ink:#2d3142;--muted:#4f5d75}}
body{{font-family:system-ui,"Segoe UI",sans-serif;background:var(--paper);color:var(--ink);padding:2rem}}
.frame{{max-width:1000px;margin:0 auto}}h1{{font-size:clamp(1.4rem,2vw+.7rem,1.9rem);font-weight:600;letter-spacing:-.01em;margin-bottom:.4rem}}
p{{color:var(--muted);margin-bottom:1.2rem;max-width:70ch;line-height:1.5}}.c{{overflow-x:auto}}svg{{width:100%;min-width:760px;display:block}}
</style></head><body><div class="frame"><h1>De un correo a una respuesta aprobada</h1>
<p>Todos los caminos sin clic válido terminan sin envío. El borde derecho muestra por qué un correo sale del flujo.</p>
<div class="c">{svg}</div></div></body></html>'''
p = pathlib.Path(__file__).resolve().parent.parent / "docs" / "diagrama-flujo.html"
p.write_text(html, encoding="utf-8")
print(p, len(html))
