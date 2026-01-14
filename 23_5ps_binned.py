import uproot
import numpy as np

ROOT_PATH = "/Users/2025/Documents/David/root_files/readimg28.root:Coincidences;1"
OUT_PATH  = "/Users/2025/Documents/David/raw_files/test_TOF_ordered_bias_removed_false23_5_swap.RAW"

TDC_BIN_PS = 23.5
FLIP_SIGN = False   # leave false
REMOVE_BIAS = True  # leave true - subtract median dt_bins

def build_pair_lut_table7(n_modules=22):
    lut = -np.ones((n_modules, n_modules), dtype=np.int16)
    base = [20, 39, 57, 74, 90, 105, 119, 132, 144, 155, 165, 174, 182, 189, 195, 200, 204, 207, 209]
    for i in range(n_modules):# row (larger module index)
        for j in range(i):# col (smaller module index)
            if i >= j + 2:
                if j == 0:
                    code = i - 1
                else:
                    code = base[j - 1] + (i - (j + 2))
                lut[i, j] = lut[j, i] = code
    return lut

def pack_timestamp(year, month, day, hour, minute, second, ms):
    w1 = np.uint64((month & 0xF) << 0)
    w1 |= np.uint64(0) << 4
    w1 |= np.uint64(0) << 5
    w1 |= np.uint64((year & 0xFFF) << 7)
    w1 |= np.uint64((day & 0x1F) << 19)
    w2 = np.uint64(0)
    w2 |= np.uint64((hour   & 0x1F) << 32)
    w2 |= np.uint64(0) << 37
    w2 |= np.uint64((minute & 0x3F) << 39)
    w2 |= np.uint64((second & 0x3F) << 45)
    w2 |= np.uint64((ms     & 0x3FF) << 51)
    w2 |= np.uint64(1) << 63
    return np.uint64(w1 | w2)

tree = uproot.open(ROOT_PATH)
cols = ["time1","time2","rsectorID1","submoduleID1","crystalID1","rsectorID2","submoduleID2","crystalID2"]
arr = tree.arrays(cols, library="np")

t1 = arr["time1"].astype(np.float64)
t2 = arr["time2"].astype(np.float64)
rsec1 = arr["rsectorID1"].astype(np.int64)
rsec2 = arr["rsectorID2"].astype(np.int64)
sub1  = arr["submoduleID1"].astype(np.int64)
sub2  = arr["submoduleID2"].astype(np.int64)
cry1  = arr["crystalID1"].astype(np.int64)
cry2  = arr["crystalID2"].astype(np.int64)
n = t1.size

#enforce ordering: A has smaller module id -- necessary so LUT consistently assigns the "higher" to i and "lower" to j
#loops occur within numpy -- no need to iterate in code
#swap is boolean
swap = (rsec2 < rsec1)

tA = np.where(swap, t2, t1)
tB = np.where(swap, t1, t2)

mA = np.where(swap, rsec2, rsec1).astype(np.int64)
mB = np.where(swap, rsec1, rsec2).astype(np.int64)

subA = np.where(swap, sub2, sub1).astype(np.int64)
subB = np.where(swap, sub1, sub2).astype(np.int64)

cryA = np.where(swap, cry2, cry1).astype(np.int64)
cryB = np.where(swap, cry1, cry2).astype(np.int64)

blk_A_ax = (subA // 5).astype(np.uint64); blk_A_tr = (subA % 5).astype(np.uint64)
blk_B_ax = (subB // 5).astype(np.uint64); blk_B_tr = (subB % 5).astype(np.uint64)
cry_A_ax = (cryA // 7).astype(np.uint64); cry_A_tr = (cryA % 7).astype(np.uint64)
cry_B_ax = (cryB // 7).astype(np.uint64); cry_B_tr = (cryB % 7).astype(np.uint64)

pair_lut = build_pair_lut_table7()
pair_code = pair_lut[mA, mB]
pair_code = np.where(pair_code < 0, 255, pair_code).astype(np.uint16)
mod_pair_A = (pair_code & 0xF).astype(np.uint64)
mod_pair_B = ((pair_code >> 4) & 0xF).astype(np.uint64)

# --- TOF from ordered times ---
dt_ps = (tA - tB) * 1e12
if FLIP_SIGN:
    dt_ps = -dt_ps

dt_bins = np.rint(dt_ps / TDC_BIN_PS).astype(np.int64)
dt_bins = np.clip(dt_bins, -512, 511)

if REMOVE_BIAS:
    bias = int(np.median(dt_bins))
    dt_bins = np.clip(dt_bins - bias, -512, 511)
else:
    bias = 0

tof10 = (dt_bins & 0x3FF).astype(np.uint64)
TA_TB_L = tof10 & np.uint64(0x1F)
TA_TB_H = (tof10 >> np.uint64(5)) & np.uint64(0x1F)

print("[Script 4] dt_ps min/max:", float(dt_ps.min()), float(dt_ps.max()))
print("[Script 4] dt_bins median before bias removal:", bias)
print("[Script 4] dt_bins frac==0:", float(np.mean(dt_bins == 0)), "unique:", np.unique(dt_bins).size)

# pack
E1 = np.full(n, 42, dtype=np.uint64)
E2 = np.full(n, 42, dtype=np.uint64)

word1 = np.zeros(n, dtype=np.uint64)
word1 |= (mod_pair_A & 0xF) << 0
word1 |= np.uint64(1) << 4
word1 |= (cry_A_ax & 0x7) << 5
word1 |= (blk_A_ax & 0xF) << 8
word1 |= (cry_A_tr & 0x7) << 12
word1 |= (blk_A_tr & 0x7) << 15
word1 |= (E1 & 0xFF) << 18
word1 |= (TA_TB_L & 0x1F) << 26

w2low = np.zeros(n, dtype=np.uint64)
w2low |= (mod_pair_B & 0xF) << 0
w2low |= np.uint64(0) << 4
w2low |= (cry_B_ax & 0x7) << 5
w2low |= (blk_B_ax & 0xF) << 8
w2low |= (cry_B_tr & 0x7) << 12
w2low |= (blk_B_tr & 0x7) << 15
w2low |= (E2 & 0xFF) << 18
w2low |= (TA_TB_H & 0x1F) << 26
w2low |= np.uint64(1) << 31

packed_coinc = (w2low << 32) | word1

# timestamps
evt_t = np.minimum(tA, tB).astype(np.float64)
order = np.argsort(evt_t)
t0 = float(evt_t.min())
next_tick = t0
elapsed_ms = 0
YEAR, MONTH, DAY = 2025, 10, 1

words = []
for idx in order:
    t = float(evt_t[idx])
    while t >= next_tick:
        H = (elapsed_ms // 3600000) % 24
        M = (elapsed_ms // 60000) % 60
        S = (elapsed_ms // 1000) % 60
        MS = elapsed_ms % 1000
        words.append(pack_timestamp(YEAR, MONTH, DAY, H, M, S, MS))
        elapsed_ms += 100
        next_tick = t0 + elapsed_ms / 1000.0
    words.append(np.uint64(packed_coinc[idx]))

words_arr = np.array(words, dtype=np.uint64)
with open(OUT_PATH, "wb") as f:
    f.write(words_arr.astype("<u8").tobytes())

rawdata_tag_set = (words_arr & np.uint64(0x10)) != 0
n_coinc = int(np.count_nonzero(rawdata_tag_set))
n_ts = int(words_arr.size - n_coinc)
print(f"[Script 4] Wrote {words_arr.size:,} words -> {OUT_PATH} ({n_ts:,} TS, {n_coinc:,} coinc)")
