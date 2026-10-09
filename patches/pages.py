"""Fidelity (Interp, 0xd2) on the pad settings page of Clip, Slicer and Granular pads, right after Excl Group as on
Sample pads. Stock has it only on Sample. Data only.

Page tables: 6 pages x 45 halfword parameter ids per pad mode, selected in 0x08076d8c (two variants per mode). Page 5
is the pad settings page. Clip / Slicer / Granular pads can store 0xd2: every loaded pad gets the full pad store
(type 3, 58 ids, Interp included; store init 0x08089fc4 run in Unicorn, see re/symbols.md "Pad-Seiten").
"""
import struct

P_INTERP, P_EXCL = 0xD2, 0xA6
LAUNCH, OUTPUT, MIDI_IN, ROOT, PAD_NOTE = 0x75, 0x77, 0x4D, 0xB2, 0xD6
POLY_CS = 0x83      # "Poly Mode:" on Clip / Slicer (Sample uses 0x82, same label)

PAGE5 = 5 * 0x5A


def insert_after_excl(table, ids):
    """Page 5 of `table` holds `ids` then zeros; put Interp after Excl Group. Checks one spare zero slot."""
    at = table + PAGE5
    old = struct.pack(f"<{len(ids) + 1}H", *ids, 0)
    k = ids.index(P_EXCL) + 1
    new_ids = ids[:k] + [P_INTERP] + ids[k:]
    return (at, old, struct.pack(f"<{len(new_ids)}H", *new_ids))


CLIP = [LAUNCH, OUTPUT, POLY_CS, P_EXCL, MIDI_IN, PAD_NOTE]
SLICER = [LAUNCH, OUTPUT, POLY_CS, P_EXCL, MIDI_IN, ROOT, PAD_NOTE]
SLICER_B = [LAUNCH, OUTPUT, POLY_CS, P_EXCL, MIDI_IN, PAD_NOTE]
GRANULAR = [LAUNCH, OUTPUT, P_EXCL, MIDI_IN, ROOT, PAD_NOTE]

PATCHES = [
    insert_after_excl(0x080C6A1C, CLIP),
    insert_after_excl(0x080C6C38, CLIP),
    insert_after_excl(0x080C7E28, SLICER_B),
    insert_after_excl(0x080C8044, SLICER),
    insert_after_excl(0x080C6EEC, GRANULAR),
    insert_after_excl(0x080C7108, GRANULAR),
]
