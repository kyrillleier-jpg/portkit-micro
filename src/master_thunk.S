/*
 * Master section (master.c) hooks:
 * - 0x08096d1c `ldrb.w r3, [sl, r3]` (the block driver's compressor flag, after the FX returns and the master EQ;
 *   bus 0 = r4): master_dist(bus 0) first, then the load. Flags are set by the cmp after it; lr is not live.
 * - 0x080839bc `movw r3, #0x7fe4` (button handler, Tools button): master_tools(), then the movw.
 * - the right arrow's case table 0x08083800, entry for screen 0x25 (stock: 0x080837e9 = nothing): tools_right, entered
 *   by `ldr.w pc` with the app in r4; leaves through the handler's exit 0x080837e8.
 */
    .syntax unified
    .thumb
    .text

    .global master_dist_thunk
    .thumb_func
    .type master_dist_thunk, %function
master_dist_thunk:
    push    {r0, r1, r2, r3, ip, lr}
    vpush   {s0-s15}
    mov     r0, r4
    bl      master_dist
    vpop    {s0-s15}
    pop     {r0, r1, r2, r3, ip, lr}
    ldrb.w  r3, [sl, r3]
    bx      lr

    .global tools_btn
    .thumb_func
    .type tools_btn, %function
tools_btn:
    push    {r0, r1, r2, r3, ip, lr}
    bl      master_tools
    pop     {r0, r1, r2, r3, ip, lr}
    movw    r3, #0x7fe4
    bx      lr

    .global tools_right
    .thumb_func
    .type tools_right, %function
tools_right:
    mov     r0, r4
    bl      master_right
    ldr     ip, =0x080837e9
    bx      ip
    .ltorg
