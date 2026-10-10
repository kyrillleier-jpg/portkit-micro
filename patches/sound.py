"""Drive and Filter 2 (src/filter.c): the three new pad parameters in every pad record and on the main page of every
pad mode. Shift for clips (src/clipshift.c): parameter on the Clip loop page, clip stream reads / seeks rotated. Their registration (Drive, Filter 2, Res 2) rides on `interp_register` in patches/fidelity.py, the DSP on
filter_process; so this patchset needs `fidelity` and the cave. Addresses: re/symbols.md "Drive und Filter 2"."""
import os
import struct

from thumb import ROOT, bl, symbols

sym = symbols(os.path.join(ROOT, "out", "cave.elf"))

P_FILT2, P_RES2, P_DRIVE, P_SHIFT, P_PLAYLEN, P_STRETCH = 0x1C0, 0x1C1, 0x1C2, 0x1C3, 0x1C4, 0x1C6  # 0x1c5 is taken by the firmware (0x0807d37e)
P_SMODE = 0x1C7
STORE_ADD = 0x0808951E

# pad record init 0x08089548: the two pad blocks' "add Filter (0xaa)" -> add it, then the new parameters
HOOKS = [
    (0x080896F8, STORE_ADD, "pad_store_add"),
    (0x08089922, STORE_ADD, "pad_store_add"),
    # smooth time stretch (src/stretch.c): the clip slot reader's read + resample
    (0x080B58FC, 0x080B55AC, "clip_render"),
    # audio load (src/load.c): the audio task's two per-block calls, both call sites each; status bar right text
    (0x08042458, 0x08093D44, "load_in"),
    (0x08042474, 0x08093D44, "load_in"),
    (0x08042464, 0x08093E48, "load_out"),
    (0x08042480, 0x08093E48, "load_out"),
    (0x08070754, 0x08060366, "load_text"),           # the idle (empty) case; 0x08070748 is "FULL"
    # Sync list + "1/32"
    (0x0806AB7E, 0x08069E7C, "sync_register"),
    # parameter pages: hide Play Len / Stretch when the clip is not synced (every caller of the page builder)
    (0x08085312, 0x08076D8C, "clip_page"),
    (0x0808542C, 0x08076D8C, "clip_page"),
    (0x08087D82, 0x08076D8C, "clip_page"),
    (0x08087DE8, 0x08076D8C, "clip_page"),
    (0x08088110, 0x08076D8C, "clip_page"),
    (0x0808814A, 0x08076D8C, "clip_page"),
    (0x080910DE, 0x08076D8C, "clip_page"),
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
    # stretch, live at every segment start (0x080b490c): file position = index x length x speed; last-segment test
    (0x080B4A68, "27ee888a", "clip_pos_thunk"),
    (0x080B49B4, "d4f84032", "clip_last_thunk"),
]

EXCLUSIVE = {0x08076D8C, 0x080B55AC, 0x08093D44, 0x08093E48}

# Pad record capacity 64 -> 72 entries (`movs r1, #0x40` before the store allocation 0x0808949e in the record init
# 0x08089548 and the record reset 0x08089f8c): the full pad record holds 58 stock + 6 new entries, no spare; on the
# device Stretch (the 64th) did not stick. Only the first allocation of a record sets its capacity.
CAPACITY = [(0x0808954E, "4021", "4821"), (0x08089F98, "4021", "4821")]

# Sync's beats table (0x080c4f7c, 7 entries) -> sync_beats (8) in the clip parameter handler's literal
DATA = [(0x080B74E4, 0x080C4F7C, "sync_beats")]

# Clip loop page (page 2): Loop Mode, Beat Count, Quant Size, Sync -> + Shift, Play Len, Stretch, Stretch Mode
CLIP_TABLES = [0x080C6A1C, 0x080C6C38]
LOOP_PAGE = 2 * 0x5A
LOOP = [0x6F, 0xB4, 0x2A, 0x76]

PATCHES = (
    [(at, bl(at, stock), bl(at, sym[name])) for at, stock, name in HOOKS]
    + [(t, struct.pack("<8H", *MAIN, 0, 0, 0), struct.pack("<8H", *MAIN, *NEW)) for t in MAIN_PAGES]
    + [(at, bytes.fromhex(old), bl(at, sym[name])) for at, old, name in THUNKS]
    + [(at, struct.pack("<I", old), struct.pack("<I", sym[name])) for at, old, name in DATA]
    + [(at, bytes.fromhex(old), bytes.fromhex(new)) for at, old, new in CAPACITY]
    + [(t + LOOP_PAGE, struct.pack("<8H", *LOOP, 0, 0, 0, 0),
       struct.pack("<8H", *LOOP, P_SHIFT, P_PLAYLEN, P_STRETCH, P_SMODE)) for t in CLIP_TABLES]
)
