#!/usr/bin/env python3
"""Generatore del sito di Un Mondo Migliore.

Converte i documenti Markdown (manifesto, roadmap, diario) in un piccolo sito
HTML statico con menù di navigazione e immagine "hero". Nessuna dipendenza
esterna: solo la libreria standard di Python.

Uso:
    python3 build.py SITE_DIR
"""

import html
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Pagine del sito  (output, sorgente, etichetta nel menù)
# ---------------------------------------------------------------------------

PAGES = [
    ("index.html",   "MANIFESTO.md",     "Manifesto"),
    ("roadmap.html", "ROADMAP.md",       "Roadmap"),
    ("diario.html",  "diario/README.md", "Diario"),
]


# ---------------------------------------------------------------------------
# Mini-convertitore Markdown -> HTML (sottoinsieme sufficiente ai documenti)
# ---------------------------------------------------------------------------

def inline(text: str) -> str:
    """Formattazione inline: grassetto, corsivo, codice, link."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def _render_list_item(raw: str) -> str:
    """Voce di elenco, con supporto alle checkbox '[ ]' / '[x]'."""
    m = re.match(r"\[([ xX])\]\s+(.*)", raw)
    if m:
        done = m.group(1).lower() == "x"
        cls = "task done" if done else "task"
        box = "☑" if done else "☐"
        return f'<li class="{cls}"><span class="box">{box}</span>{inline(m.group(2))}</li>'
    return f"<li>{inline(raw)}</li>"


def convert(md: str) -> str:
    """Converte un blocco Markdown in HTML."""
    lines = md.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        stripped = lines[i].strip()

        # Commenti HTML — salta fino a -->
        if stripped.startswith("<!--"):
            while i < n and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        # Riga vuota o bullet vuoto segnaposto
        if not stripped or stripped in ("-", "*"):
            i += 1
            continue

        # Linea orizzontale
        if re.fullmatch(r"-{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # Titoli
        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Citazione (blockquote)
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]).strip())
                i += 1
            inner = "<br>".join(inline(b) for b in buf if b)
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # Elenco numerato
        if re.match(r"\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                items.append(f"<li>{inline(item)}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue

        # Elenco puntato (con eventuali checkbox)
        if re.match(r"[-*]\s+", stripped):
            items, has_task = [], False
            while i < n and re.match(r"[-*]\s+", lines[i].strip()):
                raw = re.sub(r"^[-*]\s+", "", lines[i].strip())
                if re.match(r"\[([ xX])\]\s+", raw):
                    has_task = True
                items.append(_render_list_item(raw))
                i += 1
            cls = ' class="tasklist"' if has_task else ""
            out.append(f"<ul{cls}>" + "".join(items) + "</ul>")
            continue

        # Paragrafo
        buf = []
        while i < n and lines[i].strip() and lines[i].strip() not in ("-", "*") \
                and not lines[i].strip().startswith("<!--") \
                and not re.match(r"(#{1,6}\s|>|[-*]\s|\d+\.\s|-{3,}$)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")

    return "\n".join(out)


def split_header(md: str):
    """Estrae il titolo (primo H1), il sottotitolo (prima citazione) e il corpo.

    Restituisce (titolo, sottotitolo, corpo_completo, corpo_senza_citazione):
    - corpo_completo  -> tutto ciò che segue l'H1 (citazione inclusa)
    - corpo_senza_citazione -> corpo con la prima citazione rimossa
      (usata quando la citazione diventa il sottotitolo dell'hero).
    """
    lines = md.splitlines()
    title = "Un Mondo Migliore"
    i = 0

    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    if i < len(lines):
        title = lines[i][2:].strip()
        i += 1
    after_title = i

    j = i
    while j < len(lines) and not lines[j].strip():
        j += 1
    sub_lines: list[str] = []
    k = j
    while k < len(lines) and lines[k].strip().startswith(">"):
        sub_lines.append(re.sub(r"^\s*>\s?", "", lines[k]).strip())
        k += 1

    subtitle = "<br>".join(inline(s) for s in sub_lines if s)
    body_full = "\n".join(lines[after_title:])
    body_stripped = "\n".join(lines[k:])
    return title, subtitle, body_full, body_stripped


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

STYLE = """
  :root {
    --ink: #2c2620; --muted: #6b5f4f; --cream: #f7f0e1; --paper: #fffdf8;
    --gold: #d39134; --gold-soft: #e8b25e; --terracotta: #b5612f;
    --sky: #3c5d86; --line: #e6dac1; --done: #8a9a6b;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; background: var(--cream); color: var(--ink);
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    font-size: 19px; line-height: 1.72; -webkit-font-smoothing: antialiased;
  }

  /* --- NAV --- */
  .nav {
    position: sticky; top: 0; z-index: 10;
    display: flex; flex-wrap: wrap; align-items: center; gap: .5rem 1.5rem;
    justify-content: space-between;
    padding: .8rem clamp(1rem, 4vw, 2.4rem);
    background: rgba(44,38,32,.92); backdrop-filter: blur(8px);
    border-bottom: 1px solid rgba(211,145,52,.4);
  }
  .nav .brand {
    color: #fff; text-decoration: none; font-weight: 600; font-size: 1.05rem;
    letter-spacing: .01em;
  }
  .nav__links { display: flex; gap: .3rem; flex-wrap: wrap; }
  .nav__links a {
    color: #e9dcc4; text-decoration: none; font-family: system-ui, sans-serif;
    font-size: .92rem; padding: .35rem .85rem; border-radius: 999px;
    transition: background .15s, color .15s;
  }
  .nav__links a:hover { background: rgba(232,178,94,.18); color: #fff; }
  .nav__links a.active { background: var(--gold); color: #2c2620; font-weight: 600; }

  /* --- HERO --- */
  .hero {
    position: relative; display: flex; flex-direction: column;
    justify-content: flex-end; color: #fff;
    padding: clamp(1.5rem, 5vw, 5rem);
    /* spazio extra in basso: il testo non deve finire sotto la "scheda" */
    padding-bottom: clamp(7rem, 11vw, 9.5rem);
    background:
      linear-gradient(180deg, rgba(20,28,46,.10) 0%, rgba(20,18,28,.12) 45%, rgba(28,20,16,.82) 100%),
      url("assets/hero.png") center/cover no-repeat;
  }
  .hero--full { min-height: 74vh; }
  .hero--slim { min-height: 34vh; }
  .hero__kicker {
    text-transform: uppercase; letter-spacing: .32em; font-size: .72rem;
    font-family: system-ui, sans-serif; font-weight: 600; margin-bottom: 1rem;
    opacity: .92; text-shadow: 0 1px 12px rgba(0,0,0,.5);
  }
  .hero__title {
    margin: 0; font-weight: 600; letter-spacing: -.01em; line-height: 1.02;
    font-size: clamp(2.3rem, 7vw, 5rem); max-width: 18ch;
    text-shadow: 0 2px 28px rgba(0,0,0,.45);
  }
  .hero__sub {
    margin: 1.3rem 0 0; font-style: italic; line-height: 1.5; max-width: 44ch;
    font-size: clamp(1rem, 2.2vw, 1.4rem); text-shadow: 0 1px 16px rgba(0,0,0,.55);
  }
  .hero__sub em { font-style: normal; }

  /* --- CONTENUTO --- */
  main { max-width: 46rem; margin: 0 auto; padding: 0 clamp(1.4rem, 5vw, 2rem) 1rem; }
  .sheet {
    background: var(--paper); border: 1px solid var(--line); border-radius: 14px;
    padding: clamp(1.8rem, 5vw, 3.4rem); margin-top: -4.5rem; position: relative;
    box-shadow: 0 30px 60px -28px rgba(60,40,20,.35);
  }
  h2 {
    font-size: clamp(1.5rem, 3.5vw, 2rem); font-weight: 600;
    margin: 2.6rem 0 .8rem; color: var(--terracotta); letter-spacing: -.01em;
  }
  h2:first-child { margin-top: 0; }
  h2::before {
    content: ""; display: block; width: 2.4rem; height: 3px; border-radius: 3px;
    background: linear-gradient(90deg, var(--gold), var(--gold-soft)); margin-bottom: 1rem;
  }
  h3 { font-size: 1.2rem; color: var(--sky); margin: 1.8rem 0 .6rem; }
  p { margin: 0 0 1.1rem; }
  strong { color: var(--sky); font-weight: 700; }
  a { color: var(--terracotta); text-decoration-thickness: 1px; text-underline-offset: 2px; }
  code {
    font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: .85em;
    background: rgba(181,97,47,.10); padding: .12em .4em; border-radius: 5px; color: var(--terracotta);
  }
  ul, ol { padding-left: 1.4rem; margin: 0 0 1.2rem; }
  ul { list-style: none; padding-left: 0; }
  ul li { position: relative; padding-left: 1.7rem; margin: .55rem 0; }
  ul li::before { content: "✦"; position: absolute; left: 0; color: var(--gold); font-size: .85em; top: .15em; }
  ol li { margin: .5rem 0; padding-left: .3rem; }

  /* checklist (roadmap) */
  ul.tasklist li { padding-left: 2rem; }
  ul.tasklist li::before { content: none; }
  ul.tasklist .box { position: absolute; left: 0; top: 0; color: var(--gold); font-size: 1.15em; }
  ul.tasklist .done { color: var(--done); }
  ul.tasklist .done .box { color: var(--done); }
  ul.tasklist .done strong { color: var(--done); }

  blockquote {
    margin: 1.6rem 0; padding: .2rem 0 .2rem 1.4rem; border-left: 3px solid var(--gold-soft);
    font-style: italic; color: var(--muted); font-size: 1.06em;
  }
  hr { border: 0; height: 1px; background: var(--line); margin: 2.6rem 0; }

  footer {
    max-width: 46rem; margin: 0 auto; padding: 2.5rem clamp(1.4rem, 5vw, 2rem) 4rem;
    text-align: center; color: var(--muted); font-size: .9rem; font-family: system-ui, sans-serif;
  }
  footer .names { color: var(--terracotta); font-weight: 600; }
  footer a { color: var(--muted); }

  @media (prefers-color-scheme: dark) {
    :root { --ink:#ece3d2; --muted:#b3a589; --cream:#1c1812; --paper:#26201a; --line:#3a3026; }
  }
"""

PAGE = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Un Mondo Migliore</title>
<style>{style}</style>
</head>
<body>
  <nav class="nav">
    <a class="brand" href="index.html">🌍 Un Mondo Migliore</a>
    <div class="nav__links">{nav}</div>
  </nav>

  <header class="hero {hero_mod}">
    <div class="hero__kicker">{kicker}</div>
    <h1 class="hero__title">{title}</h1>
    {sub_block}
  </header>

  <main>
    <article class="sheet">
{body}
    </article>
  </main>

  <footer>
    <span class="names">Comincia chi c'è. Continua chi arriva.</span><br>
    e chiunque, leggendo, pensi anche solo per un attimo: «ci sto».
  </footer>
</body>
</html>
"""

KICKERS = {
    "index.html":   "Un sogno matto · si comincia da qui",
    "roadmap.html": "La mappa dei semi · non rigida",
    "diario.html":  "I piccoli gesti reali · il sogno che accade",
}


def build_nav(active: str) -> str:
    parts = []
    for out, _src, label in PAGES:
        cls = ' class="active"' if out == active else ""
        parts.append(f'<a href="{out}"{cls}>{label}</a>')
    return "".join(parts)


def build_page(out_name: str, src: Path) -> str:
    md = src.read_text(encoding="utf-8")
    title, subtitle, body_full, body_stripped = split_header(md)

    # Solo la home porta la citazione nell'hero (è breve e iconica: il motto).
    # Nelle pagine interne l'introduzione resta nel corpo, così l'hero non
    # deborda sotto la "scheda" del contenuto.
    if out_name == "index.html":
        hero_mod = "hero--full"
        sub_block = f'<p class="hero__sub">{subtitle}</p>' if subtitle else ""
        body = convert(body_stripped)
    else:
        hero_mod = "hero--slim"
        sub_block = ""
        body = convert(body_full)

    return PAGE.format(
        style=STYLE,
        title=html.escape(title, quote=False),
        nav=build_nav(out_name),
        kicker=KICKERS.get(out_name, ""),
        hero_mod=hero_mod,
        sub_block=sub_block,
        body=body,
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 build.py SITE_DIR", file=sys.stderr)
        return 1

    site = Path(sys.argv[1])
    site.mkdir(parents=True, exist_ok=True)

    for out_name, src_name, _label in PAGES:
        src = Path(src_name)
        if not src.exists():
            print(f"  ! salto {out_name}: manca {src_name}", file=sys.stderr)
            continue
        (site / out_name).write_text(build_page(out_name, src), encoding="utf-8")
        print(f"  {src_name}  ->  {site / out_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
