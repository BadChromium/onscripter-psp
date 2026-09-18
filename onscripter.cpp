/* -*- C++ -*-
 * 
 *  onscripter.cpp -- main function of ONScripter
 *
 *  Copyright (c) 2001-2006 Ogapee. All rights reserved.
 *
 *  ogapee@aqua.dti2.ne.jp
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include "ONScripterLabel.h"
#include "version.h"
#include "PSPDiagnostic.h"
#if defined(PSP)
#include <unistd.h>
#endif

void optionHelp()
{
    printf( "Usage: onscripter [option ...]\n" );
    printf( "      --cdaudio\t\tuse CD audio if available\n");
    printf( "      --cdnumber no\tchoose the CD-ROM drive number\n");
    printf( "  -f, --font file\tset a TTF font file\n");
    printf( "      --registry file\tset a registry file\n");
    printf( "      --dll file\tset a dll file\n");
    printf( "  -r, --root path\tset the root path to the archives\n");
    printf( "      --fullcsreen\tstart in fullscreen mode\n");
    printf( "      --window\t\tstart in window mode\n");
    printf( "      --force-button-shortcut\tignore useescspc and getenter command\n");
    printf( "      --enable-wheeldown-advance\tadvance the text on mouse wheeldown event\n");
    printf( "      --disable-rescale\tdo not rescale the images in the archives when compiled with -DPDA\n");
    printf( "      --edit\t\tenable editing the volumes and the variables when 'z' is pressed\n");
    printf( "      --key-exe file\tset a file (*.EXE) which contains a key table\n");
    printf( "  -h, --help\t\tshow this help and exit\n");
    printf( "  -v, --version\t\tshow the version information and exit\n");
    exit(0);
}

void optionVersion()
{
    printf("Written by Ogapee <ogapee@aqua.dti2.ne.jp>\n\n");
    printf("Copyright (c) 2001-2006 Ogapee.\n");
    printf("This is free software; see the source for copying conditions.\n");
    exit(0);
}
#if defined(QWS)
int SDL_main( int argc, char **argv )
#elif defined(PSP)
extern "C" int main( int argc, char **argv )
#else
int main( int argc, char **argv )
#endif
{
    // UMD/ISO entry starts beside EBOOT.BIN, while data lives in USRDIR.
#if defined(PSP)
    char startup_cwd[512] = {0};
    if (getcwd(startup_cwd, sizeof(startup_cwd)) &&
        (!strncmp(startup_cwd, "disc0:", 6) || !strncmp(startup_cwd, "umd0:", 5))) {
        if (chdir("disc0:/PSP_GAME/USRDIR") != 0) {
            fprintf(stderr, "Cannot open disc asset directory\n");
            return 1;
        }
    }
#endif
    pspDiagInit();
    pspDiagLog("ISO_STARTUP_DIAG=1");
    pspDiagFileCheck("0.txt");
    pspDiagFileCheck("0.TXT");
    pspDiagFileCheck("arc.nsa");
    pspDiagFileCheck("ARC.NSA");
    pspDiagFileCheck("default.ttf");
    pspDiagFileCheck("DEFAULT.TTF");
    pspDiagFileCheck("gbk_flat.dat");
    pspDiagFileCheck("GBK_FLAT.DAT");
    printf("ONScripter version %s\n", ONS_VERSION );

    ONScripterLabel ons;

#if defined(PSP)
    ons.disableRescale();
    // Honor script useescspc/getenter; forced shortcuts conflate Cross/advance.
#endif

    // ----------------------------------------
    // Parse options
    argv++;
    while( argc > 1 ){
        if ( argv[0][0] == '-' ){
            if ( !strcmp( argv[0]+1, "h" ) || !strcmp( argv[0]+1, "-help" ) ){
                optionHelp();
            }
            else if ( !strcmp( argv[0]+1, "v" ) || !strcmp( argv[0]+1, "-version" ) ){
                optionVersion();
            }
            else if ( !strcmp( argv[0]+1, "-cdaudio" ) ){
                ons.enableCDAudio();
            }
            else if ( !strcmp( argv[0]+1, "-cdnumber" ) ){
                argc--;
                argv++;
                ons.setCDNumber(atoi(argv[0]));
            }
            else if ( !strcmp( argv[0]+1, "f" ) || !strcmp( argv[0]+1, "-font" ) ){
                argc--;
                argv++;
                ons.setFontFile(argv[0]);
            }
            else if ( !strcmp( argv[0]+1, "-registry" ) ){
                argc--;
                argv++;
                ons.setRegistryFile(argv[0]);
            }
            else if ( !strcmp( argv[0]+1, "-dll" ) ){
                argc--;
                argv++;
                ons.setDLLFile(argv[0]);
            }
            else if ( !strcmp( argv[0]+1, "r" ) || !strcmp( argv[0]+1, "-root" ) ){
                argc--;
                argv++;
                ons.setArchivePath(argv[0]);
            }
            else if ( !strcmp( argv[0]+1, "-fullscreen" ) ){
                ons.setFullscreenMode();
            }
            else if ( !strcmp( argv[0]+1, "-window" ) ){
                ons.setWindowMode();
            }
            else if ( !strcmp( argv[0]+1, "-force-button-shortcut" ) ){
                ons.enableButtonShortCut();
            }
            else if ( !strcmp( argv[0]+1, "-enable-wheeldown-advance" ) ){
                ons.enableWheelDownAdvance();
            }
            else if ( !strcmp( argv[0]+1, "-disable-rescale" ) ){
                ons.disableRescale();
            }
            else if ( !strcmp( argv[0]+1, "-edit" ) ){
                ons.enableEdit();
            }
            else if ( !strcmp( argv[0]+1, "-key-exe" ) ){
                argc--;
                argv++;
                ons.setKeyEXE(argv[0]);
            }
            else{
                printf(" unknown option %s\n", argv[0] );
            }
        }
        else{
            optionHelp();
        }
        argc--;
        argv++;
    }
    
    // ----------------------------------------
    // Run ONScripter

    pspDiagLog("STARTUP ons.init enter");
    int init_result = ons.init();
    pspDiagLog("STARTUP ons.init result=%d", init_result);
    if (init_result) exit(-1);
    pspDiagLog("STARTUP eventLoop enter");
    ons.eventLoop();
    
    exit(0);
}
