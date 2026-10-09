"""Pad pages: pads 9-16 as a second page of the 2 x 4 pad grid (src/padpages.c, src/padpages_thunk.S, re/symbols.md
"Seiten-Variante"). Needs the code cave from ./build.sh, appended by `cave`."""
import os
import struct

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

# (call site, stock callee, cave symbol): every call of each stock callee (EXCLUSIVE, checked by patch.py).
HOOKS = [
    # guarded entries -> page-aware guards (the stock guards run before the push of lr, so no thunk can go there)
    (0x080863CA, 0x080862A4, "padpages_a_update"),
    (0x08086412, 0x080862A4, "padpages_a_update"),
    (0x0808642E, 0x080862A4, "padpages_a_update"),
    (0x0808660E, 0x08086478, "padpages_a_touch"),
    (0x08084320, 0x08084034, "padpages_b_update"),
    (0x08084340, 0x08084034, "padpages_b_update"),
    (0x08084374, 0x08084034, "padpages_b_update"),
    (0x08084252, 0x08084138, "padpages_b_visible"),
    (0x0808428E, 0x08084138, "padpages_b_visible"),
    (0x080842CA, 0x08084138, "padpages_b_visible"),
    (0x08084306, 0x08084138, "padpages_b_visible"),
    # the UI manager constructs the three grid screens once (0x08085130): remember them
    (0x08085140, 0x08083E40, "ctor_b"),
    (0x0808519C, 0x080696E0, "ctor_d"),
    (0x080851C4, 0x080866B0, "ctor_a"),
]
EXCLUSIVE = {0x080862A4, 0x08086478, 0x08084034, 0x08084138, 0x08083E40, 0x080696E0, 0x080866B0}

# (site, stock instruction bytes, cave symbol): a 4-byte instruction in a function body becomes a BL to a thunk.
THUNKS = [
    (0x0808407C, "c3f30312", "row_b_r2_r3"),     # ubfx r2, r3, #4, #4
    (0x080840A0, "c3f30310", "row_b_r0_r3"),     # ubfx r0, r3, #4, #4
    (0x08084268, "c5f30315", "row_b_r5_r5"),     # ubfx r5, r5, #4, #4
    (0x080842A4, "c5f30315", "row_b_r5_r5"),
    (0x080842D2, "c6f30310", "row_b_r0_r6"),     # ubfx r0, r6, #4, #4
    (0x080862F2, "c3f30317", "row_a_r7_r3"),     # ubfx r7, r3, #4, #4
    (0x080864EA, "c0f30312", "row_a_r2_r0"),     # ubfx r2, r0, #4, #4
    (0x0808655E, "c0f30312", "row_a_r2_r0"),
    (0x08069280, "4fea2318", "row_d_r8_r3"),     # asr.w r8, r3, #4
    (0x080839E6, "47f6e473", "left_arrow"),      # movw r3, #0x7fe4 (button 2 = left arrow, per-screen case)
]

# (vtable slot, stock word, cave symbol)
WORDS = [
    (0x080C64AC, 0x080865E5, "padpages_a_input"),    # Effects screen (A) vtable +0x30
    (0x080C64B0, 0x080863A1, "padpages_a_notify"),   # Effects screen (A) vtable +0x34
    (0x080C6374, 0x08083DED, "padpages_b_input"),    # Pads screen (B) vtable +0x30
    (0x080C6378, 0x08084155, "padpages_b_notify"),   # Pads screen (B) vtable +0x34
]

PATCHES = (
    [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
    + [(at, bytes.fromhex(old), bl(at, sym[name])) for at, old, name in THUNKS]
    + [(at, struct.pack("<I", old), struct.pack("<I", sym[name] | 1)) for at, old, name in WORDS]
)
