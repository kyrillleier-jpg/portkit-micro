"""Master section (src/master.c, src/master_thunk.S): the stock compressor's settings (Threshold, Ratio, Attack, Release,
Gain) and a master distortion, on pages next to the settings page (Tools screen: left arrow = Compressor, right arrow =
Distortion). Needs `fidelity` (registers the parameters), `sound` (page wrapper clip_page), `padpages` (left arrow) and
the cave. Addresses: re/symbols.md "Master-Sektion"."""
import os
import struct

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

HOOKS = [
    (0x08089F78, 0x0808951E, "master_store_add"),   # settings store init 0x08089e04: last add (0x17b), then ours
    (0x08097056, 0x080B9B04, "master_comp"),        # block driver: compressor (engine +0xfb38): Stock / SSL, Mix
    (0x0807E884, 0x0807D358, "master_knob"),        # dispatcher, command 0x6e (knob): Comp Type change -> page again
]

THUNKS = [
    (0x08096D1C, "1af80330", "master_dist_thunk"),  # ldrb.w r3, [sl, r3]: compressor flag; distortion on bus 0 first
    (0x080839BC, "47f6e473", "tools_btn"),          # movw r3, #0x7fe4: Tools button -> settings page first
]

# right arrow: case table 0x08083800 (ldr pc, index screen - 2), screen 0x25 (Tools / settings) -> tools_right
DATA = [(0x08083800 + 4 * (0x25 - 2), 0x080837E9, "tools_right")]

PATCHES = (
    [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
    + [(at, bytes.fromhex(old), bl(at, sym[name])) for at, old, name in THUNKS]
    + [(at, struct.pack("<I", old), struct.pack("<I", sym[name] | 1)) for at, old, name in DATA]
)
