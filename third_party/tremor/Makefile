# Pinned Tremor source + the SDK's sezero fixes, full-accuracy arithmetic.
PSPPRE = $(shell psp-config --psp-prefix)
PSPSDK = $(shell psp-config --pspsdk-path)
CC = psp-gcc
AR = psp-ar
CFLAGS = -O2 -G0 -Wall -fsigned-char -DHAVE_ALLOCA -DHAVE_ALLOCA_H -DHAVE_SYS_TYPES_H -I$(PSPPRE)/include -I$(PSPSDK)/include -MMD -MP
SOURCES = mdct.c block.c window.c synthesis.c info.c floor1.c floor0.c vorbisfile.c res012.c mapping0.c registry.c codebook.c sharedbook.c
OBJECTS = $(SOURCES:.c=.o)
all: libvorbisidec.a
libvorbisidec.a: $(OBJECTS)
	$(AR) rcs $@ $(OBJECTS)
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@
-include $(OBJECTS:.o=.d)
.PHONY: all clean
clean:
	rm -f $(OBJECTS) $(OBJECTS:.o=.d) libvorbisidec.a
