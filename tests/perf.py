"""CPU cost of the patch's DSP, measured as executed instructions per audio block (128 frames, 48 kHz) in Unicorn,
next to the stock code it extends or replaces. Instructions are counted per basic block (Capstone, cached).

Budget: 480 MHz x 128 / 48000 s = 1.28 M cycles per block. Cycles per instruction on the M7 are not known here
(dual issue, caches, SDRAM waits, VFP divides): the percentages are given for CPI 1.0 and 1.5 - an estimate, not a
measurement on the device (that is the load meter in the status bar, pkS).

  python3 -I tests/perf.py
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "test_fidelity.py")).read()
exec(compile(_src[:_src.index("\ne = Emu()\n")], "test_fidelity.py (header)", "exec"))   # Emu, IMG, SYM, ...

from capstone import CS_ARCH_ARM, CS_MODE_MCLASS, CS_MODE_THUMB, Cs  # noqa: E402
from unicorn import UC_HOOK_BLOCK  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5  # noqa: E402

BLOCK = 128
BUDGET = 480e6 * BLOCK / 48000
APP = 0x24013CB0
APP_PADS = APP + 0x1840
SET = APP + 0x7FD0

e = Emu()
e.stub(0x08042DFC, lambda uc: uc.reg_write(UC_ARM_REG_R0, e.new(uc.reg_read(UC_ARM_REG_R0))))
e.stub(0x080442F6, lambda uc: None)
_md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
_md.skipdata = True
_icache = {}
_count = [0, False]


def _blk(uc, addr, size, _):
    if _count[1]:
        n = _icache.get((addr, size))
        if n is None:
            n = _icache[(addr, size)] = sum(1 for _ in _md.disasm(bytes(uc.mem_read(addr, size)), addr))
        _count[0] += n


e.mu.hook_add(UC_HOOK_BLOCK, _blk)


def measure(fn, reps):
    """average instructions of fn() over reps calls (after one warm-up call)"""
    fn()
    _count[0], _count[1] = 0, True
    for _ in range(reps):
        fn()
    _count[1] = False
    return _count[0] / reps


rows = []


def row(group, what, instr, per_block=1.0, note=""):
    rows.append((group, what, instr * per_block, note))


# --- pad records (grid pads, type 0x45) and settings store, as at boot
typ = e.new(4)
e.mu.mem_write(typ, b"\x45")
for r in range(4):
    for c in range(4):
        e.call(0x08089FC4, APP_PADS + r * 0xF0 + c * 0x30, typ)
e.call(0x08089E04, SET)


def set_pad(pid, v, r=1, c=2):
    e.call(0x080894FA, APP_PADS + r * 0xF0 + c * 0x30, pid, v & 0xFFFFFFFF)


def set_glob(pid, v):
    e.call(0x080894FA, SET, pid, v & 0xFFFFFFFF)


# --- per voice: the pad filter (stock 0x080b8420) and our hook (Fidelity, Drive, Filter 2 around it)
def engine_pad(r=1, c=2):
    p = e.new(0x700)
    e.w32(p + 0x18, r << 8 | c)
    return p


def param(at, value):
    src = e.new(8)
    e.wf(src + 4, [value])
    e.w32(at, src)
    e.wf(at + 4, [1.0])
    e.w32(at + 0x20, 0)
    e.w32(at + 0x24, 1)
    e.wf(at + 0x28, [-1.0, 1.0])


def filter_obj(knob, res=0.5):
    obj = e.new(0x100)
    e.call(0x080B81F0, obj)
    params = e.new(0x100)
    param(params + 8, knob)
    param(params + 0x44, res)
    e.w32(obj + 0x84, params)
    return obj


def buffer(n=BLOCK):
    b = e.new(0x20)
    L, R = e.new(4 * n), e.new(4 * n)
    sig = [0.5 * math.sin(2 * math.pi * 440 * i / 48000) for i in range(n)]
    e.wf(L, sig)
    e.wf(R, sig)
    e.w32(b, n)
    e.w32(b + 4, n)
    e.w32(b + 8, L)
    e.w32(b + 0xC, R)
    e.mu.mem_write(b + 0x10, bytes([0, 1]))
    return b


pad = engine_pad()
obj = filter_obj(-0.4)
buf = buffer()
row("Stimme (pro Pad)", "Stock-Filter 0x080B8420 (LP)", measure(lambda: e.call(0x080B8420, obj, buf), 20))
for label, interp, drive, f2 in (("Hook: Fidelity Normal, Drive 0, Filter 2 aus", 0, 0, 0),
                                 ("Hook: Fidelity 12k, Drive 50 %, Filter 2 LP", 4, 500, -400),
                                 ("Hook: Fidelity SP-1200, Drive 100 %, Filter 2 HP", 2, 1000, 300)):
    set_pad(0xD2, interp)
    set_pad(0x1C2, drive)
    set_pad(0x1C0, f2)
    row("Stimme (pro Pad)", label + " (inkl. Stock-Filter)",
        measure(lambda: e.call(SYM["filter_voice_a"], obj, buf, regs=[(UC_ARM_REG_R5, pad)]), 20))
set_pad(0xD2, 0)
set_pad(0x1C2, 0)
set_pad(0x1C0, 0)

# --- per clip voice: the stream read, stock (Jump) and WSOLA (Stretch +/-50 %)
FILE_N = 96000
wsrc = e.new(0x40)
wplane = e.new(4 * FILE_N)
e.wf(wplane, [0.8 * math.sin(2 * math.pi * 1000 * i / 48000) for i in range(FILE_N)])
e.w32(wsrc + 4, wplane)
e.w32(wsrc + 8, wplane)
e.w32(wsrc + 0x10, FILE_N)


def wbuf(cap):
    b = e.new(0x20)
    e.w32(b, cap)
    e.w32(b + 4, cap)
    e.w32(b + 8, e.new(4 * cap))
    e.w32(b + 0xC, e.new(4 * cap))
    return b


def clip_cost(stretch, mode):
    set_pad(0x1C6, stretch)
    set_pad(0x1C7, mode)
    p_ = engine_pad()
    e.w32(p_ + 0x24, wsrc)
    e.wf(p_ + 0x1FC, [24000.0])
    e.wf(p_ + 0x204, [24000.0])
    e.mu.mem_write(p_ + 0x1F5, b"\x01")
    frac = p_ + 0x30 + 0x70 + 0x1C
    e.wf(frac, [0.0])
    src_b, out_b = wbuf(600), wbuf(600)
    cons, res = e.new(4), e.new(4)
    pos = [4000]

    def one():
        e.call(SYM["clip_render"], p_, 0, pos[0], 0, s=(1.0,), stack=(BLOCK, cons, frac, src_b, out_b, res))
        pos[0] += struct.unpack("<i", e.mu.mem_read(cons, 4))[0]
    for _ in range(8):
        one()
    return measure(one, 30)


row("Clip-Stimme", "Stream lesen, Stretch Mode Jump (Stock-Pfad)", clip_cost(0, 1))
row("Clip-Stimme", "WSOLA Smooth, Stretch +50 %", clip_cost(50, 2))
row("Clip-Stimme", "WSOLA Smooth, Stretch -50 %", clip_cost(-50, 2))
set_pad(0x1C6, 0)
set_pad(0x1C7, 0)

# --- reverb core at 29.8 kHz: per 128 frames at 48 kHz = 79.5 frames
RV_N = 80
REC1 = APP + 0x2200 + 0x18
t44 = e.new(4)
e.mu.mem_write(t44, b"\x44")
e.call(0x08089FC4, REC1, t44)
rvobj = e.new(0x200)
e.w32(rvobj + 0x18, 0x30100)
inb, lb, rb = e.new(4 * RV_N), e.new(4 * RV_N), e.new(4 * RV_N)
e.wf(inb, [0.3 * math.sin(i * 0.37) for i in range(RV_N)])


def new_state():
    st = e.new(0xB0)
    e.call(0x080A9C94, st)
    e.wf(st, [0.6 * 0.93, 0.5])
    return st


st = new_state()
row("Reverb (FX2 / FX3)", "Stock-Plate-Kern 0x080A9EC4", measure(lambda: e.call(0x080A9EC4, st, inb, lb, rb, stack=(RV_N,)), 20))
for t, name in ((1, "Room"), (2, "Hall"), (3, "Chamber")):
    e.call(0x080894FA, REC1, 0x178, t)
    st = new_state()
    row("Reverb (FX2 / FX3)", f"Typ {name} (reverb_core_thunk)",
        measure(lambda: e.call(SYM["reverb_core_thunk"], st, inb, lb, rb, stack=(RV_N,),
                               regs=[(UC_ARM_REG_R4, rvobj)]), 20))
e.call(0x080894FA, REC1, 0x178, 0)

# --- FX3 (bus 0xc -> decimation, pre-delay, reverb, interpolation -> bus 0), Hall
engine = e.new(0x16000)


def bus(i):
    return engine + 0x150E4 + 20 * i


for i in (0, 0xC, 0xD, 0xE):
    e.call(0x080A310C, bus(i), BLOCK)
e.call(SYM["fx3_record_ensure"])
e.stub(0x08042E44, lambda uc: uc.reg_write(UC_ARM_REG_R0, 32 * 1024 * 1024))
e.call(SYM["fx3_init"])
REC3 = APP + 0x2200 + 3 * 0x18
e.call(0x080894FA, REC3, 0x178, 2)


def fill(b, amp=0.3):
    e.call(0x080A31D4, b)
    e.call(0x080A31C8, b, BLOCK)
    il, ir = e.new(4), e.new(4)
    e.call(0x080A32D4, b, il, ir)
    sig = [amp * math.sin(2 * math.pi * 300 * i / 48000) for i in range(BLOCK)]
    e.wf(e.r32(il), sig)
    e.wf(e.r32(ir), sig)


def fx3_block():
    fill(bus(0xC))
    fill(bus(0))
    e.call(SYM["fx3_master"], bus(0), bus(0xE))


fill_cost = measure(lambda: (fill(bus(0xC)), fill(bus(0))), 10)
row("FX3", "fx3_master komplett (Typ Hall, inkl. Bus 0 += FX2)", measure(fx3_block, 20) - fill_cost)

# --- master: distortion (2x oversampled), compressor Stock (the real DSP) / SSL
comp = e.new(0x800)
e.call(0x080B9D34, comp)


def master_block(dist, comp_on, ctype):
    fill(bus(0), 0.5)
    if dist:
        e.call(SYM["master_dist"], bus(0))
    if comp_on:
        set_glob(0x19D, ctype)
        e.call(SYM["master_comp"], comp, engine)


set_glob(0x1A1, -18000)
set_glob(0x1A2, 4)
base = measure(lambda: fill(bus(0), 0.5), 10)
for t, name in ((1, "Soft"), (4, "Tube"), (3, "Fold")):
    set_glob(0x1A7, t)
    row("Master", f"Distortion {name} (2x Oversampling)", measure(lambda: master_block(True, False, 0), 10) - base)
set_glob(0x1A7, 0)
row("Master", "Distortion Off (Abfrage)", measure(lambda: master_block(True, False, 0), 10) - base)
row("Master", "Kompressor Stock (echter DSP + Settings)", measure(lambda: master_block(False, True, 0), 10) - base)
row("Master", "Kompressor SSL", measure(lambda: master_block(False, True, 1), 10) - base)
set_glob(0x19E, 500)
row("Master", "Kompressor SSL + Mix 50 %", measure(lambda: master_block(False, True, 1), 10) - base)
set_glob(0x19E, 1000)

# --- report
print(f"Budget pro Block (128 Frames @ 48 kHz, 480 MHz): {BUDGET / 1e6:.2f} M Takte\n")
print(f"{'Bereich':20s} {'Stufe':58s} {'Befehle':>9s} {'% CPI 1.0':>10s} {'% CPI 1.5':>10s}")
group = None
for g, what, instr, note in rows:
    if g != group:
        print()
        group = g
    print(f"{g:20s} {what:58s} {instr:9.0f} {100 * instr / BUDGET:9.1f}% {150 * instr / BUDGET:9.1f}% {note}")
