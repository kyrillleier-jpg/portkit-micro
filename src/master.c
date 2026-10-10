/*
 * Master section (portkit): the stock compressor's settings and a master distortion, each on a page of its own next to
 * the settings page (Tools screen 0x25: left arrow = Compressor, right arrow = Distortion, back the other way).
 *
 * - Compressor: the firmware has a compressor across Out 1/2 (object engine +0xfb38, run by the block driver at
 *   0x08097056 when the On/Off flag engine +0x28cc0 is set, i.e. "Compressor:" 0x96 on the settings page). Only On/Off
 *   is reachable stock; threshold (+0x428, float dB), ratio (+0x42c, float), makeup (+0x430, float dB), attack (+0x448)
 *   and release (+0x44c, samples, the gain ramp's lengths) are set by its constructor (0x080b9d88: -4 dB, 4:1, -4 dB,
 *   480, 12000) and read raw every block (0x080b9b04; same offsets as bitbox-micro-fw-patch, its guards hold here).
 *   master_comp (hooked at 0x08097056) writes them from the settings store before every block.
 * - Distortion: on bus 0 (Out 1/2) after the FX returns and the master EQ, before the compressor (thunk at 0x08096d1c,
 *   the compressor flag's load, so it runs whether the compressor is on or not). 2x oversampled (31-tap half-band
 *   up / down), shapers Soft (tanh) / Hard (clip) / Fold (triangle) / Tube (asymmetric tanh, DC blocked), Tone (one-pole
 *   low-pass, the stock cutoff curve), Mix (dry delayed by the filters' 15 samples), Level.
 * - Settings: new ids 0x1a1-0x1a3, 0x1a5-0x1a9, 0x1ab, 0x1ac (none of them a constant anywhere in the stock code) in the settings store app +0x7fd0 (init 0x08089e04, capacity 64, 36
 *   stock entries; hooked at its last add 0x08089f78), registered next to Fidelity (filter.c). The engine never sees
 *   them (ids > 0x17a). Defaults = the stock compressor; distortion Off.
 * - Pages: the page builder 0x08076d8c fills code 0x40 (the settings page, screen 0x25) from a table; clip_page
 *   (clipshift.c, wraps all its callers) asks master_page first, which fills our list while a master page is shown.
 *   The knob handler 0x0807d358 writes code-0x40 knobs straight into app +0x7fd0 (0x0807d3aa), so editing needs nothing.
 */
#include <stdint.h>

#pragma GCC optimize("O2", "no-tree-loop-distribute-patterns")

#define FN(addr) ((addr) | 1u)

typedef void (*register_list_fn)(void *table, int param, const char *label, const char *const *names, int count,
                                 const char *xml);
typedef void (*register_knob_fn)(void *table, int param, int type, const char *label, int min, int max,
                                 const char *xml);
typedef int (*store_get_fn)(const void *store, unsigned param);
typedef void (*store_add_fn)(void *store, unsigned param, int value);
typedef void (*list_add_fn)(void *list, unsigned param, int value);
typedef void (*screen_fn)(void *app, unsigned screen, unsigned a, unsigned b);
typedef void (*comp_fn)(void *comp, void *engine);
typedef int (*planes_fn)(void *buf, float **l, float **r);
typedef int (*frames_fn)(void *buf);
typedef float (*curve_fn)(float x);
#define fw_register_list ((register_list_fn)FN(0x08069e7c))
#define fw_register_knob ((register_knob_fn)FN(0x08069ed4))
#define fw_store_get     ((store_get_fn)FN(0x080894d0))
#define fw_store_add     ((store_add_fn)FN(0x0808951e))
#define fw_list_add      ((list_add_fn)FN(0x080836a4))     /* list: +0 count (u32, max 0x2f), entries of 12 bytes */
#define fw_screen        ((screen_fn)FN(0x0808eedc))
#define fw_comp          ((comp_fn)FN(0x080b9b04))
#define fw_planes        ((planes_fn)FN(0x080a3288))
#define fw_frames        ((frames_fn)FN(0x080a31e0))
#define fw_cutoff_hz     ((curve_fn)FN(0x080a01bc))        /* knob 0..1 -> Hz (Filter, EQ Freq display type 10) */

#define APP        ((uint8_t *)0x24013cb0u)
#define SETTINGS   (APP + 0x7fd0u)                          /* settings store (globals: tempo, Compressor, ...) */
#define SCREEN_ID  0x7fe4u                                  /* app: current screen; +0x7fe5 the previous one */
#define SCR_TOOLS  0x25                                     /* Tools: the settings page (page code 0x40) */
#define PAGE_SET   0x40

#define P_COMP_ON  0x96                                     /* stock "Compressor:" (On/Off, xml globcomp) */
#define P_C_THRESH 0x1a1
#define P_C_RATIO  0x1a2
#define P_C_ATTACK 0x1a3
#define P_C_REL    0x1a5
#define P_C_GAIN   0x1a6
#define P_D_TYPE   0x1a7
#define P_D_DRIVE  0x1a8
#define P_D_TONE   0x1a9
#define P_D_MIX    0x1ab
#define P_D_LEVEL  0x1ac

#define FS         48000.0f
#define SR_MS      48                                       /* samples per ms */

/* --- registration and the settings store -------------------------------------------------------------------------- */
static const char *const dist_names[] = {"Off", "Soft", "Hard", "Fold", "Tube"};
enum { D_OFF, D_SOFT, D_HARD, D_FOLD, D_TUBE, D_TYPES };

struct pdef { uint16_t id; uint8_t type; const char *label; int min, max, def; const char *xml; };
static const struct pdef pdefs[] = {
    {P_C_THRESH, 7, "Threshold:", -48000, 0, -4000, "pkcthresh"},    /* type 7: milli-dB, "-4.0 dB" */
    {P_C_RATIO, 1, "Ratio:", 1, 20, 4, "pkcratio"},                  /* type 1: integer (x:1) */
    {P_C_ATTACK, 1, "Attack ms:", 1, 200, 10, "pkcattack"},
    {P_C_REL, 1, "Release ms:", 10, 2000, 250, "pkcrelease"},
    {P_C_GAIN, 7, "Gain:", -12000, 24000, -4000, "pkcgain"},
    {P_D_TYPE, 0, "Dist Type:", 0, D_TYPES, D_OFF, "pkdtype"},       /* list */
    {P_D_DRIVE, 7, "Drive:", 0, 36000, 12000, "pkddrive"},
    {P_D_TONE, 10, "Tone:", 0, 1000, 1000, "pkdtone"},               /* type 10: Hz, the stock cutoff curve */
    {P_D_MIX, 8, "Mix:", 0, 1000, 1000, "pkdmix"},
    {P_D_LEVEL, 7, "Level:", -24000, 12000, 0, "pkdlevel"},
};
#define NPDEFS (int)(sizeof pdefs / sizeof pdefs[0])

/* from interp_register (filter.c): the parameter table */
void master_register(void *table)
{
    for (int k = 0; k < NPDEFS; k++) {
        const struct pdef *p = &pdefs[k];
        if (p->type == 0)
            fw_register_list(table, p->id, p->label, dist_names, p->max, p->xml);
        else
            fw_register_knob(table, p->id, p->type, p->label, p->min, p->max, p->xml);
    }
}

/* hook at the settings store init's last add (0x08089f78): that add, then ours with their defaults */
void master_store_add(void *store, unsigned param, int value)
{
    fw_store_add(store, param, value);
    for (int k = 0; k < NPDEFS; k++)
        fw_store_add(store, pdefs[k].id, pdefs[k].def);
}

/* --- pages: Tools screen, left / right arrow ----------------------------------------------------------------------- */
struct mstate {
    uint32_t magic;
    uint8_t page;                /* 0 = settings (stock), 1 = Compressor, 2 = Distortion; reset by the Tools button */
    uint8_t pad[3];
};
#define MS ((volatile struct mstate *)0x2406d400u)
#define MMAGIC 0x4d535452u       /* "MSTR" */
enum { PG_SET, PG_COMP, PG_DIST };

static const uint16_t comp_page[] = {P_COMP_ON, P_C_THRESH, P_C_RATIO, P_C_ATTACK, P_C_REL, P_C_GAIN, 0};
static const uint16_t dist_page[] = {P_D_TYPE, P_D_DRIVE, P_D_TONE, P_D_MIX, P_D_LEVEL, 0};

static unsigned page(void)
{
    return MS->magic == MMAGIC ? MS->page : PG_SET;
}

static void show(uint8_t *app, unsigned pg)
{
    MS->magic = MMAGIC;
    MS->page = (uint8_t)pg;
    uint8_t prev = app[SCREEN_ID + 1];                  /* back target: keep what it was before the Tools screen */
    fw_screen(app, SCR_TOOLS, 0, 0);                    /* rebuilds the page (page code 0x40) */
    app[SCREEN_ID + 1] = prev;
}

/* left arrow (padpages_left): settings -> Compressor, Distortion -> settings; 1 if taken */
int master_left(uint8_t *app)
{
    if (app[SCREEN_ID] != SCR_TOOLS)
        return 0;
    unsigned pg = page();
    if (pg == PG_SET)
        show(app, PG_COMP);
    else if (pg == PG_DIST)
        show(app, PG_SET);
    return 1;
}

/* right arrow (master_thunk.S, the right arrow's case for screen 0x25): settings -> Distortion, Compressor -> settings */
void master_right(uint8_t *app)
{
    if (app[SCREEN_ID] != SCR_TOOLS)
        return;
    unsigned pg = page();
    if (pg == PG_SET)
        show(app, PG_DIST);
    else if (pg == PG_COMP)
        show(app, PG_SET);
}

/* Tools button (master_thunk.S): always the settings page first */
void master_tools(void)
{
    if (MS->magic == MMAGIC)
        MS->page = PG_SET;
}

/* clip_page (clipshift.c), after the stock builder: the settings page's list replaced while a master page is shown */
int master_page(void *app, const void *msg, uint8_t *list)
{
    unsigned code = *(const uint16_t *)((const uint8_t *)msg + 4) & ~0x100u;
    unsigned pg = page();
    if (code != PAGE_SET || pg == PG_SET)
        return 0;
    *(volatile uint32_t *)list = 0;
    for (const uint16_t *p = pg == PG_COMP ? comp_page : dist_page; *p; p++)
        fw_list_add(list, *p, fw_store_get((const uint8_t *)app + 0x7fd0u, *p));
    return 1;
}

/* --- compressor: settings onto the live object, every block (hook at 0x08097056) ----------------------------------- */
#define C_THRESH  0x428
#define C_RATIO   0x42c
#define C_MAKEUP  0x430
#define C_ATTACK  0x448
#define C_RELEASE 0x44c

void master_comp(uint8_t *comp, void *engine)
{
    int ratio = fw_store_get(SETTINGS, P_C_RATIO);
    if (ratio >= 1) {                                    /* our entries are there (0 = missing: stock values stay) */
        int att = fw_store_get(SETTINGS, P_C_ATTACK), rel = fw_store_get(SETTINGS, P_C_REL);
        *(volatile float *)(comp + C_THRESH) = (float)fw_store_get(SETTINGS, P_C_THRESH) * 0.001f;
        *(volatile float *)(comp + C_RATIO) = (float)(ratio > 20 ? 20 : ratio);
        *(volatile float *)(comp + C_MAKEUP) = (float)fw_store_get(SETTINGS, P_C_GAIN) * 0.001f;
        *(volatile int32_t *)(comp + C_ATTACK) = (att < 1 ? 1 : att > 200 ? 200 : att) * SR_MS;
        *(volatile int32_t *)(comp + C_RELEASE) = (rel < 10 ? 10 : rel > 2000 ? 2000 : rel) * SR_MS;
    }
    fw_comp(comp, engine);
}

/* --- distortion ---------------------------------------------------------------------------------------------------- */
static float exp2_fast(float x)
{
    if (x < -60.0f)
        return 0.0f;
    if (x > 60.0f)
        x = 60.0f;
    int i = (int)x - (x < 0.0f && (float)(int)x != x);
    float f = x - (float)i, p = 1.0f + f * (0.6951f + f * (0.2262f + f * 0.0782f));
    union { float f; uint32_t u; } v = {p};
    v.u += (uint32_t)i << 23;
    return v.f;
}

static float db_gain(int mdb)
{
    return exp2_fast((float)mdb * (0.001f / 6.0206f));
}

static inline __attribute__((always_inline)) float tanh_r(float x)
{
    x = x > 3.0f ? 3.0f : x < -3.0f ? -3.0f : x;
    float x2 = x * x;
    return x * (27.0f + x2) / (27.0f + 9.0f * x2);
}

#define TUBE_BIAS 0.35f
static inline __attribute__((always_inline)) float shape(int type, float u)
{
    switch (type) {
    case D_SOFT:
        return tanh_r(u);
    case D_HARD:
        return u > 1.0f ? 1.0f : u < -1.0f ? -1.0f : u;
    case D_FOLD: {                                        /* triangle fold: identity up to +-1, then back and forth */
        float t = (u + 1.0f) * 0.25f;
        t -= (float)(int)t - (t < 0.0f && (float)(int)t != t);
        float a = t - 0.5f;
        return 1.0f - 4.0f * (a < 0.0f ? -a : a);
    }
    default:                                              /* Tube: asymmetric, even harmonics; DC removed after */
        return tanh_r(u + TUBE_BIAS) - tanh_r(TUBE_BIAS);
    }
}

/* 2x half-band (31 taps, Kaiser 7): odd taps 1, 3, .. 15; centre 0.5 */
static const float HB[8] = {0.314318663f, -0.094598776f, 0.046056884f, -0.023741433f,
                            0.011624296f, -0.005037228f, 0.001760217f, -0.000394379f};
#define HLEN 16

struct dch {
    float x[HLEN];               /* input history, x[0] newest (x[15] = the dry signal, aligned with the output) */
    float sb[HLEN];              /* shaped odd (in-between) samples, newest first */
    float sa[8];                 /* shaped even samples, newest first */
    float lp, dcx, dcy;          /* tone low-pass, DC blocker */
};
struct dist {
    uint32_t magic;
    float drive, mix, level;     /* smoothed: the last block's values */
    struct dch ch[2];
};
#define DS ((struct dist *)0x2406d410u)
#define DMAGIC 0x44495354u       /* "DIST" */

static float run1(struct dch *c, int type, float in, float drive, float tone_a, int tone_on)
{
    for (int i = HLEN - 1; i > 0; i--)
        c->x[i] = c->x[i - 1];
    c->x[0] = in;
    /* up: even = x[n-8], odd = interpolated at n-7.5 */
    float b = 0.0f;
    for (int m = 0; m < 8; m++)
        b += HB[m] * (c->x[7 - m] + c->x[8 + m]);
    float sa = shape(type, c->x[8] * drive);
    float sbv = shape(type, 2.0f * b * drive);
    for (int i = 7; i > 0; i--)
        c->sa[i] = c->sa[i - 1];
    c->sa[0] = sa;
    for (int i = HLEN - 1; i > 0; i--)
        c->sb[i] = c->sb[i - 1];
    c->sb[0] = sbv;
    /* down: centre sa[7] (= x[n-15]) */
    float y = 0.5f * c->sa[7];
    for (int m = 0; m < 8; m++)
        y += HB[m] * (c->sb[7 - m] + c->sb[8 + m]);
    if (type == D_TUBE) {                                  /* DC blocker, ~8 Hz */
        float o = y - c->dcx + 0.999f * c->dcy;
        c->dcx = y;
        c->dcy = o;
        y = o;
    }
    if (tone_on) {
        c->lp += tone_a * (y - c->lp);
        y = c->lp;
    }
    return y;
}

/* master_thunk.S at 0x08096d1c (bus 0 = r4): bus 0 through the distortion */
void master_dist(void *bus0)
{
    struct dist *d = DS;
    int type = fw_store_get(SETTINGS, P_D_TYPE);
    if (type <= D_OFF || type >= D_TYPES) {
        d->magic = 0;                                    /* fresh state when it is switched on again */
        return;
    }
    if (*((const uint8_t *)bus0 + 0x10))                 /* silent: nothing to shape (the tails are 15 samples) */
        return;
    int n = fw_frames(bus0);
    if (n <= 0 || n > 512)
        return;
    float *l, *r;
    fw_planes(bus0, &l, &r);
    if (!l)
        return;

    float drive = db_gain(fw_store_get(SETTINGS, P_D_DRIVE));
    float mix = (float)fw_store_get(SETTINGS, P_D_MIX) * 0.001f;
    float level = db_gain(fw_store_get(SETTINGS, P_D_LEVEL));
    mix = mix < 0.0f ? 0.0f : mix > 1.0f ? 1.0f : mix;
    if (d->magic != DMAGIC) {
        uint32_t *w = (uint32_t *)d;
        for (unsigned k = 0; k < sizeof *d / 4; k++)
            w[k] = 0;
        d->drive = drive;
        d->mix = mix;
        d->level = level;
        d->magic = DMAGIC;
    }
    int tone = fw_store_get(SETTINGS, P_D_TONE), tone_on = tone < 990;
    float tone_a = 1.0f;
    if (tone_on) {
        float hz = fw_cutoff_hz((float)tone * 0.001f);
        hz = hz < 20.0f ? 20.0f : hz > 20000.0f ? 20000.0f : hz;
        float w = 6.2831853f * hz / FS;                  /* one-pole: a = 1 - e^-w, ~ w / (1 + w) */
        tone_a = w / (1.0f + w);
    }

    /* per-sample ramps from the last block's values (no zipper) */
    float inv = 1.0f / (float)n;
    float dr = d->drive, dd = (drive - dr) * inv;
    float mx = d->mix, dm = (mix - mx) * inv;
    float lv = d->level, dl = (level - lv) * inv;
    for (int k = 0; k < n; k++) {
        dr += dd;
        mx += dm;
        lv += dl;
        float wl = run1(&d->ch[0], type, l[k], dr, tone_a, tone_on);
        float dryl = d->ch[0].x[HLEN - 1];
        l[k] = (dryl + mx * (wl - dryl)) * lv;
        if (r && r != l) {
            float wr = run1(&d->ch[1], type, r[k], dr, tone_a, tone_on);
            float dryr = d->ch[1].x[HLEN - 1];
            r[k] = (dryr + mx * (wr - dryr)) * lv;
        }
    }
    d->drive = drive;
    d->mix = mix;
    d->level = level;
}
