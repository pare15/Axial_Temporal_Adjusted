import uproot
import pandas as pd
import numpy as np

print(uproot.__version__)

# Load ROOT file and TTree
file = uproot.open("C:/Users/david/OneDrive/Documents/Python/VaskaData/Shereical_test.root")
coincidences = uproot.open("C:/Users/david/OneDrive/Documents/Python/VaskaData/Shereical_test.root:Coincidences;181")

# Put tree into DataFrame
df1 = coincidences.arrays(library="pd")
print(df1.head)


# Geometry alignment: each block has 5 crystals axially, dividing 5 tells you which block row you’re in
#Submodules: 0–70:axial (//5), transaxial (%5)
df1["blk_ax_A"] = df1["submoduleID1"] // 5
df1["blk_tr_A"] = df1["submoduleID1"] % 5
df1["blk_ax_B"] = df1["submoduleID2"] // 5
df1["blk_tr_B"] = df1["submoduleID2"] % 5

# Crystals: 0–29: axial (//5), transaxial (%5)
df1["crys_ax_A"] = df1["crystalID1"] // 5
df1["crys_tr_A"] = df1["crystalID1"] % 5
df1["crys_ax_B"] = df1["crystalID2"] // 5
df1["crys_tr_B"] = df1["crystalID2"] % 5

#Absolute IDs for 71x30 system
df1["AbsID_A"] = df1["submoduleID1"] * 30 + df1["crystalID1"]
df1["AbsID_B"] = df1["submoduleID2"] * 30 + df1["crystalID2"]

#Scale to 8 bit
E_max = df1[["energy1", "energy2"]].max().max()
df1["Energy1_int"] = (df1["energy1"] / E_max * 255).astype(int)
df1["Energy2_int"] = (df1["energy2"] / E_max * 255).astype(int)

# delta T calculation (split into low/high bits)
df1["deltaT"] = (df1["time1"] - df1["time2"]).abs().astype(int)
df1["TA_TB_L"] = (df1["deltaT"] & 0x1F)
df1["TA_TB_H"] = np.right_shift(df1["deltaT"], 5) & 0x1F

#packing
def pack_rawdata(row):
    # first 32
    word1 = 0
    word1 |= (row["blk_ax_A"] & 0xF)
    word1 |= (1 << 4)
    word1 |= ((row["crys_ax_A"] & 0x7) << 5)
    word1 |= ((row["blk_ax_A"] & 0xF) << 8)
    word1 |= ((row["crys_tr_A"] & 0x7) << 12)
    word1 |= ((row["blk_tr_A"] & 0x7) << 15)
    word1 |= ((row["Energy1_int"] & 0xFF) << 18)
    word1 |= ((row["TA_TB_L"] & 0x1F) << 26)

    # second 32 bit
    word2 = 0
    word2 |= (row["blk_ax_B"] & 0xF)
    word2 |= (1 << 4)
    word2 |= ((row["crys_ax_B"] & 0x7) << 5)
    word2 |= ((row["blk_ax_B"] & 0xF) << 8)
    word2 |= ((row["crys_tr_B"] & 0x7) << 12)
    word2 |= ((row["blk_tr_B"] & 0x7) << 15)
    word2 |= ((row["Energy2_int"] & 0xFF) << 18)
    word2 |= ((row["TA_TB_H"] & 0x1F) << 26)
    word2 |= (1 << 31)
    #combine
    raw64 = (np.uint64(word2) << 32) | np.uint64(word1)
    return raw64

raw64_words = df1.apply(pack_rawdata, axis=1)

# Write out .raw file
with open("Rdctime_geometry.raw", "wb") as f:
    for word in raw64_words:
        f.write(int(word).to_bytes(8, byteorder="little"))

print(f"Finished. Wrote {len(raw64_words)} events.")

#sanity check
def unpack_rawdata(raw64):
    word1 = np.uint32(raw64 & 0xFFFFFFFF)
    word2 = np.uint32((raw64 >> 32) & 0xFFFFFFFF)

    return {
        "blk_ax_A": (word1 >> 0) & 0xF,
        "crys_ax_A": (word1 >> 5) & 0x7,
        "blk_tr_A": (word1 >> 15) & 0x7,
        "crys_tr_A": (word1 >> 12) & 0x7,
        "Energy_A": (word1 >> 18) & 0xFF,
        "TA_TB_L": (word1 >> 26) & 0x1F,
        "mark1": (word1 >> 31) & 0x1,

        "blk_ax_B": (word2 >> 0) & 0xF,
        "crys_ax_B": (word2 >> 5) & 0x7,
        "blk_tr_B": (word2 >> 15) & 0x7,
        "crys_tr_B": (word2 >> 12) & 0x7,
        "Energy_B": (word2 >> 18) & 0xFF,
        "TA_TB_H": (word2 >> 26) & 0x1F,
        "mark2": (word2 >> 31) & 0x1,
    }

print("\n--- First 5 unpacked events ---")
with open("Rdctime_geometry.raw", "rb") as f:
    for i in range(5):
        raw_bytes = f.read(8)
        raw_word = np.frombuffer(raw_bytes, dtype=np.uint64)[0]
        print(f"Event {i+1}: {unpack_rawdata(raw_word)}, "
              f"AbsID_A={df1['AbsID_A'].iloc[i]}, AbsID_B={df1['AbsID_B'].iloc[i]}")

#checking ranges
print("\n####### Range diagnostics #######")
expected_ranges = {
    "blk_ax_A": (0, 13),
    "blk_tr_A": (0, 4),
    "crys_ax_A": (0, 8),
    "crys_tr_A": (0, 4),
    "blk_ax_B": (0, 13),
    "blk_tr_B": (0, 4),
    "crys_ax_B": (0, 8),
    "crys_tr_B": (0, 4),
    "AbsID_A": (0, 2111),
    "AbsID_B": (0, 2111),
}

for col, (emin, emax) in expected_ranges.items():
    vmin, vmax = df1[col].min(), df1[col].max()
    print(f"{col}: min={vmin}, max={vmax}, expected=[{emin},{emax}]")
    if vmin < emin or vmax > emax:
        print(f"WARNING: {col} outside expected range!")

