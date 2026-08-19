#!/usr/bin/env python3
"""Genera HOMER.MID: loop original estilo MIDI de pagina personal de los 90."""
import struct

TPQN = 480
E = TPQN // 2          # corchea
Q = TPQN               # negra

def vlq(n):
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)

def track(events):
    """events: lista de (delta, bytes)"""
    data = b''.join(vlq(d) + b for d, b in events) + b'\x00\xff\x2f\x00'
    return b'MTrk' + struct.pack('>I', len(data)) + data

def notes(ch, seq, vel=100, prog=None):
    """seq: lista de (pitch|None, duracion). None = silencio."""
    ev = []
    if prog is not None:
        ev.append((0, bytes([0xC0 | ch, prog])))
    rest = 0
    for pitch, dur in seq:
        if pitch is None:
            rest += dur
            continue
        ev.append((rest, bytes([0x90 | ch, pitch, vel])))
        ev.append((dur, bytes([0x80 | ch, pitch, 0])))
        rest = 0
    return ev

# --- la cancioncita (melodia propia, 4 compases, C - Ab - Bb - C) ---
MEL = [
    (76, E), (74, E), (72, E), (74, E), (76, E), (79, E), (76, Q),
    (72, E), (75, E), (79, E), (75, E), (72, E), (68, E), (75, Q),
    (74, E), (77, E), (81, E), (77, E), (74, E), (70, E), (77, Q),
    (76, E), (79, E), (84, E), (79, E), (76, Q), (72, Q),
]
BASS_ROOTS = [36, 32, 34, 36]                     # C, Ab, Bb, C
BASS = [(r + off, E) for r in BASS_ROOTS
        for off in (0, 12, 0, 7, 0, 12, 7, 0)]
DRUMS = []
for _ in range(4):                                # 4 compases
    for beat in range(4):
        DRUMS += [(36 if beat % 2 == 0 else 38, E), (42, E)]

REPS = 6                                          # ~40 s de loop
tracks = [
    track([(0, b'\xff\x51\x03' + struct.pack('>I', 60000000 // 132)[1:])]),
    track(notes(0, MEL * REPS, 105, prog=80)),     # square lead
    track(notes(1, BASS * REPS, 90, prog=33)),     # finger bass
    track(notes(9, [(p, d) for p, d in DRUMS * REPS], 95)),
]
mid = b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), TPQN) + b''.join(tracks)
open('HOMER.MID', 'wb').write(mid)

assert vlq(0) == b'\x00' and vlq(127) == b'\x7f' and vlq(128) == b'\x81\x00'
assert vlq(0x3FFF) == b'\xff\x7f' and mid[:4] == b'MThd'
print('HOMER.MID', len(mid), 'bytes')
