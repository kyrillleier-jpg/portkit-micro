/*
 * Pad pages: pads 9-16 on the bitbox micro 2.3.4 as a second page of the 2 x 4 pad grid (re/symbols.md, "Seiten-Variante").
 *
 * The engine, the app's pad records and presets already hold 16 pads (rows 0-3 of the framework's 4 x 4 grid); the
 * micro's UI shows rows 0-1 only. Page 1 shows rows 2-3 in the same eight tiles:
 *   - every pad tile carries its real pad address (row << 4 | col) at tile + 0x38; a page switch rewrites them, so
 *     touch, labels and selection compares follow the page by themselves;
 *   - every place that turns a pad address back into a tile (row * 0x680 + col * 0x1a0) gets the page: guards accept
 *     only the current page (C wrappers below, called instead of the stock guarded entry points), row extractions in
 *     the function bodies subtract 2 * page (padpages_thunk.S);
 *   - screen D (the Waveform screen's pad grid) has 16 tile widgets with rows 2-3 hidden; there the rows are swapped
 *     (row ^ 2 * page), no guard needed;
 *   - the Pads screen switches page when the encoder runs over the end of a page (selection jumps from the page's last
 *     pad to its first or back, not caused by a touch), or when the selection lands on the other page.
 * Not in this build: Mixer / FX (widget 0x28c, indexed by pad number; pads 9-16 are rejected there, no overflow), MIDI
 * and gate inputs for pads 9-16, a page indicator.
 */
#include <stdint.h>

#define FN(addr) ((addr) | 1u)

struct pmsg {                    /* the stock tile-update message: listener vtable, pad address */
    uint32_t lit;
    uint16_t code;
    uint16_t pad;
};
#define MSG_LIT 0x080bf4ccu

struct cmd {                     /* a command to the app, as the Pads screen posts "select pad" (0x08086678) */
    uint16_t id, pad0;
    uint32_t lit;
    uint16_t code, pad1;
    uint32_t z[3];
};
#define CMD_LIT    0x080bee0cu
#define CMD_SELECT 0x111

struct note {                    /* a notification from the app to a screen: id, listener, pad address */
    uint16_t id, pad0;
    uint32_t lit;
    uint16_t code;
};

typedef void (*scr_fn)(void *scr, const void *msg);
typedef int (*vis_fn)(void *scr, const void *msg);
#define fw_a_update_body ((scr_fn)FN(0x080862b6))   /* Pads screen: update one tile (after its row/col guard) */
#define fw_a_touch_body  ((scr_fn)FN(0x08086482))   /* Pads screen: tile pressed (after its column guard) */
#define fw_a_notify      ((scr_fn)FN(0x080863a0))   /* Pads screen: notifications (vtable +0x34) */
#define fw_a_input       ((vis_fn)FN(0x080865e4))   /* Pads screen: input events (vtable +0x30) */
#define fw_b_update_body ((scr_fn)FN(0x08084046))   /* screen B: update one tile (after its guard) */
#define fw_b_notify      ((scr_fn)FN(0x08084154))   /* screen B: notifications */
#define fw_d_update      ((scr_fn)FN(0x08069268))   /* screen D: update one tile (rows 0-3, 16 tiles) */
#define fw_post_cmd      ((scr_fn)FN(0x08060df8))   /* widget: pass a command up to the app */

/* State above the stack top, next to Fidelity's PARK (0x2406c100..0x2406c10b); MPU device memory, aligned accesses. */
struct pstate {
    uint32_t magic;
    uint8_t page;                /* 0: pads 1-8, 1: pads 9-16; read by the thunks at +4 */
    uint8_t touch;               /* the next selection change comes from a touch */
    uint8_t busy;                /* inside a page switch */
    uint8_t pad0;
    uint16_t last_sel;           /* last selection the Pads screen saw */
    uint16_t pad1;
    uint8_t *inst[3];            /* screen objects: A (Pads), B, D (Waveform pad grid) */
};
#define ST     ((volatile struct pstate *)0x2406c110u)
#define PMAGIC 0x50414745u       /* "PAGE" */
enum { SCR_A, SCR_B, SCR_D };

_Static_assert(sizeof(struct pstate) == 0x18, "thunks read page at +4");

static unsigned page(void)
{
    return ST->magic == PMAGIC ? ST->page & 1u : 0u;
}

static unsigned row_of(unsigned code) { return (code >> 4) & 0xfu; }
static unsigned col_of(unsigned code) { return code & 0xfu; }

/* on the current page: column 0-3, row 2 * page or 2 * page + 1 */
static int on_page(unsigned code)
{
    return col_of(code) < 4 && (row_of(code) >> 1) == page();
}

static unsigned first_of(unsigned p) { return (2u * p) << 4; }
static unsigned last_of(unsigned p) { return ((2u * p + 1u) << 4) | 3u; }

/* --- constructors: remember the screen objects (padpages_thunk.S calls this after each stock constructor) ------- */
void padpages_ctor(unsigned which, uint8_t *scr)
{
    if (ST->magic != PMAGIC) {
        ST->inst[0] = ST->inst[1] = ST->inst[2] = 0;
        ST->magic = PMAGIC;
    }
    ST->page = 0;                /* a fresh screen has the stock ids: pads 1-8 */
    ST->touch = 0;
    ST->busy = 0;
    ST->last_sel = 0xffff;
    if (which < 3)
        ST->inst[which] = scr;
}

/* --- guards: replace the stock guarded entries at their call sites ------------------------------------------------ */
void padpages_a_update(void *scr, const struct pmsg *m)          /* for 0x080862a4 */
{
    if (on_page(m->code))
        fw_a_update_body(scr, m);
}

void padpages_a_touch(void *scr, const struct pmsg *m)           /* for 0x08086478 */
{
    if (on_page(m->code))
        fw_a_touch_body(scr, m);
}

void padpages_b_update(void *scr, const struct pmsg *m)          /* for 0x08084034 */
{
    if (on_page(m->code))
        fw_b_update_body(scr, m);
}

int padpages_b_visible(void *scr, const struct pmsg *m)          /* for 0x08084138: also no layer bits */
{
    (void)scr;
    return (m->code & 0x1f00u) == 0 && on_page(m->code);
}

/* --- page switch ------------------------------------------------------------------------------------------------------ */
static volatile uint16_t *tile_id(uint8_t *scr, unsigned base, unsigned row, unsigned col)
{
    return (volatile uint16_t *)(scr + base + row * 0x680u + col * 0x1a0u + 0x38u);
}

/* Update the tiles of one screen with the current page's pads (D: all 16, its rows are swapped). */
static void refresh(unsigned which)
{
    uint8_t *scr = ST->inst[which];
    struct pmsg m = {MSG_LIT, 0, 0};
    if (!scr)
        return;
    for (unsigned r = 0; r < (which == SCR_D ? 4u : 2u); r++)
        for (unsigned c = 0; c < 4; c++) {
            m.code = (uint16_t)(((which == SCR_D ? r : 2u * page() + r) << 4) | c);
            if (which == SCR_A)
                fw_a_update_body(scr, &m);
            else if (which == SCR_B)
                fw_b_update_body(scr, &m);
            else
                fw_d_update(scr, &m);
        }
}

static void set_page(unsigned p)
{
    p &= 1u;
    ST->page = (uint8_t)p;
    for (unsigned r = 0; r < 2; r++)
        for (unsigned c = 0; c < 4; c++) {
            uint16_t id = (uint16_t)(((2u * p + r) << 4) | c);
            if (ST->inst[SCR_A])
                *tile_id(ST->inst[SCR_A], 0x34, r, c) = id;
            if (ST->inst[SCR_B])
                *tile_id(ST->inst[SCR_B], 0x34, r, c) = id;
        }
    if (ST->inst[SCR_D])
        for (unsigned r = 0; r < 4; r++)
            for (unsigned c = 0; c < 4; c++)
                *tile_id(ST->inst[SCR_D], 0x3ac, r, c) = (uint16_t)(((r ^ (2u * p)) << 4) | c);
    refresh(SCR_A);
    refresh(SCR_B);
    refresh(SCR_D);
}

static void select_pad(void *scr, unsigned code)
{
    struct cmd c = {CMD_SELECT, 0, CMD_LIT, (uint16_t)code, 0, {0, 0, 0}};
    fw_post_cmd(scr, &c);
}

/* --- Pads screen: vtable +0x30 (inputs) and +0x34 (notifications) ----------------------------------------------------- */
int padpages_a_input(void *scr, const struct note *n)
{
    if (n->id == 3)              /* a tile pressed: the selection change that follows is a touch */
        ST->touch = 1;
    return fw_a_input(scr, n);
}

void padpages_a_notify(void *scr, const struct note *n)
{
    if (ST->magic != PMAGIC || ST->busy) {
        fw_a_notify(scr, n);
        return;
    }
    if (n->id == 0x112) {
        unsigned sel = n->code, prev = ST->last_sel, p = page(), touch = ST->touch;
        ST->touch = 0;
        ST->last_sel = (uint16_t)sel;
        if (!touch && (sel & 0x1f00u) == 0 && col_of(sel) < 4 && row_of(sel) < 4) {
            unsigned np = p, target = 0xffff;
            if (prev == last_of(p) && sel == first_of(p)) {          /* encoder ran past the page's last pad */
                np = p ^ 1u;
                target = first_of(np);
            } else if (prev == first_of(p) && sel == last_of(p)) {   /* ... or back past its first */
                np = p ^ 1u;
                target = last_of(np);
            } else if ((row_of(sel) >> 1) != p) {                    /* selection already on the other page */
                np = p ^ 1u;
            }
            if (np != p) {
                ST->busy = 1;
                set_page(np);
                ST->busy = 0;
                if (target != 0xffff) {
                    ST->last_sel = (uint16_t)target;
                    select_pad(scr, target);
                }
            }
        }
        fw_a_notify(scr, n);
        return;
    }
    fw_a_notify(scr, n);
    if (n->id == 0x67 && page())  /* "all new": the stock loop used the fixed addresses of pads 1-8 */
        refresh(SCR_A);
}

void padpages_b_notify(void *scr, const struct note *n)
{
    fw_b_notify(scr, n);
    if (n->id == 0x67 && ST->magic == PMAGIC && !ST->busy && page())
        refresh(SCR_B);
}
