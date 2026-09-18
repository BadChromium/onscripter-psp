#ifndef PSP_GAME_CONFIG_H
#define PSP_GAME_CONFIG_H
// Override for each game build; the default is for engine development only.
#ifndef ONS_PSP_GAME_ID
#define ONS_PSP_GAME_ID "ONSP00001"
#endif
static const char onsPspGameId[] = ONS_PSP_GAME_ID;
// PSP savedata namespaces use four uppercase letters followed by five digits.
typedef char onsPspGameIdLengthCheck[(sizeof(onsPspGameId) == 10) ? 1 : -1];
static inline bool onsPspValidGameId() {
    for (int i=0;i<9;++i) {
        const char c=onsPspGameId[i];
        if (i<4 ? (c<'A' || c>'Z') : (c<'0' || c>'9')) return false;
    }
    return true;
}
#endif
