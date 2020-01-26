swig -python ucac4.i
gcc -c ucac4.c ucac4_wrap.c -I/usr/include/python3.7 -fPIC
ld -shared ucac4.o ucac4_wrap.o -o _ucac4.so
cp _ucac4.so ..
cp ucac4.py ..
