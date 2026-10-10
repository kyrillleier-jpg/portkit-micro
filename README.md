# portkit

Funktionen aus dem [Blackbox-Mod](https://github.com/j3threejay/blackbox-mod) als Patch fuer die 1010music
bitbox micro, Firmware 2.3.4. Keine Firmware in diesem Repo: Der Patcher arbeitet auf deiner eigenen `MICRO.BIN`.

## Stand

| Funktion | Status |
|---|---|
| Fidelity (Interp-Liste: Normal, HighQ, SP1200, SP-12, S950, MPC60, SP Raw, 16k..2k) | am Geraet: laeuft, auf Sample-Pads einstellbar (pk1) |
| 24-dB-SVF (ersetzt den Pad-Biquad), Res sauber | durch Emulation bestaetigt, nicht am Geraet |
| Drive (tanh, vor den Filtern) und Filter 2 + Res 2 (zweiter 24-dB-SVF in Serie), neue Regler auf der Hauptseite jedes Pad-Modus (`patches/sound.py`); alte Presets bekommen Defaults | pkF: durch Emulation bestaetigt, nicht am Geraet |
| Shift fuer Clips (−100..100 ms, dreht den Loop gegen das Raster; Loop-Seite der Clip-Pads, `src/clipshift.c`) | pkG: durch Emulation bestaetigt, nicht am Geraet |
| Abspiellaenge fuer Clips (Play Len: Full, 1/4..32 Takte; Loop-Seite, mit Sync) | pkH: durch Emulation bestaetigt, nicht am Geraet |
| Machine-Drive (Saturation als Wandler-Eingang) | nicht portiert (Micro hat keinen Saturation-Parameter) |
| Fidelity auch auf der Pad-Seite von Clip, Slicer, Granular (`patches/pages.py`) | durch Emulation bestaetigt, nicht am Geraet |
| Pads 9-16 als zweite Seite des Pad-Rasters (`patches/padpages.py`), Umschalten nur per Button: Pads = Linkspfeil, Mixer = Feld oben links, Effects = erneuter Druck auf die gewaehlte Zelle DLY/RVB, Pad-Waehler = Linkspfeil (Pad-Namen 5 Zeichen, folgt der Seite des markierten Pads); Encoder waehlt innerhalb der Seite | pkB am Geraet: Seiten und Waehler gehen; pkE: Encoder auf Seite 2 (Encoder-Listen des Pads-Bildschirms), nicht am Geraet |

Splash: Zeile 2 `portkit mod`, Version `2.3.4-pkH`.

## Bauen

```sh
./setup.sh                                  # Repos, venv, Hash-Check; firmware/MICRO.BIN muss 2.3.4 sein
./build.sh                                  # src/ -> out/cave.elf, out/cave.bin
.venv/bin/python -I patch.py fidelity pages padpages sound cave  # -> out/fidelity+pages+padpages+sound+cave/MICRO.BIN
.venv/bin/python -I tests/test_fidelity.py  # Unicorn-Tests auf dem gepatchten Image
.venv/bin/python -I tests/test_padpages.py
```

`patch.py` schreibt nur, wenn alles gruen ist: Stock-Hash, erwartete Stock-Bytes an jeder Stelle, Null-Repack,
alle Aenderungen in registrierten Bereichen, jeder umgeleitete Aufruf landet auf einer Cave-Funktion, und jeder
Aufrufer der ersetzten Funktionen ist erfasst.

Flashen (Recovery: weisse Pfeiltaste rechts beim Einschalten, `MICRO.BIN` im SD-Root) erst nach Sicherung des
Stock-Images. Adressen und Belege: `re/symbols.md`. Lizenzen: `THIRD_PARTY.md`.
