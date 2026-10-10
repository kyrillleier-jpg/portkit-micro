"""Unicorn tests for patches/master.py (src/master.c, src/master_thunk.S): the settings store with the new entries (real
init 0x08089e04), the Tools pages (left / right arrow, Tools button, page list), the compressor's settings on its object,
and the master distortion on a real bus buffer.

  python3 -I tests/test_master.py   (after ./build.sh and patch.py fidelity pages padpages sound reverb fx3 master cave)
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "test_fidelity.py")).read()
exec(compile(_src[:_src.index("\ne = Emu()\n")], "test_fidelity.py (header)", "exec"))   # Emu, check, IMG, SYM, ...

from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3  # noqa: E402

e = Emu()
e.stub(0x08042DFC, lambda uc: uc.reg_write(UC_ARM_REG_R0, e.new(uc.reg_read(UC_ARM_REG_R0))))   # DTCM allocator
APP = 0x24013CB0
SET = APP + 0x7FD0
MS = 0x2406D400
COMP = {"thresh": 0x1A1, "ratio": 0x1A2, "attack": 0x1A3, "release": 0x1A5, "gain": 0x1A6}
DIST = {"type": 0x1A7, "drive": 0x1A8, "tone": 0x1A9, "mix": 0x1AB, "level": 0x1AC}

def w8(a, v):
    e.mu.mem_write(a, bytes([v]))

def r8(a):
    return e.mu.mem_read(a, 1)[0]

def store_ids(store):
    cnt = struct.unpack("<H", e.mu.mem_read(store + 0xA, 2))[0]
    ent = e.r32(store + 4)
    out = {}
    for k in range(cnt):
        pid, = struct.unpack("<H", e.mu.mem_read(ent + 8 * k, 2))
        out[pid] = struct.unpack("<i", e.mu.mem_read(ent + 8 * k + 4, 4))[0]
    return cnt, out

def get(pid):
    return struct.unpack("<i", struct.pack("<I", e.call(0x080894D0, SET, pid)))[0]

def put(pid, v):
    e.call(0x080894FA, SET, pid, v & 0xFFFFFFFF)

# --- settings store: the real init (0x08089e04) with the hook at its last add
e.stub(0x080442F6, lambda uc: None)                       # its last call (not about the store)
e.call(0x08089E04, SET)
cnt, ids = store_ids(SET)
check("settings store: 36 stock entries + 10 new (46 of 64), 0x17b (the hooked add) still there",
      cnt == 46 and 0x17B in ids and 0x96 in ids, cnt)
check("new entries with defaults: compressor = stock (-4 dB, 4:1, 10 ms, 250 ms, -4 dB), distortion Off / 12 dB / "
      "Tone open / Mix 100 % / Level 0 dB",
      [ids.get(COMP[k]) for k in ("thresh", "ratio", "attack", "release", "gain")] == [-4000, 4, 10, 250, -4000]
      and [ids.get(DIST[k]) for k in ("type", "drive", "tone", "mix", "level")] == [0, 12000, 1000, 1000, 0],
      {hex(k): v for k, v in ids.items() if k >= 0x1A0})

# --- pages: Tools screen 0x25, arrows, Tools button, the page list
screens = []
def _screen(uc):
    a = uc.reg_read(UC_ARM_REG_R0)
    screens.append(uc.reg_read(UC_ARM_REG_R1))
    uc.mem_write(a + 0x7FE5, bytes(uc.mem_read(a + 0x7FE4, 1)))          # like the stock tail: previous = current
    uc.mem_write(a + 0x7FE4, bytes([uc.reg_read(UC_ARM_REG_R1)]))
e.stub(0x0808EEDC, _screen)
w8(APP + 0x7FE4, 0x25)
w8(APP + 0x7FE5, 0x02)
r = e.call(SYM["master_left"], APP)
check("left arrow on Tools: Compressor page (screen 0x25 again), back target kept (previous screen 2)",
      r == 1 and r8(MS + 4) == 1 and screens == [0x25] and r8(APP + 0x7FE5) == 2, (r, r8(MS + 4), screens))

msg = e.new(0x18)
e.mu.mem_write(msg + 4, struct.pack("<H", 0x40))
lst = e.new(4 + 12 * 0x30)
e.w32(lst, 3)                                              # the stock page's entries, replaced
r = e.call(SYM["master_page"], APP, msg, lst)
n = e.r32(lst)
entries = [(e.r16(lst + 4 + 12 * k), struct.unpack("<i", e.mu.mem_read(lst + 0xC + 12 * k, 4))[0]) for k in range(n)]
check("Compressor page: Compressor (0x96), Threshold, Ratio, Attack, Release, Gain with their values",
      r == 1 and entries == [(0x96, ids[0x96]), (0x1A1, -4000), (0x1A2, 4), (0x1A3, 10), (0x1A5, 250), (0x1A6, -4000)],
      entries)

screens.clear()
e.call(SYM["master_right"], APP)
check("right arrow on the Compressor page: settings page", r8(MS + 4) == 0 and screens == [0x25])
e.w32(lst, 3)
check("settings page: stock list kept (master_page 0)", e.call(SYM["master_page"], APP, msg, lst) == 0 and e.r32(lst) == 3)
e.call(SYM["master_right"], APP)
e.w32(lst, 0)
e.call(SYM["master_page"], APP, msg, lst)
check("right arrow on settings: Distortion page (Dist Type, Drive, Tone, Mix, Level)",
      r8(MS + 4) == 2 and [e.r16(lst + 4 + 12 * k) for k in range(e.r32(lst))] == [0x1A7, 0x1A8, 0x1A9, 0x1AB, 0x1AC])
e.call(SYM["master_left"], APP)
check("left arrow on the Distortion page: settings page", r8(MS + 4) == 0)
e.call(SYM["master_right"], APP)
e.call(SYM["tools_btn"])
check("Tools button: settings page first (mode reset); thunk keeps the stock movw r3, #0x7fe4",
      r8(MS + 4) == 0 and e.mu.reg_read(UC_ARM_REG_R3) == 0x7FE4)
w8(APP + 0x7FE4, 0x30)
screens.clear()
check("arrows on other screens: not taken", e.call(SYM["master_left"], APP) == 0 and not screens)
e.mu.mem_write(msg + 4, struct.pack("<H", 0x310))
w8(MS + 4, 1)
check("other pages (e.g. FX cell 0x310) untouched while the Compressor page is set",
      e.call(SYM["master_page"], APP, msg, lst) == 0)
w8(MS + 4, 0)
check("right arrow table: entry for screen 0x25 -> tools_right (Thumb)",
      struct.unpack_from("<I", IMG, 0x08083800 + 4 * (0x25 - 2) - 0x08040000)[0] == SYM["tools_right"] | 1)

# --- compressor: settings stamped onto the object before the stock DSP
comp = e.new(0x700)
seen = []
def _comp(uc):
    c = uc.reg_read(UC_ARM_REG_R0)
    seen.append((uc.reg_read(UC_ARM_REG_R1),
                 struct.unpack("<fffI", uc.mem_read(c + 0x428, 12) + uc.mem_read(c + 0x448, 4)),
                 struct.unpack("<I", uc.mem_read(c + 0x44C, 4))[0]))
e.stub(0x080B9B04, _comp)
put(COMP["thresh"], -18000)
put(COMP["ratio"], 6)
put(COMP["attack"], 30)
put(COMP["release"], 600)
put(COMP["gain"], 6500)
e.call(SYM["master_comp"], comp, 0x1234)
(eng, (th, ra, mk, at), rel), = seen
check("compressor: -18 dB, 6:1, makeup +6.5 dB, attack 30 ms = 1440, release 600 ms = 28800 samples; engine passed on",
      eng == 0x1234 and abs(th + 18) < 1e-4 and ra == 6.0 and abs(mk - 6.5) < 1e-4 and at == 1440 and rel == 28800,
      seen)

# --- distortion on bus 0
N = 128
bus = e.new(20)
e.call(0x080A310C, bus, N)
def run(block_fn, blocks, **params):
    for k, v in params.items():
        put(DIST[k], v)
    outl, outr = [], []
    for b in range(blocks):
        e.call(0x080A31D4, bus)
        e.call(0x080A31C8, bus, N)
        il, ir = e.new(4), e.new(4)
        e.call(0x080A32D4, bus, il, ir)
        xl, xr = block_fn(b)
        e.wf(e.r32(il), xl)
        e.wf(e.r32(ir), xr)
        e.call(SYM["master_dist"], bus)
        pl, pr = e.r32(bus + 8), e.r32(bus + 0xC)
        outl += e.rf(pl, N)
        outr += e.rf(pr, N)
    return outl, outr

def sine(f, a):
    def fn(b):
        x = [a * math.sin(2 * math.pi * f * (b * N + k) / 48000) for k in range(N)]
        return x, x
    return fn

def harm(sig, f, h):
    """amplitude of harmonic h of f (single-bin DFT over whole periods)"""
    L = len(sig) - len(sig) % int(48000 / f)
    re_ = sum(sig[k] * math.cos(2 * math.pi * f * h * k / 48000) for k in range(L))
    im = sum(sig[k] * math.sin(2 * math.pi * f * h * k / 48000) for k in range(L))
    return 2 * math.hypot(re_, im) / L

src = sine(1000, 0.5)
L0, _ = run(src, 8, type=0, drive=12000, tone=1000, mix=1000, level=0)
check("Off: bus 0 unchanged", all(abs(a - b) < 1e-6 for a, b in zip(L0, sum((src(b)[0] for b in range(8)), []))))

e.w32(0x2406D410, 0)                                       # fresh state
L, R = run(src, 12, type=1, drive=0, tone=1000, mix=0, level=0)
ref = sum((src(b)[0] for b in range(12)), [])
check("Mix 0: the dry signal, delayed by the filters' 15 samples (aligned with the wet path)",
      all(abs(L[k] - ref[k - 15]) < 1e-5 for k in range(15, len(L))), max(abs(L[k] - ref[k - 15]) for k in range(15, len(L))))

for name, t in (("Soft", 1), ("Hard", 2), ("Fold", 3), ("Tube", 4)):
    e.w32(0x2406D410, 0)
    L, R = run(sine(1000, 0.25), 20, type=t, drive=0, tone=1000, mix=1000, level=0)
    s = L[N * 4:]
    h1 = harm(s, 1000, 1)
    lin = abs(h1 - 0.25) < 0.02 if t != 4 else 0.15 < h1 < 0.3
    e.w32(0x2406D410, 0)
    L, R = run(sine(1000, 0.5), 40, type=t, drive=18000, tone=1000, mix=1000, level=0)
    s = L[N * 24:]                                          # after the DC blocker (Tube) has settled
    h1, h2, h3 = harm(s, 1000, 1), harm(s, 1000, 2), harm(s, 1000, 3)
    dc = sum(s) / len(s)
    print(f"     {name}: 18 dB drive -> h1 {h1:.3f}, h2 {h2:.4f}, h3 {h3:.4f}, peak {max(map(abs, s)):.3f}, dc {dc:.4f}")
    ok = all(math.isfinite(v) for v in L + R) and max(map(abs, s)) < 1.3 and h3 > 0.02 and L == R and abs(dc) < 0.01
    if t == 4:
        ok = ok and h2 > 0.02                              # asymmetric: even harmonics
    check(f"{name}: 0 dB drive, -12 dB sine passes ~linearly; 18 dB drive: bounded, odd harmonics, no DC", lin and ok)

# aliasing: 7 kHz at 24 dB drive (hard clip); harmonics above 24 kHz fold back, 2x oversampling must keep them down
e.w32(0x2406D410, 0)
L, _ = run(sine(7000, 0.5), 30, type=2, drive=24000, tone=1000, mix=1000, level=0)
s = L[N * 6:]
f_alias = [abs(48000 - 7000 * 5)]                          # 5th harmonic 35 kHz -> 13 kHz
a_alias = harm(s[:len(s) - len(s) % 48], 13000 / 1000 * 1000, 1)
a_fund = harm(s[:len(s) - len(s) % 48], 7000, 1)
print(f"     Hard 7 kHz +24 dB: fundamental {a_fund:.3f}, alias at 13 kHz {a_alias:.4f} ({20 * math.log10(a_alias / a_fund + 1e-9):.1f} dB)")
check("2x oversampling: the 5th harmonic's alias (13 kHz) at least 20 dB below the fundamental",
      a_alias < a_fund * 0.1)

# Tone and Level
e.w32(0x2406D410, 0)
Lo, _ = run(sine(8000, 0.1), 16, type=1, drive=0, tone=1000, mix=1000, level=0)
e.w32(0x2406D410, 0)
Lt, _ = run(sine(8000, 0.1), 16, type=1, drive=0, tone=300, mix=1000, level=0)
e.w32(0x2406D410, 0)
Ll, _ = run(sine(1000, 0.1), 16, type=1, drive=0, tone=1000, mix=1000, level=-6000)
a_o, a_t = harm(Lo[N * 4:], 8000, 1), harm(Lt[N * 4:], 8000, 1)
a_l = harm(Ll[N * 4:], 1000, 1)
print(f"     Tone 300 at 8 kHz: {20 * math.log10(a_t / a_o):.1f} dB; Level -6 dB: {20 * math.log10(a_l / 0.1):.2f} dB")
check("Tone 300: 8 kHz damped by > 6 dB; Level -6 dB: -6 dB (+-0.3)",
      a_t < a_o * 0.5 and abs(20 * math.log10(a_l / 0.1) + 6) < 0.3)

put(DIST["type"], 0)
print(f"\n{'FAILED: ' + str(failures) if failures else 'all passed'}")
sys.exit(1 if failures else 0)
