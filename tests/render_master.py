"""Audio examples of the master section, rendered with the firmware's own code in Unicorn (pkX image): the settings store
(real init 0x08089e04 with our entries), the master distortion (master_dist) and the stock compressor (constructor
0x080b9d34, settings stamped by master_comp, DSP 0x080b9b04) on a real engine bus 0, block by block (128 frames), in
the block driver's order: distortion, then compressor.

  python3 -I tests/render_master.py <in.wav> <out.wav> [id=value ...]
      ids: thresh ratio attack release gain (compressor), dtype drive tone mix level (distortion); values as stored
      (milli-dB, ms, list index, 0..1000). Default: compressor neutral (0 dB, 1:1, 0 dB), distortion off.
  python3 -I tests/render_master.py --examples <dir>       renders the example set from sim/testsignals.py
"""
import math
import os
import struct
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "test_fidelity.py")).read()
exec(compile(_src[:_src.index("\ne = Emu()\n")], "test_fidelity.py (header)", "exec"))   # Emu, IMG, SYM, ...

from unicorn.arm_const import UC_ARM_REG_R0  # noqa: E402

APP = 0x24013CB0
SET = APP + 0x7FD0
IDS = {"thresh": 0x1A1, "ratio": 0x1A2, "attack": 0x1A3, "release": 0x1A5, "gain": 0x1A6,
       "dtype": 0x1A7, "drive": 0x1A8, "tone": 0x1A9, "mix": 0x1AB, "level": 0x1AC}
NEUTRAL = {"thresh": 0, "ratio": 1, "attack": 10, "release": 250, "gain": 0, "dtype": 0}
N = 128


class Master:
    def __init__(self):
        e = self.e = Emu()
        e.stub(0x08042DFC, lambda uc: uc.reg_write(UC_ARM_REG_R0, e.new(uc.reg_read(UC_ARM_REG_R0))))
        e.stub(0x080442F6, lambda uc: None)
        e.call(0x08089E04, SET)                                   # settings store with the new entries
        self.engine = e.new(0x16000)
        for i in (0, 0xC, 0xD, 0xE):
            e.call(0x080A310C, self.engine + 0x150E4 + 20 * i, N)
        self.bus0 = self.engine + 0x150E4
        self.comp = e.new(0x800)
        e.call(0x080B9D34, self.comp)                             # stock compressor object (as at engine init)
        e.w32(0x2406D410, 0)                                      # distortion state: fresh

    def set(self, **kw):
        for k, v in kw.items():
            self.e.call(0x080894FA, SET, IDS[k], v & 0xFFFFFFFF)

    def block(self, left, right):
        e = self.e
        e.call(0x080A31D4, self.bus0)                             # clear, n frames, write planes
        e.call(0x080A31C8, self.bus0, N)
        pl, pr = e.new(4), e.new(4)
        e.call(0x080A32D4, self.bus0, pl, pr)
        e.wf(e.r32(pl), left)
        e.wf(e.r32(pr), right)
        e.call(SYM["master_dist"], self.bus0)
        e.call(SYM["master_comp"], self.comp, self.engine)
        return e.rf(e.r32(self.bus0 + 8), N), e.rf(e.r32(self.bus0 + 0xC), N)

    def run(self, left, right):
        out_l, out_r = [], []
        for b in range(0, len(left) - N + 1, N):
            l, r = self.block(left[b:b + N], right[b:b + N])
            out_l += l
            out_r += r
        return out_l, out_r


def read_wav(path):
    with wave.open(path, "rb") as w:
        ch, n = w.getnchannels(), w.getnframes()
        data = w.readframes(n)
    fr = [struct.unpack_from(f"<{ch}h", data, 2 * ch * k) for k in range(n)]
    return [f[0] / 32768 for f in fr], [f[-1] / 32768 for f in fr]


def write_wav(path, left, right):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(b"".join(struct.pack("<hh", *(max(-32768, min(32767, int(round(x * 32767)))) for x in (a, b)))
                               for a, b in zip(left, right)))


def stats(left):
    peak = max(abs(x) for x in left)
    rms = math.sqrt(sum(x * x for x in left) / len(left))
    return f"peak {20 * math.log10(peak + 1e-12):6.1f} dBFS, rms {20 * math.log10(rms + 1e-12):6.1f} dBFS"


def render(src, dst, settings):
    m = Master()
    s = dict(NEUTRAL)
    s.update(settings)
    m.set(**s)
    l, r = read_wav(src)
    ol, orr = m.run(l, r)
    write_wav(dst, ol, orr)
    print(f"{os.path.basename(dst):28s} {stats(ol)}   ({' '.join(f'{k}={v}' for k, v in settings.items())})")


EXAMPLES = [
    ("drums.wav", "drums_1_neutral.wav", {}),
    ("drums.wav", "drums_2_comp_stock.wav", dict(thresh=-4000, ratio=4, attack=10, release=250, gain=-4000)),
    ("drums.wav", "drums_3_comp_glue.wav", dict(thresh=-14000, ratio=2, attack=30, release=300, gain=0)),
    ("drums.wav", "drums_4_comp_heavy.wav", dict(thresh=-26000, ratio=8, attack=3, release=120, gain=4500)),
    ("chord.wav", "chord_1_clean.wav", {}),
    ("chord.wav", "chord_2_soft.wav", dict(dtype=1, drive=18000, tone=1000, mix=1000, level=-8000)),
    ("chord.wav", "chord_3_hard.wav", dict(dtype=2, drive=18000, tone=1000, mix=1000, level=-8000)),
    ("chord.wav", "chord_4_fold.wav", dict(dtype=3, drive=18000, tone=1000, mix=1000, level=-6000)),
    ("chord.wav", "chord_5_tube.wav", dict(dtype=4, drive=18000, tone=1000, mix=1000, level=-8000)),
    ("chord.wav", "chord_6_soft_dark_mix50.wav", dict(dtype=1, drive=24000, tone=450, mix=500, level=-4000)),
    ("drums.wav", "drums_5_tube_plus_comp.wav", dict(dtype=4, drive=12000, tone=800, mix=1000, level=-6000,
                                                      thresh=-18000, ratio=4, attack=10, release=200, gain=4500)),
]

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--examples":
        d = a[1]
        os.makedirs(d, exist_ok=True)
        sig = os.path.join(os.path.dirname(HERE), "out", "sim", "signals")
        for src, dst, s in EXAMPLES:
            render(os.path.join(sig, src), os.path.join(d, dst), s)
    else:
        render(a[0], a[1], {k: int(v, 0) for k, v in (x.split("=") for x in a[2:])})
