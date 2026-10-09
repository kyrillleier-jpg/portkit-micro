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

    .ltorg
