**portkit 2.3.4-pkZD: community firmware mod for the bitbox micro (Fidelity, 24 dB filters, clip stretch, FX3, master section, pads 9–16)**

Hi all,

I've been working on a mod for the **bitbox micro** that adds a bunch of features on top of the stock firmware 2.3.4, partly ported from Justin Joe's Blackbox mod (blackbox-mod / JOEBOX), partly new. It is now public:

- **Patch in your browser:** https://kyrillleier-jpg.github.io/portkit-micro/
- **Manual with screenshots:** https://github.com/kyrillleier-jpg/portkit-micro/blob/main/docs/manual/README.md (PDF in the same folder)
- **Changelog / source:** https://github.com/kyrillleier-jpg/portkit-micro

**What's new**

- **Fidelity** (replaces Interp): SP1200, SP-12, S950, MPC60, SP Raw machine modes plus 16k…2k sample-rate crunch, on all pad modes
- **24 dB filter** instead of the stock 12 dB one, plus **Drive** and a second filter (**Filter 2 / Res 2**) on every pad
- **Clips:** Shift (−100…+100 ms), Play Len (1/4…32 bars), Stretch ±100 % with a **Smooth** mode that keeps the pitch, Loop Fade against clicks, Sync 1/32
- **Reverb types** Plate / Room / Hall / Chamber with more settings
- **FX3:** a third send with its own second reverb (e.g. short room on drums, long hall on synths)
- **Master section:** compressor page with an **SSL-style bus compressor** and Mix (parallel compression), plus a **master distortion** (Soft / Hard / Fold / Tube)
- **Pads 9–16** as a second page of the pad grid
- FX sends survive recording; the input monitor goes through the pad's effects

**How to install**

1. Download the stock 2.3.4 firmware from 1010music and take `MICRO.BIN` out of the zip.
2. Open the patcher page, drop the stock `MICRO.BIN` on it, download the patched one. Everything runs in your browser, nothing is uploaded, and the page only produces the exact tested build.
3. Copy it to the SD card root and hold the white right arrow while powering on. The splash shows "portkit mod / 2.3.4-pkZD".

Going back is the same with the stock file.

**Status, honestly:** Fidelity on sample pads, Shift, Stretch / Smooth, the reverb types, FX3 and the pads 9–16 paging have been tested on my unit. The rest (including the master section, Loop Fade and the fixes in the latest builds) passes the automated tests and the simulator but hasn't been confirmed on hardware yet. Reports are very welcome, good or bad: GitHub issues or here, please mention the version.

**Please note:** this is unofficial and not supported by 1010music. Modified firmware is at your own risk and may affect your warranty, so keep your stock `MICRO.BIN`. The patcher contains no 1010music firmware, you bring your own. Please share the link, not patched files.

Big thanks to Justin Joe for blackbox-mod, which made the Fidelity and filter part possible.
