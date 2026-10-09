"""Unicorn tests for patches/fidelity.py and patches/pages.py on the patched image (out/fidelity+pages+padpages+cave/MICRO.BIN).

Real firmware code runs for: the Interp registration call, the app pad store (init 0x08089fc4, get/set), the stock
cutoff / resonance curves, the parameter evaluator, the audio-buffer accessors, the two resampling kernels and the
voice-start filter reset. Only the allocator (0x08042dc0) is replaced, by a bump allocator.

  python3 -I tests/test_fidelity.py        (after ./build.sh and patch.py fidelity pages padpages cave)
"""
import math
import os
import struct
import sys

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB, Uc
from unicorn.arm_const import UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC, UC_CPU_ARM_MAX
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_S0, UC_ARM_REG_S1,
                               UC_ARM_REG_SP)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "patches"))
from thumb import BASE, symbols  # noqa: E402

IMG = open(os.path.join(ROOT, "out", "fidelity+pages+padpages+cave", "MICRO.BIN"), "rb").read()
SYM = symbols(os.path.join(ROOT, "out", "cave.elf"))

APP_PADS = 0x24013CB0 + 0x1840
PARK = 0x2406C100
RET = 0x24000000
STACK = 0x2407F000
P_INTERP = 0xD2
NAMES = ["Normal", "HighQ", "SP1200", "SP-12", "S950", "MPC60", "SP Raw", "16k", "12k", "10k", "8k", "6k", "4k", "2k"]
N = 64

failures = 0


def check(what, ok, detail=""):
    global failures
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"   {detail}"))
    failures += 0 if ok else 1


class Emu:
    def __init__(self):
        # Unicorn 2.1's M-profile CPUs have no double precision, which the stock Res curve uses (vcvt.f64.f32 at
        # 0x080a028e). As blackbox-mod/emu.py: an A-profile CPU in Thumb state with the FPU on runs the same Thumb-2
        # and FPv5 code.
        mu = self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        mu.ctl_set_cpu_model(UC_CPU_ARM_MAX)
        mu.mem_map(BASE, (len(IMG) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, IMG)
        mu.mem_map(0x24000000, 0x80000)          # AXI SRAM
        mu.reg_write(UC_ARM_REG_C1_C0_2, 0xF << 20)   # FPU on
        mu.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        self.heap = 0x24030000                   # scratch for test objects (inside the stock heap range)
        self.alloc_at = 0x24040000               # bump allocator for the firmware's own allocations
        self.stubs, self.hooked = {}, set()
        mu.hook_add(UC_HOOK_CODE, lambda uc, a, size, _: uc.emu_stop(), begin=RET, end=RET)
        self.stub(0x08042DC0, self._alloc)

    def _hook(self, uc, addr, size, _):
        if addr in self.stubs:
            self.stubs[addr](uc)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def stub(self, addr, fn):
        addr &= ~1
        self.stubs[addr] = fn
        if addr not in self.hooked:              # one hook per address; a hook on every instruction is ~50x slower
            self.hooked.add(addr)
            self.mu.hook_add(UC_HOOK_CODE, self._hook, begin=addr, end=addr)

    def _alloc(self, uc):
        n = uc.reg_read(UC_ARM_REG_R0) * max(1, uc.reg_read(UC_ARM_REG_R1))
        p = self.alloc_at
        self.alloc_at += (n + 7) & ~7
        uc.mem_write(p, bytes(n))
        uc.reg_write(UC_ARM_REG_R0, p)

    def new(self, size):
        p = self.heap
        self.heap += (size + 15) & ~15
        self.mu.mem_write(p, bytes(size))
        return p

    def w32(self, a, v):
        self.mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))

    def r32(self, a):
        return struct.unpack("<I", self.mu.mem_read(a, 4))[0]

    def wf(self, a, vals):
        self.mu.mem_write(a, struct.pack(f"<{len(vals)}f", *vals))

    def rf(self, a, n):
        return list(struct.unpack(f"<{n}f", self.mu.mem_read(a, 4 * n)))

    def call(self, fn, *args, s=(), regs=(), stack=()):
        mu = self.mu
        sp = STACK - 4 * len(stack)
        for k, v in enumerate(stack):
            self.w32(sp + 4 * k, v)
        for r, v in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            mu.reg_write(r, v & 0xFFFFFFFF)
        for r, v in zip((UC_ARM_REG_S0, UC_ARM_REG_S1), s):
            mu.reg_write(r, struct.unpack("<I", struct.pack("<f", v))[0])
        for r, v in regs:
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM_REG_SP, sp)
        mu.reg_write(UC_ARM_REG_LR, RET | 1)
        mu.emu_start(fn | 1, RET, count=20_000_000)
        return mu.reg_read(UC_ARM_REG_R0)

    def cstr(self, a):
        return bytes(self.mu.mem_read(a, 32)).split(b"\0")[0].decode()


e = Emu()

# --- the Interp registration call site in the patched image now reaches interp_register
seen = {}


def fake_register(uc):
    sp = uc.reg_read(UC_ARM_REG_SP)
    seen.update(param=uc.reg_read(UC_ARM_REG_R1), label=uc.reg_read(UC_ARM_REG_R2), names=uc.reg_read(UC_ARM_REG_R3),
                count=e.r32(sp), xml=e.r32(sp + 4))


e.stub(0x08069E7C, fake_register)
# run the stock instructions around the call site: r4 = table, 0x0806b33a .. 0x0806b34e
e.mu.reg_write(UC_ARM_REG_R0, 0)
e.mu.reg_write(UC_ARM_REG_SP, STACK - 0x40)
e.mu.reg_write(UC_ARM_REG_LR, RET | 1)
e.mu.hook_add(UC_HOOK_CODE, lambda uc, a, s, _: uc.emu_stop(), begin=0x0806B34E, end=0x0806B34E)
e.mu.emu_start(0x0806B33A | 1, 0x0806B34E, count=1000)
names = [e.cstr(e.r32(seen["names"] + 4 * k)) for k in range(seen.get("count", 0))]
check("Fidelity list: Normal, HighQ, 5 machines, 16k .. 2k", names == NAMES and seen["param"] == P_INTERP, names)
check("label 'Fidelity:', xml name stays 'interpqual'",
      e.cstr(seen["label"]) == "Fidelity:" and e.cstr(seen["xml"]) == "interpqual", (e.cstr(seen["label"]), e.cstr(seen["xml"])))
del e.stubs[0x08069E7C]

# --- app pad records (real store init, type 0x45 = grid pads at boot) and engine pads
typ = e.new(4)
e.mu.mem_write(typ, b"\x45")


def record(row, col):
    return APP_PADS + row * 0xF0 + col * 0x30


for row in range(4):
    for col in range(4):
        e.call(0x08089FC4, record(row, col), typ)


def set_interp(v, row=1, col=2):
    e.call(0x080894FA, record(row, col), P_INTERP, v)


def engine_pad(row=1, col=2):
    p = e.new(0x700)
    e.w32(p + 0x18, row << 8 | col)
    return p


# --- filter object (stock ctor 0x080b81f0) with a parameter block: Filter knob @+8, Res @+0x44 (evaluator 0x080a19f4)
def param(at, value):
    src = e.new(8)
    e.wf(src + 4, [value])
    e.w32(at + 0, src)          # slot 0: source
    e.wf(at + 4, [1.0])         # slot 0: amount
    e.w32(at + 0x20, 0)         # slot order
    e.w32(at + 0x24, 1)         # one slot
    e.wf(at + 0x28, [-1.0, 1.0])
    return src


def filter_obj(knob, res=0.5):
    obj = e.new(0x100)
    e.call(0x080B81F0, obj)
    params = e.new(0x100)
    param(params + 8, knob)
    param(params + 0x44, res)
    e.w32(obj + 0x84, params)
    return obj


def buffer(left, right=None):
    b = e.new(0x20)
    L = e.new(4 * len(left))
    e.wf(L, left)
    R = 0
    if right is not None:
        R = e.new(4 * len(right))
        e.wf(R, right)
    e.w32(b + 0, len(left))
    e.w32(b + 4, len(left))
    e.w32(b + 8, L)
    e.w32(b + 0xC, R)
    e.mu.mem_write(b + 0x10, bytes([0, 1]))
    return b, L, R


def sine(f, n=N, a=0.8, ph=0):
    return [a * math.sin(2 * math.pi * f * (i + ph) / 48000.0) for i in range(n)]


def run_a(obj, b, pad):
    e.call(SYM["filter_voice_a"], obj, b, regs=[(UC_ARM_REG_R5, pad)])


def run_b(obj, b, pad):
    e.call(SYM["filter_voice_b"], obj, b, regs=[(UC_ARM_REG_R6, pad)])


pad = engine_pad()
x = sine(997)

set_interp(0)
obj = filter_obj(0.0)
b, L, R = buffer(x, x)
run_a(obj, b, pad)
check("Normal, knob centre: buffer untouched", all(abs(p - q) < 1e-7 for p, q in zip(e.rf(L, N), x)))

set_interp(NAMES.index("12k"))
obj = filter_obj(0.0)
b, L, R = buffer(x, x)
run_a(obj, b, pad)
out = e.rf(L, N)
runs = [out[i] == out[i + 1] for i in range(N - 1)]
check("12k: zero-order hold (one new value per 4 samples)", len(set(out)) <= N // 4 + 1, len(set(out)))
check("12k: 12-bit values", all(abs(v * 2048 - round(v * 2048)) < 1e-4 for v in out))
check("12k: right channel crunched too", e.rf(R, N) == out)

other = engine_pad(row=0, col=0)
set_interp(0, row=0, col=0)
obj = filter_obj(0.0)
b, L, R = buffer(x, x)
run_a(obj, b, other)
check("another pad's Interp (Normal) is its own: no crunch", all(abs(p - q) < 1e-7 for p, q in zip(e.rf(L, N), x)))

obj = filter_obj(0.0)
b, L, R = buffer(x, x)
run_b(obj, b, pad)
check("class B thunk (pad in r6) finds the pad: crunch applies", len(set(e.rf(L, N))) <= N // 4 + 1)

obj = filter_obj(0.0)
b, L, R = buffer(x, x)
run_a(obj, b, 0)
check("no pad: no crunch", all(abs(p - q) < 1e-7 for p, q in zip(e.rf(L, N), x)))

# --- 24 dB SVF
set_interp(0)


def rms_after(f, knob, blocks=8):
    obj = filter_obj(knob)
    acc = []
    for k in range(blocks):
        y = sine(f, ph=k * N)
        b, L, R = buffer(y, y)
        run_a(obj, b, pad)
        acc = e.rf(L, N)
    return math.sqrt(sum(v * v for v in acc) / N)


lp_hi, lp_lo = rms_after(12000, -0.6), rms_after(200, -0.6)
check("Filter left (LP): 12 kHz far below 200 Hz", lp_hi < 0.05 * lp_lo, (lp_hi, lp_lo))
hp_hi, hp_lo = rms_after(12000, 0.6), rms_after(200, 0.6)
check("Filter right (HP): 200 Hz far below 12 kHz", hp_lo < 0.05 * hp_hi, (hp_lo, hp_hi))

# --- machine modes after the voice
for name in ("SP1200", "SP-12", "S950", "MPC60", "SP Raw"):
    set_interp(NAMES.index(name))
    obj = filter_obj(0.0)
    y = sine(997)
    b, L, R = buffer(y, y)
    run_a(obj, b, pad)
    out = e.rf(L, N)
    finite = all(math.isfinite(v) for v in out)
    changed = any(abs(p - q) > 1e-6 for p, q in zip(out, y))
    check(f"{name}: output finite and processed", finite and changed)
set_interp(NAMES.index("SP Raw"))
obj = filter_obj(0.0)
b, L, R = buffer(x, x)
run_a(obj, b, pad)
out = e.rf(L, N)
check("SP Raw: 12-bit hold, no output filter", all(abs(v * 2048 - round(v * 2048)) < 1e-4 for v in out))

# --- voice-start reset (stock 0x080b8794) between blocks: no stale state, no NaN
set_interp(0)
obj = filter_obj(-0.6, res=0.9)
for k in range(4):
    b, L, R = buffer(sine(300, ph=k * N), sine(300, ph=k * N))
    run_a(obj, b, pad)
e.call(0x080B8794, obj)
check("reset clears the 'on' flag (+0x40)", e.r32(obj + 0x40) == 0)
b, L, R = buffer([0.0] * N, [0.0] * N)
e.mu.mem_write(b + 0x10, bytes([0, 1]))
z = [1e-9] * N
b, L, R = buffer(z, z)
run_a(obj, b, pad)
check("after reset: silent input stays silent (integrators re-zeroed)", max(abs(v) for v in e.rf(L, N) + e.rf(R, N)) < 1e-6)

# --- kernels: without a machine, read_normal / read_hq give exactly the stock kernels' output
src = e.new(4 * 300)
e.wf(src, [math.sin(i * 0.37) for i in range(300)])


def kernel(fn, rate, n=64):
    newpos, frac, dst = e.new(4), e.new(4), e.new(4 * n)
    e.wf(frac, [0.25])
    e.call(fn, src, 300, 8, newpos, s=(rate,), stack=(frac, dst, n))
    return e.rf(dst, n), e.r32(newpos), e.rf(frac, 1)[0]


e.w32(PARK, 0)
for wrap, stock in (("read_normal", 0x080A1400), ("read_hq", 0x080A1494)):
    check(f"{wrap}, no machine: identical to stock kernel", kernel(SYM[wrap], 1.37) == kernel(stock, 1.37))

set_interp(NAMES.index("SP1200"))
e.w32(PARK, pad)
e.w32(PARK + 4, 1000)
e.wf(PARK + 8, [1.37])
out, newpos, frac = kernel(SYM["read_normal"], 1.37)
check("read_normal, SP1200: machine reader, finite output", all(math.isfinite(v) and abs(v) < 2 for v in out))
check("read_normal, SP1200: position advances by rate x n", abs((newpos - 8 + frac - 0.25) - 1.37 * 64) < 1e-3,
      (newpos, frac))
check("read_normal, SP1200: reads on the 26.04 kHz grid (repeats samples)", len(set(out)) < 64)

# --- voice_read wrapper parks pad / position / rate and forwards everything to the stock reader
got = {}


def fake_reader(uc):
    sp = uc.reg_read(UC_ARM_REG_SP)
    got.update(r=[uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)],
               stack=[e.r32(sp + 4 * k) for k in range(4)],
               s=[struct.unpack("<f", struct.pack("<I", uc.reg_read(r)))[0] for r in (UC_ARM_REG_S0, UC_ARM_REG_S1)])
    uc.reg_write(UC_ARM_REG_R0, 77)


e.stub(0x080ADC4C, fake_reader)
r = e.call(SYM["voice_read"], pad, 0x11, 1234, 0x22, s=(0.5, 1.0), stack=(0x33, 0x44, 0x55, 0x66))
check("voice_read forwards r0-r3, four stack words, frac, and its return value",
      got["r"] == [pad, 0x11, 1234, 0x22] and got["stack"] == [0x33, 0x44, 0x55, 0x66] and got["s"][0] == 0.5 and r == 77,
      got)
check("voice_read: machine pad at rate 1.0 goes in just above 1.0", 1.0 < got["s"][1] < 1.000001, got["s"])
check("voice_read parks pad, position and rate", e.r32(PARK) == pad and e.r32(PARK + 4) == 1234)
set_interp(0)
e.call(SYM["voice_read"], pad, 0x11, 1234, 0x22, s=(0.5, 1.0), stack=(0x33, 0x44, 0x55, 0x66))
check("voice_read: Normal pad keeps rate exactly 1.0", got["s"][1] == 1.0)

# --- pad settings page (page 5) of every pad-mode table lists Interp right after Excl Group
TABLES = {"Sample": (0x080C76C0, 0x080C78DC, 0x080C7AF8), "Clip": (0x080C6A1C, 0x080C6C38),
          "Slicer": (0x080C7E28, 0x080C8044), "Granular": (0x080C6EEC, 0x080C7108)}
for mode, tables in TABLES.items():
    ok = True
    for t in tables:
        page = struct.unpack_from("<45H", IMG, t + 5 * 0x5A - BASE)
        ids = list(page[:page.index(0)])
        ok &= P_INTERP in ids and ids.index(P_INTERP) == ids.index(0xA6) + 1 and len(set(ids)) == len(ids)
    check(f"{mode}: Fidelity on the pad settings page after Excl Group", ok)

print(f"\n{'FAILED: ' + str(failures) if failures else 'all passed'}")
sys.exit(1 if failures else 0)
