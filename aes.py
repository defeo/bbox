from collections import deque
from random import getrandbits
from lib import Map, Sbox, Perm, XOR, Const, Slice

SubBytes = Map(Sbox(range(256)))
ShiftRows = Perm([0,1,2,3] + [5,6,7,4] + [10,11,8,9] + [15,12,13,14])
AddRoundKey = XOR(Const(bytes(getrandbits(8) for i in range(16))))

# MixColumns
#  [[2,3,1,1], [1,2,3,1], [1,1,2,3], [3,1,1,2]]
one = Sbox(range(256))
two = Sbox(range(256))
three = Sbox(range(256))
mc = (
    (Slice(0,8) >> two >> XOR(
        Slice(8,16) >> three >> XOR(
            Slice(16,24) >> one >> XOR(
                Slice(24,32) >> one))))
    + (Slice(32,40) >> one >> XOR(
        Slice(40,48) >> two >> XOR(
            Slice(48,56) >> three >> XOR(
                Slice(56,64) >> one))))
    + (Slice(64,72) >> one >> XOR(
        Slice(72,80) >> one >> XOR(
            Slice(80,88) >> two >> XOR(
                Slice(88,96) >> three))))
    + (Slice(96,104) >> three >> XOR(
        Slice(104,112) >> one >> XOR(
            Slice(112,120) >> one >> XOR(
                Slice(120,128) >> two)))))
transpose = (
    Slice(0,8) + Slice(32,40) + Slice(64,72) + Slice(96,104)
    + Slice(8,16) + Slice(40,48) + Slice(72,80) + Slice(104,112)
    + Slice(16,24) + Slice(48,56) + Slice(80,88) + Slice(112,120)
    + Slice(24,32) + Slice(56,64) + Slice(88,96) + Slice(120,128)
)
MixColumns = transpose >> (
    (mc << Slice(0,32))
    + (mc << Slice(32,64))
    + (mc << Slice(64,96))
    + (mc << Slice(96,128))) >> transpose

AES = SubBytes >> ShiftRows >> MixColumns >> AddRoundKey
