// Deliberately narrow eligibility. Complex scenes retain the CPU renderer.
int ONScripterLabel::tryPmfGpuFrame()
{
#if defined(PSP) && defined(BPP16)
    if(pmf_sprite_no<0||all_sprite_hide_flag||windowback_flag||nega_mode||monocro_flag||
       current_font!=&sentence_font||!current_font->is_transparent||
       current_font->window_color[0]||current_font->window_color[1]||current_font->window_color[2]||
       remaining_time>=0||!(event_mode&WAIT_INPUT_MODE)||!(event_mode&WAIT_TEXT_MODE)||
       automode_flag||autoclick_time||root_button_link.next||system_menu_mode!=SYSTEM_NULL||
       (refreshMode()&(REFRESH_TEXT_MODE|REFRESH_SHADOW_MODE))!=(REFRESH_TEXT_MODE|REFRESH_SHADOW_MODE))return 0;
    AnimationInfo *movie=&sprite_info[pmf_sprite_no];
    if(!movie->visible||movie->trans_mode!=AnimationInfo::TRANS_PMF||movie->trans!=256||
       !movie->abs_flag||movie->pos.x||movie->pos.y||movie->pos.w!=480||movie->pos.h!=272)return 0;
    for(int i=0;i<MAX_SPRITE_NUM;++i)
        if(i!=pmf_sprite_no&&sprite_info[i].visible&&sprite_info[i].image_surface)return 0;
    for(int i=0;i<3;++i)if(tachi_info[i].image_surface)return 0;
    for(int i=0;i<MAX_PARAM_NUM;++i)if(bar_info[i]||prnum_info[i])return 0;
    if(draw_cursor_flag&&(cursor_info[CURSOR_WAIT_NO].image_surface||cursor_info[CURSOR_NEWPAGE_NO].image_surface))return 0;
    if(text_info.image_surface&&(text_info.image_surface->w!=480||text_info.image_surface->h!=272))return 0;
    return pspPmfLayerPresentGpu(&pmf_background_cache,screen_surface,&sentence_font_info.pos,text_info.alpha_buf);
#else
    return 0;
#endif
}
