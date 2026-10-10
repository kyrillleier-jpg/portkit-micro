"""Drive and Filter 2 (src/filter.c): the three new pad parameters in every pad record and on the main page of every
pad mode. Shift for clips (src/clipshift.c): parameter on the Clip loop page, clip stream reads / seeks rotated. Their registration (Drive, Filter 2, Res 2) rides on `interp_register` in patches/fidelity.py, the DSP on
filter_process; so this patchset needs `fidelity` and the cave. Addresses: re/symbols.md "Drive und Filter 2"."""
import os
import struct

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

P_FILT2, P_RES2, P_DRIVE, P_SHIFT, P_PLAYLEN, P_STRETCH = 0x1C0, 0x1C1, 0x1C2, 0x1C3, 0x1C4, 0x1C5
STORE_ADD = 0x0808951E

# pad record init 0x08089548: the two pad blocks' "add Filter (0xaa)" -> add it, then the new parameters
HOOKS = [
    (0x080896F8, STORE_ADD, "pad_store_add"),
    (0x08089922, STORE_ADD, "pad_store_add"),
    # clip reader 0x080b55ac and segment starts 0x080b4644 / 0x080b490c: the stream calls get the pad (r4) and shift
    (0x080B5630, 0x080A4500, "clip_read1_thunk"),
    (0x080B5720, 0x080A4500, "clip_read1_thunk"),
    (0x080B567E, 0x080A44C8, "clip_read2_thunk"),
    (0x080B56F2, 0x080A44C8, "clip_read2_thunk"),
    (0x080B47D2, 0x080A4624, "clip_seek_thunk"),
    (0x080B4B4C, 0x080A4624, "clip_seek_thunk"),
]

# Main page (page 0 of 6 x 45 ids) of every pad-mode table (Clip, Granular, Sample, Slicer, ...; two variants each):
# Level, Pitch, Filter, Res, Pan -> + Filter 2, Res 2, Drive. 8 entries, as many as the Sample settings page has.
MAIN_PAGES = [0x080C6A1C, 0x080C6C38, 0x080C6EEC, 0x080C7108, 0x080C76C0, 0x080C78DC, 0x080C7AF8, 0x080C7E28,
              0x080C8044]
MAIN = [0x04, 0x3F, 0xAA, 0x11, 0x45]
NEW = [P_FILT2, P_RES2, P_DRIVE]

# play length: the segment-count loads before "next segment < count" in the clip voice 0x080b5aa8 (pad in r6)
THUNKS = [
    (0x080B5F2E, "d6e99012", "clip_segments_thunk"),
    (0x080B611A, "d6e99012", "clip_segments_thunk"),
    # stretch: the beat count (and the Auto estimate) the clip setup 0x080b40fc turns into the clip's length in ticks
    (0x080B42AC, "daf8803b", "clip_beatcount_thunk"),
    (0x080B4258, "07ee902a", "clip_autobeats_thunk"),
]

# Clip loop page (page 2): Loop Mode, Beat Count, Quant Size, Sync -> + Shift, Play Len, Stretch
CLIP_TABLES = [0x080C6A1C, 0x080C6C38]
LOOP_PAGE = 2 * 0x5A
LOOP = [0x6F, 0xB4, 0x2A, 0x76]

PATCHES = (
    [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
    + [(t, struct.pack("<8H", *MAIN, 0, 0, 0), struct.pack("<8H", *MAIN, *NEW)) for t in MAIN_PAGES]
    + [(at, bytes.fromhex(old), bl(at, sym[name])) for at, old, name in THUNKS]
    + [(t + LOOP_PAGE, struct.pack("<7H", *LOOP, 0, 0, 0),
       struct.pack("<7H", *LOOP, P_SHIFT, P_PLAYLEN, P_STRETCH)) for t in CLIP_TABLES]
)
