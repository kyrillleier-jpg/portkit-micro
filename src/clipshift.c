/*
 * Shift for clip pads (portkit): rotates the clip's audio against its loop by -100 .. +100 ms, so a loop whose first
 * transient sits off the file start lands on the beat. +s: at the downbeat you hear the file s ms in; the last s ms of
 * the loop come from the file start. -s: the downbeat plays the file's last s ms first.
 *
 * Clip voices (class B, 0x080b5aa8) read their sample by absolute frame position through the pad's stream (pad +0x24):
 * 0x080a4500 (one channel plane) and 0x080a44c8 (both planes, streamed files), all from 0x080b55ac; the segment
 * starts prefetch with 0x080a4624 (seek, 0x080b47d2 / 0x080b4b4c). Each read [pos, pos + n) inside the file becomes
 * [(pos + shift) mod frames, ...), split at the file end; reads past the end stay as they were (silence). The seek gets
 * the same mapping. Slicer pads (pad +0x254 set) are left alone. Positions are file frames; 1 ms = 48 frames (files at
 * other rates shift by a little more or less than the shown ms).
 *
 * Play length for clip pads: Full (default, the whole clip) or 1/4 .. 32 bars in quarter-bar steps. Clip voices play
 * segment by segment (re/symbols.md "Abspiellaenge"); when the next segment index reaches the clip's segment count
 * (pad +0x240 + pad +0x244, compared at 0x080b5f2e / 0x080b611a) the clip loops back to segment 0 or stops. With Sync
 * on (pad +0x1f5), a segment is one Sync unit: pad +0x220 = its length in ticks, 960 per beat (Sync list 0x76: 1 bar
 * 3840, 1/2 1920, 1/4 960, 1/8 480, 1/16 240; "Slice" 0xf0000 is the slicer). The count is capped at the play length:
 * quarter bars * 960 / unit, rounded, at least 1, so the length is exact down to the Sync unit (a quarter bar is one
 * beat, 4/4). Sync None or Slice: no cap.
 *
 * Stretch for clip pads: -100 .. +100 %, speed x 1 / (1 + |p| / 100) below 0 and x (1 + p / 100) above (so -100 %
 * is half, +100 % double speed). Clips play their file at its own rate and keep time by starting each Sync unit
 * (segment k) at file position k x segment length (pad +0x1fc), 0x080b4a68 in the segment start 0x080b490c
 * (re/symbols.md "Stretch"). Stretch scales that position by the speed, live at every segment start (pitch unchanged,
 * same jumping as when the firmware follows the song tempo), and the clip's segment count by 1 / speed: the loop bound
 * (clip_segments, with Play Len) and the "last segment" test 0x080b49b4. (pkJ-pkL scaled the clip length in the setup
 * 0x080b40fc instead; a synced clip does not re-run that setup on the device.)
 */
#include <stdint.h>

#define FN(addr) ((addr) | 1u)

typedef int (*read1_fn)(void *stream, float *dst, int n, int pos, int ch);
typedef int (*read2_fn)(void *stream, float *left, float *right, int n, int pos);
typedef void (*seek_fn)(void *stream, int pos);
typedef int (*frames_fn)(void *stream);
#define fw_read1  ((read1_fn)FN(0x080a4500))
#define fw_read2  ((read2_fn)FN(0x080a44c8))
#define fw_seek   ((seek_fn)FN(0x080a4624))
#define fw_frames ((frames_fn)FN(0x080a45ac))   /* frame count; 0x10000000 if the source does not know it */

#define P_SHIFT        0x1c3
#define P_PLAYLEN      0x1c4      /* list index: 0 = Full, q = q quarter bars (1 .. 128) */
#define PAD_SEGMENTS   0x240      /* + 0x244: segment count */
#define P_STRETCH      0x1c5      /* -100 .. 100 % */
#define PAD_SYNCED     0x1f5
#define PAD_UNIT_TICKS 0x220      /* int64 */
#define TICKS_PER_BEAT 960
#define SLICE_TICKS    0xf0000
#define PAD_SLICED     0x254
#define FRAMES_PER_MS  48
#define UNKNOWN_FRAMES 0x10000000

unsigned pad_setting(const uint8_t *pad, unsigned param);     /* filter.c: the pad's value from its app record */

/* the pad's shift in frames, 0 if none applies; *frames = the file's frame count */
static int shift_of(const uint8_t *pad, void *stream, int *frames)
{
    if (!pad || pad[PAD_SLICED])
        return 0;
    int ms = (int)pad_setting(pad, P_SHIFT);
    if (ms == 0 || ms < -100 || ms > 100)
        return 0;
    int total = fw_frames(stream);
    if (total <= 0 || total >= UNKNOWN_FRAMES)
        return 0;
    *frames = total;
    int s = (ms * FRAMES_PER_MS) % total;
    return s < 0 ? s + total : s;                       /* 0 <= s < total */
}

/* next run: from stock position pos, at most n frames; *at = where to read it. Returns the run length. */
static int run(int pos, int n, int s, int total, int *at)
{
    if (pos < 0 || pos >= total) {                      /* outside the file: as stock (zero-filled) */
        *at = pos;
        if (pos < 0)
            return -pos < n ? -pos : n;
        return n;
    }
    int p = pos + s;
    if (p >= total)
        p -= total;
    int m = total - pos;                                /* stay inside the file in stock terms */
    if (total - p < m)
        m = total - p;                                  /* and in shifted terms (wrap) */
    *at = p;
    return m < n ? m : n;
}

/* thunks in clipshift_thunk.S pass the pad (r4 of 0x080b55ac / 0x080b4644 / 0x080b490c) as the last argument */
int clip_read1(void *stream, float *dst, int n, int pos, int ch, const uint8_t *pad)
{
    int total, s = shift_of(pad, stream, &total);
    if (!s)
        return fw_read1(stream, dst, n, pos, ch);
    int ok = 0;
    while (n > 0) {
        int at, m = run(pos, n, s, total, &at);
        ok |= fw_read1(stream, dst, m, at, ch);
        dst += m;
        pos += m;
        n -= m;
    }
    return ok;
}

int clip_read2(void *stream, float *left, float *right, int n, int pos, const uint8_t *pad)
{
    int total, s = shift_of(pad, stream, &total);
    if (!s)
        return fw_read2(stream, left, right, n, pos);
    int ok = 0;
    while (n > 0) {
        int at, m = run(pos, n, s, total, &at);
        ok |= fw_read2(stream, left, right, m, at);
        left += m;
        if (right)
            right += m;
        pos += m;
        n -= m;
    }
    return ok;
}

void clip_seek(void *stream, int pos, const uint8_t *pad)
{
    int total, s = shift_of(pad, stream, &total);
    if (s && pos >= 0 && pos < total) {
        pos += s;
        if (pos >= total)
            pos -= total;
    }
    fw_seek(stream, pos);
}

static int stretched_count(const uint8_t *pad, int count);

/* --- play length ------------------------------------------------------------------------------------------------- */
const char *const playlen_names[129] = {
    "Full", "1/4", "1/2", "3/4", "1", "1 1/4", "1 1/2", "1 3/4", "2", "2 1/4",
    "2 1/2", "2 3/4", "3", "3 1/4", "3 1/2", "3 3/4", "4", "4 1/4", "4 1/2", "4 3/4",
    "5", "5 1/4", "5 1/2", "5 3/4", "6", "6 1/4", "6 1/2", "6 3/4", "7", "7 1/4",
    "7 1/2", "7 3/4", "8", "8 1/4", "8 1/2", "8 3/4", "9", "9 1/4", "9 1/2", "9 3/4",
    "10", "10 1/4", "10 1/2", "10 3/4", "11", "11 1/4", "11 1/2", "11 3/4", "12", "12 1/4",
    "12 1/2", "12 3/4", "13", "13 1/4", "13 1/2", "13 3/4", "14", "14 1/4", "14 1/2", "14 3/4",
    "15", "15 1/4", "15 1/2", "15 3/4", "16", "16 1/4", "16 1/2", "16 3/4", "17", "17 1/4",
    "17 1/2", "17 3/4", "18", "18 1/4", "18 1/2", "18 3/4", "19", "19 1/4", "19 1/2", "19 3/4",
    "20", "20 1/4", "20 1/2", "20 3/4", "21", "21 1/4", "21 1/2", "21 3/4", "22", "22 1/4",
    "22 1/2", "22 3/4", "23", "23 1/4", "23 1/2", "23 3/4", "24", "24 1/4", "24 1/2", "24 3/4",
    "25", "25 1/4", "25 1/2", "25 3/4", "26", "26 1/4", "26 1/2", "26 3/4", "27", "27 1/4",
    "27 1/2", "27 3/4", "28", "28 1/4", "28 1/2", "28 3/4", "29", "29 1/4", "29 1/2", "29 3/4",
    "30", "30 1/4", "30 1/2", "30 3/4", "31", "31 1/4", "31 1/2", "31 3/4", "32"
};

/* thunk (clip_segments_thunk): replaces `ldrd r1, r2, [r6, #0x240]` before `add r2, r1`; returns the segment count to
   use (pad = r6) */
int clip_segments(const uint8_t *pad)
{
    int count = *(const int32_t *)(pad + PAD_SEGMENTS) + *(const int32_t *)(pad + PAD_SEGMENTS + 4);
    if (pad[PAD_SLICED])
        return count;
    if (!pad[PAD_SYNCED] || count < 1)
        return count;
    count = stretched_count(pad, count);
    int q = (int)pad_setting(pad, P_PLAYLEN);
    int32_t unit = *(const int32_t *)(pad + PAD_UNIT_TICKS);
    if (q <= 0 || q > 128 || unit <= 0 || unit >= SLICE_TICKS || *(const int32_t *)(pad + PAD_UNIT_TICKS + 4))
        return count;
    int limit = (q * TICKS_PER_BEAT + unit / 2) / unit;
    if (limit < 1)
        limit = 1;
    return limit < count ? limit : count;
}

/* --- stretch -------------------------------------------------------------------------------------------------------- */
/* the pad's Stretch speed (1 = none) */
static float clip_speed_of(const uint8_t *pad)
{
    if (pad[PAD_SLICED])
        return 1.0f;
    int p = (int)pad_setting(pad, P_STRETCH);
    if (p == 0 || p < -100 || p > 100)
        return 1.0f;
    return p > 0 ? 1.0f + (float)p * 0.01f : 1.0f / (1.0f - (float)p * 0.01f);
}

/* segments at this speed, rounded, at least 1 */
static int stretched_count(const uint8_t *pad, int count)
{
    float n = (float)count / clip_speed_of(pad) + 0.5f;
    int c = (int)n;
    return c < 1 ? 1 : c;
}

/* thunk (clip_pos_thunk): `vmul.f32 s16, s15, s16` (segment index x segment length) at 0x080b4a68 */
float clip_speed(const uint8_t *pad)
{
    return clip_speed_of(pad);
}

/* thunk (clip_last_thunk): `ldr.w r3, [r4, #0x240]` at 0x080b49b4 (r3 - 1 == index: last segment) */
int clip_last_count(const uint8_t *pad)
{
    int count = *(const int32_t *)(pad + PAD_SEGMENTS);
    return count < 1 ? count : stretched_count(pad, count);
}


/* --- Sync 1/32 ------------------------------------------------------------------------------------------------------ */
/* Sync (0x76) list: the stock 7 entries (pointers into the stock strings, list at 0x080c4770) + "1/32", appended so the
   stored indexes of old presets keep their meaning (6 = None). Its beats table (0x080c4f7c, read only by the clip param
   handler at 0x080b7386 through the literal 0x080b74e4, x 960 ticks) gets the same eighth entry: 1/32 = 0.125 beat,
   120 ticks. The preset reader's legacy conversion (0x080807b6) keeps searching the stock 7. */
typedef void (*register_list_fn)(void *table, int param, const char *label, const char *const *names, int count,
                                 const char *xml);
#define fw_register_list ((register_list_fn)FN(0x08069e7c))

const char *const sync_names[8] = {
    (const char *)0x080c3488u, (const char *)0x080c33acu, (const char *)0x080c33b4u, (const char *)0x080c33b8u,
    (const char *)0x080c33bcu, (const char *)0x080c33c0u, (const char *)0x080c21ccu, "1/32",
};
const float sync_beats[8] = {1024.0f, 4.0f, 2.0f, 1.0f, 0.5f, 0.25f, 0.0f, 0.125f};

void sync_register(void *table, int param, const char *label, const char *const *names, int count, const char *xml)
{
    (void)names;
    (void)count;
    fw_register_list(table, param, label, sync_names, 8, xml);
}

/* --- hide Play Len / Stretch where they do nothing ------------------------------------------------------------------- */
/* Both need the clip synced: Quant Size (0x2a) not None (8) and Sync (0x76) neither Slice (0) nor None (6) (pad +0x1f5,
   0x080b6fd4). The page builder 0x08076d8c(app, msg, list, ..) fills a parameter page; the stock hides entries the same
   way (0x080836c8, Delay vs. Beat Sync at 0x08076f48). */
typedef int (*page_fn)(void *app, const void *msg, void *list, int arg);
typedef void *(*record_fn)(void *app, const void *msg);
typedef void (*list_remove_fn)(void *list, unsigned param);
typedef int (*store_get_fn)(const void *store, unsigned param);
#define fw_page        ((page_fn)FN(0x08076d8c))
#define fw_record      ((record_fn)FN(0x08076d54))
#define fw_list_remove ((list_remove_fn)FN(0x080836c8))
#define fw_store_get   ((store_get_fn)FN(0x080894d0))
#define P_QUANT        0x2a
#define P_SYNC         0x76
#define QUANT_NONE     8
#define SYNC_SLICE     0
#define SYNC_NONE      6

static int list_has(const uint8_t *list, unsigned param)
{
    unsigned n = *(const uint32_t *)list;
    for (unsigned i = 0; i < n && i < 0x30; i++)
        if (*(const uint16_t *)(list + 4 + 12 * i) == param)
            return 1;
    return 0;
}

int clip_page(void *app, const void *msg, void *list, int arg)
{
    int r = fw_page(app, msg, list, arg);
    if (!list_has(list, P_PLAYLEN) && !list_has(list, P_STRETCH))
        return r;
    const void *rec = fw_record(app, msg);
    int quant = fw_store_get(rec, P_QUANT), sync = fw_store_get(rec, P_SYNC);
    if (quant == QUANT_NONE || sync == SYNC_SLICE || sync == SYNC_NONE) {
        fw_list_remove(list, P_PLAYLEN);
        fw_list_remove(list, P_STRETCH);
    }
    return r;
}
