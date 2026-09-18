#ifndef PSP_PMF_TIMING_H
#define PSP_PMF_TIMING_H
inline int pspPmfDelayAfterPublish(int interval_ms,unsigned int elapsed_us,bool pending)
{
    if(pending)return 1;
    if(interval_ms<1)interval_ms=1;
    if(interval_ms>100)interval_ms=100;
    unsigned int elapsed_ms=elapsed_us/1000;
    return elapsed_ms>=(unsigned int)interval_ms ? 1 : interval_ms-(int)elapsed_ms;
}
#endif
