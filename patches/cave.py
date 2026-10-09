"""The compiled code cave (./build.sh), appended after the stock image, plus the splash marking a modified build:
line 2 "by 1010music" -> "portkit mod", line 3 "2.3.4" -> "2.3.4-pk<BUILD>". Slots are 16 bytes; a pointer table
follows at 0x080c5780, and the panel shows at most 10 characters of the version (bitbox-micro-fw-patch)."""
import os

from thumb import ROOT, STOCK_END

BUILD = b"3"    # 1 = Fidelity + 24 dB SVF (no machine drive), 2 = + Fidelity on Clip / Slicer / Granular pages, 3 = + pad pages (pads 9-16)


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
