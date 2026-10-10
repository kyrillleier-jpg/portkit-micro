"""Reverb types for the FX2 reverb cell: Type (Plate / Room / Hall / Chamber) and eleven settings incl. Level (src/reverb.c).
Needs the cave; the page filter for Type = Plate lives in clip_page (patches/sound.py hooks the page builder), so this
patchset goes together with `sound`. Addresses: re/symbols.md "Reverb"."""
import os

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

HOOKS = [
    (0x0806B89A, 0x08069E7C, "reverb_register"),         # list 0x178 "FX2" -> "Type:" + the eleven settings
    (0x08089AA8, 0x0808951E, "reverb_defaults_first"),   # reverb record (type 0x44): Type before "Decay 600"
    (0x08089ABE, 0x0808951E, "reverb_defaults_last"),    # ... settings after "Damping 500"
    (0x080A9912, 0x080A9EC4, "reverb_core_thunk"),       # reverb process: the plate core call
]
EXCLUSIVE = {0x080A9EC4}

PATCHES = [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
