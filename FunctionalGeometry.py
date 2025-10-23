##########10/3/25###########


import uproot
import numpy as np
import pandas as pd


tree = uproot.open("C:/Users/david/OneDrive/Documents/Python/VaskaData/Hoffman_test.root:Coincidences;132")
cols = [
    "time1","time2",
    "rsectorID1","submoduleID1","crystalID1",
    "rsectorID2","submoduleID2","crystalID2"
]
df = tree.arrays(cols, library="pd")

#Convert columns to NumPy
t1    = df["time1"].to_numpy(np.float64)
t2    = df["time2"].to_numpy(np.float64)
rsec1 = df["rsectorID1"].to_numpy(np.int64)
rsec2 = df["rsectorID2"].to_numpy(np.int64)
sub1  = df["submoduleID1"].to_numpy(np.int64)
sub2  = df["submoduleID2"].to_numpy(np.int64)
cry1  = df["crystalID1"].to_numpy(np.int64)
cry2  = df["crystalID2"].to_numpy(np.int64)

#Derive indices
blk_A_ax = ((sub1) // 5).astype(np.uint64)
blk_A_tr = ((sub1) %  5).astype(np.uint64)

blk_B_ax = ((sub2) // 5).astype(np.uint64)
blk_B_tr = ((sub2) %  5).astype(np.uint64)

cry_A_ax = ((cry1) // 7).astype(np.uint64)
cry_A_tr = ((cry1) %  7).astype(np.uint64)

cry_B_ax = ((cry2) // 7).astype(np.uint64)
cry_B_tr = ((cry2) %  7).astype(np.uint64)


#explicit LUT(Table 7)
#22x22 LUT of pair codes for unordered, non-adjacent pairs (i >= j+2).
#adjacent or same-module pairs remain -1. Higher ID row and lower column (it is a bottom half triangle)
def build_pair_lut_table7(n_modules=22):
    lut = -np.ones((n_modules, n_modules), dtype=np.int16)

    # Column start codes for j >= 1 (from Table 7).
    # j:   1   2   3   4   5    6    7    8    9    10   11   12   13   14   15   16   17   18   19
    base = [20, 39, 57, 74, 90, 105, 119, 132, 144, 155, 165, 174, 182, 189, 195, 200, 204, 207, 209]

    for i in range(n_modules):      #row (larger module index)
        for j in range(i):          #col (smaller module index)
            if i >= j + 2:
                if j == 0:
                    code = i - 1
                else:
                    code = base[j - 1] + (i - (j + 2))
                lut[i, j] = lut[j, i] = code
    return lut

# modules == rsector ID (GATE geometry == uMI)
mA = rsec1.astype(np.int64)
mB = rsec2.astype(np.int64)

pair_lut  = build_pair_lut_table7(22)
pair_code = pair_lut[mA, mB]                        # int16, -1 for adjacent/same

#Map invalid/adjacent/same pairs to 0xFF (both nibbles 0xF)
pair_code = np.where(pair_code < 0, 255, pair_code).astype(np.uint16)

#Split 8-bit code into nibbles for the raw word
mod_pair_A = (pair_code & 0xF).astype(np.uint64)          # bits [3:0]
mod_pair_B = ((pair_code >> 4) & 0xF).astype(np.uint64)   # bits [35:32]

#Time delta and TA/TB split (int-safe)
deltaT_i = np.abs(t1 - t2).astype(np.uint64)
TA_TB_L  = (deltaT_i & np.uint64(0x1F))
TA_TB_H  = ((deltaT_i >> np.uint64(5)) & np.uint64(0x1F))  # left the same

#Energy constants
n  = len(df)
E1 = np.full(n, 42, dtype=np.uint64)
E2 = np.full(n, 42, dtype=np.uint64)

#Pack 64-bit raw coincidence words
word1 = np.zeros(n, dtype=np.uint64)
#First 32-bit word (bits 0->31)
word1 |= (mod_pair_A & np.uint64(0xF)) << np.uint64(0)    # [3:0]
word1 |= np.uint64(1) << np.uint64(4)                     # Rawdata Tag [4] = 1
word1 |= (cry_A_ax  & np.uint64(0x7)) << np.uint64(5)     # [7:5]
word1 |= (blk_A_ax  & np.uint64(0xF)) << np.uint64(8)     # [11:8]
word1 |= (cry_A_tr  & np.uint64(0x7)) << np.uint64(12)    # [14:12]
word1 |= (blk_A_tr  & np.uint64(0x7)) << np.uint64(15)    # [17:15]
word1 |= (E1        & np.uint64(0xFF)) << np.uint64(18)   # [25:18]
word1 |= (TA_TB_L   & np.uint64(0x1F)) << np.uint64(26)   # [30:26]

w2low = np.zeros(n, dtype=np.uint64)
w2low |= (mod_pair_B & np.uint64(0xF)) << np.uint64(0)    # [35:32] after shift
w2low |= np.uint64(0) << np.uint64(4)                     # Prompt/Delay mark [36] = 0 (Prompt)
w2low |= (cry_B_ax  & np.uint64(0x7)) << np.uint64(5)     # [39:37]
w2low |= (blk_B_ax  & np.uint64(0xF)) << np.uint64(8)     # [43:40]
w2low |= (cry_B_tr  & np.uint64(0x7)) << np.uint64(12)    # [46:44]
w2low |= (blk_B_tr  & np.uint64(0x7)) << np.uint64(15)    # [49:47]
w2low |= (E2       & np.uint64(0xFF)) << np.uint64(18)    # [57:50]
w2low |= (TA_TB_H  & np.uint64(0x1F)) << np.uint64(26)    # [62:58]
w2low |= np.uint64(1) << np.uint64(31)                    # second 32-bit word mark

packed_coinc = (w2low << np.uint64(32)) | word1           # shape (n,)



#check mod_pair packing
A_bits = (packed_coinc & np.uint64(0xF))
B_bits = ((packed_coinc >> np.uint64(32)) & np.uint64(0xF))
okA = np.all(A_bits == (mod_pair_A & np.uint64(0xF)))
okB = np.all(B_bits == (mod_pair_B & np.uint64(0xF)))
back_code = (B_bits << np.uint64(4)) | A_bits
okCode = np.all(back_code.astype(np.uint16) == (pair_code & 0xFF))

print("mod_pair_A packed correctly:", okA)
print("mod_pair_B packed correctly:", okB)
print("pair_code reconstructed correctly:", okCode)
print("First 5 examples (A,B | packed A,B | code):")
for k in range(min(5, len(packed_coinc))):
    print(int(mod_pair_A[k]), int(A_bits[k]),
          int(mod_pair_B[k]), int(B_bits[k]),
          int(pair_code[k]))





#Timestamp packets every 100 ms
def pack_timestamp(year, month, day, hour, minute, second, ms):
    # Low 32 bits
    w1 = np.uint64((month & 0xF) << 0)          #[3:0]
    w1 |= np.uint64(0) << 4                     #Rawdata Tag = 0
    w1 |= np.uint64(0) << 5                     #Tag0
    w1 |= np.uint64((year & 0xFFF) << 7)        #[18:7]
    w1 |= np.uint64((day & 0x1F) << 19)         #[23:19]
    #High 32 bits placed directly in 64-bit word
    w2 = np.uint64(0)
    w2 |= np.uint64((hour   & 0x1F) << 32)      #[36:32]
    w2 |= np.uint64(0) << 37                    #Tag1
    w2 |= np.uint64((minute & 0x3F) << 39)      #[44:39]
    w2 |= np.uint64((second & 0x3F) << 45)      #[50:45]
    w2 |= np.uint64((ms     & 0x3FF) << 51)     #[61:51]
    w2 |= np.uint64(1) << 63                    #second 32-bit word mark
    return np.uint64(w1 | w2)

#Event times (seconds), chronological order
evt_t = np.minimum(t1, t2).astype(np.float64)
order = np.argsort(evt_t)
t0 = float(evt_t.min())
next_tick = t0                    #schedule timestamps at t0, t0+0.1, ...
elapsed_ms = 0

#Choose a wall date
YEAR, MONTH, DAY = 2025, 10, 1

words = []
for idx in order:
    t = float(evt_t[idx])
    #Insert all timestamps up to this event time, every 100 ms
    while t >= next_tick:
        H = (elapsed_ms // 3600000) % 24
        M = (elapsed_ms // 60000)   % 60
        S = (elapsed_ms // 1000)    % 60
        MS = elapsed_ms % 1000
        words.append(pack_timestamp(YEAR, MONTH, DAY, H, M, S, MS))
        elapsed_ms += 100
        next_tick = t0 + elapsed_ms / 1000.0

    #Then the coincidence word
    words.append(np.uint64(packed_coinc[idx]))


out_path = r"C:/Users/david/OneDrive/Documents/Python/October_3/Hoffman_10_3_.RAW"

#Correct counters: use RawdataTag (bit 4 in low 32 bits)
words_arr = np.array(words, dtype=np.uint64)
rawdata_tag_set = (words_arr & np.uint64(0x10)) != 0  #bit 4
n_coinc = int(np.count_nonzero(rawdata_tag_set))      #RawdataTag=1
n_ts    = int(words_arr.size - n_coinc)               #RawdataTag=0

#Write interleaved stream 
with open(out_path, "wb") as f:
    f.write(words_arr.astype("<u8").tobytes())

print(f"Wrote {words_arr.size:,} 64-bit words to {out_path} "
      f"({n_ts:,} timestamps, {n_coinc:,} coincidences)")

duration_s  = float(evt_t.max() - evt_t.min())
expected_ts = int(np.floor(duration_s / 0.1)) + 1  # iterates at t0, t0+0.1, ...
print(f"Expected timestamps at 100 ms: ~{expected_ts:,}")


