CC = gcc
MEMBENCH = membench
CFLAGS =
LDFLAGS = -lnuma

all: $(MEMBENCH)

$(MEMBENCH) : % : %.o
	$(CC) -o $@ $^ $(LDFLAGS)

cleanobject:
	/bin/rm -f $(addsuffix .o, $(MEMBENCH))

clean: cleanobject
	/bin/rm -f $(MEMBENCH) membench-inner-rand.c

.PHONY: check-syntax

check-syntax:
	$(CC) -Wall -fsyntax-only $(CHK_SOURCES)

membench-inner-rand.c:
	python ./genmembenchinnerloop.py > $@

$(MEMBENCH).c: membench-inner-rand.c

.c.o:
	$(CC) -c $(CFLAGS) $<
