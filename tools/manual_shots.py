"""Screenshots for docs/manual/: the patched image in the Renode simulation, scaled 2x (pixel-sharp).

  python3 -I tools/manual_shots.py          # needs the patched image (patch.py with all sets) and Renode

1. An SD card with one pad per mode (Sample, Clip, Slicer, Granular, a pad on page 2), the synthetic test signals of
   sim/testsignals.py, and example values for the new controls (Fidelity SP1200, Drive 35 %, clip Shift / Stretch /
   Smooth / Loop Fade).
2. Three simulation runs (sim/run.py) through the screens the manual shows.
3. out/sim/man*.png -> docs/manual/img/*.png at 2x.

Navigation used (screenshot coordinates, 320 x 240): pads in the bottom row at y 200, x 40 / 120 / 200 / 280;
pad page header: picker icon x 25, page-menu icon x 75 (y 40); page menu: Main (94, 94), LFO (183, 94), Env (94, 149),
Config (183, 149), Pos (94, 203); Effects top row: DLY x 40, RVB / FX3 x 200 (y 52). Lists scroll by a swipe.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sim"))
import fb2png  # noqa: E402
from sheet import readpng  # noqa: E402

PY = sys.executable
SIM = os.path.join(ROOT, "out", "sim")
TREE = os.path.join(SIM, "manual_tree")
SD = os.path.join(SIM, "sd_manual.img")
IMG = os.path.join(ROOT, "docs", "manual", "img")

# (row, column, name, cell mode, extra params); row 0 = bottom row of the Pads screen
PADS = [
    (0, 0, "Sample", 0, 'interpqual="2" pkdrive="350"'),
    (0, 1, "Clip", 1, 'synctype="5" quantsize="3" beatcount="8" pkshift="30" pkstretch="25" pkstretchmode="2" '
                      'pkloopfade="10"'),
    (0, 2, "Slicer", 2, ""),
    (0, 3, "Granular", 3, ""),
    (1, 0, "Keys", 0, ""),
    (2, 0, "Page2", 0, ""),
]
SWIPE = ("touch 160 225 wait 0.08 touch 160 195 wait 0.08 touch 160 165 wait 0.08 touch 160 135 wait 0.08 "
         "touch 160 105 wait 0.08 release wait 0.6")
OPEN_PAD = "tap {x} 200 0.15 wait 0.6 press RIGHT wait 0.6 press RIGHT wait 0.6"
MENU = "tap 75 40 0.15 wait 0.6"
RUNS = [
    "wait 2.5 shot man01_splash wait 10 shot man02_pads press LEFT wait 0.6 shot man03_pads2 press LEFT wait 0.5 "
    + OPEN_PAD.format(x=40) + f" {SWIPE} shot man06_sample_main {MENU} shot man07_menu tap 183 149 0.15 wait 0.6 "
    "shot man08_fidelity tap 25 40 0.15 wait 0.8 shot man04_picker press LEFT wait 0.6 shot man05_picker2",
    "wait 12 " + OPEN_PAD.format(x=120) + f" {MENU} tap 94 203 0.15 wait 0.6 {SWIPE} shot man09_clip_pos",
    "wait 12 set 0x19D 1 set 0x1A7 2 set 0x1A8 24000 press HOME wait 0.5 press HOME wait 0.6 tap 200 52 0.15 wait 0.6 "
    "shot man10_effects press RIGHT wait 0.6 shot man11_reverb press LEFT wait 0.5 tap 200 52 0.15 wait 0.6 "
    "shot man12_effects_fx3 press RIGHT wait 0.6 shot man13_fx3 press RIGHT wait 0.6 shot man14_eq press TOOLS "
    "wait 0.6 shot man15_settings press LEFT wait 0.6 shot man16_comp press RIGHT wait 0.5 press RIGHT wait 0.6 "
    "shot man17_dist",
]


def card():
    pre = os.path.join(TREE, "Presets", "Manual")
    shutil.rmtree(TREE, ignore_errors=True)
    os.makedirs(pre)
    subprocess.run([PY, "-I", os.path.join(ROOT, "sim", "testsignals.py"), pre], check=True, stdout=subprocess.DEVNULL)
    src = {0: "drums.wav", 1: "drums.wav", 2: "chord.wav", 3: "chord.wav"}
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<document>", '    <session version="2">']
    for r, c, name, mode, extra in PADS:
        shutil.copyfile(os.path.join(pre, src[mode] if name != "Keys" else "chord.wav"), os.path.join(pre, name + ".wav"))
        out += [f'        <cell row="{r}" column="{c}" layer="0" filename=".\\{name}.wav" type="sample">',
                f'            <params cellmode="{mode}" {extra}/>'.replace(" />", "/>"),
                "            <slices/>", "        </cell>"]
    out += ["    </session>", "</document>", ""]
    for f in ("drums.wav", "chord.wav"):
        os.remove(os.path.join(pre, f))
    open(os.path.join(pre, "preset.xml"), "w").write("\n".join(out))
    if os.path.exists(SD):
        os.remove(SD)
    subprocess.run([PY, "-I", os.path.join(ROOT, "sim", "mksd.py"), TREE, SD], check=True)


def scale2(src, dst):
    w, h, rows = readpng(src)
    px = bytearray()
    for row in rows:
        line = bytearray()
        for x in range(w):
            line += row[x * 3:x * 3 + 3] * 2
        px += line + line
    fb2png.png(dst, w * 2, h * 2, list(px))


def main():
    card()
    for r in RUNS:
        subprocess.run([PY, "-I", os.path.join(ROOT, "sim", "run.py"), "--image", "pk", "--sd", SD] + r.split(),
                       check=True)
    os.makedirs(IMG, exist_ok=True)
    names = sorted(f for f in os.listdir(SIM) if f.startswith("man") and f.endswith(".png"))
    for f in names:
        scale2(os.path.join(SIM, f), os.path.join(IMG, f[3:]))
    print(f"{len(names)} screenshots -> {os.path.relpath(IMG, ROOT)}")


if __name__ == "__main__":
    main()
