"""Build, test and publish the browser patcher: docs/index.html (GitHub Pages) + docs/patches/<slug>.json.

  python3 -I tools/make_web.py [--skip-tests] [--allow-dirty]

1. build.sh + patch.py with every patch set, then the Unicorn tests.
2. tools/webpatch.py: patch = only our bytes (no stock byte; checked), with the result's SHA-256.
3. The page (tools/patcher.html) with the patch inlined: works from GitHub Pages and as a downloaded file.
Same patch format as blackbox-mod's docs/*.json.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "patches"))
import webpatch  # noqa: E402
from cave import VERSION  # noqa: E402

PY = sys.executable
SETS = ["fidelity", "pages", "padpages", "sound", "reverb", "fx3", "master", "cave"]
TESTS = ["test_fidelity", "test_padpages", "test_reverb", "test_fx3", "test_master", "test_ram"]
STOCK = os.path.join(ROOT, "firmware", "MICRO.BIN")
REPO = "https://github.com/kyrillleier-jpg/portkit-micro"

FEATURES = [
    ["Fidelity", "Interp list Normal, HighQ, SP1200, SP-12, S950, MPC60, SP Raw, 16k..2k; on Sample, Clip, Slicer and Granular pads"],
    ["24 dB filter", "State-variable filter replacing the pad biquad, clean resonance"],
    ["Drive and Filter 2", "tanh drive before the filters, second 24 dB SVF in series (pad main page)"],
    ["Clip Shift", "Rotate the loop against the grid, -100..100 ms (clip loop page)"],
    ["Clip Play Len", "Full or 1/4..32 bars (needs Sync)"],
    ["Clip Stretch", "Tempo ±100 %, Stretch Mode Auto / Jump / Smooth (WSOLA, pitch kept)"],
    ["Clip Loop Fade", "0..50 ms dip at the loop seams"],
    ["Sync 1/32", "Eighth Sync entry; Play Len / Stretch hidden when they would have no effect"],
    ["Reverb types", "Plate / Room / Hall / Chamber with 10 settings and Level"],
    ["FX3", "Third send with a second reverb, on its own FX row"],
    ["Master section", "Tools: compressor page (Stock / SSL type, Mix) and master distortion (Soft / Hard / Fold / Tube)"],
    ["Recording", "Pad sends survive recording; the input monitor goes through the pad's sends"],
    ["Pads 9-16", "Second page of the pad grid, paging on Pads, Mixer, Effects and the pad picker"],
    ["Audio load", "CPU load in the status bar"],
]

CONFIG = {
    "lead": "Fidelity, 24 dB filters, clip stretch, a third FX send, a master section and more for the 1010music "
            "bitbox micro. Patch your own stock firmware right here; nothing is uploaded.",
    "stockName": "MICRO.BIN",
    "stockHint": "The unmodified 2.3.4 from 1010music (the <code>MICRO.BIN</code> inside the download zip).",
    "stockSource": "Download the 2.3.4 firmware from 1010music and use the <code>MICRO.BIN</code> inside the zip.",
    "outName": "MICRO.BIN",
    "install": [
        "Keep your stock <code>MICRO.BIN</code> as a backup.",
        "Copy the patched <code>MICRO.BIN</code> to the root of the microSD card.",
        "Hold the <b>white right arrow</b> key while powering on to install.",
        f"The splash shows <b>portkit mod</b> and version <b>{VERSION.decode()}</b>.",
        "To go back: the same steps with the stock <code>MICRO.BIN</code>.",
    ],
    "footer": f'<a href="{REPO}">portkit-micro</a> · MIT · uses findings and code from blackbox-mod by Justin Joe '
              f'(MIT, <a href="{REPO}/blob/main/THIRD_PARTY.md">notices</a>) · not affiliated with 1010music',
}


def run(title, cmd):
    print(f"## {title}", flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args(argv)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty and not a.allow_dirty:
        sys.exit("uncommitted changes: commit first (the page names the commit it was built from), or --allow-dirty")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()

    run("Compile", ["sh", "build.sh"])
    run("Patch (all sets)", [PY, "-I", "patch.py"] + SETS)
    if not a.skip_tests:
        for t in TESTS:
            run(t, [PY, "-I", f"tests/{t}.py"])

    version = VERSION.decode()
    stock = open(STOCK, "rb").read()
    built = open(os.path.join(ROOT, "out", "+".join(SETS), "MICRO.BIN"), "rb").read()
    patch = webpatch.make("portkit-micro", version, "2.3.4", stock, built, features=FEATURES)
    patch.update(title=f"{version}: everything", source_commit=commit + ("-dirty" if dirty else ""),
                 summary="All patch sets; the combination the tests cover.")
    assert webpatch.apply(patch, stock)["image"] == built

    os.makedirs(os.path.join(ROOT, "docs", "patches"), exist_ok=True)
    jpath = os.path.join(ROOT, "docs", "patches", f"{patch['slug']}.json")
    json.dump(patch, open(jpath, "w"), indent=1)
    page = open(os.path.join(ROOT, "tools", "patcher.html")).read()
    for k, v in (("__TITLE__", f"portkit {version} patcher · bitbox micro"),
                 ("__H1__", f"portkit <span>{version}</span> for bitbox micro"),
                 ("__CONFIG__", json.dumps(CONFIG)),
                 ("__PATCHES__", json.dumps([patch], separators=(",", ":")))):
        assert page.count(k) == 1, k
        page = page.replace(k, v)
    open(os.path.join(ROOT, "docs", "index.html"), "w").write(page)
    print(f"docs/index.html ({len(page):,} bytes), {os.path.relpath(jpath, ROOT)}: {len(patch['writes'])} writes, "
          f"{len(patch['append']) // 2} appended; output sha256 {patch['output_sha256'][:16]}, from {patch['source_commit']}")
    print("open docs/index.html in a browser to try it; commit docs/ to publish")


if __name__ == "__main__":
    main(sys.argv[1:])
