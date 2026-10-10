"""The compiled code cave (./build.sh), appended after the stock image, plus the splash marking a modified build:
line 2 "by 1010music" -> "portkit mod", line 3 "2.3.4" -> "2.3.4-pk<BUILD>". Slots are 16 bytes; a pointer table
follows at 0x080c5780, and the panel shows at most 10 characters of the version (bitbox-micro-fw-patch)."""
import os

from thumb import ROOT, STOCK_END

BUILD = b"G"    # 1 = Fidelity + 24 dB SVF (no machine drive), 2 = + Fidelity on Clip / Slicer / Granular pages, 3 = + pad pages (pads 9-16), 4 = page switch on the real Pads screen (0x63), 5 = left arrow pages, page indicator on Pads, 6 = select via 0x63, touch toggles on Pads and Mixer, 7 = Effects: selected cell toggles, P1/P2, 8 = page in the title (Pads, FX), Mixer toggle via click command, 9 = tile play state / progress follow the page, 10 = pad picker pages + toggle, B = pages by button only, picker footer toggle, pad names in the picker, C = encoder within the page, picker: left arrow, small footer, 5-char names, selected mark kept, D = DIAG title (encoder paths), picker footer stock, picker follows the marked pad, E = Pads encoder lists follow the page, no DIAG, F = Drive (tanh) + Filter 2 (24 dB) on the main page, Res clean, G = Shift for clips (-100..100 ms, loop rotation)


def slot(text, size=16):
    assert len(text) < size
    return text + b"\0" * (size - len(text))


VERSION = b"2.3.4-pk" + BUILD
assert len(VERSION) <= 10, "the panel shows 10 characters of the version"

PATCHES = [
    (0x080C5760, slot(b"by 1010music"), slot(b"portkit mod")),
    (0x080C5770, slot(b"2.3.4"), slot(VERSION)),
    (STOCK_END, b"", open(os.path.join(ROOT, "out", "cave.bin"), "rb").read()),
]
