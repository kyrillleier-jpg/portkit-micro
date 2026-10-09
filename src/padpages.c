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
 * Screens (identified from their constructors' layouts, tools/emu_layout.py): A = Effects (8 tiles, DLY / RVB cells,
 * send meters; pk3 wrongly took it for the Pads screen), B = Pads (8 tiles, Keys / Stop; selection arrives as
 * notification 0x63, not 0x112), D = probably the Mixer (8 visible of 16 tiles, four buttons below).
 * The left arrow button (no function on the Pads screen in stock) toggles the page there. The page shows in the title
 * bar on the Pads and Effects screens ("Pads 1-8", "FX 9-16"; the title's snprintf calls in 0x080769e0 are replaced).
 * On the Mixer, one of its four empty text buttons (top left on the device; the UI is turned by 180 degrees) shows the
 * page and toggles it: a text button reports its click to its screen as event 2 carrying the command id at +0x14
 * (0x0805cc74); that field gets PAGE_CMD and the Mixer's input handler is wrapped. pk6 / pk7 put our own text widgets
 * over the Pads panel and the send meters; those were overdrawn by their live neighbours and are gone.
 * Selecting a pad is app command 0x63 (0x08075984: app + 0x14 = selected pad, notification 0x63); 0x111 selects an
 * effect cell (app + 0x28) and was wrongly used up to pk5.
 * On the Effects screen a second touch on the already selected effect cell (DLY / RVB, app + 0x28) toggles the page.
 * Not in this build: MIDI and gate inputs for pads 9-16.
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
#define CMD_SELECT 0x63      /* "select pad" (0x08075984); 0x111 selects an effect cell */

struct note {                    /* a notification from the app to a screen: id, listener, pad address */
    uint16_t id, pad0;
    uint32_t lit;
    uint16_t code;
};

typedef void (*scr_fn)(void *scr, const void *msg);
typedef int (*vis_fn)(void *scr, const void *msg);
#define fw_a_update_body ((scr_fn)FN(0x080862b6))   /* Effects screen: update one tile (after its row/col guard) */
#define fw_a_touch_body  ((scr_fn)FN(0x08086482))   /* Effects screen: tile pressed (after its column guard) */
#define fw_a_notify      ((scr_fn)FN(0x080863a0))   /* Effects screen: notifications (vtable +0x34) */
#define fw_a_input       ((vis_fn)FN(0x080865e4))   /* Effects screen: input events (vtable +0x30) */
#define fw_b_input       ((vis_fn)FN(0x08083dec))   /* Pads screen: input events (vtable +0x30) */
#define fw_b_update_body ((scr_fn)FN(0x08084046))   /* Pads screen: update one tile (after its guard) */
#define fw_b_notify      ((scr_fn)FN(0x08084154))   /* Pads screen: notifications (vtable +0x34) */
#define fw_d_update      ((scr_fn)FN(0x08069268))   /* screen D: update one tile (rows 0-3, 16 tiles) */
#define fw_post_cmd      ((scr_fn)FN(0x08060df8))   /* widget: pass a command up to the app */

typedef void (*text_fn)(void *w, const char *text);
#define fw_set_text   ((text_fn)FN(0x0805d1dc))      /* copies the text, then relayouts / redraws (vt+0x3c) */
#define APP           ((volatile uint8_t *)0x24013cb0u)   /* the app object (as in filter.c) */
#define APP_SELECTED  0x14                            /* app + 0x14: selected pad (0x08075984) */
#define APP_FX_CELL   0x28                            /* app + 0x28: selected effect cell (0x0807b20c) */
#define TEXT_VT       0x080bfc9cu                     /* text widget vtable */
#define TEXT_CMD      0x14                            /* text widget: command id its click reports (event 2, +0xc) */
#define PAGE_CMD      0x7f01u                         /* our command id: no app command (the dispatcher ends at 0x181) */
#define MIXER_TOGGLE  0x2ae8                          /* Mixer screen: text button {161, 186, 158, 35} */
#define fw_d_input    ((vis_fn)FN(0x080691b0))        /* Mixer screen: input events (vtable +0x30) */
typedef int (*snprintf_fn)(char *buf, unsigned size, const char *fmt, ...);
#define fw_snprintf   ((snprintf_fn)FN(0x080bcd58))

/* State above the stack top, next to Fidelity's PARK (0x2406c100..0x2406c10b); MPU device memory, aligned accesses. */
struct pstate {
    uint32_t magic;
    uint8_t page;                /* 0: pads 1-8, 1: pads 9-16; read by the thunks at +4 */
    uint8_t touch;               /* the next selection change comes from a touch */
    uint8_t busy;                /* inside a page switch */
    uint8_t pad0;
    uint16_t last_sel;           /* last selection the Pads screen saw */
    uint16_t pad1;
    uint8_t *inst[3];            /* screen objects: A (Effects), B (Pads), D (Mixer?) */
    uint8_t *ind2;               /* page label / toggle on the Mixer screen */
};
#define ST     ((volatile struct pstate *)0x2406c110u)
#define PMAGIC 0x50414745u       /* "PAGE" */
enum { SCR_A, SCR_B, SCR_D };

_Static_assert(sizeof(struct pstate) == 0x1c, "thunks read page at +4");

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

static const char *page_label(void)
{
    return page() ? "Pads 9-16" : "Pads 1-8";
}

static void toggle(void *from);

/* The Mixer's toggle: one of its four empty text buttons (only if it is the text widget we expect). Its click now
   reports PAGE_CMD, which padpages_d_input takes. */
static void make_mixer_toggle(uint8_t *scr)
{
    uint8_t *w = scr + MIXER_TOGGLE;
    if (*(uint32_t *)w != TEXT_VT)
        return;
    *(uint32_t *)(w + TEXT_CMD) = PAGE_CMD;
    ST->ind2 = w;
    fw_set_text(w, page_label());
}

/* --- constructors: remember the screen objects (padpages_thunk.S calls this after each stock constructor) ------- */
void padpages_ctor(unsigned which, uint8_t *scr)
{
    if (ST->magic != PMAGIC) {
        ST->inst[0] = ST->inst[1] = ST->inst[2] = 0;
        ST->ind2 = 0;
        ST->magic = PMAGIC;
    }
    ST->page = 0;                /* a fresh screen has the stock ids: pads 1-8 */
    ST->touch = 0;
    ST->busy = 0;
    ST->last_sel = 0xffff;
    if (which < 3)
        ST->inst[which] = scr;
    if (which == SCR_D)
        make_mixer_toggle(scr);
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
    if (ST->ind2)
        fw_set_text(ST->ind2, page_label());
}

static void select_pad(void *scr, unsigned code)
{
    struct cmd c = {CMD_SELECT, 0, CMD_LIT, (uint16_t)code, 0, {0, 0, 0}};
    fw_post_cmd(scr, &c);
}

/* --- Pads screen (B): vtable +0x30 (inputs) and +0x34 (notifications) --------------------------------------------- */
int padpages_b_input(void *scr, const struct note *n)
{
    if (n->id == 3)              /* a tile pressed: the selection change that follows is a touch */
        ST->touch = 1;
    return fw_b_input(scr, n);
}

/* The Pads screen learns the selected pad from notification 0x63 (code at +8; stored at +0xd38, tile highlighted). */
static void selection_seen(void *scr, unsigned sel)
{
    unsigned prev = ST->last_sel, p = page(), touch = ST->touch;
    ST->touch = 0;
    ST->last_sel = (uint16_t)sel;
    if (touch || (sel & 0x1f00u) != 0 || col_of(sel) >= 4 || row_of(sel) >= 4)
        return;
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
    if (np == p)
        return;
    ST->busy = 1;
    set_page(np);
    ST->busy = 0;
    if (target != 0xffff) {
        ST->last_sel = (uint16_t)target;
        select_pad(scr, target);
    }
}

void padpages_b_notify(void *scr, const struct note *n)
{
    if (ST->magic != PMAGIC || ST->busy) {
        fw_b_notify(scr, n);
        return;
    }
    if (n->id == 0x63)
        selection_seen(scr, n->code);
    fw_b_notify(scr, n);
    if (n->id == 0x67 && page())  /* "all new": the stock loops used the fixed addresses of pads 1-8 */
        refresh(SCR_B);
}

/* --- Effects screen (A): a second touch on the selected effect cell toggles the page; refresh on "all new" --------- */
int padpages_a_input(void *scr, const struct note *n)
{
    if (n->id == 3 && ((n->code >> 8) & 0x1fu) == 3 && n->code == *(volatile uint16_t *)(APP + APP_FX_CELL)) {
        toggle(scr);
        return 0;
    }
    return fw_a_input(scr, n);
}

void padpages_a_notify(void *scr, const struct note *n)
{
    fw_a_notify(scr, n);
    if (n->id == 0x67 && ST->magic == PMAGIC && !ST->busy && page())
        refresh(SCR_A);
}

/* --- toggling: left arrow on the Pads screen, the two toggle widgets ------------------------------------------------ */
/* Flip the page and select the pad at the same place on the other page (rows 0 <-> 2, 1 <-> 3); `from` is the widget
   the select command is passed up from. */
static void toggle(void *from)
{
    if (ST->magic != PMAGIC || ST->busy)
        return;
    unsigned sel = *(volatile uint16_t *)(APP + APP_SELECTED);
    ST->busy = 1;
    set_page(page() ^ 1u);
    ST->busy = 0;
    if (from && (sel & 0x1f00u) == 0 && col_of(sel) < 4 && row_of(sel) < 4) {
        unsigned target = sel ^ 0x20u;
        ST->last_sel = (uint16_t)target;
        select_pad(from, target);
    }
}

/* padpages_thunk.S: left_arrow, at the button handler 0x080839e6, on the Pads screen only */
void padpages_left(uint8_t *app)
{
    (void)app;
    toggle(ST->inst[SCR_B]);
}

/* --- Mixer (D): its toggle's click (event 2 with PAGE_CMD) --------------------------------------------------------- */
int padpages_d_input(void *scr, const struct note *n)
{
    if (n->id == 2 && *(const uint32_t *)((const uint8_t *)n + 0xc) == PAGE_CMD) {
        toggle(scr);
        return 0;
    }
    return fw_d_input(scr, n);
}

/* --- title bar: replaces snprintf(buf, 0x18, "Pads") / ("FX") in 0x080769e0 --------------------------------------- */
int padpages_title(char *buf, unsigned size, const char *name)
{
    return fw_snprintf(buf, size, "%s %s", name, page() ? "9-16" : "1-8");
}
