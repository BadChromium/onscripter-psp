#ifndef PSPAV_TIMING_H
#define PSPAV_TIMING_H
/* A published frame is paced externally and needs its real AU timestamp.
 * Preserve the historical direct-player convention outside that path. */
static inline int pspavPresentationTimestamp(int current,int previous,int publishing){
    return publishing ? current : previous;
}
#endif
