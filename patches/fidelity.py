"""Fidelity (Interp list + pad crunch + machine modes) and the 24 dB SVF in place of the stock pad biquad
(src/filter.c). Needs the code cave from ./build.sh, appended by `cave`. Addresses: re/symbols.md."""
import os

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

# (call site, stock callee, cave symbol). Each list covers EVERY call to its stock callee in the image; patch.py checks
# that, so a missed caller fails the build instead of running the stock path unnoticed.
HOOKS = [
    # parameter registration: Interp list 2 -> 14 entries, label "Fidelity:"
    (0x0806B34A, 0x08069E7C, "interp_register"),
    # per-voice filter process: class A (sample, granular), class B (clip, slicer)
    (0x080AD960, 0x080B8420, "filter_voice_a"),
    (0x080B5CCC, 0x080B8420, "filter_voice_b"),
    # machine modes: park pad / position / rate on the way into the sample-voice reader, then swap its two kernels
    (0x080AEE92, 0x080ADC4C, "voice_read"),
    (0x080AF0D8, 0x080ADC4C, "voice_read"),
    (0x080AF19A, 0x080ADC4C, "voice_read"),
    (0x080ADF00, 0x080A1400, "read_normal"),
    (0x080ADF24, 0x080A1400, "read_normal"),
    (0x080ADF48, 0x080A1400, "read_normal"),
    (0x080ADD4C, 0x080A1494, "read_hq"),
    (0x080ADDD8, 0x080A1494, "read_hq"),
    (0x080ADDFC, 0x080A1494, "read_hq"),
]

# Stock callees whose every caller must be hooked. register_list has many other callers (every list parameter), so it
# is not in here.
EXCLUSIVE = {0x080B8420, 0x080ADC4C, 0x080A1400, 0x080A1494}

PATCHES = [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
