#!/usr/bin/python3
import sys; f=sys.stdin.buffer
assert f.read(8)==b"!<arch>\n"; off=8
while True:
    h=f.read(60); name=h[:16].rstrip(b" /").decode(); size=int(h[48:58])
    if name.startswith("control.tar"): print(off+60+1, name); break
    f.read(size+size%2); off+=60+size+size%2
