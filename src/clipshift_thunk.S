/*
 * Clip shift (clipshift.c): the clip reader's stream calls with the pad (r4 at every site) added as the last argument.
 * 0x080a4500 (stream, dst, n, pos, [sp] ch)  at 0x080b5630, 0x080b5720 -> clip_read1(..., ch, pad)
 * 0x080a44c8 (stream, l, r, n, [sp] pos)     at 0x080b567e, 0x080b56f2 -> clip_read2(..., pos, pad)
 * 0x080a4624 (stream, pos)                   at 0x080b47d2, 0x080b4b4c -> clip_seek(stream, pos, pad)
 */
    .syntax unified
    .thumb
    .text

    .macro STACK5 name, target
    .global \name
    .thumb_func
    .type \name, %function
\name:
    push    {r4, lr}
    ldr     ip, [sp, #8]          /* the caller's fifth argument */
    sub     sp, sp, #8
    str     ip, [sp]
    str     r4, [sp, #4]          /* sixth: the pad */
    bl      \target
    add     sp, sp, #8
    pop     {r4, pc}
    .endm

    STACK5 clip_read1_thunk, clip_read1
    STACK5 clip_read2_thunk, clip_read2

    .global clip_seek_thunk
    .thumb_func
    .type clip_seek_thunk, %function
clip_seek_thunk:
    mov     r2, r4
    b.w     clip_seek
