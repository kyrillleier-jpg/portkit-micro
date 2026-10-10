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
 * is half, +100 % double speed). The clip's tempo comes from its beat count: the clip setup 0x080b40fc turns Beat
 * Count (pad +0xb80, set from 0xb4; 0 = Auto) or, on Auto, its power-of-two estimate (r2 at 0x080b4258) into the
 * clip's length in ticks (beats x 960). Both become round(beats / speed), at least 1: the stretch is quantized to whole
 * beats, as with Beat Count itself. The setup runs at every trigger and loop start (0x080b5f5a), so a change applies
 * from the next loop.
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
#define PAD_BEATCOUNT  0xb80
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
static int stretched(const uint8_t *pad, int beats)
{
    if (beats < 1 || pad[PAD_SLICED])
        return beats;
    int p = (int)pad_setting(pad, P_STRETCH);
    if (p == 0 || p < -100 || p > 100)
        return beats;
    /* beats / speed: speed = (100 + p) / 100 above 0, 100 / (100 - p) below */
    int num = p > 0 ? beats * 100 : beats * (100 - p);
    int den = p > 0 ? 100 + p : 100;
    int b = (num + den / 2) / den;
    return b < 1 ? 1 : b > 512 ? 512 : b;
}

/* thunks: 0x080b42ac `ldr.w r3, [sl, #0xb80]` and 0x080b4258 `vmov s15, r2` (Auto estimate), pad in sl */
int clip_beatcount(const uint8_t *pad)
{
    int beats = *(const int32_t *)(pad + PAD_BEATCOUNT);
    return beats ? stretched(pad, beats) : 0;
}

int clip_autobeats(const uint8_t *pad, int beats)
{
    return stretched(pad, beats);
}
