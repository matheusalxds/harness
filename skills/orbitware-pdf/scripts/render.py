#!/usr/bin/env python3
"""Gera o PDF Orbitware: injeta o CSS da marca e o logo no HTML e imprime com o Chrome headless.

    python3 render.py documento.html [saida.pdf]
"""
import base64
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    origem = Path(sys.argv[1]).resolve()
    destino = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else origem.with_suffix(".pdf")

    css = (SKILL / "assets" / "orbitware.css").read_text(encoding="utf-8")
    logo = base64.b64encode((SKILL / "assets" / "logo.png").read_bytes()).decode()
    html = origem.read_text(encoding="utf-8")
    html = html.replace("{{CSS}}", css).replace("{{LOGO}}", f"data:image/png;base64,{logo}")

    pendentes = [m for m in ("[NÚMERO]", "[DATA]", "[VALIDADE]", "[Nome do cliente]", "R$ [0,00]") if m in html]
    if pendentes:
        print(f"aviso: placeholders ainda no documento: {', '.join(pendentes)}", file=sys.stderr)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(html)
    resultado = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={destino}", f"file://{tmp.name}"],
        capture_output=True, text=True, timeout=120,
    )
    Path(tmp.name).unlink(missing_ok=True)
    if resultado.returncode != 0 or not destino.exists():
        print(resultado.stderr, file=sys.stderr)
        return 1
    print(destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
