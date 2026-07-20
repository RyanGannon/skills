#!/usr/bin/env python3
"""Extract mermaid blocks from a Markdown file and render each to PNG via mmdc.

The source Markdown is never modified — blocks are read, not rewritten.

Usage:
    render_mermaid.py --input REPORT.md --outdir ./diagrams
    render_mermaid.py --input REPORT.md --outdir ./diagrams --theme dark
    render_mermaid.py --input REPORT.md --outdir ./diagrams \
        --names blackbox-probe-flow,argocd-app-of-apps

Prints a JSON manifest to stdout: one entry per diagram with filename,
pixel dimensions, and the display width to use when embedding.
"""
import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

# Mermaid's dark theme needs an opaque dark surface. Transparent would put
# light text onto a light page and render the diagram unreadable.
DARK_BACKGROUND = "#1D2125"  # Atlassian dark surface
LIGHT_BACKGROUND = "white"


def find_chrome() -> str:
    """Return a usable Chrome/Chromium binary path, or exit with guidance.

    Snap-packaged browsers are confined and cannot read files outside the
    user's home, so they are rejected: mmdc feeds Chrome a temp file.
    """
    if env := os.environ.get("PUPPETEER_EXECUTABLE_PATH", "").strip():
        if Path(env).is_file():
            return env

    # Puppeteer's own cache is the most reliable source.
    cache = Path.home() / ".cache" / "puppeteer" / "chrome"
    if cache.is_dir():
        for d in sorted(cache.iterdir(), reverse=True):
            binary = d / "chrome-linux64" / "chrome"
            if binary.is_file():
                return str(binary)
            binary = d / "chrome-mac" / "Chromium.app" / "Contents" / "MacOS" / "Chromium"
            if binary.is_file():
                return str(binary)

    for name in ("google-chrome-stable", "google-chrome", "chromium-browser", "chromium"):
        path = shutil.which(name)
        if path and "/snap/" not in os.path.realpath(path):
            return path

    sys.exit(
        "No usable Chrome found.\n"
        "  Snap-packaged browsers are confined and cannot read mmdc's temp files.\n"
        "  Fix: npx puppeteer browsers install chrome\n"
        "  Or:  export PUPPETEER_EXECUTABLE_PATH=/path/to/chrome"
    )


def find_mmdc() -> list[str]:
    """Return the argv prefix that invokes mmdc."""
    if path := shutil.which("mmdc"):
        return [path]
    local = Path.cwd() / "node_modules" / ".bin" / "mmdc"
    if local.is_file():
        return [str(local)]
    if shutil.which("npx"):
        return ["npx", "--yes", "@mermaid-js/mermaid-cli"]
    sys.exit("mmdc not found. Install with: npm install @mermaid-js/mermaid-cli")


def png_size(path: Path) -> tuple[int, int]:
    return struct.unpack(">II", path.read_bytes()[16:24])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--theme", default="default", choices=["default", "dark", "forest", "neutral"])
    ap.add_argument("--scale", default=2, type=int, help="render multiplier; 2 keeps text crisp")
    ap.add_argument("--names", default="", help="comma-separated basenames, in document order")
    ap.add_argument("--background", default="", help="override the theme's background")
    args = ap.parse_args()

    blocks = re.findall(r"```mermaid\n(.*?)```", args.input.read_text(), flags=re.S)
    if not blocks:
        sys.exit(f"No mermaid blocks found in {args.input}")

    names = [n.strip() for n in args.names.split(",") if n.strip()]
    if names and len(names) != len(blocks):
        sys.exit(f"--names has {len(names)} entries but the file has {len(blocks)} diagrams")
    if not names:
        names = [f"diagram-{i + 1}" for i in range(len(blocks))]

    background = args.background or (
        DARK_BACKGROUND if args.theme == "dark" else LIGHT_BACKGROUND
    )

    args.outdir.mkdir(parents=True, exist_ok=True)
    pptr = args.outdir / ".puppeteer.json"
    pptr.write_text(json.dumps({
        "executablePath": find_chrome(),
        "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    }))

    mmdc = find_mmdc()
    manifest = []
    for source, name in zip(blocks, names):
        mmd = args.outdir / f"{name}.mmd"
        png = args.outdir / f"{name}.png"
        mmd.write_text(source)
        subprocess.run(
            [*mmdc, "-i", str(mmd), "-o", str(png), "-p", str(pptr),
             "-t", args.theme, "-b", background, "-s", str(args.scale)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        w, h = png_size(png)
        manifest.append({
            "name": f"{name}.png",
            "path": str(png),
            "width": w,
            "height": h,
            # Rendered at args.scale; embed at 1x so it displays at its true size.
            "display_width": w // args.scale,
            "bytes": png.stat().st_size,
        })

    json.dump({"theme": args.theme, "diagrams": manifest}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
