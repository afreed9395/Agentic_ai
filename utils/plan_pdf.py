"""Build a PDF from markdown travel plans (fpdf2 + DejaVu for INR and symbols)."""

from __future__ import annotations

import html
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Final

import markdown
from fpdf import FPDF

_DEJAVU_BASE: Final = (
    "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf"
)
_FONT_SPECS: Final[tuple[tuple[str, str], ...]] = (
    ("", "DejaVuSans.ttf"),
    ("B", "DejaVuSans-Bold.ttf"),
    ("I", "DejaVuSans-Oblique.ttf"),
    ("BI", "DejaVuSans-BoldOblique.ttf"),
)
_SYSTEM_FONT_DIRS: Final[tuple[Path, ...]] = (
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/TTF"),
)


def _cache_dir() -> Path:
    d = Path.home() / ".cache" / "ai_trip_planner" / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _font_paths() -> dict[str, Path]:
    """Resolve DejaVu TTF paths (system install or download into ~/.cache)."""
    out: dict[str, Path] = {}
    for d in _SYSTEM_FONT_DIRS:
        if not d.is_dir():
            continue
        ok = True
        tmp: dict[str, Path] = {}
        for style, fname in _FONT_SPECS:
            p = d / fname
            if not p.is_file():
                ok = False
                break
            tmp[style] = p
        if ok:
            return tmp

    cache = _cache_dir()
    for style, fname in _FONT_SPECS:
        target = cache / fname
        if not target.is_file() or target.stat().st_size < 10_000:
            url = f"{_DEJAVU_BASE}/{fname}"
            with urllib.request.urlopen(url) as resp, target.open("wb") as f:
                f.write(resp.read())
        out[style] = target
    return out


def render_travel_plan_pdf(
    markdown_plan: str,
    request_text: str,
    generated_at: datetime,
) -> bytes:
    """Return PDF bytes for the given markdown plan."""
    fonts = _font_paths()
    body_html = markdown.markdown(
        markdown_plan,
        extensions=["tables", "nl2br", "fenced_code"],
    )
    meta = html.escape(
        f"Generated: {generated_at:%Y-%m-%d %H:%M} · Request: {request_text[:800]}"
    )
    full_html = f"""<h1>Travel plan</h1>
<p style="font-size: 9pt; color: #444;">{meta}</p>
<hr/>
{body_html}
"""

    pdf = FPDF(orientation="portrait", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    for style, path in fonts.items():
        pdf.add_font("PlanFont", style, str(path))
    pdf.set_font("PlanFont", size=10)
    pdf.add_page()
    pdf.write_html(full_html)
    buf = pdf.output()
    return bytes(buf)
