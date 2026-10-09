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
    # pad pickers: every construction
    (0x0806CC48, 0x080733B4, "ctor_picker"),
    (0x0806CC58, 0x080733B4, "ctor_picker"),
    (0x0806E25E, 0x080733B4, "ctor_picker"),
    (0x0807237E, 0x080733B4, "ctor_picker"),
    (0x08082602, 0x080733B4, "ctor_picker"),
    (0x0808747E, 0x080733B4, "ctor_picker"),
    (0x08090BF0, 0x080733B4, "ctor_picker"),
    (0x080922DC, 0x080733B4, "ctor_picker"),
    # picker placing: its last set_rect (the footer's), then tiles / names / footer brought to the page
    (0x08073564, 0x0805CB36, "padpages_picker_place"),
]
EXCLUSIVE = {0x080862A4, 0x08086478, 0x08084034, 0x08084138, 0x08083E40, 0x080696E0, 0x080866B0, 0x080733B4}

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
    (0x08084842, "00273e46", "loop_rows"),       # movs r7, #0; mov r6, r7: Pads tile state loop, first row
    (0x08086B5A, "00273e46", "loop_rows"),       # ... Effects tile state loop
    (0x08069DF8, "47ea0403", "loop_d_code"),     # orr.w r3, r7, r4: Mixer tile state loop, pad address
    (0x080732DC, "12f00e0f", "picker_sel_tst"),  # tst.w r2, #0xe: picker "mark selected", row on the page
    (0x0807331E, "a3b29942", "picker_mark0"),    # uxth r3, r4; cmp r1, r3: picker "mark playing", row 0
    (0x0807332E, "44f01003", "picker_mark1"),    # orr r3, r4, #0x10: ... row 1
    (0x08076AD4, "46f040f9", "padpages_title"),  # bl snprintf(buf, 0x18, "Pads") in the title builder
    (0x08076AF0, "46f032f9", "padpages_title"),  # bl snprintf(buf, 0x18, "FX")
]

# (vtable slot, stock word, cave symbol)
WORDS = [
    (0x080C64AC, 0x080865E5, "padpages_a_input"),    # Effects screen (A) vtable +0x30
    (0x080C64B0, 0x080863A1, "padpages_a_notify"),   # Effects screen (A) vtable +0x34
    (0x080C6378, 0x08084155, "padpages_b_notify"),   # Pads screen (B) vtable +0x34
    (0x080C0690, 0x080691B1, "padpages_d_input"),    # Mixer screen (D) vtable +0x30
    (0x080C5CBC, 0x08073255, "padpages_picker_input"),  # pad picker vtable +0x30
]

PATCHES = (
    [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
    + [(at, bytes.fromhex(old), bl(at, sym[name])) for at, old, name in THUNKS]
    + [(at, struct.pack("<I", old), struct.pack("<I", sym[name] | 1)) for at, old, name in WORDS]
)
