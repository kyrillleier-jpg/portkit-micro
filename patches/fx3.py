"""FX3: a third send effect on engine bus 0xc (src/fx3.c, src/fx3_thunk.S) and its cell on the Effects screen
(src/padpages.c: second touch on RVB switches the right cell RVB <-> FX3; pages by the left arrow). Needs `fidelity`
(registers FX3 Send), `sound` (pad record entry), `padpages`, `reverb` and the cave. Addresses: re/symbols.md "FX3"."""
import os

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

HOOKS = [
    (0x080B2600, 0x080A3328, "fx3_mix_a"),      # sample pads: final mix scratch -> output, first scratch -> bus 0xc
    (0x080B8046, 0x080A3328, "fx3_mix_b"),      # clip pads
    (0x08096D04, 0x080A3328, "fx3_master"),     # block driver: bus 0 += bus 0xe, then += FX3(bus 0xc)
]

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
)
