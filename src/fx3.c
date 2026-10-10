/*
 * FX3: a third send effect on an engine bus of its own (portkit). For now a second reverb (any of the reverb types,
 * src/reverb.c), next to the stock FX1 (delay, bus 0xd) and FX2 (reverb, bus 0xe).
 *
 * Buses (re/symbols.md "FX3"): the engine has 18 stereo buses of 128 frames at engine +0x150e4, 20 bytes each
 * (0x080a82b8), all allocated (0x08094c48) and cleared every block (0x080a82f4); 0-11 are the outputs (pad Output),
 * 0xd / 0xe the FX sends, 0xf / 0x10 special; 0xc and 0x11 are unused. FX3 uses 0xc.
 * - Send: every pad mixes its voices into a scratch buffer and from there into the send buses (gain = pad's send),
 *   then into its output, but only when one of its sends is on (sample pads 0x080b13e0, clip pads 0x080b7d8c); the
 *   checks also look at FX3 Send now, and the final mix (0x080b2600, 0x080b8046) first adds scratch x FX3 gain to bus
 *   0xc (0x080a33ec). FX3 Send (0x1c8) is a pad setting read from the app record, like Stretch.
 * - Effect: the engine's block driver 0x08096530 mixes bus 0xe into bus 0 (Out1/2) at 0x08096d04; right after that,
 *   bus 0xc runs through FX3 and is added to bus 0 as well. No graph node: the reverb runs here, at 29.8 kHz like the
 *   stock reverb (decimated 48 -> 29.8 kHz with a two-pole low-pass, interpolated back), with a pre-delay of its own.
 * - Settings: FX cell record row 3 (cell 0x330, app +0x2200 + 3 x 0x18), unused by the stock firmware (its eight init
 *   sites make it an empty type-0 record; patches/fx3.py makes them type 0x44 = reverb, fx3_record_ensure is the
 *   fallback). Row 2 (0x320) is the master EQ (type 0x36). The record is edited on the stock FX cell page (screen 0x23,
 *   right arrow on the Effects screen with FX3 selected); engine messages for 0x330 find no node and are dropped
 *   (0x08095440). Right arrow again: the master EQ (fx3_right).
 * - Memory: a plate state (0xb0 + its 12 buffers, ~210 KB, the stock init 0x080a9c94) and a pre-delay ring, from the
 *   firmware's heap (0x08042dc0, a bump allocator without free) when the Effects screen is built at boot, and only if
 *   more than 4 MB stay free (0x08042e44); otherwise FX3 stays silent.
 */
#include <stdint.h>

#pragma GCC optimize("O2", "no-tree-loop-distribute-patterns")

#define FN(addr) ((addr) | 1u)

typedef void *(*bus_fn)(void *engine, unsigned id);
typedef void (*mix_fn)(void *dst, const void *src);
typedef void (*mix_gain_fn)(void *dst, const void *src, float gain);
typedef int (*planes_fn)(void *buf, float **l, float **r);
typedef int (*frames_fn)(void *buf);
typedef void *(*alloc_fn)(unsigned size, unsigned n);
typedef unsigned (*free_fn)(void);
typedef void (*init_fn)(float *state);
typedef float (*curve_fn)(float x);
typedef void (*screen_fn)(void *app, unsigned screen, unsigned a, unsigned b);
typedef void (*cell_fn)(void *app, const void *msg);
typedef int (*store_get_fn)(const void *store, unsigned param);
typedef void (*store_init_fn)(void *store, const uint8_t *type);
#define fw_bus        ((bus_fn)FN(0x080a82b8))
#define fw_mix        ((mix_fn)FN(0x080a3328))
#define fw_mix_gain   ((mix_gain_fn)FN(0x080a33ec))
#define fw_planes     ((planes_fn)FN(0x080a3288))     /* read access: zero-fills a silent buffer; L, R */
#define fw_frames     ((frames_fn)FN(0x080a31e0))
#define fw_alloc      ((alloc_fn)FN(0x08042dc0))
#define fw_heap_free  ((free_fn)FN(0x08042e44))
#define fw_plate_init ((init_fn)FN(0x080a9c94))
#define fw_send_curve ((curve_fn)FN(0x080a04c0))      /* send value / 1000 -> gain (the stock send setters) */
#define fw_store_get  ((store_get_fn)FN(0x080894d0))
#define fw_store_init ((store_init_fn)FN(0x08089fc4))
#define fw_screen     ((screen_fn)FN(0x0808eedc))     /* app: show screen (0x23 = FX cell page of app +0x28) */
#define fw_set_cell   ((cell_fn)FN(0x0807b20c))       /* app command 0x111: app +0x28 = msg +4, notification 0x112 */

unsigned pad_setting(const uint8_t *pad, unsigned param);                                   /* filter.c */
void reverb_run_record(float *state, const void *rec, const float *in, float *outl, float *outr, int n);  /* reverb.c */

#define P_FX3SEND 0x1c8
#define BUS_FX3   0xc
#define BUS_FX2   0xe
#define BUS_SIZE  20
#define APP       ((uint8_t *)0x24013cb0u)
#define FX3_REC   ((void *)(APP + 0x2200u + 3u * 0x18u))
#define CELL_EQ   0x320
#define CELL_FX3  0x330
#define SCR_FXCELL 0x23
#define REC_COUNT 0xa                                   /* store: entry count (u16) */
#define P_DECAY   0x1a
#define P_DAMP    0x1d
#define P_PREDLY  0x1e
#define FS_IN     48000.0f
#define FS_RVB    29800.0f
#define PRE_LEN   16384                                 /* pre-delay ring (>= 12256 = 12000 + 256, the stock range) */
#define MAXN      128                                   /* bus frames */
#define MAXM      (MAXN * 2 / 3 + 4)                    /* 29.8 kHz frames per block */
#define RUN_ON    (30u * 48000u / 32u)                  /* blocks the tail runs on after the last input (~30 s) */

struct fx3 {
    uint32_t magic;
    float *plate;                /* the reverb's plate state (0xb0, buffers allocated by the stock init) */
    float *pre;                  /* pre-delay ring */
    uint32_t pre_w;
    float ph, lp1, lp2, px;      /* decimator: phase (29.8 kHz periods), two-pole low-pass, last filtered input */
    float ol, or_, pl, pr;       /* interpolator: current and previous reverb outputs */
    uint32_t idle;               /* blocks since the bus last had signal */
};
#define F3 ((volatile struct fx3 *)0x2406d200u)
#define F3MAGIC 0x46583321u      /* "FX3!" */

/* the FX3 record made into a reverb record if it is still empty (UI thread: allocates) */
void fx3_record_ensure(void)
{
    if (*(const uint16_t *)((const uint8_t *)FX3_REC + REC_COUNT) == 0) {
        static const uint8_t type = 0x44;
        fw_store_init(FX3_REC, &type);
    }
}

/* boot (Effects screen constructor, UI thread): memory and the record */
void fx3_init(void)
{
    fx3_record_ensure();
    if (F3->magic == F3MAGIC)
        return;
    F3->plate = 0;
    if (fw_heap_free() < 4u * 1024u * 1024u + 512u * 1024u)
        return;
    float *st = fw_alloc(0xb0, 1);
    float *pre = fw_alloc(PRE_LEN * 4, 1);
    if (!st || !pre)
        return;
    for (unsigned k = 0; k < 0xb0 / 4; k++)
        st[k] = 0.0f;
    fw_plate_init(st);
    for (unsigned k = 0; k < PRE_LEN; k++)
        pre[k] = 0.0f;
    F3->pre = pre;
    F3->pre_w = 0;
    F3->ph = F3->lp1 = F3->lp2 = F3->px = 0.0f;
    F3->ol = F3->or_ = F3->pl = F3->pr = 0.0f;
    F3->idle = RUN_ON;
    F3->plate = st;
    F3->magic = F3MAGIC;
}

/* right arrow on the FX cell page (screen 0x23): stock goes on to screen 0x14 (call 0x08083964, hooked). From FX3 it
   opens the master EQ's page instead: select cell 0x320 as a touch does, then the FX cell page again. */
void fx3_right(uint8_t *app, unsigned screen, unsigned a, unsigned b)
{
    if (*(volatile uint16_t *)(app + 0x28) == CELL_FX3) {
        uint16_t m[12] = {0};
        m[2] = CELL_EQ;
        fw_set_cell(app, m);
        fw_screen(app, SCR_FXCELL, 0, 0);
        return;
    }
    fw_screen(app, screen, a, b);
}

/* --- pad sends ------------------------------------------------------------------------------------------------------ */
static float send_gain(const uint8_t *pad)
{
    int v = (int)pad_setting(pad, P_FX3SEND);
    if (v <= 0)
        return 0.0f;
    return fw_send_curve((float)(v > 1000 ? 1000 : v) * 0.001f);
}

/* thunks fx3_check_a / _b: the "any send on" checks' first load; 1 if FX3 Send is on */
int fx3_send_on(const uint8_t *pad)
{
    return F3->magic == F3MAGIC && F3->plate && pad_setting(pad, P_FX3SEND) > 0;
}

/* thunks fx3_mix_a / _b: the pad's final mix (scratch -> its output, 0x080a3328): first scratch x FX3 gain -> bus 0xc */
void fx3_padmix(void *out, const void *scratch, const uint8_t *pad, void *engine)
{
    float g = send_gain(pad);
    if (g > 0.0f && F3->magic == F3MAGIC && F3->plate)
        fw_mix_gain(fw_bus(engine, BUS_FX3), scratch, g);
    fw_mix(out, scratch);
}

/* --- the effect, in the block driver ------------------------------------------------------------------------------- */
/* replaces the driver's "bus 0 += bus 0xe" (0x08096d04): that, then bus 0 += FX3(bus 0xc) */
void fx3_master(void *bus0, void *bus_fx2)
{
    fw_mix(bus0, bus_fx2);
    volatile struct fx3 *f = F3;
    if (f->magic != F3MAGIC || !f->plate)
        return;
    void *bus = (uint8_t *)bus_fx2 - (BUS_FX2 - BUS_FX3) * BUS_SIZE;
    int n = fw_frames(bus);
    if (n <= 0 || n > MAXN)
        return;
    int silent = *((const uint8_t *)bus + 0x10);
    if (silent) {
        if (f->idle >= RUN_ON)
            return;                                     /* no input and the tail has run out */
        f->idle++;
    } else {
        f->idle = 0;
    }
    float *il, *ir, *ol, *or_;
    fw_planes(bus, &il, &ir);
    fw_planes(bus0, &ol, &or_);
    if (!ir)
        ir = il;

    const void *rec = FX3_REC;
    float *st = f->plate;
    st[0] = (float)fw_store_get(rec, P_DECAY) * (0.001f * 0.93f);
    st[1] = (float)fw_store_get(rec, P_DAMP) * 0.001f;
    int pre_d = (int)((float)fw_store_get(rec, P_PREDLY) * 0.001f * 12000.0f) + 256;
    if (pre_d > PRE_LEN - 2)
        pre_d = PRE_LEN - 2;

    /* decimate 48 -> 29.8 kHz: two one-pole low-passes, linear interpolation at the 29.8 kHz instants */
    const float r = FS_RVB / FS_IN, a = 0.6f;            /* corner ~ 7.3 kHz per pole at 48 kHz */
    float tin[MAXM], tl[MAXM], tr[MAXM];
    float ph0 = f->ph, ph = ph0, l1 = f->lp1, l2 = f->lp2, px = f->px;
    float *pre = f->pre;
    uint32_t w = f->pre_w;
    int m = 0;
    for (int k = 0; k < n; k++) {
        float x = 0.5f * (il[k] + ir[k]);
        l1 += a * (x - l1);
        l2 += a * (l1 - l2);
        float cur = l2;
        ph += r;
        if (ph >= 1.0f && m < MAXM) {
            ph -= 1.0f;
            float back = ph / r;                         /* 48 kHz samples since the 29.8 kHz instant */
            float v = cur + (px - cur) * back;
            pre[w & (PRE_LEN - 1)] = v;
            tin[m++] = pre[(w - (uint32_t)pre_d) & (PRE_LEN - 1)];
            w++;
        }
        px = cur;
    }
    f->lp1 = l1;
    f->lp2 = l2;
    f->px = px;
    f->pre_w = w;
    if (m > 0)
        reverb_run_record(st, rec, tin, tl, tr, m);

    /* back to 48 kHz: the same instants, linear between the previous and the current reverb output */
    float cl = f->ol, cr = f->or_, pl = f->pl, pr = f->pr;
    int j = 0;
    ph = ph0;
    for (int k = 0; k < n; k++) {
        ph += r;
        if (ph >= 1.0f && j < m) {
            ph -= 1.0f;
            pl = cl;
            pr = cr;
            cl = tl[j];
            cr = tr[j];
            j++;
        }
        ol[k] += pl + (cl - pl) * ph;
        if (or_ && or_ != ol)
            or_[k] += pr + (cr - pr) * ph;
    }
    f->ph = ph;
    f->ol = cl;
    f->or_ = cr;
    f->pl = pl;
    f->pr = pr;
}
