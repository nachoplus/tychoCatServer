# Makefile for gcc (and MinGW,  and clang)
# Note dependence of 'sub_eph' on the 'lunar' library.  This is available
# at http://www.projectpluto.com/source.htm .
# Note also that 'sub_eph' is the last file to be built.  You can make
# everything else and ignore the missing dependency error if you aren't
# interested in building 'sub_eph'.

ifdef CLANG
CC=clang
LIB=-lm
else
CC=g++
LIB=
endif

ifdef MSWIN
EXE=.exe
else
EXE=
endif

all: asc2eph$(EXE) dump_eph$(EXE) eph2asc$(EXE) merge_de$(EXE) testeph$(EXE) sub_eph$(EXE)

CFLAGS=-c -Wall -O3

.cpp.o:
	$(CC) $(CFLAGS) $<

asc2eph$(EXE):    asc2eph.o f_strtod.o
	$(CC) -o asc2eph asc2eph.o f_strtod.o $(LIB)

eph2asc$(EXE):    eph2asc.o jpleph.o
	$(CC) -o eph2asc eph2asc.o jpleph.o $(LIB)

dump_eph$(EXE):    dump_eph.o jpleph.o
	$(CC) -o dump_eph dump_eph.o jpleph.o $(LIB)

merge_de$(EXE):    merge_de.o jpleph.o
	$(CC) -o merge_de merge_de.o jpleph.o $(LIB)

sub_eph$(EXE):    sub_eph.o jpleph.o lunar.a
	$(CC) -o sub_eph sub_eph.o jpleph.o lunar.a $(LIB)

sub_eph.o: sub_eph.cpp
	$(CC) $(CFLAGS) -DTEST_MAIN sub_eph.cpp

testeph$(EXE):    testeph.o jpleph.o
	$(CC) -o testeph testeph.o jpleph.o $(LIB)

clean:
	$(RM) *.o
	$(RM) asc2eph$(EXE)
	$(RM) dump_eph$(EXE)
	$(RM) eph2asc$(EXE)
	$(RM) merge_de$(EXE)
	$(RM) sub_eph$(EXE)
	$(RM) testeph$(EXE)
