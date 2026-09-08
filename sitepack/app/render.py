"""HTML + PDF rendering. Reuses sample CSS shell via Jinja template."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import SitePack

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "output"
SAMPLE_HTML = Path("/workspace/sitepack/sample/sitepack-pro-ukazka.html")


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_html(pack: SitePack) -> str:
    tpl = _env().get_template("report.html")
    return tpl.render(pack=pack)


def write_html(pack: SitePack, out_path: Path | None = None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if out_path is None:
        slug = pack.parcel.ruian_id or "pack"
        out_path = OUTPUT_DIR / f"sitepack-{slug}.html"
    out_path.write_text(render_html(pack), encoding="utf-8")
    return out_path.resolve()


def html_to_pdf(html_path: Path, pdf_path: Path | None = None) -> Path:
    """Chrome/Chromium headless — same approach as sample/README.md."""
    html_path = html_path.resolve()
    if pdf_path is None:
        pdf_path = html_path.with_suffix(".pdf")
    pdf_path = pdf_path.resolve()
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise RuntimeError("google-chrome / chromium not found for PDF export")
    uri = html_path.as_uri()
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--no-sandbox",
        f"--print-to-pdf={pdf_path}",
        uri,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    if not pdf_path.exists():
        raise RuntimeError(f"PDF was not created: {pdf_path}")
    return pdf_path


def generate_pack_files(pack: SitePack, stem: str | None = None) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = stem or f"sitepack-{pack.parcel.ruian_id or 'pack'}"
    html_path = OUTPUT_DIR / f"{stem}.html"
    pdf_path = OUTPUT_DIR / f"{stem}.pdf"
    write_html(pack, html_path)
    html_to_pdf(html_path, pdf_path)
    return html_path.resolve(), pdf_path.resolve()
