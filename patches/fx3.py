"""FX3: a third send effect on engine bus 0xc (src/fx3.c, src/fx3_thunk.S) and its cell on the Effects screen
(src/padpages.c: second touch on RVB switches the right cell RVB <-> FX3; pages by the left arrow). Needs `fidelity`
(registers FX3 Send), `sound` (pad record entry), `padpages`, `reverb` and the cave. Addresses: re/symbols.md "FX3"."""
import os
import struct

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

HOOKS = [
    (0x080B2600, 0x080A3328, "fx3_mix_a"),      # sample pads: final mix scratch -> output, first scratch -> bus 0xc
    (0x080B8046, 0x080A3328, "fx3_mix_b"),      # clip pads
    (0x08096D04, 0x080A3328, "fx3_master"),     # block driver: bus 0 += bus 0xe, then += FX3(bus 0xc)
    (0x08083964, 0x0808EEDC, "fx3_right"),      # right arrow on the FX cell page (0x23 -> 0x14); from FX3: master EQ
    (0x0807B59E, 0x08089FC4, "rec_reinit"),     # recording: pad record rebuilt as a clip pad; the sends kept (recmon.c)
]

# the input node's process (vtable entry): the monitor through the selected pad's sends (src/recmon.c)
DATA = [(0x080DDFB4, 0x080A4D1D, "mon_node")]

# FX cell record row 3 (app +0x2248, cell 0x330): the eight stock inits (boot, new / loaded preset) make it an empty
# type-0 record; `movs r3, #0` before each (type byte for 0x08089fc4) -> `movs r3, #0x44` (reverb) for FX3
ROW3_TYPE = [0x08078180, 0x0807ACC4, 0x0807ACEA, 0x0807C3DE, 0x08080F74, 0x0808AE36, 0x0808B2BE, 0x0808E2F0]

THUNKS = [
    (0x080B13E0, "d6ed007a", "fx3_check_a"),    # vldr s15, [r6]: sample pads' "any send on"
    (0x080B7D8C, "dbed007a", "fx3_check_b"),    # vldr s15, [fp]: clip pads'
    (0x08086336, "bc222146", "fx3id_r2_r1r4"),  # Effects screen: FX2 send id -> FX3 Send while FX3 is shown
    (0x08086376, "019abc21", "fx3id_r1_r2sp4"),
    (0x080864BE, "bc222946", "fx3id_r2_r1r5"),
    (0x080864CE, "bc213846", "fx3id_r1_r0r7"),
    (0x08086542, "0099bc20", "fx3id_r0_r1sp"),
]

PATCHES = (
    [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
    + [(at, bytes.fromhex(old), bl(at, sym[name])) for at, old, name in THUNKS]
    + [(at, bytes.fromhex("0023"), bytes.fromhex("4423")) for at in ROW3_TYPE]
    + [(at, struct.pack("<I", old), struct.pack("<I", sym[name] | 1)) for at, old, name in DATA]
)
