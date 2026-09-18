#ifndef BIMAN_MASK_GAIN_H
#define BIMAN_MASK_GAIN_H
// Called in the framebuffer's blue-channel precision (5 or 8 bits).
// h02 QLIE $02 reference fit: gain=4, phase spans 0..(max+1)*5.
static inline unsigned bimanMaskWeight(unsigned phase, unsigned mask,
                                      unsigned maximum, unsigned gain)
{
    const unsigned threshold = mask * gain;
    if (phase <= threshold) return 0;
    const unsigned weight = phase - threshold;
    return weight > maximum ? maximum : weight;
}
#endif
