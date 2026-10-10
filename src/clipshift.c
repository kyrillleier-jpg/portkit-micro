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
