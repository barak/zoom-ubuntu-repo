#!/usr/bin/python3
"""Read Version from .deb without seeking. Usage: dpkg-version.py foo.deb (or stdin)."""
import sys, io, tarfile

def read_exact(f, n):
    d = f.read(n)
    if len(d) != n: sys.exit('truncated')
    return d

class BoundedReader(io.RawIOBase):
    def __init__(self, f, n):
        self.f, self.n = f, n
    def readable(self): return True
    def readinto(self, b):
        if not self.n: return 0
        r = self.f.read(min(len(b), self.n))
        self.n -= len(r)
        b[:len(r)] = r
        return len(r)

f = open(sys.argv[1], 'rb') if len(sys.argv) > 1 else sys.stdin.buffer

assert read_exact(f, 8) == b'!<arch>\n', 'not ar archive'

while True:
    hdr = read_exact(f, 60)
    assert hdr[58:60] == b'`\n', 'bad ar header'
    name = hdr[:16].rstrip().rstrip(b'/').decode()
    size = int(hdr[48:58])

    if name.startswith('control.tar'):
        ext = name[len('control.tar'):]
        bounded = io.BufferedReader(BoundedReader(f, size))
        if ext == '.zst':
            import zstandard
            src, mode = zstandard.ZstdDecompressor().stream_reader(bounded), 'r|'
        elif ext == '.gz':  src, mode = bounded, 'r|gz'
        elif ext == '.xz':  src, mode = bounded, 'r|xz'
        elif ext == '':     src, mode = bounded, 'r|'
        else: sys.exit(f'unknown compression: {name}')

        with tarfile.open(fileobj=src, mode=mode) as tf:
            for m in tf:
                if m.name.lstrip('./') == 'control':
                    for line in tf.extractfile(m):
                        if line.startswith(b'Version:'):
                            print(line[8:].strip().decode())
                            sys.exit(0)
                    sys.exit('Version not found')
        sys.exit('control not found in control.tar')

    read_exact(f, size + size % 2)  # skip member data + even-padding
