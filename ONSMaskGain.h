#ifndef ONS_MASK_GAIN_H
#define ONS_MASK_GAIN_H
// Called in the framebuffer's blue-channel precision (5 or 8 bits).
// Gain-controlled mask transition; phase spans 0..(maximum+1)*(gain+1).
static inline unsigned onsPspMaskWeight(unsigned phase, unsigned mask,
                                      unsigned maximum, unsigned gain)
{
    const unsigned threshold = mask * gain;
    if (phase <= threshold) return 0;
    const unsigned weight = phase - threshold;
    return weight > maximum ? maximum : weight;
}
#endif
