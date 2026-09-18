// Playback IDs prevent queued completion events from owning newer audio.
ONSAudioGeneration ons_music_generation;
ONSAudioGeneration ons_wave_generation[ONS_MIX_CHANNELS+ONS_MIX_EXTRA_CHANNELS];
int onsPlayChannel(int channel,Mix_Chunk *chunk,int loops)
{
    if(channel<0||channel>=ONS_MIX_CHANNELS+ONS_MIX_EXTRA_CHANNELS)return -1;
    // Halt first: its callback still belongs to the previous generation.
    Mix_HaltChannel(channel);
    SDL_LockAudio();ons_wave_generation[channel].begin();SDL_UnlockAudio();
    int result=Mix_PlayChannel(channel,chunk,loops);
    if(result<0){SDL_LockAudio();ons_wave_generation[channel].retire();SDL_UnlockAudio();}
    return result;
}

bool ONScripterLabel::isCurrentAudioEvent(const SDL_Event &event)
{
    if(event.type!=ONS_SOUND_EVENT&&event.type!=ONS_WAVE_EVENT)return true;
    uint32_t token=(uint32_t)(uintptr_t)event.user.data1;
    if(event.type==ONS_SOUND_EVENT&&event.user.code==ONS_OGG_COMPLETION)
        return ons_music_generation.matches(token);
    if(event.type==ONS_WAVE_EVENT){
        int ch=event.user.code;
        return ch>=0&&ch<ONS_MIX_CHANNELS+ONS_MIX_EXTRA_CHANNELS&&ons_wave_generation[ch].matches(token);
    }
    return true;
}
