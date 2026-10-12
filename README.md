# portkit

Funktionen aus dem [Blackbox-Mod](https://github.com/j3threejay/blackbox-mod) als Patch fuer die 1010music
bitbox micro, Firmware 2.3.4. Keine Firmware in diesem Repo: Der Patcher arbeitet auf deiner eigenen `MICRO.BIN`.

## Stand

| Funktion | Status |
|---|---|
| Fidelity (Interp-Liste: Normal, HighQ, SP1200, SP-12, S950, MPC60, SP Raw, 16k..2k) | am Geraet: laeuft, auf Sample-Pads einstellbar (pk1) |
| 24-dB-SVF (ersetzt den Pad-Biquad), Res sauber | durch Emulation bestaetigt, nicht am Geraet |
| Drive (tanh, vor den Filtern) und Filter 2 + Res 2 (zweiter 24-dB-SVF in Serie), neue Regler auf der Hauptseite jedes Pad-Modus (`patches/sound.py`); alte Presets bekommen Defaults | pkF: durch Emulation bestaetigt, nicht am Geraet |
| Shift fuer Clips (−100..100 ms, dreht den Loop gegen das Raster; Loop-Seite der Clip-Pads, `src/clipshift.c`) | pkI am Geraet: funktioniert |
| Abspiellaenge fuer Clips (Play Len: Full, 1/4..32 Takte; Loop-Seite, mit Sync) | pkH: durch Emulation bestaetigt, nicht am Geraet |
| Stretch fuer Clips (±100 %, stufenlos ueber die Segment-Startpositionen, braucht Sync; Loop-Seite) | pkQ am Geraet: funktioniert (Jump) |
| Smooth Time-Stretch (WSOLA, Tonhoehe bleibt), Stretch Mode Auto/Jump/Smooth | pkR am Geraet: funktioniert |
| Audio-Last rechts in der Kopfzeile | pkS: korrigiert, nicht am Geraet |
| Reverb-Typen Plate / Room / Hall / Chamber mit 10 Reglern + Level, Pegel aufs Plate abgeglichen (`patches/reverb.py`) | pkT am Geraet: funktioniert; pkV: Pegel, nicht am Geraet |
| FX3: dritter Send (Bus 0xC) mit zweitem Reverb; Effects: Linkspfeil = Seiten, zweites Tippen auf RVB = RVB/FX3; Rechtspfeil = FX3-Regler, nochmal = Master-EQ (`patches/fx3.py`) | pkU am Geraet: laeuft (Hall leise → pkV); pkW: FX3 auf Zeile 3 statt EQ, nicht am Geraet |
| Master-Sektion: Tools-Seite Linkspfeil = Kompressor (Threshold, Ratio, Attack, Release, Gain; stock Kompressor), Rechtspfeil = Master-Distortion (Soft / Hard / Fold / Tube, Drive, Tone, Mix, Level; 2x Oversampling) (`patches/master.py`) | pkX: durch Emulation bestaetigt, nicht am Geraet |
| Kompressor-Typ SSL (Schalter Ratio 2/4/10, Attack 0,1-30 ms, Release 0,1-1,2 s/Auto) und Mix fuer beide Typen (`patches/master.py`) | pkY: durch Emulation bestaetigt, nicht am Geraet |
| Sync-Raster 1/32 (Clips); Play Len / Stretch ausgeblendet, wenn Quant Size / Sync sie unwirksam machen | pkK: durch Emulation bestaetigt, nicht am Geraet |
| Machine-Drive (Saturation als Wandler-Eingang) | nicht portiert (Micro hat keinen Saturation-Parameter) |
| Fidelity auch auf der Pad-Seite von Clip, Slicer, Granular (`patches/pages.py`) | durch Emulation bestaetigt, nicht am Geraet |
| Pads 9-16 als zweite Seite des Pad-Rasters (`patches/padpages.py`), Umschalten nur per Button: Pads = Linkspfeil, Mixer = Feld oben links, Effects = erneuter Druck auf die gewaehlte Zelle DLY/RVB, Pad-Waehler = Linkspfeil (Pad-Namen 5 Zeichen, folgt der Seite des markierten Pads); Encoder waehlt innerhalb der Seite | pkB am Geraet: Seiten und Waehler gehen; pkE: Encoder auf Seite 2 (Encoder-Listen des Pads-Bildschirms), nicht am Geraet |

Splash: Zeile 2 `portkit mod`, Version `2.3.4-pkZ`.

## Bauen

```sh
./setup.sh                                  # Repos, venv, Hash-Check; firmware/MICRO.BIN muss 2.3.4 sein
./build.sh                                  # src/ -> out/cave.elf, out/cave.bin
.venv/bin/python -I patch.py fidelity pages padpages sound reverb fx3 master cave  # -> out/fidelity+pages+padpages+sound+reverb+fx3+master+cave/MICRO.BIN
.venv/bin/python -I tests/test_fidelity.py  # Unicorn-Tests auf dem gepatchten Image
.venv/bin/python -I tests/test_padpages.py
.venv/bin/python -I tests/test_reverb.py
.venv/bin/python -I tests/test_fx3.py
```

`patch.py` schreibt nur, wenn alles gruen ist: Stock-Hash, erwartete Stock-Bytes an jeder Stelle, Null-Repack,
alle Aenderungen in registrierten Bereichen, jeder umgeleitete Aufruf landet auf einer Cave-Funktion, und jeder
Aufrufer der ersetzten Funktionen ist erfasst.

Flashen (Recovery: weisse Pfeiltaste rechts beim Einschalten, `MICRO.BIN` im SD-Root) erst nach Sicherung des
Stock-Images. Adressen und Belege: `re/symbols.md`. Lizenzen: `THIRD_PARTY.md`.
