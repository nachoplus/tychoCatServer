# Note dependence of 'sub_eph' on the 'lunar' library.  This is available
# at http://www.projectpluto.com/source.htm .

all: asc2eph.exe dump_eph.exe eph2asc.exe merge_de.exe testeph.exe sub_eph.exe

!ifdef BITS_32
COMMON_FLAGS=-nologo -W3 -EHsc -c -FD
LIBNAME=lunar
RM=rm
!else
COMMON_FLAGS=-nologo -W3 -EHsc -c -FD -D_CRT_SECURE_NO_WARNINGS
LIBNAME=lunar64
RM=del
!endif

clean:
   $(RM) asc2eph.obj
   $(RM) asc2eph.exe
   $(RM) dump_eph.obj
   $(RM) dump_eph.exe
   $(RM) eph2asc.obj
   $(RM) eph2asc.exe
   $(RM) f_strtod.obj
   $(RM) jpleph.dll
   $(RM) jpleph.exp
   $(RM) jpleph.lib
   $(RM) jpleph.obj
   $(RM) merge_de.obj
   $(RM) merge_de.exe
   $(RM) sub_eph.obj
   $(RM) sub_eph.exe
   $(RM) testeph.obj
   $(RM) testeph.exe

testeph.exe:    testeph.obj jpleph.lib
   link /nologo testeph.obj jpleph.lib

merge_de.exe:   merge_de.obj jpleph.lib
   link /nologo merge_de.obj jpleph.lib

eph2asc.exe:    eph2asc.obj jpleph.lib
   link /nologo eph2asc.obj jpleph.lib

dump_eph.exe:   dump_eph.obj jpleph.lib
   link /nologo dump_eph.obj jpleph.lib

asc2eph.exe:    asc2eph.obj f_strtod.obj
   link /nologo asc2eph.obj f_strtod.obj

sub_eph.exe:    sub_eph.obj jpleph.lib
   link /nologo sub_eph.obj jpleph.lib $(LIBNAME).lib

jpleph.lib: jpleph.obj
   $(RM) jpleph.lib
!ifdef DLL
   $(RM) jpleph.dll
   link /nologo /DLL /IMPLIB:jpleph.lib /DEF:jpleph.def jpleph.obj
!else
   lib /OUT:jpleph.lib jpleph.obj
!endif

CFLAGS=-Ox -MT $(COMMON_FLAGS)

jpleph.obj: jpleph.cpp
!ifdef DLL
   cl $(CFLAGS) -LD jpleph.cpp
!else
   cl $(CFLAGS)     jpleph.cpp
!endif

sub_eph.obj: sub_eph.cpp
   cl $(CFLAGS) -DTEST_MAIN sub_eph.cpp

.cpp.obj:
   cl $(CFLAGS) $<

