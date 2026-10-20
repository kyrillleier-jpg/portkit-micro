# portkit for the 1010music bitbox micro

Community firmware for the **1010music bitbox micro** (firmware 2.3.4): Fidelity / vintage sampler modes and 24 dB
filters (ported from Justin Joe's [blackbox-mod](https://github.com/j3threejay/blackbox-mod)), plus clip
time-stretch tools, more reverb types, a third FX send, a master compressor and distortion, and a second page of pads.

**→ [Patch your firmware in the browser](https://kyrillleier-jpg.github.io/portkit-micro/)**

> Unofficial. Not affiliated with or supported by 1010music. Running modified firmware is at your own risk and may
> affect your warranty. Keep your stock `MICRO.BIN` and flash it back before sending a unit in for service.

## Install

1. Download the stock firmware **2.3.4** from 1010music and take the `MICRO.BIN` out of the zip.
2. Open the [patcher page](https://kyrillleier-jpg.github.io/portkit-micro/), drop that `MICRO.BIN` on it and
   download the patched `MICRO.BIN`. Everything happens in your browser; nothing is uploaded. The page only accepts
   the unmodified 2.3.4 and checks the result against the tested build.
3. Copy it to the root of the microSD card.
4. Hold the **white right arrow** key while powering on to install.
5. The splash shows **portkit mod** and version **2.3.4-pkZD**.

**Going back:** the same steps with the stock `MICRO.BIN`.

## What you get

**hardware** = tested on a unit, **emulation** = verified in the test suite and the simulator, not yet on a unit.

| Feature | Where on the unit | Status |
|---|---|---|
| **Fidelity**: Interp list Normal, HighQ, SP1200, SP-12, S950, MPC60, SP Raw, 16k..2k | Sample pads → Interp | hardware |
| Fidelity also on Clip, Slicer and Granular pads | pad page of those modes | emulation |
| **24 dB filter**: state-variable filter instead of the pad biquad, clean resonance | pad filter | emulation |
| **Drive** (before the filters) and **Filter 2** + Res 2 (a second 24 dB filter in series) | main page of every pad mode | emulation |
| **Clip Shift**: moves the audio against the loop by −100..+100 ms | clip loop page | hardware |
| **Clip Play Len**: Full or 1/4..32 bars (needs Sync) | clip loop page | emulation |
| **Clip Stretch**: tempo ±100 % (needs Sync); **Stretch Mode** Auto / Jump / Smooth (Smooth keeps the pitch) | clip loop page | hardware |
| **Clip Loop Fade**: 0..50 ms fade at the loop seams (against clicks) | clip loop page | emulation |
| **Sync 1/32**; Play Len / Stretch are hidden when Quant Size / Sync would make them ineffective | clip loop page | emulation |
| **Reverb types** Plate / Room / Hall / Chamber with 10 settings and Level | Effects → RVB | hardware (levels: emulation) |
| **FX3**: a third send with a second reverb, on its own FX row | Effects: left arrow = pages, tap RVB again = RVB/FX3; right arrow = FX3 settings, again = master EQ | hardware (row layout: emulation) |
| **Master compressor page** (threshold, ratio, attack, release, gain) with type **Stock / SSL** and **Mix** | Tools → left arrow | emulation |
| **Master distortion**: Soft / Hard / Fold / Tube with 2x oversampling; Drive, Tone, Mix, Level | Tools → right arrow | emulation |
| **Recording**: a pad's FX1 / FX2 / FX3 sends are kept when it is recorded into; the input monitor goes through them | recording to a pad | emulation |
| **Pads 9–16** as a second page of the pad grid | left arrow on Pads, top-left field on Mixer, tap DLY/RVB again on Effects, left arrow in the pad picker | hardware (encoder on page 2: emulation) |
| **CPU load** in the status bar | right end of the status bar | emulation |

Not ported: the Blackbox mod's machine drive (the micro has no saturation parameter to drive it from).

**Presets:** values are stored by parameter name. Presets from the stock firmware load as before; the new controls
start at their defaults.

## Build from source

Only needed if you want to change something. You need macOS or Linux, Python 3, `arm-none-eabi-gcc` (macOS:
`brew install --cask gcc-arm-embedded`, Debian/Ubuntu: `sudo apt install gcc-arm-none-eabi`) and the stock 2.3.4
`MICRO.BIN` in `firmware/` (SHA-256 `54ecc3e5c09b9aed7ad8e2d9d1c9f8ee63e06a8351c857304c3ff21fcb9c4365`).
Optional, for the simulation: [Renode](https://renode.io).

```sh
./setup.sh            # reference repos, Python venv (capstone, unicorn), firmware hash check
./build.sh            # src/ -> out/cave.elf, out/cave.bin
.venv/bin/python -I patch.py fidelity pages padpages sound reverb fx3 master cave
                      # -> out/fidelity+pages+padpages+sound+reverb+fx3+master+cave/MICRO.BIN
.venv/bin/python -I tests/test_fidelity.py     # Unicorn tests on the patched image
.venv/bin/python -I tests/test_padpages.py
.venv/bin/python -I tests/test_reverb.py
.venv/bin/python -I tests/test_fx3.py
.venv/bin/python -I tests/test_master.py
.venv/bin/python -I tests/test_ram.py
```

`patch.py` only writes an image when every check passes: stock hash, expected stock bytes at every patch site, zero
repack (applying nothing reproduces stock bit for bit), every change inside a registered range, every redirected call
lands on a function of ours, and every caller of a replaced function is covered.

### Updating the browser patcher

```sh
.venv/bin/python -I tools/make_web.py            # needs a clean commit
```

Builds, tests, and writes `docs/index.html` + `docs/patches/*.json`. The patch holds only this project's bytes, no
1010music firmware: the script fails if any 32-byte run of the stock image turns up in it. The JSON uses
blackbox-mod's patch format, so its `apply.py` can apply it as well. Commit `docs/` and push; GitHub Pages serves
the page.

## Repository layout

| Path | What |
|---|---|
| `patch.py`, `patches/` | patcher and patch definitions (sites, expected bytes, detours) |
| `src/` | C / assembly appended to the image (DSP, UI hooks) |
| `tests/` | Unicorn tests, CPU cost (`perf.py`), audio renders |
| `sim/` | Renode simulation of the unit (boot, screenshots, keys, SD card); `sim/README.md` |
| `tools/` | reverse-engineering helpers, browser patcher template and generator |
| `docs/` | the browser patcher (GitHub Pages) and `firmware-mod.md`, the general modding workflow behind this project |
| `re/symbols.md` | addresses, evidence and status of every function used (German) |

Sister project: [portkit-blackbox](https://github.com/kyrillleier-jpg/portkit-blackbox), these features on the
Blackbox, merged with JOEBOX 1.

## Credits and licence

The Fidelity modes, the 24 dB filter and the BL encoder come from blackbox-mod by Justin Joe (MIT); the filter
follows Emilie Gillet's stmlib (MIT). See `THIRD_PARTY.md`. portkit's code: MIT, see `LICENSE`. The 1010music
firmware is not part of this project and not covered by any licence here. Please share the patcher link or the build
instructions, not patched firmware files.
