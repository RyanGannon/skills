#!/usr/bin/env python3
"""
Batch OCR pipeline for scanned PDFs -> a searchable PDF with an invisible text layer.

Designed to be called multiple times in small page batches (bash tool calls have a
runtime limit, and OCR-ing 30+ pages in one call will time out). Workflow:

    python3 ocr_pdf.py setup   <input.pdf> <workdir>
    python3 ocr_pdf.py ocr     <workdir> <start_page> <end_page>   # repeat over ranges
    python3 ocr_pdf.py status  <workdir>
    python3 ocr_pdf.py merge   <workdir> <output.pdf>

Batch size of ~6 pages per `ocr` call is a safe default (fits comfortably under a
5-minute tool timeout). Increase/decrease based on how fast calls are completing.
"""
import sys
import os
import glob
import subprocess
import pickle
import io

def setup(input_pdf, workdir):
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(os.path.join(workdir, "batches"), exist_ok=True)
    print("Converting pages to JPEG images (300 DPI, quality 85)...")
    subprocess.run(
        ["pdftoppm", "-jpeg", "-jpegopt", "quality=85", "-r", "300",
         input_pdf, os.path.join(workdir, "page")],
        check=True
    )
    images = sorted(glob.glob(os.path.join(workdir, "page-*.jpg")))
    print(f"Converted {len(images)} pages. Now run:")
    print(f"  python3 ocr_pdf.py ocr {workdir} 1 6")
    print(f"  python3 ocr_pdf.py ocr {workdir} 7 12")
    print("  ...(continue in batches of ~6 until all pages are covered)")
    print(f"  python3 ocr_pdf.py status {workdir}")
    print(f"  python3 ocr_pdf.py merge {workdir} <output.pdf>")

def ocr_batch(workdir, start, end):
    import pytesseract
    images = sorted(glob.glob(os.path.join(workdir, "page-*.jpg")))
    if not images:
        print("No page images found — did you run `setup` first?")
        sys.exit(1)
    results = {}
    for i in range(start, min(end, len(images)) + 1):
        img_path = images[i - 1]
        print(f"OCR page {i}/{len(images)}: {img_path}", flush=True)
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(img_path, extension='pdf', config='--psm 3')
        results[i] = pdf_bytes
    batch_path = os.path.join(workdir, "batches", f"batch_{start}_{end}.pkl")
    with open(batch_path, "wb") as f:
        pickle.dump(results, f)
    print(f"Saved batch to {batch_path}")

def status(workdir):
    images = sorted(glob.glob(os.path.join(workdir, "page-*.jpg")))
    total = len(images)
    done = set()
    for bf in glob.glob(os.path.join(workdir, "batches", "batch_*.pkl")):
        with open(bf, "rb") as f:
            done.update(pickle.load(f).keys())
    missing = [i for i in range(1, total + 1) if i not in done]
    print(f"Total pages: {total}")
    print(f"OCR'd: {len(done)}")
    if missing:
        print(f"Missing pages: {missing}")
        print("Run more `ocr` batches to cover these page ranges.")
    else:
        print("All pages OCR'd. Ready to `merge`.")

def merge(workdir, output_pdf):
    from pypdf import PdfWriter, PdfReader
    all_results = {}
    for bf in sorted(glob.glob(os.path.join(workdir, "batches", "batch_*.pkl"))):
        with open(bf, "rb") as f:
            all_results.update(pickle.load(f))
    images = sorted(glob.glob(os.path.join(workdir, "page-*.jpg")))
    total = len(images)
    missing = [i for i in range(1, total + 1) if i not in all_results]
    if missing:
        print(f"ERROR: missing OCR results for pages {missing}. Run `ocr` batches to cover them first.")
        sys.exit(1)
    writer = PdfWriter()
    for i in range(1, total + 1):
        reader = PdfReader(io.BytesIO(all_results[i]))
        writer.add_page(reader.pages[0])
    with open(output_pdf, "wb") as f:
        writer.write(f)
    print(f"Saved searchable PDF: {output_pdf}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "setup":
        setup(sys.argv[2], sys.argv[3])
    elif cmd == "ocr":
        ocr_batch(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "status":
        status(sys.argv[2])
    elif cmd == "merge":
        merge(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
