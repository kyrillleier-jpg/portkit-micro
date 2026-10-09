/* Code cave: appended directly after the stock bitbox micro 2.3.4 image (671376 bytes, ends at 0x080E3E90).
   The micro patcher appends the same way (_append in patch_micro.py), so the bootloader takes a longer image. */
MEMORY { CAVE (rx) : ORIGIN = 0x080E3E90, LENGTH = 0x8000 }
SECTIONS {
  .cave : { *(.text .text.* .rodata .rodata.*) } > CAVE
  /* No RAM: the cave has no startup code, so initialised or zeroed globals would never be set up. */
  .ram (NOLOAD) : { *(.data .data.* .bss .bss.* COMMON) } > CAVE
  ASSERT(SIZEOF(.ram) == 0, "cave code must not use .data/.bss; put state in the filter object or at a fixed address")
  /DISCARD/ : { *(.ARM.exidx* .ARM.attributes .comment) }
}
