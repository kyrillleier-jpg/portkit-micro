# portkit for the 1010music bitbox micro

Community patch for the **bitbox micro, firmware 2.3.4**: features from Justin Joe's
[blackbox-mod](https://github.com/j3threejay/blackbox-mod) and new ones, appended to the stock firmware as extra code.
**No firmware is included.** The patcher works on your own copy of the stock `MICRO.BIN` and checks its hash first.

> Unofficial, not affiliated with or supported by 1010music. Running modified firmware is at your own risk and may
> affect your warranty. Keep the stock `MICRO.BIN` and flash it back before sending a unit in for service.

The patched image identifies itself: splash line 2 `portkit mod`, version `2.3.4-pkZD`.

## Features

Status: **hardware** = tested on a unit, **emulation** = verified in Unicorn / Renode only.

| Feature | Status |
|---|---|
| Fidelity (Interp list: Normal, HighQ, SP1200, SP-12, S950, MPC60, SP Raw, 16k..2k) on sample pads | hardware (pk1) |
| Fidelity on the Clip, Slicer and Granular pad pages | emulation |
| 24 dB state-variable filter replacing the pad biquad, clean resonance | emulation |
| Drive (tanh, before the filters) and Filter 2 + Res 2 (second 24 dB SVF in series) on every pad mode's main page; old presets get defaults | emulation (pkF) |
| Clip **Shift** (−100..100 ms, rotates the loop against the grid; clip loop page) | hardware (pkI) |
| Clip **Play Len** (Full, 1/4..32 bars, needs Sync) | emulation (pkH) |
| Clip **Stretch** (±100 %, via segment start positions, needs Sync) | hardware (pkQ, Jump) |
| Smooth time stretch (WSOLA, pitch kept), Stretch Mode Auto / Jump / Smooth | hardware (pkR) |
| Clip **Loop Fade** (0–50 ms dip at loop start/end and the Shift seam) | emulation (pkZD) |
| Sync grid 1/32 for clips; Play Len / Stretch hidden when Quant Size / Sync make them ineffective | emulation (pkK) |
| Audio load in the status bar | emulation (pkS) |
| Reverb types Plate / Room / Hall / Chamber with 10 settings + Level, level-matched to the plate | hardware (pkT), levels emulation (pkV) |
| **FX3**: third send (bus 0xC) with a second reverb, on its own FX row; Effects: left arrow = pages, second tap on RVB = RVB/FX3; right arrow = FX3 settings, again = master EQ | hardware (pkU), row layout emulation (pkW) |
| Master section on Tools: left arrow = compressor page (threshold, ratio, attack, release, gain), right arrow = master distortion (Soft / Hard / Fold / Tube, drive, tone, mix, level; 2x oversampling) | emulation (pkX) |
| Compressor type **SSL** (ratio 2/4/10, attack 0.1–30 ms, release 0.1–1.2 s / Auto) and a Mix control for both types | emulation (pkY) |
| Recording: FX1/FX2/FX3 sends survive the pad being re-created; the input monitor goes through the selected pad's sends | emulation (pkZA) |
| Pads 9–16 as a second page of the pad grid (button paging on Pads, Mixer, Effects, pad picker) | hardware (pkB: pages and picker), encoder on page 2 emulation (pkE) |
| Machine drive (saturation as converter input) | not ported (the micro has no saturation parameter) |

## Patch in the browser

`docs/index.html` is a one-page patcher: open it (or the GitHub Pages site of this repo), drop your stock
`MICRO.BIN` 2.3.4, download the result. Everything runs in the browser, nothing is uploaded. The page holds only this
project's bytes (no 1010music firmware), checks the stock file's SHA-256 before and the result's SHA-256 after, so it
can only produce the tested build. The patch is also in `docs/patches/*.json` (blackbox-mod's format; its `apply.py`
applies it too).

Regenerate after a change: `python3 -I tools/make_web.py` (needs a clean commit; builds, runs the tests, checks that no
32-byte run of the stock image ends up in the patch, then writes `docs/`).

## Requirements

- macOS or Linux, Python 3, `arm-none-eabi-gcc` (macOS: `brew install --cask gcc-arm-embedded`,
  Debian/Ubuntu: `sudo apt install gcc-arm-none-eabi`)
- Stock bitbox micro firmware 2.3.4 as `firmware/MICRO.BIN`
  (SHA-256 `54ecc3e5c09b9aed7ad8e2d9d1c9f8ee63e06a8351c857304c3ff21fcb9c4365`)
- Optional, for the simulation: [Renode](https://renode.io)

## Build

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

`patch.py` only writes an image when every check passes: stock hash, expected stock bytes at every patch site,
zero repack (applying nothing reproduces stock bit for bit), every change inside a registered range, every
redirected call lands on a cave function, and every caller of a replaced function is covered.

## Flashing

1. Back up the stock `MICRO.BIN`.
2. Put the patched `MICRO.BIN` in the SD card root.
3. Hold the white right arrow key while powering on (recovery / update mode).

To go back, do the same with the stock file.

## Layout

| Path | What |
|---|---|
| `patch.py`, `patches/` | patcher and patch definitions (sites, expected bytes, detours) |
| `src/` | C / assembly appended to the image (DSP, UI hooks) |
| `tests/` | Unicorn tests, CPU cost (`perf.py`), audio renders |
| `sim/` | Renode simulation of the unit (boot, screenshots, keys, SD image); see `sim/README.md` |
| `tools/` | reverse-engineering helpers (disassembly, xrefs, callers, cross-image function matching) |
| `re/symbols.md` | addresses, evidence and status of every function used (German) |
| `docs/firmware-mod.md` | the general workflow behind this project |

A sister project ports these features to the Blackbox (merged with JOEBOX 1): **portkit-blackbox**.

## Licence

MIT for this project's code, see `LICENSE`. Third-party parts: `THIRD_PARTY.md`.
The 1010music firmware is not part of this project and not covered by any licence here.
