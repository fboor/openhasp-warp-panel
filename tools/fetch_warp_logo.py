#!/usr/bin/env python3
"""Download the official WARP logo and prepare it for the openHASP header.

The logo is **not** part of this repository: it is a trademark of Tinkerforge GmbH.
This script fetches the original vector file from Tinkerforge's public repository
and renders it into the white-on-transparent PNG that the openHASP ``img`` object
in ``openhasp/pages.jsonl`` expects:

    openhasp/pages.jsonl  ->  {"id": 11, "obj": "img", "w": 215, "h": 28,
                               "src": "L:/warp-logo.png", "auto_size": 0}

openHASP does not scale images into the ``w``/``h`` box, so the file has to match
it exactly - 215x28 px, RGB white, alpha only.

Usage
-----
    python3 tools/fetch_warp_logo.py                 # writes openhasp/warp-logo.png
    python3 tools/fetch_warp_logo.py --out /tmp/x.png
    python3 tools/fetch_warp_logo.py --url <other svg url>     # track a newer logo
    python3 tools/fetch_warp_logo.py --list-backends           # show what is available

Requirements (any SVG rasteriser, plus Pillow *or* ImageMagick for the last step)
-------------------------------------------------------------------------------
    cairosvg            python3 -m pip install cairosvg
    rsvg-convert        package librsvg2-bin
    inkscape            package inkscape
    ImageMagick         package imagemagick     (its built-in SVG renderer works)
    Pillow              python3 -m pip install pillow

The script reports which rasteriser it used and verifies the result; it exits
non-zero if the output is not a 215x28 white/transparent PNG.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# Pinned to the commit that last touched the file, so the result is reproducible.
# Use --url with the master branch if you deliberately want the newest artwork:
#   https://raw.githubusercontent.com/Tinkerforge/warp-charger/master/warp-charger.com/static/images/warp-logo.svg
PINNED_COMMIT = "25096d35d8ee1ae360971f8367f04509bb3cfcf4"
DEFAULT_URL = ("https://raw.githubusercontent.com/Tinkerforge/warp-charger/"
               + PINNED_COMMIT + "/warp-charger.com/static/images/warp-logo.svg")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(REPO, "openhasp", "warp-logo.png")

WIDTH, HEIGHT = 215, 28          # must match the img object in pages.jsonl
OVERSAMPLE = 4                  # rasterise at 4x, then downscale for smooth edges


# --------------------------------------------------------------------------- #
# SVG rasterisers
# --------------------------------------------------------------------------- #
def rasterise_with_cairosvg(src, dst, width, height):
    import cairosvg                                    # noqa: F401  (import = check)
    subprocess.run([sys.executable, "-m", "cairosvg", "-f", "png",
                    "-o", dst, "--output-width", str(width),
                    "--output-height", str(height), src],
                   check=True, stdout=subprocess.DEVNULL)
    return "cairosvg"


def rasterise_with_rsvg(src, dst, width, height):
    subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height),
                    "-o", dst, src], check=True)
    return "rsvg-convert"


def rasterise_with_inkscape(src, dst, width, height):
    # inkscape derives the height from the aspect ratio; ask for the exact size
    # afterwards by passing the page size only - we crop/scale in the next step.
    subprocess.run(["inkscape", "--export-type=png",
                    "--export-filename=" + dst,
                    "--export-width=" + str(width), src],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "inkscape"


def rasterise_with_imagemagick(src, dst, width, height):
    tool = imagemagick_tool()
    subprocess.run([tool, "-background", "none", src,
                    "-resize", "%dx%d!" % (width, height), dst], check=True)
    return "ImageMagick " + os.path.basename(tool)


RASTERISERS = [
    ("cairosvg", rasterise_with_cairosvg),
    ("rsvg-convert", rasterise_with_rsvg),
    ("inkscape", rasterise_with_inkscape),
    ("ImageMagick", rasterise_with_imagemagick),
]


def imagemagick_tool():
    """Path of the ImageMagick binary, or None."""
    return shutil.which("magick") or shutil.which("convert")


def probe_cairosvg():
    import cairosvg                                        # noqa: F401
    return True


def probe_binary(name):
    return lambda: shutil.which(name) is not None


PROBES = {
    "cairosvg": probe_cairosvg,
    "rsvg-convert": probe_binary("rsvg-convert"),
    "inkscape": probe_binary("inkscape"),
    "ImageMagick": imagemagick_tool,
}


def available():
    """Return [(name, function)] for rasterisers that look usable."""
    found = []
    for name, fn in RASTERISERS:
        try:
            if PROBES[name]():
                found.append((name, fn))
        except ImportError:
            pass
    return found


# --------------------------------------------------------------------------- #
# Resize / whiten / verify
# --------------------------------------------------------------------------- #
def have_pillow():
    try:
        import PIL                                          # noqa: F401
        return True
    except ImportError:
        return False


def ink_ratio(path):
    """Fraction of opaque pixels in an image, or None if it cannot be measured."""
    if have_pillow():
        from PIL import Image
        with Image.open(path) as im:
            alpha = im.convert("RGBA").getchannel("A")
            hist = alpha.histogram()
            opaque = sum(hist[16:])
            return opaque / float(alpha.size[0] * alpha.size[1])
    tool = imagemagick_tool()
    if tool:
        out = subprocess.run(
            [tool, path, "-format", "%[fx:mean.a]", "info:"],
            check=True, capture_output=True, text=True).stdout.strip()
        try:
            return float(out)
        except ValueError:
            return None
    return None


def finish_with_pillow(big, out):
    from PIL import Image
    im = Image.open(big).convert("RGBA").resize((WIDTH, HEIGHT), Image.LANCZOS)
    # keep the alpha channel, force pure white RGB so any fill colour becomes white
    logo = Image.new("RGBA", im.size, (255, 255, 255, 0))
    logo.putalpha(im.getchannel("A"))
    logo.save(out, "PNG", optimize=True)
    return "Pillow"


def finish_with_imagemagick(big, out):
    tool = imagemagick_tool()
    subprocess.run([tool, big, "-resize", "%dx%d!" % (WIDTH, HEIGHT),
                    "-fill", "white", "-colorize", "100",
                    "PNG32:" + out], check=True)
    return "ImageMagick " + os.path.basename(tool)


def verify(out):
    """Sanity-check the produced PNG. Returns a list of problems (empty = ok)."""
    problems = []
    if not os.path.exists(out):
        return ["%s was not created" % out]
    try:
        from PIL import Image
    except ImportError:
        # Without Pillow we can still check the PNG header dimensions
        with open(out, "rb") as fh:
            head = fh.read(26)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            problems.append("output is not a PNG")
        else:
            w = int.from_bytes(head[16:20], "big")
            h = int.from_bytes(head[20:24], "big")
            if (w, h) != (WIDTH, HEIGHT):
                problems.append("size is %dx%d, expected %dx%d" % (w, h, WIDTH, HEIGHT))
            if head[24] != 8:
                problems.append("expected 8 bit per channel")
            if head[25] not in (4, 6):
                problems.append("expected a PNG with an alpha channel "
                                "(colour type %d)" % head[25])
        return problems

    from PIL import Image
    im = Image.open(out)
    if im.size != (WIDTH, HEIGHT):
        problems.append("size is %sx%s, expected %dx%d" % (im.size + (WIDTH, HEIGHT)))
    if im.mode != "RGBA":
        problems.append("mode is %s, expected RGBA" % im.mode)
    px = im.convert("RGBA").load()
    ink = sum(1 for y in range(HEIGHT) for x in range(WIDTH) if px[x, y][3] > 16)
    ratio = ink / float(WIDTH * HEIGHT)
    if not 0.02 < ratio < 0.7:
        problems.append("ink coverage %.0f%% looks wrong (empty or solid image?)"
                        % (ratio * 100))
    coloured = {(px[x, y][0], px[x, y][1], px[x, y][2])
                for y in range(HEIGHT) for x in range(WIDTH) if px[x, y][3] > 16}
    if coloured - {(255, 255, 255), (255, 255, 255)}:
        problems.append("non-white pixels found: %s" % sorted(coloured)[:3])
    print("    size %dx%d, %.0f%% ink, %d colour(s)" % (WIDTH, HEIGHT, ratio * 100, len(coloured)))
    return problems


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Download the official WARP logo and render it as "
                    "%dx%d white/transparent PNG." % (WIDTH, HEIGHT))
    ap.add_argument("--url", default=DEFAULT_URL,
                    help="SVG to download (default: pinned official file)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output PNG path")
    ap.add_argument("--list-backends", action="store_true",
                    help="show which rasterisers are available and exit")
    args = ap.parse_args()

    found = available()
    if args.list_backends:
        print("SVG rasterisers : %s" % (", ".join(n for n, _ in found) or "none"))
        resize = ("Pillow" if have_pillow()
                  else "ImageMagick" if imagemagick_tool() else "none")
        print("final resize    : %s" % resize)
        return 0 if found and resize != "none" else 1

    if not found:
        sys.stderr.write(
            "No SVG rasteriser found. Install one of:\n"
            "  python3 -m pip install cairosvg     (or)\n"
            "  apt install librsvg2-bin inkscape imagemagick\n")
        return 1

    try:
        import urllib.request
    except ImportError:
        sys.stderr.write("need Python 3 (urllib is missing)\n")
        return 1

    tmp = tempfile.mkdtemp(prefix="warp-logo-")
    src = os.path.join(tmp, "warp-logo.svg")
    big = os.path.join(tmp, "warp-logo-big.png")

    print("Downloading %s" % args.url)
    with urllib.request.urlopen(args.url, timeout=60) as response:
        data = response.read()
    if not data.lstrip()[:5].startswith((b"<?xml", b"<svg ")) and b"<svg" not in data[:2048]:
        sys.stderr.write("Downloaded file does not look like an SVG\n")
        return 1
    with open(src, "wb") as fh:
        fh.write(data)
    print("    %d bytes" % len(data))

    for name, fn in found:
        if os.path.exists(big):
            os.remove(big)
        try:
            used = fn(src, big, WIDTH * OVERSAMPLE, HEIGHT * OVERSAMPLE)
        except Exception as exc:                                # noqa: BLE001
            print("    %s failed (%s), trying next" % (name, exc))
            continue
        # A rasteriser can exit 0 and still hand out an empty image - ImageMagick's
        # built-in SVG renderer does that on some systems.  Only accept real output.
        ratio = ink_ratio(big) if os.path.exists(big) else None
        if ratio is None:
            print("Rasterised with %s" % used)
            break
        if ratio < 0.01:
            print("    %s produced an empty image, trying next" % name)
            continue
        print("Rasterised with %s (%.0f%% ink)" % (used, ratio * 100))
        break
    else:
        sys.stderr.write(
            "No usable SVG rasteriser: every backend failed or returned an empty\n"
            "image. Install one of cairosvg (pip), rsvg-convert (librsvg2-bin) or\n"
            "inkscape; ImageMagick's built-in SVG renderer is the last resort.\n")
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    try:
        if have_pillow():
            print("Resized with %s" % finish_with_pillow(big, args.out))
        elif imagemagick_tool():
            print("Resized with %s" % finish_with_imagemagick(big, args.out))
        else:
            sys.stderr.write("Need Pillow or ImageMagick for the resize step\n")
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    problems = verify(args.out)
    if problems:
        for p in problems:
            sys.stderr.write("FAILED: %s\n" % p)
        return 1

    print("Wrote %s (%d bytes)" % (args.out, os.path.getsize(args.out)))
    print("Copy it to the plate as /warp-logo.png (see README, step 1.2).")
    print("The logo is a trademark of Tinkerforge GmbH and is not covered by this "
          "project's MIT license.")
    return 0


if __name__ == "__main__":
    sys.exit(main())