# portkit

Funktionen aus dem [Blackbox-Mod](https://github.com/j3threejay/blackbox-mod) als Patch fuer die 1010music
bitbox micro, Firmware 2.3.4. Keine Firmware in diesem Repo: Der Patcher arbeitet auf deiner eigenen `MICRO.BIN`.

## Stand

| Funktion | Status |
|---|---|
| Fidelity (Interp-Liste: Normal, HighQ, SP1200, SP-12, S950, MPC60, SP Raw, 16k..2k) | am Geraet: laeuft, auf Sample-Pads einstellbar (pk1) |
| 24-dB-SVF mit Drive auf Res (ersetzt den Pad-Biquad) | durch Emulation bestaetigt, nicht am Geraet |
| Machine-Drive (Saturation als Wandler-Eingang) | nicht portiert (Micro hat keinen Saturation-Parameter) |
| Fidelity auch auf der Pad-Seite von Clip, Slicer, Granular (`patches/pages.py`) | durch Emulation bestaetigt, nicht am Geraet |
| Pads 9-16 als zweite Seite des Pad-Rasters (`patches/padpages.py`): Pads = Linkspfeil oder Encoder ueber Pad 8 / 16 hinaus, Mixer = Feld oben links, Effects = erneuter Druck auf die gewaehlte Zelle DLY/RVB, Pad-Waehler der Slot-Seite = eigener Umschalter neben den Kacheln; Anzeige in der Kopfzeile ("Pads 1-8", "FX 9-16") bzw. im Mixer-Feld | pk8 am Geraet: Blaettern und Anzeigen gehen; pk9 behebt Spielzustand/Fortschritt auf Seite 2, nicht am Geraet |

Splash: Zeile 2 `portkit mod`, Version `2.3.4-pkA`.

## Bauen

```sh
./setup.sh                                  # Repos, venv, Hash-Check; firmware/MICRO.BIN muss 2.3.4 sein
./build.sh                                  # src/ -> out/cave.elf, out/cave.bin
.venv/bin/python -I patch.py fidelity pages padpages cave  # -> out/fidelity+pages+padpages+cave/MICRO.BIN
.venv/bin/python -I tests/test_fidelity.py  # Unicorn-Tests auf dem gepatchten Image
.venv/bin/python -I tests/test_padpages.py
```

`patch.py` schreibt nur, wenn alles gruen ist: Stock-Hash, erwartete Stock-Bytes an jeder Stelle, Null-Repack,
alle Aenderungen in registrierten Bereichen, jeder umgeleitete Aufruf landet auf einer Cave-Funktion, und jeder
Aufrufer der ersetzten Funktionen ist erfasst.

Flashen (Recovery: weisse Pfeiltaste rechts beim Einschalten, `MICRO.BIN` im SD-Root) erst nach Sicherung des
Stock-Images. Adressen und Belege: `re/symbols.md`. Lizenzen: `THIRD_PARTY.md`.
