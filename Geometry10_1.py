import uproot
import numpy as np
import pandas as pd

# --- Load just what's needed ---
tree = uproot.open("C:/Users/david/OneDrive/Documents/Python/VaskaData/Shereical_test.root:Coincidences;181")
cols = [
    "time1","time2",
    "rsectorID1","submoduleID1","crystalID1",
    "rsectorID2","submoduleID2","crystalID2"
]
df = tree.arrays(cols, library="pd")

# --- Convert columns to NumPy first ---
t1    = df["time1"].to_numpy(np.float64)
t2    = df["time2"].to_numpy(np.float64)
rsec1 = df["rsectorID1"].to_numpy(np.int64)
rsec2 = df["rsectorID2"].to_numpy(np.int64)
sub1  = df["submoduleID1"].to_numpy(np.int64)
sub2  = df["submoduleID2"].to_numpy(np.int64)
cry1  = df["crystalID1"].to_numpy(np.int64)
cry2  = df["crystalID2"].to_numpy(np.int64)

# --- Derived indices (your formulas) ---
blk_A_ax = ((sub1 + 1) // 14).astype(np.uint64)
blk_A_tr = ((sub1 + 1) %  5).astype(np.uint64)

blk_B_ax = ((sub2 + 1) // 14).astype(np.uint64)
blk_B_tr = ((sub2 + 1) %  5).astype(np.uint64)   # use sub1 instead if you really want that

cry_A_ax = ((cry1 + 1) // 6).astype(np.uint64)
cry_A_tr = ((cry1 + 1) %  7).astype(np.uint64)

cry_B_ax = ((cry2 + 1) // 6).astype(np.uint64)
cry_B_tr = ((cry2 + 1) %  7).astype(np.uint64)

# mod_pair := rsectorID (4 bits)
mod_pair_A = (rsec1.astype(np.uint64) & np.uint64(0xF))
mod_pair_B = (rsec2.astype(np.uint64) & np.uint64(0xF))

# --- Time delta and TA/TB split (int-safe) ---
deltaT_i = np.abs(t1 - t2).astype(np.uint64)
TA_TB_L  = (deltaT_i & np.uint64(0x1F))
TA_TB_H  = ((deltaT_i >> np.uint64(5)) & np.uint64(0x1F))  # left the same

# --- Energy constant (low end) ---
n  = len(df)
E1 = np.full(n, 42, dtype=np.uint64)
E2 = np.full(n, 42, dtype=np.uint64)

# --- Pack 64-bit raw coincidence words ---
word1 = np.zeros(n, dtype=np.uint64)
# First 32-bit word (bits 0..31)
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
w2low |= np.uint64(0) << np.uint64(4)                     # Prompt/Delay mark [36] = 0
w2low |= (cry_B_ax  & np.uint64(0x7)) << np.uint64(5)     # [39:37]
w2low |= (blk_B_ax  & np.uint64(0xF)) << np.uint64(8)     # [43:40]
w2low |= (cry_B_tr  & np.uint64(0x7)) << np.uint64(12)    # [46:44]
w2low |= (blk_B_tr  & np.uint64(0x7)) << np.uint64(15)    # [49:47]
w2low |= (E2       & np.uint64(0xFF)) << np.uint64(18)    # [57:50]
w2low |= (TA_TB_H  & np.uint64(0x1F)) << np.uint64(26)    # [62:58]
w2low |= np.uint64(1) << np.uint64(31)                    # second 32-bit word mark

packed_coinc = (w2low << np.uint64(32)) | word1           # shape (n,)

# ---------- Timestamp packets every 100 ms ----------
def pack_timestamp(year, month, day, hour, minute, second, ms):
    # Low 32 bits
    w1 = np.uint64((month & 0xF) << 0)          # [3:0]
    w1 |= np.uint64(0) << 4                     # Rawdata Tag = 0
    w1 |= np.uint64(0) << 5                     # Tag0
    w1 |= np.uint64((year & 0xFFF) << 7)        # [18:7]
    w1 |= np.uint64((day & 0x1F) << 19)         # [23:19]
    # High 32 bits placed directly in 64-bit word
    w2 = np.uint64(0)
    w2 |= np.uint64((hour   & 0x1F) << 32)      # [36:32]
    w2 |= np.uint64(0) << 37                    # Tag1
    w2 |= np.uint64((minute & 0x3F) << 39)      # [44:39]
    w2 |= np.uint64((second & 0x3F) << 45)      # [50:45]
    w2 |= np.uint64((ms     & 0x3FF) << 51)     # [61:51]
    w2 |= np.uint64(1) << 63                    # second 32-bit word mark
    return np.uint64(w1 | w2)

# Event times (seconds), chronological order
evt_t = np.minimum(t1, t2).astype(np.float64)
order = np.argsort(evt_t)
t0 = float(evt_t.min())
next_tick = t0                    # schedule timestamps at t0, t0+0.1, ...
elapsed_ms = 0

# Choose a wall date
YEAR, MONTH, DAY = 2025, 10, 1

words = []
for idx in order:
    t = float(evt_t[idx])
    # Insert all timestamps up to this event time, every 100 ms
    while t >= next_tick:
        H = (elapsed_ms // 3600000) % 24
        M = (elapsed_ms // 60000)   % 60
        S = (elapsed_ms // 1000)    % 60
        MS = elapsed_ms % 1000
        words.append(pack_timestamp(YEAR, MONTH, DAY, H, M, S, MS))
        elapsed_ms += 100
        next_tick = t0 + elapsed_ms / 1000.0

    # Then the coincidence word
    words.append(np.uint64(packed_coinc[idx]))

# --- Output path defined BEFORE printing ---
out_path = r"C:/Users/david/OneDrive/Documents/Python/October_1/NoDelay10_1.RAW"

# Correct counters: use RawdataTag (bit 4 in low 32 bits)
words_arr = np.array(words, dtype=np.uint64)
rawdata_tag_set = (words_arr & np.uint64(0x10)) != 0  # bit 4
n_coinc = int(np.count_nonzero(rawdata_tag_set))      # RawdataTag=1
n_ts    = int(words_arr.size - n_coinc)               # RawdataTag=0

# --- Write interleaved stream ---
with open(out_path, "wb") as f:
    f.write(words_arr.astype("<u8").tobytes())

print(f"Wrote {words_arr.size:,} 64-bit words to {out_path} "
      f"({n_ts:,} timestamps, {n_coinc:,} coincidences)")

duration_s  = float(evt_t.max() - evt_t.min())
expected_ts = int(np.floor(duration_s / 0.1)) + 1  # ticks at t0, t0+0.1, ...
print(f"Expected timestamps at 100 ms: ~{expected_ts:,}")

