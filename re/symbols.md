# Symbole: Bitbox micro 2.3.4 (`MICRO.BIN`, SHA-256 54ecc3e5…4365)

Status: `vermutet` = statisch belegt, nicht emuliert. `durch Emulation bestaetigt` / `hardware-verified` noch nirgends.
Spalte "BB 3.1.9" = Adresse im Blackbox-Mod (`patches/filter.py`, `src/filter.c`); "BB 3.1.8" = dieselbe Funktion in der
lokal vorliegenden 3.1.8 (Referenz, SHA-256 0788…1e7a). 3.1.9 liegt nicht vor.

## Fidelity / Interp: Anker fuer den Port von `filter.c`

| Micro | Name | BB 3.1.9 | BB 3.1.8 | Beleg | Status |
|---|---|---|---|---|---|
| 0x08069E7C | `register_list(table, id, label, names, count, xml)` | 0x0808C0D8 | 0x0808C0F8 | 40 Bytes identisch mit 3.1.8; Aufrufe mit Label/Liste/Anzahl/xml im Param-Init | vermutet |
| 0x0806B34A | Aufruf: Interp-Registrierung (Hook-Punkt fuer `interp_register`) | 0x0808D92A | – | `movs r1,#0xd2`; r2=`"Interp:"`, r3=Namensliste, [sp]=2, [sp+4]=`"interpqual"` | vermutet |
| 0xD2 | Param-ID Interp | 0xF1 | – | Registrierung oben | vermutet |
| 0x080C475C | Namensliste {Normal, HighQ} | – | – | Zeiger auf 0x080C2414 `Normal`, 0x080C241C `HighQ` | vermutet |
| 0x0E / 0x11 | Param-IDs Cutoff (`cutoff`) / Res (`res`) | Filter / Res | – | Param-Init 0x08069F80 / 0x08069FA8 | vermutet |
| 0x080B8420 | Pad-Filter-Prozess `(obj, buf)` | 0x080762D8 | 0x080762E8 | gleiche Feldbelegung (+0, +0x84 Params, +8 Knob, +0x44 Res, +0x88/+0x8C/+0x90), ruft silent/frames/chans | vermutet |
| 0x080B827C | Koeffizienten-Helper (nur von 0x080B8420 gerufen) | 0x0807612C | 0x0807613C | identische Feldbelegung, 1 Aufrufer | vermutet |
| 0x080AD960 | Aufruf Filter Klasse A (Sample/Granular): r0=voice+0xA4, r1=buf, **Pad in r5** | 0x08055C60 (Pad in r6) | 0x08055C70 | danach `ldrb [r5,#0x560]`; r5=r0 des Aufrufers, kein Schreibzugriff dazwischen | vermutet |
| 0x080B5CCC | Aufruf Filter Klasse B (Clip/Slicer): r0=sub+0x14C, **Pad in r6** | 0x080669D6 (`r0-0x3ac`) | 0x080669E6 | Klasse-B-Funktion 0x080B5AA8 bekommt Pad in r0 (`mov r6,r0`) und sub=pad+0x260 **oder pad+0x670** | vermutet |
| 0x080A01BC | Cutoff-Kurve knob→Hz | 0x08060640 | 0x08060650 | Befehlsfolge identisch (x10, Tabelle 2001 Eintraege) | vermutet |
| 0x080A0240 | Res→Q-Kurve | 0x080606C0 | 0x080606D0 | Befehlsfolge identisch (x7.5, Tabelle) | vermutet |
| 0x080A19F4 | modulierter Param-Wert | 0x0806FB30 | 0x0806FB40 | Befehlsfolge identisch | vermutet |
| 0x080A31E0 | buf_frames | 0x0804D8E8 | 0x0804D8F8 | 13 Bytes identisch | vermutet |
| 0x080A31EC | buf_silent | 0x0804D8F4 | 0x0804D904 | gleiche Logik | vermutet |
| 0x080A3228 | buf_chans(buf, &L, &R) | 0x0804D944 | 0x0804D954 | gleiche Logik, R=0 bei Mono | vermutet |
| 0x080894D0 | Store get `(store, id)` | 0x08093E9C | 0x08093EBC | gleiche Logik (count @+0xA, Eintraege @+4, 8 Byte) | vermutet |
| 0x080894FA | Store set `(store, id, val)` | – | – | Nachbar, gleiche Struktur | vermutet |
| 0x080ADC4C | Voice-Reader (s0 frac, s1 rate, r0 pad, r1 src, r2 pos …) | 0x08055F0C | 0x08055F1C | ruft beide Kernels je 3x | vermutet |
| 0x080AEE92, 0x080AF0D8, 0x080AF19A | Aufrufe des Voice-Readers (3; BB hat 4) | 0x08057214 … | 0x08057224 … | Call-Graph | vermutet |
| 0x080A1400 | Kernel Normal | 0x080619D0 | 0x080619E0 | nur vom Voice-Reader gerufen (3x); Abstand zu HQ 0x94 wie bei BB | vermutet |
| 0x080A1494 | Kernel HighQ | 0x08061A64 | 0x08061A74 | dto. | vermutet |
| pad+0x564 | Engine-Kopie Interp (≠0 → HQ-Kernel) | im Bereich +0x550..+0x582 | – | `ldr.w r3,[r7,#0x564]; cmp; beq` in 0x080ADD22 | vermutet |
| 0x080C788A, 0x080C7AA6, 0x080C7CC2 | Pad-Seiten mit Interp (Launch Mode, Output, Poly, Excl Group, **Interp**, MIDI In, …) | 0x080EFD38 … | 0x080EF4A8 (Sample) | Halfword-Listen von Param-IDs | vermutet; welcher Pad-Typ welche Seite: offen |

## Interp-Einstellung pro Pad lesen (Punkt 1, geklaert 2026-10-09)

| Micro | Name | BB 3.1.9 | Beleg | Status |
|---|---|---|---|---|
| 0x080B2FE8 | Engine-Setter Interp: `pad+0x564 = msg+0x10` | – | 2. Switch in 0x080B10BE (Tabelle 0x080B1AFC, Index = Param-ID − 2 = 0xD0), nur wenn `pad+0x18 == msg+8` | vermutet |
| 0x080B17AA | **Reset** pad+0x550..+0x5AC inkl. Interp → 0, im Fall Nachrichtentyp 0x40 desselben Handlers (Tabelle 0x080B1134) | FUN_080596b0 | gleicher Block wie im Init 0x080AD35C | vermutet |
| pad+0x18 | Engine-Pad-ID = `row<<8 \| col`, row/col 0..3 (Sonderpads 0x400, 0x10400) | `bank<<16\|row<<8\|col`, col 0..4 | Schleife 0x08096066..0x08096142 (`sl += 0x100` bis 0x400, col bis 4) | vermutet |
| 0x24013CB0 | `app` (statisch, 74 Literal-Verweise) | 0x24020088 | Literal 0x08084A68, an 0x08077F28 uebergeben | vermutet |
| app+0x1840+row*0xF0+col*0x30 | App-Pad-Record (= Store) | identisch | Init-Schleife 0x08077F5E..0x08077FA4 (sl = app+0x1C00..+0x1CF0, r4 = sl−0x3C0, +0xF0) | vermutet |
| 0x08089FC4 / 0x08089548 | Store-Init `(record, &type)`; Typ 0x45 (Grid-Pads beim Start) und Typ 3 legen 0xD2 an | – | tbh-Tabelle 0x08089562; Unicorn: 36 Eintraege, 0xD2 vorhanden | **durch Emulation bestaetigt** (`tools/emu_store.py`, Allocator 0x08042DC0 gestubbt) |
| 0x080894D0 / 0x080894FA | Store get / set | 0x08093E9C | Unicorn: get 0xD2 = 0 nach Init, = 1 nach set 1 | **durch Emulation bestaetigt** |

Ergebnis: Die Engine-Kopie pad+0x564 ist nicht verlaesslich (Reset in Nachrichtentyp 0x40 setzt sie bedingungslos auf Normal).
Der Mod-Weg funktioniert in der Micro mit denselben Strides: `fw_setting = 0x080894D0`, `APP_PADS = 0x24013CB0 + 0x1840`,
in `pad_setting()` nur `col >= 4` statt `col >= 5`. Nicht geprueft: ob die UI auf genau diese Records schreibt (statt einer Kopie);
das klaert erst der Hardware-Test.

Pad-Anzahl: Die Micro hat 8 Pads (Geraet). Die Engine legt 16 Pad-Objekte an (row 0..3, col 0..3), die App 20 Records
(row 0..3, col 0..4, Framework-Groesse). Welche 8 Slots die Micro belegt: nicht verifiziert. Fuer den Mod egal, solange
`pad_setting()` row < 4 und col < 4 zulaesst: Engine-ID und App-Record kommen aus demselben (row, col).

## Filterobjekt-Layout (Punkt 4, geprueft 2026-10-09)

Ctor 0x080B81F0, Reset 0x080B8760 / 0x080B8794 (zwei identische Kopien; 6 Aufrufer beim Voice-Start, u. a. 0x080AD55C),
Setter 0x080B8254 (+0x84), 0x080B825C (Cutoff → params+4), 0x080B826C (Res → params+0x40).

| Offset | Stock | Ctor | Reset | Mod (`filter.c`) |
|---|---|---|---|---|
| +0x00 | Typ-Byte | 1 | 1 | – |
| +0x04..+0x17 | Koeff.-Satz 1 (Ziel, via +0x60) | 0 | – | `fstate` magic, g, r, drive, s1[0][0] |
| +0x18..+0x2B | Koeff.-Satz 2 (via +0x64) | 0 | **+0x18 = 1.0, Rest 0** | s1[0][1] .. s2[0][1] |
| +0x2C..+0x3F | Koeff.-Satz 3 (geglaettet) | 0 | – | s2[1][*], phase, held |
| +0x40..+0x4F | Biquad-Zustand L | 0 | **0** | +0x40 = `on` |
| +0x50..+0x5F | Biquad-Zustand R | 0 | 0 | – |
| +0x60 / +0x64 | Zeiger auf +0x04 / +0x18 | gesetzt | – | `ostate` magic, z[0][0] |
| +0x68 / +0x6C | Konstanten | gesetzt | – | z[0][1], z[1][0] |
| +0x70..+0x83 | Koeffizienten (nur Prozess + Helper) | – | – | z[1][1] (+0x70) |
| +0x84 | Zeiger Parameterblock | 0 / Setter | – | gelesen |
| +0x88 / +0x8C / +0x90 | letzte Werte / Dirty | 0 / 0.5 / 0 | 0 / 0.5 / 0 | – |

Unicorn (`tests/test_fidelity.py`): Reset 0x080B8794 nullt `on`, danach bleibt Stille still → **durch Emulation bestaetigt**.

Ergebnis: +0x60..+0x83 liest und schreibt ausser Prozess (ersetzt) und Koeffizienten-Helper (nur vom Prozess gerufen) niemand
→ `ostate` ist sicher. Der Reset beim Voice-Start ueberschreibt s1[0][1] mit 1.0 und nullt `on` (+0x40); `filter_process`
setzt bei `on == 0` alle Integratoren auf 0, bevor es sie benutzt → kein Knackser. Magic (+0x04) bleibt stehen.
Fuer Crunch-Zustand (phase, held) nicht relevant (Reset beruehrt +0x34..+0x3F nicht). Status: vermutet (statisch), noch nicht emuliert.

## RAM (Punkt 2, geprueft 2026-10-09)

MPU (MPU_Config 0x08041098, HAL_MPU_ConfigRegion 0x0804A340, in Unicorn ausgelesen, `tools/emu_mpu.py`):

| Region | Bereich | Attribute |
|---|---|---|
| 4 | 0x24060000–0x2406FFFF | TEX0 C0 B1 (Device, nicht gecacht), XN |
| 5 | 0x24070000–0x2407FFFF | dto. |
| 8 | 0xC0000000–0xC3FFFFFF (64 MB SDRAM) | gecacht, XN |
| 9 | 0x30000000–0x3007FFFF (D2-SRAM) | gecacht, XN |

Belegung AXI-SRAM: .bss/Heap bis 0x24068AA8, Stack 0x24068AA8–0x240692A8, darueber bis 0x24080000 keine Literal- und keine
movw/movt-Referenz (zwei scheinbare Treffer 0x2406E7DA / 0x2407FC0D sind Befehlsbytes). Micro-Patcher-Store 0x2406C000–0x2406C07C
(dort hardware-erprobt). Vorschlag `PARK` = 0x2406C100 (12 Bytes, wortweise ausgerichtet; Device-Speicher erlaubt keine
unausgerichteten Zugriffe). "Keine Referenz" beweist nicht "unbenutzt" (DMA mit berechneten Adressen) → erst Hardware-Test.

## Offen (blockiert den Port)
1. ~~Pad-Einstellung aus der App lesen~~: geklaert, siehe oben.
2. **Machine-Drive.** BB nutzt Saturation (0xDB). Die Micro hat keinen Saturation-Parameter → Drive weglassen oder anderen Knopf waehlen.
3. ~~Patch-RAM fuer `PARK`~~: Vorschlag 0x2406C100, siehe RAM.
4. ~~Filterobjekt +0x60/+0x64~~: geprueft, siehe Filterobjekt-Layout.
5. Cutoff in der Micro bipolar (LP links / HP rechts) wie in der BB? Typbyte obj+0 und Param `Type:` (0x12) noch nicht ausgewertet.

## Fidelity-Patch (Build pk1, 2026-10-09)

`patches/fidelity.py` + `patches/cave.py`, Code-Cave ab 0x080E3E90 (3252 Bytes). Hooks: Interp-Registrierung, beide
Filter-Aufrufe (Thunks r5 / r6), 3 Voice-Reader-Aufrufe, 6 Kernel-Aufrufe; `patch.py` prueft, dass jeder Aufrufer von
0x080B8420, 0x080ADC4C, 0x080A1400, 0x080A1494 umgeleitet ist. Unicorn auf dem gepatchten Image, 28 Checks gruen:
Fidelity-Liste und Label ueber die echte Aufrufstelle, Crunch/12 Bit, Interp pro Pad aus dem App-Store, Thunks A/B,
LP/HP des SVF, alle Machine-Modi, Kernels ohne Machine bitgleich mit Stock, Voice-Reader-Wrapper reicht alle Argumente
durch. Status: **durch Emulation bestaetigt**, nicht hardware-verified.
Emulator-Hinweis: Unicorn 2.1 hat auf M-Profil kein Double (Stock-Res-Kurve nutzt `vcvt.f64.f32`) → Tests laufen wie
blackbox-mod/emu.py mit `UC_CPU_ARM_MAX` im Thumb-Modus.

## 16 Pads? (Untersuchung 2026-10-09)

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x08095CE8 (Schleife 0x08096066..0x08096142) | Engine-Graph-Aufbau | 16 Pad-Zellen (Node-Typ 0x4C, ID `row<<8\|col`, row/col 0..3), je mit Sample-Engine (Typ 0x48, vtable 0x080DE300), beide in den Graphen gehaengt | vermutet |
| 0x080B3650 (vtable +0x0C) → 0x080B10B8 | Block-Verarbeitung Klasse A (Klasse B: 0x080B8148 → 0x080B74EC) | Graph verarbeitet jede eingehaengte Zelle | vermutet |
| 0x08080EC4 | Preset-Leser (`cell` row/column/layer) | Pad-Zellen (Typ 3 / 0x45, layer 0): Record = Basis + row*0xF0 + col*0x30, **keine** Grenze auf 8 Pads | vermutet |
| 0x08080AF4 | Preset-Writer | laeuft ueber 4 Zeilen x 5 Spalten der App-Records, ueberspringt leere | vermutet |
| – | UI: Touch/Anzeige → (row, col) | kein Muster `i>>2 / i&3` gefunden; Zuordnung vermutlich tabellen- oder koordinatenbasiert | offen |

Folgerung: Engine, App-Records und Preset-Format sind fuer 16 Pads ausgelegt (Framework der Blackbox). Die Grenze 8 sitzt
vermutlich nur in der Bedienung (Touch, Anzeige, Pad-Auswahl) und bei MIDI (8 Kanaele laut Micro-Patcher). Nicht geprueft:
CPU-Reserve bei 16 spielenden Pads, Speicher fuer 16 geladene Samples.

## Hardware-Test pk1 (2026-10-09)

Laeuft auf dem Geraet; Fidelity auf Sample-Pads sichtbar und einstellbar, "sonst geht schon sehr viel". Bei Clip, Slicer,
Granular fehlte Interp in der Stock-Firmware schon (Geraet). Status Fidelity auf Sample-Pads: **hardware-verified**
(Umfang laut Rueckmeldung; einzelne Modi, SVF, Last noch nicht einzeln rueckgemeldet).

## Pad-Seiten (Build pk2)

Pad-Modi (`cellmode` 0x6D): Sample, Clip, Slicer, Granular (+ Aktionen New Rec, New Multi).
Seitentabellen je 6 Seiten x 45 Halfword-IDs (0x21C Bytes), Auswahl in 0x08076D8C (tbb auf Modus, zwei Varianten je Modus);
Seite 5 = Pad-Einstellungen.

| Modus | Tabellen | Seite 5 stock |
|---|---|---|
| Sample | 0x080C76C0, 0x080C78DC, 0x080C7AF8 | ... Excl Group, **Interp**, MIDI In, (Root Note), Pad Note |
| Clip | 0x080C6A1C, 0x080C6C38 | Launch, Output, Poly (0x83), Excl Group, MIDI In, Pad Note |
| Slicer | 0x080C7E28, 0x080C8044 | dto. (+ Root Note in 0x080C8044) |
| Granular | 0x080C6EEC, 0x080C7108 | Launch, Output, Excl Group, MIDI In, Root Note, Pad Note |

Store-Typen (Unicorn, Store-Init 0x08089FC4 fuer Typ 1..0x4A): Typ 3 = voller Pad-Store (58 IDs, u. a. Interp, Beat Count,
Slice, Density, Pad Mode), Typ 0x45 = Boot-Default (36 IDs, Interp ja, Slice/Density nein). Der Preset-Leser behandelt
Zellen vom Typ 3 / 0x45 als Pads → Interp ist fuer alle Pad-Modi speicherbar. `patches/pages.py` traegt 0xD2 hinter
Excl Group in Clip/Slicer/Granular ein (beide Varianten). Status: durch Emulation bestaetigt (Tabelleninhalt), nicht am Geraet.
Hinweis: "Poly Mode:" ist bei Sample 0x82, bei Clip/Slicer 0x83 (gleiches Label).

## UI: Pad-Raster (Untersuchung 16 Pads, 2026-10-09)

Panel 240x320 nativ (CASET 0..0xEF, RASET 0..0x13F, 0x080462EA..), UI quer 320 breit; Inhaltsbereich {0,0,320,221}
(0x08070828). Touch GT911, Punkte bei 0x0804659E (Micro-Patcher "Flip UI"). Widgets mit vtable, setRect = vt+0x20 mit
{x, y, w, h} (int32) auf dem Stack, Kind anhaengen = 0x08060D30. Katalog aller setRect-Aufrufe: `tools/rects.py`.

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x080866B0 (Schleife 0x08086974..0x080869D8) | Pad-Raster | 2 Zeilen (`cmp sb,#2`) x 4 Spalten (`cmp r5,#4`), Kachel {1+80*col, 1+74*row, 78, 72}, Widget-Abstand 0x1A0, Kachel-ID (+0x38) = row<<4 \| col; Kacheln liegen im Bildschirm-Objekt, danach weitere Member ab +0xD34 | vermutet |
| 0x08083E40 | weiteres 4er-Kachelraster 78x72, Abstand 0x1A0 | Bildschirm unbekannt | vermutet |
| 0x08085664 | 4 Spalten x 2 Elemente (Schleife `sb` += 2 bis 8), Widget-Klasse mit 0x08085E34, Abstand 0x28C | Kandidat Send-/Mixer-Ansicht | vermutet |
| 0x080696E0 | Kacheln 78x72 bei y=75 | Bildschirm unbekannt | vermutet |
| 0x080860DC | Menue mit 8 grossen Buttons 160x66 (Texte "Pads", "FX", Icons) | kein Pad-Raster | vermutet |
| app+0x7FE4 | aktueller Bildschirm: 2 = Pads, 0x2E/0x2F = Mixer, 0x30 = FX (0x080769E0) | | vermutet |

Folgerung: Die 8 Micro-Pads sind Zeilen 0-1 des 4x4-Rasters (App-Code row<<4|col, Engine-ID row<<8|col). Fuer 16 Pads
muessen die Zeilen 2-3 als Kacheln dazukommen. Problem: Die 8 Kachel-Widgets sind fest ins Bildschirm-Objekt eingebettet
(danach folgen weitere Member), d. h. 8 zusaetzliche Widgets brauchen eigenen Speicher, und jeder Code, der ueber die
Kacheln iteriert (Zeichnen, Beschriften, Auswahl, Touch), muss sie mit abdecken.

## Seiten-Variante (Pads 9-16 als Seite 2), Analyse 2026-10-09

Kachel-Widget (Button-Klasse, Ctor 0x0805DB34, vtable 0x080BFDC0, Rect +4..+0x10, **Pad-Adresse u16 +0x38**).
Pads-Bildschirm: Ctor 0x080866B0 (aufgerufen aus 0x08085130), vtable 0x080C647C; 8 Kacheln bei +0x34 (Zeile 0x680,
Spalte 0x1A0), danach 5 weitere Buttons +0xD34..+0x1554; ausgewaehltes Pad (Kopie) bei +0x1BD4 / +0x1BDC.

| Micro | Was | Befund |
|---|---|---|
| 0x080863A0 (vt+0x34) | Benachrichtigungen | 0x66: Pad geaendert (Adresse msg+8, Bits 8-12 muessen 0 sein) → 0x080862A4; **0x67: alles neu, feste Adressen 0x00-0x03, 0x10-0x13** → 0x080862A4; 0x112: Auswahl geaendert → +0x1BDC, Markierung per Vergleich mit Button-ID; 0x32: Encoder-Anzeige |
| 0x080865E4 (vt+0x30) | Eingaben | Ereignis 3 (Touch auf Kachel, ID msg+8) → 0x08086478 bzw. Befehl 0x111 (Bits 8-12 == 3); 0x3C/0x3D (Knoepfe) → Befehl 0x6E mit +0x1BD4 |
| 0x0807E3B8 | App-Befehls-Dispatcher (tbh, Befehl-3) | 0x111 → 0x0807B20C SetSelectedPad (app+0x28 = Adresse, Nachricht 0x112); 0x6E → 0x0807D358 (allg. Parameter-Knopf) |
| 0x0807B20C | SetSelectedPad | einziger Aufrufer 0x0807E744 (Dispatcher) |

Rueckrechnungen Adresse → Kachel ohne Grenzpruefung (Zeile 2/3 wuerde hinter das Kachel-Array schreiben):
0x08084034, 0x08084154 (vtable 0x080C6378), 0x080862A4, 0x08086478 (Pads-Umfeld); 0x080853FC (Mixer/FX, Widget 0x28C);
0x08064B04, 0x080654A8 (vtable 0x080C04C0), 0x0806580C (vtable 0x080C048C), 0x08069268 (anderer Raster-Bildschirm).

Design: globales Seiten-Byte; Kachel-IDs tragen die echte Adresse (beim Seitenwechsel neu gesetzt); an jeder
Rueckrechnung ersetzt ein Thunk `ubfx rZeile, rAdr, #4, #4` durch Zeile − 2·Seite oder springt bei Pad nicht auf der
Seite zum Funktionsende; 0x67-Schleife mit Seiten-Offset; Seitenwechsel bei Auswahl (0x112) eines Pads der anderen Seite.
Offen: wo die Knopf-Auswahl das naechste Pad bestimmt und ob dort auf 8 begrenzt wird (nicht in 0x0807D358 gefunden).

Nachtrag Encoder (2026-10-09): Am Geraet springt die Encoder-Auswahl nach Pad 8 auf Pad 1 (Geraet). Nicht gefunden:
kein 0x111 ausser Touch (0x08086678), keine Index-Tabelle, nicht in 0x0807D358 (Sonderfaelle 0x7D/0xBE/0x1C5 sind Rec
Input / Mon Output). Button (0x0805D44C): Touch-Down → Ereignis 3 mit ID, Touch-Up → Ereignis 4. Pads-Bildschirm
behandelt Encoder 0x3C/0x3D nur bei Flag +0x1BE0, sonst "nicht behandelt" (→ uebergeordnete Ebene).
UI-Manager (vtable 0x080C6384, Handler 0x08084A70): beim Bildschirmwechsel 0x63, 0x67 (alles neu), 0x112 (Auswahl)
an den neuen Bildschirm (0x08084FA0 / 0x08084FF8).
Ausweg: Seitenwechsel im 0x112-Handler erkennen (Auswahl springt von letztem auf erstes Pad der Seite, nicht durch Touch).

## Pad-Seiten, Build pk3 (Prototyp, 2026-10-09)

`src/padpages.c`, `src/padpages_thunk.S`, `patches/padpages.py`. Zustand ab 0x2406C110 (magic "PAGE", page @+4, touch,
busy, last_sel, Instanzen A/B/D). Raster-Bildschirme: A = Pads (vtable 0x080C647C, Kacheln +0x34, 8), B = vtable
0x080C6378 (Kacheln +0x34, 8), D = Waveform-Pad-Raster (vtable 0x080C0694, Kacheln +0x3AC, **16, Zeilen 2-3 unsichtbar**,
eigene Pruefung laesst Zeilen 0-3 zu), C = Mixer/FX (Widget 0x28C, nach Pad-Nummer indiziert, Pads 9-16 abgewiesen →
unveraendert).

Pruefungen vor dem push von lr (0x08084034, 0x08084138, 0x080862A4, 0x08086478) → Aufrufer auf C-Wrapper umgeleitet
(Seite pruefen, dann Rumpf hinter der Pruefung: 0x08084046, 0x080862B6, 0x08086482). `ubfx`-Zeilen in den Ruempfen
(8 Stellen) → Thunk Zeile − 2·Seite; D: `asr.w r8, r3, #4` → Zeilen per XOR getauscht. Konstruktoren im UI-Manager
(0x08085140 B, 0x0808519C D, 0x080851C4 A) → Wrapper merken die Instanzen, Seite 0. vtable A +0x30/+0x34 und B-Notify
→ Wrapper: Touch-Flag, Encoder-Ueberlauf (letztes → erstes Pad der Seite ohne Touch = naechste Seite, Auswahl per
Befehl 0x111), 0x67 auf Seite 1 mit Pads 9-16 nachgefuellt.
Unicorn (`tests/test_padpages.py`, 22 Checks): Thunks, echte Ruempfe von A/B/D adressieren auf beiden Seiten dieselbe
sichtbare Kachel, fremde Pads uebersprungen, Seitenwechsel/Encoder-Logik. Nicht emuliert: Zeichnen, echtes
Encoder-Verhalten auf Seite 2. Status: durch Emulation bestaetigt (Logik), nicht am Geraet.

## Korrektur Bildschirm-Zuordnung (pk4, 2026-10-09)

Layouts per Emulation der Konstruktoren (`tools/emu_layout.py`, Kinder-Widgets mit Rect/vtable/ID/Text):
- **A (Ctor 0x080866B0, vtable 0x080C647C) = Effects**, nicht Pads: 8 Kacheln (Rumpf fragt 0xBB FX1 Send / 0xBC FX2 Send),
  unten DLY-Zelle {1,149,119,72} ID 0x300, RVB-Zelle {200,149,119,72} ID 0x310 (Ebene 3), Send-Anzeigen x=122 / x=161 (37 breit).
- **B (Ctor 0x08083E40, vtable 0x080C6344) = Pads**: 8 Kacheln, unten Panel {1,149,318,72} mit Keys {1,149,78,72},
  Mitte {81,149,158,72} (Klasse 0x080BFCE8, ID 0xA0), Stop {241,149,78,72}. Eingaben vt+0x30 = 0x08083DEC (nur eigene
  Buttons; Kachel-Touch und Encoder gehen nach oben). Notify vt+0x34 = 0x08084154: **Auswahl = 0x63** (Adresse msg+8 →
  +0xD38, Kachel-Markierung), 0x66 Pad geaendert, 0x67 alles neu; 0x112 wird ignoriert.
- **D (Ctor 0x080696E0, vtable 0x080C0694) = vermutlich Mixer**: 16 Kacheln (8 sichtbar), Rumpf fragt 0x77 Output ab,
  unten vier Buttons 158x35.
- C (Ctor 0x08085664) = Ein-/Ausgaenge (Kacheln = Buchsen, IDs Index<<4, Parameter 0xD9 Input / 0xDA Output) → keine Pads.
- Kopfzeile gibt es nicht: Bildschirme y 0..219, Statuszeile unten y 220..239 (UI-Manager +0x2BC).
pk3-Fehler am Geraet: Encoder-Erkennung haengte am Effects-Bildschirm und wartete auf 0x112. pk4: an B, Nachricht 0x63,
Touch-Flag aus B vt+0x30. Tests angepasst (22 gruen).

## Tasten und Build pk5 (2026-10-09)

Tastentreiber 0x08041A50 (4 Tasten, Index = 3 − i ohne Flip UI; Tabelle im RAM 0x24009DA4, 0x18 je Taste, +8 Ereignis
beim Druecken = 0xF4, Index im Ereignis +0xC). App-Ebene 0x080837D0: 0xF4 → 0x08083982, tbb ueber den Index:
0 = HOME (Pads 2 → Mixer 0x2E → FX 0x30 → Pads, 0x0808EEDC), 1 = TOOLS (0x25 / 0x33 / 0x32), **2 = Linkspfeil**
(Tabelle je Bildschirm ab ID 4: Pads → nichts; Mixer 0x2E → Pads; Mixer-Mute 0x2F und FX 0x30 → Mixer),
3 = Rechtspfeil (Nachricht 0xC → Detail je Bildschirm). Bildschirm-IDs: Pads 2, Mixer 0x2E (Mute 0x2F), FX 0x30.
Foto vom Geraet: UI am Geraet um 180° gedreht; Keys / Mitte / Stop erscheinen oben, Pads darunter.

pk5: `left_arrow` ersetzt `movw r3, #0x7fe4` bei 0x080839E6; auf Bildschirm 2 → padpages_left(app) (Seite umschalten,
Pad an gleicher Stelle per 0x111 waehlen; app+0x28 = Auswahl) und Ausstieg ueber 0x080837E8, sonst unveraendert.
Seitenanzeige: Text-Widget (Ctor 0x0805D124, 0xA0 Bytes, per 0x08042DC0 angelegt), Rect {100,165,120,40} als Kind des
Pads-Bildschirms ueber der leeren Panel-Mitte, setText 0x0805D1DC ("Pads 1-8" / "Pads 9-16"). Status: Emulation.
Offen: Mixer- und FX-Seitenumschaltung per Bildschirm-Button.

## Build pk6 (2026-10-09)

- App-Befehl **0x63 = Pad waehlen** (0x08075984: app+0x14 = Auswahl, Nachricht 0x63, Engine-Parameter 0xC1);
  0x111 waehlt eine Effekt-Zelle (app+0x28, Nachricht 0x112). pk3-pk5 haben faelschlich 0x111 benutzt. App = 0x24013CB0.
- Touch-Zustellung: vt+0x28 (0x08060C4C) sucht das tiefste Widget, das den Punkt enthaelt und Touches annimmt
  (vt+0x1C); Text-Widgets (vtable 0x080BFC9C) nehmen an (0x0805CB32 → 1), ignorieren sie aber (vt+0x30 = 0x08060CF2 → 1).
  Kachel-Buttons: Ereignis 1 (Touch runter) → Ereignis 3 mit ID an den Elternteil, 2 → 4. Hochreichen: 0x08060DF8.
- Mixer = D bestaetigt (Foto): vier leere Text-Buttons oben (UI 180° gedreht); {161,186,158,35} = D+0x2AE8 = oben links.
- pk6: RAM-Kopie der Text-vtable (0x80 Bytes, Heap) mit vt+0x30 = padpages_toggle_input (Ereignis 1 → Seite um,
  Pad an gleicher Stelle per 0x63 waehlen). Pads-Anzeige (eigenes Widget) und Mixer-Feld bekommen sie; beide zeigen
  "Pads 1-8" / "Pads 9-16". Unicorn inkl. echter Konstruktoren / setRect / setText / Kind-Liste: 33 Checks gruen.
  Annahme (vermutet): Touch runter kommt auch bei Text-Widgets als Ereignis 1.

## Build pk7 (2026-10-09)

Effects (A): Foto bestaetigt DLY / RVB oben (UI gedreht), Send-Anzeigen dazwischen. Eingabe-Wrapper vt+0x30
(0x080C64AC): Ereignis 3 mit Ebene-3-Adresse == app+0x28 (bereits gewaehlte Effekt-Zelle) → Seite um (Pad an gleicher
Stelle per 0x63), sonst Stock (0x080865E4). Anzeige "P1" / "P2": passives Text-Widget {124,175,73,20} ueber der Mitte
der Send-Anzeigen ({122,149,37,72}, {161,149,37,72}). Zustand jetzt 0x28 Bytes (ind +0x18, ind2 +0x1C, ind3 +0x20,
tvt +0x24). Unicorn inkl. echter Effects-/Pads-/Mixer-Konstruktoren: 36 Checks gruen.

## Hardware-Test pk7 und Build pk8 (2026-10-09)

pk7 am Geraet: Blaettern funktioniert. Fehler: Pads-Anzeige unsichtbar, Effects-Anzeige "verschluckt" (beides
eigene Text-Widgets ueber Nachbarn, die sich laufend neu zeichnen), Mixer-Feld zeigt die Seite, leuchtet beim Antippen
auf, schaltet aber nicht.
Ursache Mixer: Text-Buttons behandeln Touch in vt+0x10 (druecken, Hervorhebung) / vt+0x18 (loslassen, 0x0805CCA0) und
melden den Klick per 0x0805CC74 als **Ereignis 2 mit dem Befehl aus +0x14** (Feld +0x0C) an den Elternteil (Keys 0xBE,
Stop 0xF1; klickbar nur mit +0x9C != 0). vt+0x30 bleibt dabei unbenutzt.
pk8: Mixer-Feld +0x14 = PAGE_CMD 0x7F01, Wrapper um Mixer vt+0x30 (0x080C0690 → padpages_d_input) faengt Ereignis 2 /
0x7F01 ab. vtable-Kopie und eigene Widgets entfernt. Kopfzeile: die snprintf-Aufrufe fuer "Pads" (0x08076AD4) und "FX"
(0x08076AF0) im Titel-Bau 0x080769E0 → padpages_title ("Pads 1-8" / "FX 9-16"; snprintf 0x080BCD58).
Unicorn: echter Klickweg (echter Mixer-Ctor, echte Loslass-Methode → Ereignis 2 → Wrapper) schaltet um; Titel mit echtem
snprintf. 32 Checks gruen.

## Hardware-Test pk8 und Build pk9 (2026-10-09)

pk8 am Geraet: Umschalten und Anzeigen funktionieren. Fehler: auf Seite 2 zeigen die Kacheln Spielzustand und
Fortschrittsbalken von Pad 1-8 ("Slot 1 gestartet → Balken auf Slot 9"), wirkte wie "startet immer Seite 1".
Ursache: die periodischen Zeichen-Methoden (vt+0x00) fragen den Zustand per 0x08078B94 mit festen Adressen ab:
Pads 0x08084838 und Effects 0x08086B50 (Zeilen 0-1, `movs r7,#0; mov r6,r7` → Thunk loop_rows: r6 = 2·Seite << 4),
Mixer 0x08069DD0 (16 Kacheln, Zeile = Kachelzeile; `orr.w r3, r7, r4` → loop_d_code: (r7 ^ Seite << 5) | Spalte).
Touch-Weg geprueft: Kachel nimmt keine Touches (vt+0x1C = 0x0805D3AC → 0), ihr Innen-Widget +0x70 (Klasse 0x080BFD80)
schon; es meldet Druecken/Loslassen an die Kachel, die Ereignis 3/4 mit **ihrer ID** an die App schickt (Container
0x08070790 → Dispatcher; 3 → 0x0807E2F8: Pad waehlen + Engine-Ausloesung aus der Adresse, 4 → 0x08093838). Ausloesen
ist also ID-basiert und auf Seite 2 richtig.
Unicorn: echte Zeichen-Methoden fragen auf Seite 1 die Pads 9-16 ab (Mixer: sichtbare Zeilen). 35 Checks gruen.

## Pad-Waehler, Build pkA (2026-10-09)

Pad-Waehler (Pop-up der Slot-Seiten, Raster-Icon): Klasse mit Ctor 0x080733B4 (8 Konstruktionen: 0x0806CC48, 0x0806CC58,
0x0806E25E, 0x0807237E, 0x08082602, 0x0808747E, 0x08090BF0, 0x080922DC), vtable 0x080C5C8C. Kacheln (kleine Buttons,
Ctor 0x0805D2DC, 0xAC Bytes) bei +0x34 + Zeile·0x2B0 + Spalte·0xAC, Adresse +0xA4; Text-Widget +0x594; Anker +0x634.
Platzieren 0x080734D6 (Kacheln 64x64, Abstand 66, 264 breit, x auf den Bildschirm geklemmt; am Geraet x = 56).
Eingabe vt+0x30 = 0x08073254: Klick (Ereignis 2, Adresse +8) → 0x118 nach oben, dann zu. "Gewaehlt markieren"
0x080732D6 (Pruefung Zeile < 2, Kachel aus Adresse), "spielt markieren" 0x08073312 (feste Adressen), Marken loeschen
0x080732B0.
pkA: Ctor-Wrapper (Instanzen, Umschalter = Text-Widget mit PAGE_CMD, klickbar, Kind des Waehlers; Liste beim Pads-Ctor
geleert), Platzieren: letzter set_rect (0x08073564) → Umschalter neben die Kacheln auf die breitere freie Seite (max 54),
Eingabe-Wrapper (Klick PAGE_CMD → Seite um, Waehler bleibt offen), Thunks picker_sel_tst / picker_mark0 / picker_mark1,
set_page schreibt die Kachel-Adressen aller Waehler um und markiert neu. Unicorn inkl. echtem Ctor, Platzieren, Klickweg:
40 Checks gruen.

## Hardware-Test pkA und Build pkB (2026-10-09)

pkA am Geraet: Pad 9 startet richtig, Balken richtig. Fehler: Encoder auf Seite 2 springt auf Seite 1 (der Encoder waehlt
nur ueber Pads 1-8; die Auswahl-Erkennung blaetterte hinterher); Umschalter im Pad-Waehler unsichtbar, aber antippbar.
Ursache unsichtbare eigene Widgets (pk6, pk7, pkA): Kinderliste +0x18 Kopf / +0x1C Ende, +0x20 naechstes / +0x24 voriges;
0x08060D30 haengt ans Ende; Zeichnen (0x08060BE6 / 0x08060C32) laeuft vom Ende zum Kopf (zuletzt Angehaengtes liegt
unten), Touch-Suche (0x08060C4C) vom Kopf. Text-Widget-Ctor 0x0805D124: +0x9C klickbar = 1 ab Werk.
Pad-Waehler-Fusszeile +0x594 (Text-Widget): Befehl +0x14 = Waehler +0x5A8 (-1 = kein Besitzer), versteckt (+0x30 =
Waehler +0x5C4) solange unbenutzt; nur 0x0806CB08 nutzt sie ("Pads"/"Seq", Befehl 0x18C, 0x08073350). Kleine Kacheln sind
Text-Widgets (Ctor 0x0805D2DC ruft 0x0805D124), setText wirkt. Pad-Name: 0x080792E8(App, {lit, Adresse}, Puffer) →
Dateiname bei +0 (wie die Kachel-Ruempfe; 0x0805DCDC schneidet die Endung ab).
pkB: Auswahl-Erkennung und Pads-Eingabe-Wrapper entfernt (nur noch Buttons). Waehler: eigenes Seiten-Widget entfernt;
beim Platzieren Kachel-Adressen + Namen (ohne Endung, 7 Zeichen) der Seite, unbenutzte Fusszeile eingeblendet mit
"Pads 1-8"/"Pads 9-16" und Befehl PAGE_CMD. patch.py verweigert eine cave.elf, die aelter als src/ ist (ein
fehlgeschlagener Build hatte ein Image mit alter Cave erzeugt; verworfen, nicht ausgeliefert). 36 Checks gruen.

## Hardware-Test pkB und Build pkC (2026-10-09)

pkB am Geraet (Foto): Waehler-Fusszeile "Pads 9-16" sichtbar und schaltet, aber zu gross; Namen zu breit; Encoder auf
Seite 2 ohne Wirkung; Markierung des Samples im Waehler fehlt auf Seite 2.
Encoder: Pad-Auswahl per Encoder = 0x0807C9FC (Werte 0x64/0x65) → 0x08076CEC(out, app, Auswahl, Richtung): sucht die
Auswahl in den ersten 8 Eintraegen der Tabelle 0x24013C30 (16 Pads zeilenweise, gefuellt von 0x0807FF90) und geht
weiter; Auswahl auf Seite 2 nicht gefunden → Pad auf Seite 1. pkC: padpages_step an 0x0807CA30 / 0x0807CA56 (innerhalb
der Seite, gleiche Reihenfolge; auf Seite 0 bitgleich mit Stock, im Test mit echtem Tabellen-Init geprueft).
UI-Manager: Zeiger in 0x24000DC8 (Heap, 0x08041276), Container +0x280, aktueller Bildschirm Container +0x34.
Pad-Waehler: Besitzer verstecken ihn im Ctor (+0x30 = 1), Elternteil = Besitzer-Bildschirm. pkC: Linkspfeil blaettert,
wenn ein Waehler des aktuellen Bildschirms offen ist (sonst Stock "zurueck"); Fusszeile 22 px, nicht klickbar; Namen 5
Zeichen; Markieren-Aufrufe der Besitzer (7 Stellen, 0x080732D6) gemerkt und nach dem Blaettern neu markiert.
43 Checks gruen.

## Hardware-Test pkC und Diagnose-Build pkD (2026-10-09)

pkC am Geraet: Fusszeile im Waehler unerwuenscht; Encoder auf Seite 2 waehlt weiterhin nichts; gewaehltes Pad im
Waehler nicht markiert.
Befund: 0x0807C9FC (±1, Werte 0x64/0x65) und 0x0807C9C4 (Index in 0x24013C30) und 0x08078F60 sind Faelle der
Engine→App-Nachrichtenschleife (0x0807F3C2, Nachricht aus 0x080939B4, Engine-ID → Adresse); ob der Hardware-Encoder
dort ankommt, ist offen (pkC-Ersatz von 0x08076CEC wirkte am Geraet nicht). Waehler oeffnen: 0x08073392 (Marken
loeschen, +0x63C/+0x640 = zuletzt markierte Adresse neu markieren).
pkD: Fusszeile wieder Stock; der Waehler folgt beim Oeffnen / Markieren (offen auf dem aktuellen Bildschirm) der Seite
des markierten Pads. DIAG: Pads-Kopfzeile "P<Seite> s<padpages_step> i<0x0807C9C4> r<0x0807C9FC> n<Nachricht 0x63>
<app+0x14 hex>" (Zaehler mod 10; Wrapper an 0x0807F7E2 / 0x0807F7EC).

## Hardware-Test pkD und Build pkE (2026-10-10)

pkD am Geraet (Fotos, Kopfzeile vorher/nachher): s, i, r bleiben bei 3 Rastungen stehen, n zaehlt mit; Seite 1:
00 → 03; Seite 2: 23 → 01 (Kopfzeile bleibt P2). Der Encoder laeuft also weder ueber 0x08076CEC noch ueber 0x0807C9C4 /
0x0807C9FC, sondern ueber den Pads-Bildschirm selbst:
- Notify 0x08084154, Nachricht 0x32 (Fall 0x0808438C): msg+0xC (0/2 → Liste +0xD40, sonst +0xD58), 0x0805F114 bewegt
  den Index (+0xD4C / +0xD64), Adresse aus der Liste → Befehl 0x63 (0x080843B4 / 0x080843FC, ueber 0x08060DF8).
- Listen 8 x {0x080BF4CC, Adresse}: 0x24021DC8 zeilenweise (10..13, 00..03), 0x24021E08 spaltenweise (10,00,11,01,...);
  einmal beim Booten gefuellt von 0x080847C4 (Init-Liste 0x080BEC1C); gelesen nur von 0x080840C4 (Auswahl → Index,
  nach 0x63) und 0x0808438C.
- Auf Seite 2 fand 0x080840C4 die Auswahl nicht (Index blieb), der Encoder waehlte aus den Pads 1-8.
pkE: set_page schreibt die Zeilen beider Listen auf die Seite um (Adresse ^ 0x20), kein Code-Patch. DIAG entfernt
(Kopfzeile wieder "Pads 1-8"/"Pads 9-16", Wrapper 0x0807F7E2 / 0x0807F7EC zurueck auf Stock). padpages_step
(0x08076CEC-Ersatz) bleibt: Engine-Pfad, am Geraet nie aufgerufen, auf Seite 0 bitgleich.
Tests: echte Init, echte Suche 0x080840C4 und echter Encoder-Fall in 0x08084154 auf Seite 1 → Befehl 0x63 mit 0x22.

## Drive und Filter 2 (Build pkF, 2026-10-10)

Neue Pad-Parameter (Vorgabe: neue Regler erlaubt, alte Presets → Defaults):

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x08069E4C | Param-Tabelle eintragen | Eintrag 0x1C Bytes, Tabelle 0x32DC Bytes (0x08069F0A) → IDs bis 0x1D0; registriert sind Stock-IDs bis 0x17B | vermutet |
| 0x08069ED4 | Knopf registrieren `(table, id, type, label, [sp] min, [sp+4] max, [sp+8] xml)` | Filter 0xAA: Typ 9, −1000..1000; Res 0x11: Typ 8, 0..1000 | vermutet |
| 0x080B1AEA / 0x080A6CA4 | Engine-Param-Nachricht (Typ 0x39) | ID − 2 > 0x167 bzw. ID > 0x17A → ignoriert; Klasse-B-Handler nimmt Typ 0x39 nicht an | vermutet |
| 0x0807D358 → 0x0807D8E8 | Knopf auf Pad (Ebene 0) | Store-Set im Pad-Record, dann Engine-Nachricht 0x080937F4 (s. o. ignoriert) | vermutet |
| 0x08089548 | Pad-Record-Init | Kapazitaet 64 (0x0808949E); Typ 3: 58 Eintraege, Typ 0x45: 36; Filter 0xAA per 0x0808951E an 0x080896F8 / 0x08089922 | durch Emulation bestaetigt |
| 0x08080030 / 0x0808056C | Preset schreiben / lesen | Writer: alle Store-Eintraege mit XML-Name (0x0806BD28); Reader: Record per Init (Defaults), dann nur vorhandene Attribute setzen | vermutet |
| Seite 0 der 9 Pad-Tabellen | Hauptseite | Level, Pitch, Filter, Res, Pan (5); 0x080C6A1C, 0x080C6C38, 0x080C6EEC, 0x080C7108, 0x080C76C0, 0x080C78DC, 0x080C7AF8, 0x080C7E28, 0x080C8044 | vermutet |

Belegung: 0x1C0 "Filter 2:" (Typ 9, −1000..1000, xml `pkfilt2`, Default 0 = aus), 0x1C1 "Res 2:" (Typ 8, 0..1000,
`pkres2`, Default 500), 0x1C2 "Drive:" (Typ 8, 0..1000, `pkdrive`, Default 0). Registrierung in `interp_register`,
Record-Eintraege per `pad_store_add` (Hook an beiden 0xAA-Stellen), Hauptseite: + Filter 2, Res 2, Drive (8 Eintraege wie
die Sample-Einstellungsseite). Engine sieht die Werte nicht; `filter_process` liest sie aus dem App-Record (wie Interp).
Keine LFO-/Mod-Ziele.
DSP: Kette Crunch → Drive → Filter → Filter 2. Drive: Gain 1 + 15 d², rationale tanh x(27 + x²)/(27 + 9x²) bei |x| ≤ 3
(musicdsp), Makeup Richtung 1/tanh(Gain), erste 10 % blenden von trocken ein. Res-Saettigung (Drive auf Res) entfernt.
Filter-2-Zustand im Filterobjekt: +0x44..+0x5F (g, r, on, Stufe 1; Stock-Reset 0x080B8794 nullt den Bereich → on = 0) und
+0x74..+0x83 (Stufe 2, hinter ostate).
Tests (`tests/test_fidelity.py`, Unicorn): Registrierung, Records Typ 3 / 0x45 mit Defaults, Filter 2 LP/HP, Serie,
Bandpass, Drive (Bypass bei 0, begrenzt, Oberwellen, Makeup), Res linear, Reset, Hauptseiten. Test-Heap nach D2-SRAM
verlegt (lief vorher in den Allocator-Bereich 0x24040000). Nicht emuliert: UI der Hauptseite, Preset-Datei, CPU-Last
bei vielen Stimmen. Status: nicht am Geraet.

## Shift fuer Clips (Build pkG, 2026-10-10)

Wunsch: Shift ±100 ms, Loop-Punkt verschieben; Variante "Loop drehen" (Inhalt rotiert gegen das Raster, Laenge/Sync bleiben).

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x080B5AA8 → 0x080B5728 → 0x080B55AC | Clip-Stimme → Slot lesen → Frames holen | r0 = Pad (Klasse B); Slot = Pad + 0x30 + i·0x70 (4 Slots), Slot+8 int64 = absolute Datei-Position, an 0x080B55AC als r2/r3 | vermutet |
| 0x080B4644 / 0x080B490C | Segment-Start (Clip / Slicer) | Clip: Start = Segment·(Pad+0x1FC), Anzahl Pad+0x240; Slot+8 = Start; Prefetch-Seek 0x080A4624(stream, max(Start−8, 0)) an 0x080B47D2 / 0x080B4B4C; Pad+0x254/+0x250 = Slices | vermutet |
| 0x080A4500 | Stream lesen, ein Kanal `(stream, dst, n, pos, [sp] ch)` | Quelle (+0x20) per vtable+8, sonst Speicher: Ebene +4/+8, Frames +0x10, hinter dem Ende Nullen | durch Emulation bestaetigt |
| 0x080A44C8 | Stream lesen, beide Kanaele `(stream, l, r, n, [sp] pos)` | nur Quelle (gestreamt) | vermutet |
| 0x080A45AC | Frame-Anzahl | Speicher: +0x10; Quelle: vtable+0x14, 0 → 0x10000000 (unbekannt) | vermutet |
| Pad+0x24 | Stream des Pads | | vermutet |

Umsetzung (`src/clipshift.c`, `src/clipshift_thunk.S`, `patches/sound.py`): Parameter 0x1C3 "Shift ms:" (Typ 1, −100..100,
xml `pkshift`, Default 0) auf der Loop-Seite der Clip-Tabellen (0x080C6A1C, 0x080C6C38, Seite 2: Loop Mode, Beat Count,
Quant Size, Sync, Shift). Die 4 Lese- und 2 Seek-Aufrufe bekommen den Pad (r4) als letztes Argument; jede Lesung
[pos, pos+n) innerhalb der Datei wird auf (pos + Shift) mod Frames abgebildet, am Dateiende geteilt; Positionen hinter
dem Ende bleiben (Stille). Slicer-Pads (+0x254) und unbekannte Laenge: kein Shift. 1 ms = 48 Frames (Datei-Frames).
Offen: Prefetch beim Umbruch an der Naht (gestreamte Dateien) springt nicht vor; ob es dort zu einem Aussetzer kommt,
nur am Geraet pruefbar. Tests: Speicher-Stream mit echtem 0x080A4500 (Shift 0 = Stock, ±10 ms, Umbruch, Ende, Slices,
Seek), Loop-Seite.

## Abspiellaenge fuer Clips (Build pkH, 2026-10-10)

Wunsch: Abspiellaenge 1/4 .. 32 Takte in Viertel-Takt-Schritten, Default = ganzer Clip.

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x080B6CE8 | Klasse-B-Param-Handler (Nachricht 0x3A) | IDs ≤ 0xD5 per tbh, sonst nur 0x13F → neue IDs ignoriert | vermutet |
| 0xB4 Beat Count → Pad+0xB80 | Liste Auto, 1..512 | | vermutet |
| 0x76 Sync → Pad+0x220 (int64), Pad+0x1F5 | Tabelle 0x080C4F7C {1024, 4, 2, 1, 0.5, 0.25, 0} Beats × 960 Ticks: Slice 0xF0000, 1 bar 3840 … 1/16 240, None 0 | vermutet |
| 0x080B40FC | Segment-Aufbau | synchron: Segmente = Clip-Ticks / Pad+0x220 → Pad+0x210, Pad+0x240 (+0x244), Laenge Pad+0x1FC | vermutet |
| 0x080B5F2E / 0x080B611A | `ldrd r1, r2, [r6, #0x240]; add r2, r1; cmp` | naechstes Segment < Anzahl → weiter, sonst Ende (Loop: Segment 0, sonst Stop); 0x080B5F2E = synchroner Pfad | vermutet |

Umsetzung: Parameter 0x1C4 "Play Len:" (Liste, 129 Eintraege: Full, 1/4, 1/2, 3/4, 1, 1 1/4 … 32; xml `pkplaylen`,
Default 0 = Full) auf der Loop-Seite der Clip-Tabellen nach Shift. Thunk `clip_segments_thunk` an beiden Stellen: Anzahl
= min(Anzahl, round(Viertel-Takte × 960 / Pad+0x220)), mindestens 1; nur mit Sync (Pad+0x1F5) und nicht Slice / Slicer.
Genauigkeit = Sync-Einheit (bei Sync 1 bar nur ganze Takte). Pad-Record jetzt 63 von 64 Eintraegen.
Tests: Liste, Defaults, Segmentgrenze bei Sync 1/4, 1/16, 1 bar, Rundung, laenger als Clip, Ausnahmen.

## Stretch fuer Clips (Build pkI, 2026-10-10)

Wunsch: Timestretch-Regler in %, ±100 %, gern ueber den Beat Count (quantisiert).

| Micro | Was | Befund | Status |
|---|---|---|---|
| Pad+0xB80 | Beat Count (0xB4: Auto = 0, 1..512) | einziger Leser 0x080B42AC im Clip-Setup 0x080B40FC: ≠ 0 → Clip-Ticks = Beats × 960 (0x080B44A2) | vermutet |
| 0x080B424E..0x080B4258 | Auto: Beats = groesste Zweierpotenz ≤ geschaetzte Beats (r2), dann × 960 | vermutet |
| 0x080B40FC | Clip-Setup | Aufrufer u. a. Loop-Neustart 0x080B5F5A, Param-Aenderungen (0x080B6FF6, 0x080B73F4), Trigger | vermutet |

Umsetzung: Parameter 0x1C5 "Stretch %:" (Typ 1, −100..100, xml `pkstretch`, Default 0) auf der Loop-Seite der Clip-Tabellen
nach Play Len. Thunks an 0x080B42AC (`ldr.w r3, [sl, #0xb80]`) und 0x080B4258 (`vmov s15, r2`): Beats → round(Beats /
Speed), Speed = 1 + p/100 (p > 0) bzw. 1 / (1 − p/100) (p < 0), also +100 % doppelt, −100 % halb so schnell; 1..512 Beats,
Auto bleibt Auto (nur die Schaetzung wird skaliert), Slicer unveraendert. Quantisiert auf ganze Beats wie Beat Count.
Wirkt ab dem naechsten Setup (Trigger / Loop-Neustart); die Tempo-Anzeige der UI (aus Beat Count) zeigt den Stretch nicht.
Pad-Record jetzt 64 von 64 Eintraegen (voll).
Tests: Registrierung, Record, Loop-Seite, beide Thunks (0, ±100 %, ±50 %, Auto, Grenzen, Register erhalten).

## Hardware-Test pkI, Clip-Parameter und Build pkJ (2026-10-10)

pkI am Geraet: Shift gut; Play Len geht, Zusammenspiel unklar; Stretch ohne Wirkung.
Ursache Stretch: bei Beat Count Auto skalierte der Thunk an 0x080B4258 nur das Rundungsraster (2^k Beats), die
geschaetzte Laenge wurde danach wieder auf fast denselben Wert gerundet (0x080B447E..0x080B4472).
pkJ: Thunks an 0x080B42AC / 0x080B4258 entfernt; stattdessen vor 0x0809F1F8(out, &Ticks, Tempo, 48000) an 0x080B42A8
(Auto) und 0x080B44DA (Beat Count): Ticks → round(Ticks / 960) Beats → Stretch → × 960. Tests: echte Umrechnung 0x0809F1F8
bei 120 BPM (16 Beats = 384000 Frames, +100 % = 192000).

Wiedergabe-Modell Clip (vermutet, aus dem Code): Slot-Rate = Datei-Rate (Pad+0x1F0) × Tastatur-Tonhoehe (0x080B4644) ×
Pitch (0x080B5728, 0x0809F45C); das Tempo geht nicht in die Rate ein. Mit Sync startet jedes Segment (Sync-Einheit) an
der Datei-Position, die zum aktuellen Beat gehoert (Segment × Pad+0x1FC = Datei-Frames / Segmente); so folgt der Clip dem
Song-Tempo ohne Tonhoehenaenderung, bei Abweichung mit Spruengen an den Segmentgrenzen. Beat Count bestimmt diese
Zuordnung, Stretch skaliert sie.

| Param | Feld | Wirkung |
|---|---|---|
| Loop Mode 0x6F (Aus/An) | Pad+0x1F4 | Ende: An → Segment 0, Aus → Stop |
| Launch Mode 0x75 (Trigger/Gate/Toggle) | Pad+0x1F8 = Wert + 1 | Ende bei Trigger (1) → Stop, auch mit Loop An (0x080B5F44) |
| Beat Count 0xB4 (Auto, 1..512) | Pad+0xB80 | Clip-Laenge in Beats → Ticks (Auto: Schaetzung aus Laenge und Tempo, gerundet) |
| Quant Size 0x2A (8 bars .. 1/16, None) | Pad+0x218 Ticks | Start-Quantisierung; Sync aktiv nur wenn Quant ≠ None und Sync ≠ None (Pad+0x1F5, 0x080B6FD4) |
| Sync 0x76 (Slice, 1 bar .. 1/16, None) | Pad+0x220 Ticks | Segment-Einheit (Neuausrichtung); Slice = Slicer |

## Sync 1/32 und Ausblenden (Build pkK, 2026-10-10)

Wunsch: Stretch / Play Len ausgrauen, wenn unwirksam; Sync-Raster 1/32.

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x0806AB7E | Registrierung Sync (0x76): Liste 0x080C4770, 7 Eintraege | Slice, 1 bar, 1/2, 1/4, 1/8, 1/16, None | durch Emulation bestaetigt |
| 0x080C4F7C | Beats je Sync-Index {1024, 4, 2, 1, 0.5, 0.25, 0} | Leser: Klasse-B-Handler 0x080B7386 (Literal 0x080B74E4), Preset-Altformat 0x080807B6 (sucht 7) | vermutet |
| 0x08076D8C | Seitenaufbau `(app, msg, list, ..)` | 7 Aufrufer (0x08085312, 0x0808542C, 0x08087D82, 0x08087DE8, 0x08088110, 0x0808814A, 0x080910DE) | vermutet |
| 0x080836A4 / 0x080836C8 | Liste: Eintrag anhaengen / per ID entfernen | Liste: +0 Anzahl (max 0x30), Eintrag 12 Byte, ID +4 (h), Wert +0xC; Stock blendet so aus (Delay/Beat Sync 0x08076F48) | vermutet |
| 0x08076D54 | Pad-Record zu msg (Adresse +4) | | vermutet |

Ein Ausgrauen gibt es im Seiten-Framework nicht (nicht gefunden); umgesetzt ist Ausblenden wie im Stock.
Umsetzung: `sync_register` (Hook 0x0806AB7E) registriert 8 Eintraege: Stock-Zeiger + "1/32" am Ende (alte Preset-Indizes
bleiben gueltig, 6 = None). `sync_beats[8]` (… 0, 0.125) per Literal 0x080B74E4 → 1/32 = 120 Ticks. `clip_page` (alle 7
Aufrufer, EXCLUSIVE): nach dem Stock-Aufbau, wenn die Liste Play Len / Stretch enthaelt und Quant Size = None (8) oder
Sync = Slice (0) / None (6): beide entfernen. Ob die UI die Seite beim Aendern von Sync / Quant sofort neu aufbaut, ist
nicht geprueft (Stock-Beispiel Delay legt es nahe).
Tests: Liste, Literal, echter Handler 0x080B6CE8 fuer alle 8 Sync-Werte (Ticks), Seite mit echtem Record und echter
Entfernen-Funktion (synchron / 1/32 / Quant None / Sync None / Slice).

## Hardware-Test pkK, Stretch sofort (Build pkL, 2026-10-10)

pkK am Geraet: Stretch weiter ohne Wirkung; Shift "macht vermutlich etwas, wirkt verschluckt".
Emulation des echten Clip-Setups 0x080B40FC (falsche Quelle: 384000 Frames, 48 kHz, 120 BPM, Sync 1/4): Stretch wirkt dort
(0: 16 Segmente, je 24000 Datei- / 24000 Ausgangs-Frames, Pad+0x258 = 120 = Clip-Tempo; +100 %: 8 × 48000 / 24000, 60).
Ursache: synchrone Clips fuehren das Setup beim Loop-Neustart nicht aus (0x080B5F4E: Pad+0x1F5 ≠ 0 → 0x080B630A); es
laeuft nur bei Sync / Quant / Beat Count aus der UI (und Laden), und die Engine sieht Stretch nie.
pkL: `pad_param_set` (Hook 0x0807D91A, Store-Set im Pad-Zweig von 0x0807D358): nach dem Speichern von Stretch die
aktuelle Sync des Pads per 0x080937F4(0x24022978, row<<8|col, 0x76, Wert, 0, 0) an die Engine (wie eine Sync-Aenderung,
Nachricht 0x39) → Setup sofort neu. Pad+0x258 (Clip-Tempo) folgt dem Stretch; ob die UI-Tempo-Anzeige daraus liest: offen.
Shift: wirkt nur auf die Lesepositionen, die Sync-Neuausrichtung sieht ihn nicht (kein Verschlucken im Code gefunden);
+s liest s ms weiter in der Datei → Transienten kommen s ms frueher.
Tests: Setup-Emulation (0, ±100 %, Beat Count fest und Auto), Nachsenden (Adresse, Sync-Wert, andere Parameter nicht).

## Hardware-Test pkL, Stretch am Segment-Start (Build pkM, 2026-10-10)

pkL am Geraet: Stretch weiter ohne Wirkung. Emulation des echten Segment-Starts 0x080B490C nach echtem Setup:
Segment k startet bei k × Pad+0x1FC (Slot+8 = 72000 fuer k = 3 bei 24000), Prefetch-Seek Start − 8, Slot+0x28 = 23744
Ausgangs-Frames (24000 − 0x100). Mit Stretch im Setup (pkJ–pkL) verdoppelt sich die Position korrekt → das Modell stimmt;
am Geraet wird das Setup fuer den laufenden Clip offenbar nicht neu gerechnet (auch nicht ueber das Nachsenden von Sync;
Ursache nicht gefunden, nicht verifiziert).
pkM: Setup-Eingriffe (0x080B42A8 / 0x080B44DA) und das Nachsenden (0x0807D91A) entfernt. Stattdessen live:
- 0x080B4A68 `vmul.f32 s16, s15, s16` (Index × Segmentlaenge) → × Speed (`clip_pos_thunk`, Pad in r4)
- Schleifengrenze (`clip_segments`): Anzahl / Speed, gerundet, dann Play Len
- 0x080B49B4 `ldr.w r3, [r4, #0x240]` (Test "letztes Segment") → Anzahl / Speed (`clip_last_thunk`)
Stretch ist damit stufenlos (nicht mehr auf Beats gerundet) und wirkt ab dem naechsten Segment.
Tests: echter Segment-Start (0, ±100 %, +50 %), Schleifengrenze mit Stretch und Play Len, Letztes-Segment-Thunk.

## Hardware-Test pkM und Diagnose-Build pkN (2026-10-10)

pkM am Geraet: Stretch weiter ohne Wirkung. Da Play Len (gleiche Funktion `clip_segments`) wirkt, liest die
Engine Stretch vermutlich als 0 oder die Segment-Pfade laufen anders. Records in Emulation: Typ 3 64/64, Typ 0x45 42/64,
0x1C5 vorhanden; Typ-1-Werte roh gespeichert (Steps 0x46 Default 16).
pkN (DIAG): Pads-Kopfzeile "U<Stretch im Record des gewaehlten Pads> E<Stretch, zuletzt von der Engine gelesen>
s<Aufrufe Schleifengrenze> p<Aufrufe Segment-Start-Position> <Anzahl stock>><Anzahl unsere>" (Zaehler mod 10, Anzahl −1 =
nicht synchron). Engine-Seite in 0x2406C180 (`clipdiag`, src/clipshift.c).

## Hardware-Test pkN, pkO verworfen, Build pkP (2026-10-10)

pkN am Geraet (Fotos, Clip-Pads "RC000…"): "U0 E0 s.. p.. 88>16". Stretch steht nicht im Record (U0), die Engine liest 0;
Schleifengrenze und Segment-Start laufen (s, p zaehlen; 88 Segmente, Play Len → 16). Am Geraet: Stretch springt beim
Verlassen der Ansicht / Neustart auf 0; Shift (gleicher Typ 1) wird gespeichert.
pkO (Shift als Liste, Stretch als Typ 9) verworfen, nicht ausgeliefert: der Regler-Typ ist es nicht.
Verbleibender Unterschied: Stretch ist der letzte (64.) Eintrag; Kapazitaet 64 (0x0808949E, nur bei der ersten
Allokation gesetzt: 0x0808954E in 0x08089548, 0x08089F98 in 0x08089F8C), Typ 3 in Emulation genau 64. Warum am Geraet ein
Eintrag mehr gebraucht wuerde, ist nicht gefunden (Init ohne Bedingungen; Add nur in 0x08089548 / 0x08089E04).
pkP: Kapazitaet 64 → 72 an beiden Stellen (`movs r1, #0x40` → `#0x48`, +64 Byte je Record). DIAG-Kopfzeile jetzt
"U<Record> E<Engine> c<Eintraege>/<Kapazitaet><+/- Stretch im Record> s<Aufrufe> <Anzahl>><unsere>".

## Hardware-Test pkP, Ursache Stretch, Build pkQ (2026-10-10)

pkP am Geraet: "U0 E0 c64/72+ s.. 88>16": Stretch steht im Record, bleibt aber 0. Ursache: der Parameter-Befehl
0x0807D358 faengt die ID 0x1C5 selbst ab (0x0807D37E: `movw r2, #0x1c5; cmp r4, r2` → app+0x8007 = (Wert ≠ 0), Ende, kein
Store-Set). Weitere Stock-Verwendungen von 0x1C5: 0x0806E614, 0x0806E664, 0x080774E6, 0x0808234A, 0x0808245A. Freie IDs
geprueft (mov/cmp-Immediates im Code): 0x1C0–0x1C4, 0x1C6 unbenutzt; benutzt u. a. 0x1BF, 0x1C5, 0x1CC.
pkQ: Stretch = 0x1C6 (xml `pkstretch` bleibt), Diagnose entfernt, Kapazitaet 72 bleibt (8 Eintraege Reserve).
Test: keine mov/cmp-Immediates der neuen IDs im Stock-Code (findet 0x1C5 an den 6 Stellen).

## Smooth Time-Stretch (WSOLA) und Lastanzeige (Build pkR, 2026-10-10)

pkQ am Geraet: Stretch (ID 0x1C6) funktioniert.

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x080B55AC | Slot lesen + umrechnen `(pad, -, int64 pos, s0 Rate, [sp] n, &verbraucht, &frac, Quellpuffer, Zielpuffer, &Ergebnis)` | einziger Aufrufer 0x080B58FC (Slot-Leser 0x080B5728; frac = Slot+0x1C, Position Slot+8); Rate 1 & frac 0: direkt lesen, sonst n·Rate+8 lesen + 0x0809FF64 | vermutet |
| Puffer | +0 Kapazitaet, +4 Frames (0 = Kapazitaet), +8 L, +0xC R, +0x10 still, +0x11 stereo | 0x080A321C mono setzen (→ L), 0x080A32D4 stereo setzen (L, R), 0x080A3288 lesen | vermutet |
| 0x080A4650 | Stream stereo (+0x1C) | Stock: stereo → 0x080A44C8, sonst 0x080A4500 Kanal 0 | vermutet |
| 0x08040E90 → 0x080423CC | audioTask (FreeRTOS, Def. 0x080BED8C, Prio 3, Stack 0xA00) | wartet auf DMA-Haelfte, dann 0x08093D44 (Eingang) und 0x08093E48 (Engine + Ausgang), je 2 Aufrufstellen | vermutet |
| 0x08070660 | Statusleiste zeichnen | +0x34 "%d:%d" (Takt:Schlag), +0x13C Titel, +0x194 Fortschritt, +0x8C rechts: Aufnahme "%dMB" / "FULL" / "" (0x08070748) | vermutet |

Umsetzung pkR:
- `src/stretch.c`: `clip_render` (Hook 0x080B58FC, EXCLUSIVE). Smooth: Lesetempo c = Pad+0x1FC × Stretch-Speed / Pad+0x204
  (Datei-Frames pro Ausgangs-Frame; Segmente schliessen nahtlos), Grains 2 × 512 Frames mit Hann-Fenster, 50 % Overlap,
  gelesen mit der Pitch-Rate (s0); neuer Grain-Start per WSOLA: ±256 Frames, grob dezimiert (8) mit 64er-Vorlage, fein
  ±32 Frames mit 64er-Vorlage, Kriterium c²/E mit Vorzeichen. Lesen ueber clip_read1/2 (Shift gilt). Grain-Zustand je
  Pad × Slot (64 × 40 Byte) ab 0x2406C400; Neustart bei Positionssprung (Segment-Start). Suchpuffer ~1,6 KB auf dem
  audioTask-Stack.
- Parameter 0x1C7 "Str Mode:" (Liste Auto / Jump / Smooth, xml `pkstretchmode`, Default Auto = Smooth bei Stretch ≠ 0)
  auf der Clip-Loop-Seite nach Stretch; mit Play Len / Stretch ausgeblendet, wenn nicht synchron. Record 65 / 72.
- `src/load.c`: DWT-Zyklenzaehler (TRCENA, CYCCNTENA); Last = (0x08093D44 + 0x08093E48) / Abstand der Blockstarts,
  geglaettet (0,02), Spitze mit Abfall; Anzeige "34%" (Spitze > 90 %: "34%!") im leeren Fall von +0x8C (0x08070748).
Tests (Emulation, echte Lesefunktionen, Speicher-Stream 1 kHz): Jump = Stock; Smooth +100 % / −50 % / Tempo-Folgen 1,5× /
Pitch-Rate 2: Vorschub exakt, Tonhoehe gleich, Pegel stabil, keine Klicks; Lastanzeige 40 % bei 4000 / 10000 Zyklen.
Aufwand (Instruktionen pro 128-Frame-Block): Stock ~1100, Smooth ~28500 (≈ 11 M/s je Stimme). Hoerproben (synthetisch)
in out/stretch_preview (nicht im Repo).

## Hardware-Test pkR, Lastanzeige (Build pkS, 2026-10-10)

pkR am Geraet: Smooth-Stretch funktioniert; die Lastanzeige ist nicht zu sehen.
Ursache: Literale vertauscht. 0x08070660: Wert = app+0xDCC8 (Aufnahmespeicher, im Leerlauf −1, gesetzt 0x08075766);
< 0 oder ≥ 256 MB → "" (Setzen an 0x08070754), < 1 MB → "FULL" (0x08070748), sonst "%dMB". Der Hook sass auf "FULL".
Layout der Statusleiste (Ctor 0x080704C0, Emulation): +0x34 Takt:Schlag {10, 222, 100, 20}, +0xE4 {80, 222, 200, 20},
+0x8C Aufnahme-Text {80, 222, 48, 20} (Ausrichtung +0xDF = 6), +0x13C Titel, +0x194 Fortschritt {256, 224, 63, 12};
App-Flag app+0x7FF8 (bereit) wird einmal gesetzt (0x080751F8), Texte also bei jedem Zeichnen.
pkS: Hook an 0x08070754 (leerer Fall), Feld nach rechts {280, 222, 39, 20}.

## Reverb-Typen (Build pkT, 2026-10-10)

| Micro | Was | Befund | Status |
|---|---|---|---|
| 0x080A9AFC | Reverb-Ctor (Objekt 0x1A0, Engine-ID 0x30100 an 0x08095D96) | Param-Slots Decay +0xB0, Damping +0xEC, Predelay +0x128, Wet +0x164; Zustand +0x58 (0xB0 Byte) | vermutet |
| 0x080A9C94 | Plate-Zustand init | 12 Puffer an Zustandswort 8, 11, 14, 17 (512), 20, 25 (1024), 30, 33, 37, 39, 41, 43 (8192) = Blackbox-Layout; ≤ 0x42CC Byte im DTCM (0x08042DFC), sonst 0x08042DC0 | durch Emulation bestaetigt |
| 0x080A9690 | Reverb-Prozess | state[0] = Decay × 0,93 (0x080A99D8), state[1] = Damping, Predelay 12000 × x + 256; Kern-Aufruf 0x080A9912: 0x080A9EC4(state, in, outL, outR, [sp] n) bei 29,8 kHz (0x080A9C74) | vermutet |
| 0x080A9EC4 | Plate-Kern (Dattorro), einziger Aufrufer 0x080A9912 | Konstanten 0,625 / 0,7 bei 0x080A9EB0 | vermutet |
| app+0x2200 + Zeile × 0x18 | FX-Zellen-Records (0x0807D854) | Reverb = Zeile 1 (0x310) = app+0x2218, Typ 0x44, Defaults 0x08089AA0: Decay 600, Predelay 40, Damping 500 | durch Emulation bestaetigt |
| 0x08076EE0 → 0x08083744 | Seitenaufbau FX-Zelle | Liste = alle Record-Eintraege in Reihenfolge (max 0x30) | vermutet |
| 0x178 "FX2" (Delay/Reverb) | Liste, Registrierung 0x0806B89A | sonst unbenutzt; globaler Handler 0x080A6C3C: Default-Fall | vermutet |

Umsetzung (`src/reverb.c`, `src/reverb_thunk.S`, `patches/reverb.py`): 0x178 → "Type:" Plate / Room / Hall / Chamber
(Default Plate), zehn Regler 0x191–0x19A (Typ 8, 0..1000): Size, Diffusion, Bass Mult, Crossover, Mod Rate, Mod Depth,
Early, Width, Hi Cut, Lo Cut; im Record nach Type, Decay, Predelay, Damping (Hooks 0x08089AA8 / 0x08089ABE), bei Plate
ausgeblendet (clip_page). Kern-Hook 0x080A9912 (EXCLUSIVE). Hall / Chamber: eigener Tank nach Griesinger/Dattorro
(Dattorro 1997), Zwei-Band-Decay, modulierte Allpaesse, ER, Hi/Lo Cut; Room: blackbox-mod-FDN mit den neuen Reglern.
Zustand 0x2406D000 (Objekt-Zeiger 0x2406CFF0). Patch-RAM-Belegung: C000 Micro-Patcher, C100 PARK, C110 Pad-Seiten,
C1C0 Last, C400–CDFF WSOLA, CFF0 / D000 Reverb.
Tests (`tests/test_reverb.py`, echter Init und Plate-Kern): Plate bitgleich, Impulsantworten (Hall RT60 0,55 / 3,6 s bei
Decay 30 / 70 %), L/R-Korrelation ≈ 0, Stabilitaet bei vollem Decay, Bass Mult, Early, Seitenfilter. Aufwand: Plate
~9,5 M Instr./s, Hall/Chamber ~20 M, Room ~32 M (bei 29,8 kHz). Hoerproben out/reverb_preview (nicht im Repo).

## FX3: dritter Send auf eigenem Bus (Build pkU, 2026-10-11)

Wunsch: zweites Reverb parallel (Drums / Synths), eigener Send; Effects-Seite: Linkspfeil fuer die Pad-Seiten, zweites
Tippen auf RVB schaltet die rechte Zelle RVB ↔ FX3.

| Micro | Was | Befund | Status |
|---|---|---|---|
| Engine +0x150E4 | 18 Stereo-Busse × 20 Byte (0x080A82B8); weitere Arrays +0x1524C (0x080A82E0, Pad-Scratch 0/1/2), +0x1588C (0x080A82CC) | alle mit 128-Frame-Puffern (Ctor 0x08094C48, Puffer-Ctor 0x080A310C), pro Block still + Laenge (0x080A82F4) | vermutet |
| Busse | 0–3 Out1/2 … Out7/8, 4–11 Out1 … Out8 (Liste 0x77), 0xD FX1, 0xE FX2, 0xF / 0x10 Sonderfall im Treiber; **0xC und 0x11 unbenutzt** | | vermutet |
| 0x08096530 | Block-Treiber: Wurzel-Knoten engine+0xFAF8 (vtable+0xC), dann Bus 0 += 0xD (0x08096CF2), += 0xE (0x08096D04), Ausgaenge | | vermutet |
| 0x08095CE8 | Graph-Aufbau: Knoten per laufendem Zaehler (+0x14) wiedergefunden oder angelegt; Reverb 0x30100 / Bus 0xE, Delay 0x30000 / Bus 0xD | nicht benutzt (FX3 ohne eigenen Knoten) | vermutet |
| Sample-Pads 0x080B10BE | Sends pad+0x558 / +0x55C; „ein Send an“ 0x080B13E0; Scratch → Sends → Ausgang 0x080B2600 | | vermutet |
| Clip-Pads 0x080B74F4 | Sends pad+0xB84 / +0xB88 (Setter 0x080B72D6 / 0x080B72B8, Wert / 1000 → 0x080A04C0); „ein Send an“ 0x080B7D8C; Endmischung 0x080B8046 | | vermutet |
| Puffer | 0x080A33EC(Ziel, Quelle, s0 Pegel) addieren; 0x080A3328 addieren; 0x080A3288 lesen (still → Nullen) | | durch Emulation bestaetigt |
| 0x08042DC0 / 0x08042E44 | Bump-Allokator ohne Freigabe (Zeiger 0x24000088, Grenze 0x2400008C, oben Samples per 0x08042E58), freier Platz | Ueberlauf → 0x08040578 | vermutet |
| Effects-Bildschirm | Zellen DLY +0xD34 / RVB +0xED4 (ID +0x38, Beschriftung im Ctor 0x080869E2 per 0x0805DCDC), Send-Anzeigen +0x1554 / +0x1600, Encoder-Regler +0x1BE8 / +0x1EC0 (0x08073810), gewaehltes Pad +0x1BD4; 0xBC an 0x08086336, 0x08086376, 0x080864BE, 0x080864CE, 0x08086542 | | vermutet |

Umsetzung (`src/fx3.c`, `src/fx3_thunk.S`, `patches/fx3.py`, `src/padpages.c`):
- Pad-Parameter 0x1C8 "FX3 Send:" (Typ 8, xml `fx3send`), Pad-Record 66 / 72.
- Send-Abfragen 0x080B13E0 / 0x080B7D8C: s15 = 1,0 wenn FX1 0 und FX3 an; Endmischung 0x080B2600 / 0x080B8046: zuerst
  Scratch × Kurve(FX3) → Bus 0xC.
- Treiber 0x08096D04: nach Bus 0 += 0xE: Bus 0xC → Tiefpass, auf 29,8 kHz, Predelay, Reverb-Instanz 2
  (`reverb_run_record`, Zustand RS2 0x2406D100, eigener Plate-Zustand), linear zurueck auf 48 kHz, in Bus 0; 30 s
  Nachlauf. Einstellungen: FX-Record Zeile 2 (app+0x2230, Typ 0x44, angelegt beim Start / Umschalten).
- Speicher: Plate-Zustand + 12 Puffer (~210 KB) + Predelay 64 KB beim Bau des Effects-Bildschirms, nur bei > 4,5 MB frei.
- UI: Linkspfeil auf dem Effects-Bildschirm (ID 0x30) = Seitenwechsel; zweites Tippen auf die gewaehlte RVB-Zelle →
  FX3 (ID 0x320, Beschriftung, Befehl 0x111, Kacheln und Sends neu), auf FX3 → zurueck; DLY wieder Stock. Send-IDs
  0xBC → 0x1C8 im FX3-Modus (pstate +5).
Tests (`tests/test_fx3.py`, `tests/test_padpages.py`): Init / Speichergrenze, Record, Send-Abfrage, Pad-Mischung,
Effekt (Plate / Hall), Ruhe, Umschalten, Send-ID-Thunks, Linkspfeil.
Offen: ob FX-Record Zeile 2 im Preset gespeichert wird; Pegel FX3 gegenueber RVB (kein Wet-Regler); Last am Geraet.

## Reverb-Pegel (Build pkV, 2026-10-11)

pkU am Geraet: Hall etwas leise. Send-Effekte geben nur das Nasssignal zurueck (der Trockenanteil bleibt im
Pad-Ausgang). Messung (Rauschen, Decay 40 / 70 %, stationaerer RMS gegen das Plate): Hall / Chamber −3,2 dB, Room −9 dB.
pkV: Ausgleich TANK_GAIN 1,45, ROOM_GAIN 2,8 (alle Typen jetzt ±0,2 dB zum Plate, Test); neuer Regler 0x19B "Level:"
(−12 … +12 dB, 500 = 0 dB, xml `rvblevel`) fuer alle Typen inkl. Plate (nach dem Kern skaliert), bei Plate sichtbar;
gilt fuer RVB und FX3. Records jetzt 15 Eintraege.

## FX3 auf FX-Zeile 3, Rechtspfeil (Build pkW)

Fehler bis pkV: FX3 lag auf Zelle 0x320 / Record app+0x2230 = **Master-EQ** (Typ 0x36, Init 0x0807ACB2 ff.); FX3 las
Decay usw. aus dem EQ-Record, der Rechtspfeil zeigte die EQ-Seite.

| Adresse | Was | Beleg | Status |
|---|---|---|---|
| app+0x2200 + Zeile·0x18 | FX-Records: 0 Delay (0x26), 1 Reverb (0x44), 2 Master-EQ (0x36), 3 leer (Typ 0) | Init-Folgen 0x0807AC8E.. | vermutet |
| 0x08078180, 0x0807ACC4, 0x0807ACEA, 0x0807C3DE, 0x08080F74, 0x0808AE36, 0x0808B2BE, 0x0808E2F0 | `movs r3,#0` = Typbyte fuer die Init (0x08089FC4) von Zeile 3 (app+0x2248 bzw. +0x1840+0xA08); einzige Nutzer von Zeile 3 | Suche nach 0x2248 / 0xA08 | vermutet |
| 0x08083800 | Rechtspfeil-Tabelle (Ereignis 0xC, `ldr pc` Wortetabelle, Index Bildschirm−2): 0x30 → 0x08083952 (Bildschirm 0x23), 0x23 → 0x0808395E (Bildschirm 0x14) | Disassembly | vermutet |
| 0x0808EEDC | Bildschirm zeigen (app, id, a, b); 0x23: Nachricht 0xB6 mit app+0x28 (FX-Zellen-Seite), 0x14: Nachricht 0xB2 mit app+0x28 (Inhalt nicht bestimmt) | tbh-Fall 0x0808F392 / 0x0808F1D6 | vermutet |
| 0x0807B20C | Zelle waehlen (app, msg): app+0x28 = msg+4, Nachricht 0x112 ueber app+0x2C; synchron | Disassembly | vermutet |
| 0x08076ED4 | Seitenaufbau FX-Zelle: Zeile = (id>>4)&0xF, ≤ 4, Record app+0x2200+Zeile·0x18 | Disassembly | vermutet |
| 0x0807D846 | FX-Regler: Store-Set im Zeilen-Record, dann Engine-Nachricht 0x39 an Adresse Ebene/Zeile/Spalte | Disassembly | vermutet |
| 0x08095440 | Engine: Nachricht 0x39 sucht den Knoten per Adresse in der Liste, ohne Treffer Ruecksprung → 0x330 (kein Knoten) wird verworfen | Disassembly | vermutet |
| 0x08095CE8 | Graph-Aufbau fest (Reverb-Knoten per Literal), nicht aus den Records → Zeile 3 Typ 0x44 erzeugt keinen Knoten | Disassembly | vermutet |

pkW: die acht Typbytes → 0x44 (Zeile 3 ist ueberall ein Reverb-Record; `fx3_record_ensure` bleibt Rueckfall), FX3 =
Zelle 0x330 / app+0x2248. Rechtspfeil auf dem Effects-Bildschirm mit gewaehltem FX3 → Stock-Seite 0x23 fuer 0x330
(FX3-Regler). Hook `fx3_right` am BL 0x08083964: auf Seite 0x23 mit app+0x28 = 0x330 → 0x0807B20C(0x320) + Seite 0x23
(Master-EQ), sonst Stock (0x14). Folge: von FX3 aus ist Seite 0x14 nicht erreichbar; nach dem EQ ist die Auswahl 0x320
(keine Kachel markiert, Rechtspfeil auf Effects fuehrt dann direkt zum EQ). Titel der Seite 0x23 fuer 0x330 nicht
verifiziert. Alte Presets: Zeile 3 bekommt beim Laden die Reverb-Defaults (vermutet; ein Preset mit Zeile-3-Typ 0 nicht
geprueft). Test: test_fx3.py (Typbytes im Image, fx3_right beide Faelle), test_padpages.py (0x330).

## Master-Sektion: Kompressor- und Distortion-Seite (Build pkX)

Wunsch: Tools, Linkspfeil = Kompressor-Seite (Threshold, Attack, Release, Gain), Rechtspfeil = Master-Distortion.

| Adresse | Was | Beleg | Status |
|---|---|---|---|
| 0x080839BC | Tools-Taste: Bildschirm 0x25 → 0x33 → 0x32 → 0x25 (von anderen: 0x25) | Disassembly | vermutet |
| 0x0808F3D4 | Bildschirm 0x25 = Settings-Seite: Nachricht 0xB6, Seitencode 0x40 | tbh-Fall | vermutet |
| 0x08076D8C | Seitenbauer: Codes 0x40 / 0x41 / 0x42 aus Tabellen (0x080C6E6C: 0x61, 0x62, 0x9C, 0x96, 0x7F, 0xC2, 0x59, 0x5A, 0xC3, 0xB5, 0x17B), Werte aus app+0x7FD0 | Disassembly | vermutet |
| app+0x7FD0 | Settings-Store (globale Werte, u. a. 0x96 `globcomp`), Init 0x08089E04: Kapazitaet 64, 36 Eintraege, letzter Add 0x17B an 0x08089F78; Init-Aufrufer 0x0807856A, 0x0808B39C, 0x0808B3A4 | Disassembly, Unicorn (echte Init) | durch Emulation bestaetigt |
| 0x0807D3A6 | Regler-Handler: Code 0x40 (bzw. 0x140) → Store-Set in app+0x7FD0 mit der ID | Disassembly | vermutet |
| 0x08083800 | Rechtspfeil-Tabelle: Eintrag Bildschirm 0x25 = 0x080837E9 (nichts) | Wortetabelle | vermutet |
| 0x080839FC | Linkspfeil-Tabelle (Index Bildschirm−4): 0x25 / 0x32 / 0x33 = nichts | Wortetabelle | vermutet |
| 0x0805EACC | Wert-Formatierer (Typ +0x31): 7 = ±x.x dB (Wert in 1/1000 dB), 8/9 = %, 10 = Frequenz ueber 0x080A01BC, 11 = Q, 1 = Ganzzahl; 14/15/16 (tote Kompressor-Regler 0x10F..0x113) nicht sinnvoll | Disassembly, Typen per Emulation der Registrierung 0x08069F00 | vermutet |
| 0x10F..0x11B | Stock-Kompressor-Regler (C Attack, C Release, C Thresh, C Ratio, ...) registriert, aber in keinem Record → auf der Micro tot | Registrierung emuliert, keine Store-Adds | vermutet |
| 0x08096D1A | Block-Treiber: nach FX-Ruecklaeufen (0x08096D04) und Objekt vt+0xC (vermutlich Master-EQ): Flag engine+0x28CC0 → Kompressor | Disassembly | vermutet |
| 0x08097056 | Kompressor `0x080B9B04(engine+0xFB38, engine)`; Objekt: +0x428 Thresh dB, +0x42C Ratio, +0x430 Makeup dB (Float), +0x448 Attack, +0x44C Release (Samples, Rampenlaengen des Gain-Glaetters +0x434); Ctor 0x080B9D88: −4 dB, 4:1, −4 dB, 480, 12000 | Disassembly; deckt sich mit bitbox-micro-fw-patch (Guards gleich) | vermutet |

Umsetzung (`src/master.c`, `src/master_thunk.S`, `patches/master.py`):
- Neue IDs (in keinem Stock-Befehl als Konstante, Test): Kompressor 0x1A1 "Threshold:" (Typ 7, −48..0 dB, Default −4),
  0x1A2 "Ratio:" (Typ 1, 1..20, 4), 0x1A3 "Attack ms:" (Typ 1, 1..200, 10), 0x1A5 "Release ms:" (Typ 1, 10..2000, 250),
  0x1A6 "Gain:" (Typ 7, −12..+24 dB, −4); Distortion 0x1A7 "Dist Type:" (Liste Off/Soft/Hard/Fold/Tube, Off),
  0x1A8 "Drive:" (Typ 7, 0..36 dB, 12), 0x1A9 "Tone:" (Typ 10, 1000 = offen), 0x1AB "Mix:" (Typ 8, 100 %), 0x1AC "Level:"
  (Typ 7, −24..+12 dB, 0). xml `pkc*` / `pkd*`. Registriert aus interp_register, Store-Eintraege per Hook 0x08089F78
  (46 von 64). Defaults = Stock-Kompressor, also klanglich unveraendert bis man dreht.
- Kompressor: Hook 0x08097056 schreibt die Werte jeden Block ins Objekt, dann Stock-DSP. Ein/Aus bleibt `Compressor:`
  (0x96, auch auf der Kompressor-Seite).
- Distortion: Thunk 0x08096D1C (`ldrb.w r3,[sl,r3]`, Bus 0 = r4), laeuft auch bei Kompressor aus. 2x Oversampling mit
  31-Tap-Halbband (Kaiser 7), Latenz 15 Samples (Dry gleich verzoegert), Tube mit DC-Blocker ~8 Hz, Tone = Einpol-
  Tiefpass ueber die Stock-Cutoff-Kurve, Drive / Mix / Level pro Sample gerampt. Zustand 0x2406D410 (360 Byte).
- Seiten: Zustand 0x2406D400 (Magic, Seite). Linkspfeil (padpages_left → master_left) und Rechtspfeil (Tabelle,
  tools_right) auf Bildschirm 0x25: Settings ↔ Kompressor / Distortion, dann 0x0808EEDC(app, 0x25) neu (vorheriger
  Bildschirm app+0x7FE5 wiederhergestellt). clip_page fragt master_page zuerst: bei Code 0x40 und Master-Seite wird die
  Liste ersetzt. Tools-Taste (Thunk 0x080839BC) setzt auf Settings zurueck.
- Offen / nicht verifiziert: Kopfzeile der Seite (bleibt die der Settings-Seite), ob der Settings-Store mit dem Preset
  oder global gespeichert wird, Encoder-Schrittweite bei Release (Typ 1, 1 ms pro Raste), Pfeile auf 0x32 / 0x33 nicht
  belegt. Test: tests/test_master.py (21 Checks), test_fidelity.py (Registrierung, ID-Scan).

## Display-Pfad (Renode-Simulation, 2026-10-11)

| Adresse | Was | Beleg | Status |
|---|---|---|---|
| 0x24002E7C | LTDC-Handle (0x50001000): Panel 240 x 320 hochkant ueber RGB-Schnittstelle; zwei Ebenen ARGB1555 (Alpha-Bit 0 = transparent) ueber Hintergrund 0x141414 | Registerstand in der Simulation | durch Emulation bestaetigt |
| 0x24009CBC | SPI3-Handle: nur die Init-Befehle des Panels (CASET/RASET/...), keine Pixel | Hook auf HAL_SPI_Transmit 0x0804DD94 | durch Emulation bestaetigt |
| 0x24002F24 | DMA2D-Handle: L8-UI-Puffer (CLUT ARGB8888 bei 0x24000000) -> ARGB1555-Ebenenpuffer | Register | durch Emulation bestaetigt |
| 0x24009E38 | SAI1-Block-A-Handle (48 kHz) | Handle-Inhalt | durch Emulation bestaetigt |

Korrektur: UI-Koordinaten zaehlen y von unten. Das Panel {1,149,318,72} des Pads-Bildschirms (Abschnitt Pad-Seiten)
liegt im Bild oben (y 19..91), nicht unten.

Eingaben (Renode-Simulation, 2026-10-11): Tastenabfrage 0x08041A50 nur aus dem Engine-Block 0x08093E48 (laeuft nur mit
Audio-DMA); Tastentabelle 0x24009DA4: HOME = PG3, TOOLS = PD4, LINKS = PC13, RECHTS = PB13, aktiv low (durch Emulation
bestaetigt). pkX Tools-Seiten (Kompressor / Distortion, Pfeile, Standardwerte) in der Simulation angezeigt: durch
Emulation bestaetigt, nicht am Geraet.

## Kompressor-Typ SSL (Build pkY)

Wunsch: zusaetzlicher Kompressor-Typ angelehnt an den SSL-Bus-Kompressor (Schalterwerte).

| Adresse | Was | Beleg | Status |
|---|---|---|---|
| 0x0807E884 | App-Dispatcher, Befehl 0x6E: Aufruf des Regler-Handlers 0x0807D358(app, msg, id, wert, [sp]); Rueckgabe unbenutzt | Disassembly | vermutet |
| 0x0807D3C4.. | Regler-Handler Code 0x40: Store-Set, bei manchen IDs settings.tml schreiben, Engine-Nachricht; kein Neuaufbau der Seite | Disassembly | vermutet |
| Kompressor-Objekt +8 | naechster Knoten; der Stock-DSP ruft ihn am Ende (vtable +0xC, (Knoten, Engine)) | 0x080B9C0C | vermutet |

Umsetzung (`src/master.c`): Comp Type 0x19D (Stock / SSL), Mix 0x19E (beide Typen, Dry-Kopie in 0x2406E000 /
0x2406E800), SSL-Schalter Ratio 0x19F (2/4/10), Attack 0x17D (0,1/0,3/1/3/10/30 ms), Release 0x17F (0,1/0,3/0,6/1,2 s/
Auto), Threshold und Gain gemeinsam. SSL-DSP: Feed-Forward, Stereo-gekoppelte Spitzenerkennung, Kennlinie in dB mit
2-dB-Soft-Knee, Glaettung der Gain-Reduktion (Attack/Release), Auto = schnelle (0,1 s) und langsame Huellkurve
(300 ms / 1,2 s), die tiefere gewinnt; Zustand 0x2406D580. Hook master_knob an 0x0807E884: Typwechsel auf der
Kompressor-Seite baut die Seite neu auf (Regler je Typ). Defaults SSL: 2:1 / 30 ms / Auto. Test: test_master.py
(Kennlinie 2/4/10:1 innerhalb 0,6 dB, Attack, Auto-Release, Mix, Seiten, Hook), Simulation: beide Seiten angezeigt.
Gefunden beim Testen: exp2_fast ist nahe 1 nur auf ~2,5e-4 genau (Zeitkonstanten > 80 ms unmoeglich) -> Koeffizienten
per Reihe; log2-Naeherung brauchte Exponent - 128.

## CPU-Last (Build pkZ, 2026-10-12)

Messung: `tests/perf.py` (Unicorn, Befehle pro 128-Frame-Block je DSP-Stufe) und Renode (`sim/prof.py`, ganze Engine
pro Block). Budget 1,28 M Takte pro Block (480 MHz); Takte pro Befehl unbekannt (Annahme 1,0-1,5), daher Schaetzung.
pkZ-Einsparungen: Parameter-Abfragen ueber einen Cache (src/fastget.c, 0x2406F000, 256 Eintraege, gegen den Store
geprueft), Distortion mit Ringpuffern (Zustand jetzt 0x2406F800; -50 %), Reverb-LFOs pro Block interpoliert (Hall /
Chamber -14 %, Room -8 %, FX3 -12 %). Engine (Renode, Befehle pro Block): Leerlauf ~67 000; 8 Granular-Pads (8 Grains,
Density max) ~300 000-340 000; dazu alle pk-Features ~+240 000. Pad-Modus im Preset: Attribut `cellmode` (0 Sample,
1 Clip, 2 Slicer, 3 Granular; Liste 0x6D). Granular-XML: graincount, graindensity, grainsizeperc, grainscat,
grainpanrnd, grainreadspeed, gainssrcwin, grainsize. Status: durch Emulation bestaetigt, nicht am Geraet.

## Aufnahme und Monitor (Renode, 2026-10-12, Stand der Untersuchung)

| Adresse | Was | Beleg | Status |
|---|---|---|---|
| app+0x7CB8 + n x 0x10 | 8 Eingangszellen (Tools-Bildschirm 0x33), Parameter 0xD9 "Input:" GATE/CV/CLK/AUDIO; In 1/2 muessen AUDIO sein, sonst verweigert die Aufnahmeseite | find_stores, Simulation | durch Emulation bestaetigt |
| 0x080950D4 | kopiert In 1/2, In 3/4 jeden Block in Eingangs-Busse (0x080A82CC(engine-Bereich, idx)); Aufruf aus der Engine 0x08093E44 | Watchpoint | durch Emulation bestaetigt |
| 0x080A4D1C | globaler Eingangsknoten (id 0x400, kein Pad): Aufnahme + Monitor; Monitor-Ausgangsbus obj+0x68 = 0 (Out 1/2), Rec Mon obj+0x58, Gain obj+0x64 | Hook | durch Emulation bestaetigt |
| 0x0807B400 (Aufruf 0x0807B59E) | 1-2 s nach Aufnahmestart: Pad-Record neu als Typ 3 (0x08089FC4 -> 0x08089548), alle Werte Standard inkl. FX1/FX2/FX3 Send; danach Pad Mode 0x6D und Output 0x77 gesetzt; Aufrufer 0x0807F6FA | Watchpoint / Hook | durch Emulation bestaetigt |

Folgerungen: Der Monitor laeuft ueber Bus 0, Master-Distortion und Kompressor wirken also schon. Fuer "Sends bleiben":
Sends vor dem Aufruf bei 0x0807B59E sichern, danach wieder setzen (auch an die Engine). Fuer "Monitor durch die Sends":
0x080A4D1C umhuellen (Bus 0 vorher sichern, Differenz = Monitorsignal) und mit den Sends des gewaehlten, leeren
bzw. aufnehmenden Pads auf FX1 (0xD) / FX2 (0xE) / FX3 (0xC) mischen.

Umgesetzt (pkZA, `src/recmon.c`): rec_reinit (Hook 0x0807B59E) haelt FX1/FX2/FX3 Send ueber das Neuanlegen;
mon_node (vtable 0x080DDFB4 statt 0x080A4D1D) mischt die Differenz am Monitor-Bus mit den Sends des gewaehlten Pads
(app+0x14) auf die FX-Busse (0x080A33EC, Stock-Send-Kurve), Puffer 0x2406E000 / Struktur 0x2406FB00.
Simulation: Rec Mon steht im Settings-Store (0x7B, Standard 1 = Auto: Monitor nur waehrend der Aufnahme); der
Eingangsknoten liefert ab ~0,2 s nach Start; ab dem Neuanlegen (~1,5 s) spielt zusaetzlich die Pad-Stimme (eigene
Sends). Nicht verifiziert: Rec Mon "On" vor der Aufnahme (Store-Schreiben erreicht die Engine nicht), ob die Engine
die geretteten FX1/FX2-Sends nach dem Neuanlegen uebernimmt (FX3 liest den Record direkt).
