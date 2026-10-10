/*
 * Clip shift (clipshift.c): the clip reader's stream calls with the pad (r4 at every site) added as the last argument.
 * 0x080a4500 (stream, dst, n, pos, [sp] ch)  at 0x080b5630, 0x080b5720 -> clip_read1(..., ch, pad)
 * 0x080a44c8 (stream, l, r, n, [sp] pos)     at 0x080b567e, 0x080b56f2 -> clip_read2(..., pos, pad)
 * 0x080a4624 (stream, pos)                   at 0x080b47d2, 0x080b4b4c -> clip_seek(stream, pos, pad)
 * Play length: `ldrd r1, r2, [r6, #0x240]` (0x080b5f2e, 0x080b611a; pad in r6, `add r2, r1; cmp` follow) ->
 *   r1 = pad[0x240], r2 = clip_segments(pad) - r1, everything else kept (flags are set by the cmp after).
 * Stretch: 0x0809f1f8 (out, &ticks, s0 tempo, s1) at 0x080b42a8 / 0x080b44da (clip setup, pad in sl) ->
 *   clip_ticks(pad, &ticks), then the stock call with r0-r3, s0, s1 as they were.
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

    .global clip_segments_thunk
    .thumb_func
    .type clip_segments_thunk, %function
clip_segments_thunk:
    push    {r0, r3, ip, lr}
    mov     r0, r6
    bl      clip_segments
    ldr     r1, [r6, #0x240]
    sub     r2, r0, r1
    pop     {r0, r3, ip, lr}
    bx      lr

    .global clip_ticks_thunk
    .thumb_func
    .type clip_ticks_thunk, %function
clip_ticks_thunk:
    push    {r0, r1, r2, r3, ip, lr}
    vpush   {s0, s1}
    mov     r0, sl
    bl      clip_ticks
    vpop    {s0, s1}
    pop     {r0, r1, r2, r3, ip, lr}
    ldr     ip, =0x0809f1f9
    bx      ip

    .ltorg
