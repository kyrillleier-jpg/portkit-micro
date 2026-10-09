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
