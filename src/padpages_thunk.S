/*
 * Pad pages (padpages.c): thunks for the stock row extractions in pad-tile lookups, and constructor wrappers.
 *
 * Row thunks replace one `ubfx rd, rn, #4, #4` (the pad address's row) inside a function body, after its push of lr,
 * with `bl`: rd = row - 2 * page. Only rd changes; flags and every other register survive (lr is not used as a
 * scratch register in these bodies, checked for each site). The page byte is at PSTATE + 4 (padpages.c).
 * Screen D swaps instead: r8 = (r3 asr 4) ^ (2 * page), for its `asr.w r8, r3, #4` (the `and r8, r8, #0xf` after it
 * stays).
 */
    .syntax unified
    .thumb
    .text

    .equ PAGE_BYTE, 0x2406c114

    .macro ROW name, rd, rn
    .global \name
    .thumb_func
    .type \name, %function
\name:
    push    {ip}
    mrs     ip, apsr
    push    {ip}
    ubfx    \rd, \rn, #4, #4
    ldr     ip, =PAGE_BYTE
    ldrb    ip, [ip]
    and     ip, ip, #1
    sub     \rd, \rd, ip, lsl #1
    pop     {ip}
    msr     apsr_nzcvq, ip
    pop     {ip}
    bx      lr
    .endm

    ROW row_b_r2_r3, r2, r3          /* 0x0808407c  screen B, update body */
    ROW row_b_r0_r3, r0, r3          /* 0x080840a0 */
    ROW row_b_r5_r5, r5, r5          /* 0x08084268, 0x080842a4  screen B, notifications */
    ROW row_b_r0_r6, r0, r6          /* 0x080842d2 */
    ROW row_a_r7_r3, r7, r3          /* 0x080862f2  Pads screen, update body */
    ROW row_a_r2_r0, r2, r0          /* 0x080864ea, 0x0808655e  Pads screen, tile pressed */

    .global row_d_r8_r3
    .thumb_func
    .type row_d_r8_r3, %function
row_d_r8_r3:                         /* 0x08069280  screen D: asr.w r8, r3, #4 */
    push    {ip}
    mrs     ip, apsr
    push    {ip}
    asr     r8, r3, #4
    ldr     ip, =PAGE_BYTE
    ldrb    ip, [ip]
    and     ip, ip, #1
    eor     r8, r8, ip, lsl #1
    pop     {ip}
    msr     apsr_nzcvq, ip
    pop     {ip}
    bx      lr

/* Periodic tile state (play state / progress) of the Pads (0x08084838) and Effects (0x08086b50) screens: their loop
   over the 8 tiles asks for the fixed addresses of pads 1-8. `movs r7, #0; mov r6, r7` (0x08084842, 0x08086b5a) becomes
   this thunk: r7 = 0 (tile row offset), r6 = 2 * page << 4 (first pad row). Flags are not live there. */
    .global loop_rows
    .thumb_func
    .type loop_rows, %function
loop_rows:
    movs    r7, #0
    ldr     r6, =PAGE_BYTE
    ldrb    r6, [r6]
    and     r6, r6, #1
    lsls    r6, r6, #5
    bx      lr

/* The Mixer's (0x08069dd0) loop runs over its 16 tiles with pad row = tile row; with the swapped rows the pad is
   (tile row ^ 2 * page) | col: `orr.w r3, r7, r4` (0x08069df8) becomes r3 = (r7 ^ (page << 5)) | r4. */
    .global loop_d_code
    .thumb_func
    .type loop_d_code, %function
loop_d_code:
    ldr     r3, =PAGE_BYTE
    ldrb    r3, [r3]
    and     r3, r3, #1
    eor     r3, r7, r3, lsl #5
    orr     r3, r3, r4
    bx      lr

/* Pad picker (class ctor 0x080733b4; 2 x 4 small tiles: +0x34 + col * 0xac + row * 0x2b0, pad address at +0xa4).
   picker_sel_tst replaces `tst.w r2, #0xe` (0x080732dc) in its "mark selected" (0x080732d6; r2 = address >> 4): Z set
   and r2 -= 2 * page when the pad's row is on the current page, Z clear otherwise (the stock test: row < 2). */
    .global picker_sel_tst
    .thumb_func
    .type picker_sel_tst, %function
picker_sel_tst:
    push    {r0, ip}
    ldr     ip, =PAGE_BYTE
    ldrb    ip, [ip]
    and     ip, ip, #1
    and     r0, r2, #0xe
    cmp     r0, ip, lsl #1
    bne     1f
    sub     r2, r2, ip, lsl #1
    cmp     r0, r0
1:  pop     {r0, ip}
    bx      lr

/* "mark playing" (0x08073312) compares with the fixed addresses of pads 1-8: `uxth r3, r4; cmp r1, r3` (0x0807331e)
   and `orr r3, r4, #0x10` (0x0807332e) get the page's rows. */
    .global picker_mark0
    .thumb_func
    .type picker_mark0, %function
picker_mark0:
    ldr     r3, =PAGE_BYTE
    ldrb    r3, [r3]
    and     r3, r3, #1
    orr     r3, r4, r3, lsl #5
    uxth    r3, r3
    cmp     r1, r3
    bx      lr

    .global picker_mark1
    .thumb_func
    .type picker_mark1, %function
picker_mark1:
    ldr     r3, =PAGE_BYTE
    ldrb    r3, [r3]
    and     r3, r3, #1
    orr     r3, r4, r3, lsl #5
    orr     r3, r3, #0x10
    bx      lr

/* Pad picker constructor wrapper: run 0x080733b4, then padpages_picker(this). */
    .global ctor_picker
    .thumb_func
    .type ctor_picker, %function
ctor_picker:
    push    {r0, lr}
    ldr     ip, =0x080733b5
    blx     ip
    pop     {r1, ip}
    push    {r0, ip}
    mov     r0, r1
    bl      padpages_picker
    pop     {r0, pc}

/* Constructor wrappers, at the UI manager's constructor calls (0x08085140 B, 0x0808519c D, 0x080851c4 A): run the
   stock constructor with r0-r3 unchanged, then padpages_ctor(which, this). Returns the constructor's r0. */
    .macro CTOR name, stock, which
    .global \name
    .thumb_func
    .type \name, %function
\name:
    push    {r0, lr}
    ldr     ip, =\stock
    blx     ip
    pop     {r1, ip}
    push    {r0, ip}
    movs    r0, #\which
    bl      padpages_ctor
    pop     {r0, pc}
    .endm

    CTOR ctor_b, 0x08083e41, 1
    CTOR ctor_d, 0x080696e1, 2
    CTOR ctor_a, 0x080866b1, 0

/* Left arrow: the button handler's case for button index 2 (0x080839e6, `movw r3, #0x7fe4`) does nothing on the Pads
   screen (screen id 2). There: padpages_left(app = r0), then leave the handler (0x080837e8: add sp, #0x48;
   pop {r4, pc}). Elsewhere: replay the replaced instruction and go on. */
    .global left_arrow
    .thumb_func
    .type left_arrow, %function
left_arrow:
    movw    r3, #0x7fe4
    ldrb    r3, [r0, r3]
    cmp     r3, #2
    beq     1f
    movw    r3, #0x7fe4
    bx      lr
1:
    bl      padpages_left
    ldr     ip, =0x080837e9
    bx      ip

    .ltorg
