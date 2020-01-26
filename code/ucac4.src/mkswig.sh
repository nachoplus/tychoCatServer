swig -python ucac4.i
gcc -c ucac4.c ucac4_wrap.c  -fPIC $(pkg-config --cflags python3)
ld -shared ucac4.o ucac4_wrap.o -o _ucac4.so $(pkg-config --libs python3)
cp _ucac4.so ..
cp ucac4.py ..
