"""Patch RAM map: every fixed address the cave code uses must lie in a registered region, regions must not overlap, and
all must stay in the gap the firmware leaves free above its initial stack pointer.

Measured in the Renode simulation (stock image, upper AXI SRAM filled with 0xa5 before boot; boot, preset load,
recording, playback): the firmware's own use above the stack starts at 0x2406f4e0 (0x2406f660-0x2407b8bf: SD /
recording transfer buffers, 0x2407bdc0..: audio / ADC DMA). pkZ / pkZA had state at 0x2406f000-0x2406fb1f, inside the
SD buffers (clicks when turning settings knobs - every step saves settings.tml -, broken recordings, no monitor sends).

  python3 -I tests/test_ram.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FREE_LO, FREE_HI = 0x240692A8, 0x2406F4E0          # initial SP .. first firmware use (Renode canary)

REGIONS = [                                         # start, size, owner
    (0x2406A000, 0x800, "fastget.c parameter cache (256 x 8)"),
    (0x2406A800, 0x300, "master.c distortion state"),
    (0x2406AB00, 0x20, "recmon.c monitor buffer struct"),
    (0x2406C000, 0x100, "bitbox-micro-fw-patch store (reserved)"),
    (0x2406C100, 0x10, "PARK"),
    (0x2406C110, 0xB0, "padpages.c state"),
    (0x2406C1C0, 0x40, "load.c meter"),
    (0x2406C400, 0xA00, "stretch.c grain states"),
    (0x2406CFF0, 0x10, "reverb.c object pointer"),
    (0x2406D000, 0x100, "reverb.c RS1 (FX2)"),
    (0x2406D100, 0x100, "reverb.c RS2 (FX3)"),
    (0x2406D200, 0x100, "fx3.c state"),
    (0x2406D400, 0x10, "master.c page state"),
    (0x2406D580, 0x10, "master.c SSL state"),
    (0x2406E000, 0x1000, "master.c Mix dry copy / recmon.c monitor signal (2 x 512 floats)"),
]

failures = 0


def check(what, ok, detail=""):
    global failures
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"   {detail}"))
    failures += 0 if ok else 1


regs = sorted(REGIONS)
check("regions inside the free gap 0x240692a8..0x2406f4df",
      all(FREE_LO <= a and a + n <= FREE_HI for a, n, _ in regs),
      [(hex(a), hex(a + n), o) for a, n, o in regs if not (FREE_LO <= a and a + n <= FREE_HI)])
check("regions do not overlap",
      all(a1 + n1 <= a2 for (a1, n1, _), (a2, _, _) in zip(regs, regs[1:])),
      [(o1, o2) for (a1, n1, o1), (a2, _, o2) in zip(regs, regs[1:]) if a1 + n1 > a2])

consts = {}
for f in sorted(os.listdir(os.path.join(ROOT, "src"))):
    if f.endswith((".c", ".S")):
        for ln, line in enumerate(open(os.path.join(ROOT, "src", f)), 1):
            code = re.sub(r"\"[^\"]*\"", "", line.split("//")[0])   # no string literals
            if code.lstrip().startswith(("*", "/*")):
                continue                                        # comments
            for m in re.finditer(r"0x(2406[0-9a-fA-F]{4})u?\b", code):
                consts.setdefault(int(m.group(1), 16), []).append(f"{f}:{ln}")
outside = {hex(a): w for a, w in consts.items() if not any(s <= a < s + n for s, n, _ in regs)}
check(f"every patch RAM constant in src/ ({len(consts)}) lies in a registered region", not outside, outside)

print(f"\n{'FAILED: ' + str(failures) if failures else 'all passed'}")
sys.exit(1 if failures else 0)
