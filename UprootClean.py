##import uproot
##import pandas as pd
##import numpy as np
##
##print(uproot.__version__)
##
##file = uproot.open("C:/Users/david/OneDrive/Documents/Python/VaskaData/Shereical_test.root")
##
###inspect TBranches of TTree
##coincidences = uproot.open("C:/Users/david/OneDrive/Documents/Python/VaskaData/Shereical_test.root:Coincidences;181")
##
###put a tree into a pandas dataframe
##df1 = coincidences.arrays(library="pd")
##print(df1.head)
### energy needs scaling from a float into an int from 0 to 255
##E_max = df1[['energy1', 'energy2']].max().max()
##df1['Energy1_int'] = (df1['energy1'] / E_max * 255).astype(int)
##df1['Energy2_int'] = (df1['energy2'] / E_max * 255).astype(int)
##
###scaling for the maximum time
##max_time = max(df1['time1'].max(), df1['time2'].max())
##print(max_time)
##
###list to hold events
##events = []
##
###iterate through DataFrame and make the rows into individual events
##for index, row in df1.iterrows():
##    event = {
##        'moduleID1': row['moduleID1'],
##        'crystalID1': row['crystalID1'],
##        'layerID1': row['layerID1'],       #include layer ID
##        'submoduleID1': row['submoduleID1'],
##        'energy1': row['Energy1_int'],
##        'time1': row['time1'],             #include time1 
##
##        'moduleID2': row['moduleID2'],
##        'crystalID2': row['crystalID2'],
##        'layerID2': row['layerID2'],       #include layer ID
##        'submoduleID2': row['submoduleID2'],
##        'energy2': row['Energy2_int'],
##        'time2': row['time2']              #include time2
##    }
##    events.append(event)
##
#####function to pack event fields into a 64-bit RawData word
##def pack_rawdata(event):
##    ####First 32-bit word####
##    word1 = 0
##    #Bits 0-3: mod_pair_A (combine moduleID1 and submoduleID1 as needed)
##    word1 |= (int(event['moduleID1']) & 0xF)  # adjust if needed to match Table 6
##    #Bit 4: Rawdata Tag (fixed 1)
##    word1 |= (1 << 4)
##    #Bits 5-7: crys_A_ax (layerID1)
##    word1 |= ((int(event['layerID1']) & 0x7) << 5)
##    #Bits 8-11: blk_A_ax (moduleID1)
##    word1 |= ((int(event['moduleID1']) & 0xF) << 8)
##    #Bits 12-14: crys_A_tr (crystalID1)
##    word1 |= ((int(event['crystalID1']) & 0x7) << 12)
##    #Bits 15-17: blk_A_tr (submoduleID1)
##    word1 |= ((int(event['submoduleID1']) & 0x7) << 15)
##    #Bits 18-25: Energy_A
##    word1 |= ((int(event['energy1']) & 0xFF) << 18)
##    #Bits 26-30: TA_TB_L
##    word1 |= ((int(event['time1']) & 0x1F) << 26)
##    #Bit 31: first 32-bit mark (always 0)
##
##    ####Second 32-bit word####
##    word2 = 0
##    #Bits 32-35: mod_pair_B (combine moduleID2 and submoduleID2 as needed)
##    word2 |= ((int(event['moduleID2']) & 0xF) << 0)  # shifted 0 for word2
##    #Bit 36: Prompt/Delay mark (always 1 for Delay)
##    word2 |= (1 << 4)
##    #Bits 37-39: crys_B_ax (layerID2)
##    word2 |= ((int(event['layerID2']) & 0x7) << 5)
##    #Bits 40-43: blk_B_ax (moduleID2)
##    word2 |= ((int(event['moduleID2']) & 0xF) << 8)
##    #Bits 44-46: crys_B_tr (crystalID2)
##    word2 |= ((int(event['crystalID2']) & 0x7) << 12)
##    #Bits 47-49: blk_B_tr (submoduleID2)
##    word2 |= ((int(event['submoduleID2']) & 0x7) << 15)
##    #Bits 50-57: Energy_B
##    word2 |= ((int(event['energy2']) & 0xFF) << 18)
##    #Bits 58-62: TA_TB_H
##    word2 |= ((int(event['time2']) & 0x1F) << 26)
##    #Bit 63: second 32-bit mark (always 1)
##    word2 |= (1 << 31)
##
##    #Combine the two 32-bit words into a 64-bit integer
##    raw64 = (np.uint64(word2) << 32) | np.uint64(word1)
##    return raw64
##
###pack all events
##raw64_words = [pack_rawdata(event) for event in events]
##
###write to .dat file
##with open("RawDataClean.2.raw", "wb") as f:
##    for word in raw64_words:
##        f.write(word.tobytes())  #write 64-bit word
##
###sanity check
##def unpack_rawdata(raw64):
##    """
##    Unpack a 64-bit RawData word into a dictionary of event fields.
##    """
##    word1 = np.uint32(raw64 & 0xFFFFFFFF)        # lower 32 bits
##    word2 = np.uint32((raw64 >> 32) & 0xFFFFFFFF)  # upper 32 bits
##
##    event = {
##        #First 32-bit word
##        'mod_pair_A': (word1 >> 0) & 0xF,
##        'Rawdata Tag': (word1 >> 4) & 0x1,
##        'crys_A_ax': (word1 >> 5) & 0x7,
##        'blk_A_ax': (word1 >> 8) & 0xF,
##        'crys_A_tr': (word1 >> 12) & 0x7,
##        'blk_A_tr': (word1 >> 15) & 0x7,
##        'Energy_A': (word1 >> 18) & 0xFF,
##        'TA_TB_L': (word1 >> 26) & 0x1F,
##        'mark1': (word1 >> 31) & 0x1,
##
##        #Second 32-bit word
##        'mod_pair_B': (word2 >> 0) & 0xF,
##        'Prompt/Delay mark': (word2 >> 4) & 0x1,
##        'crys_B_ax': (word2 >> 5) & 0x7,
##        'blk_B_ax': (word2 >> 8) & 0xF,
##        'crys_B_tr': (word2 >> 12) & 0x7,
##        'blk_B_tr': (word2 >> 15) & 0x7,
##        'Energy_B': (word2 >> 18) & 0xFF,
##        'TA_TB_H': (word2 >> 26) & 0x1F,
##        'mark2': (word2 >> 31) & 0x1
##    }
##    return event
##
###Read the first few 64-bit words for sanity check
##unpacked_events = []
##with open("RawDataClean.2.raw", "rb") as f:
##    for i in range(5):  # first 5 events
##        raw_bytes = f.read(8)  # 8 bytes = 64 bits
##        if not raw_bytes:
##            break
##        raw_word = np.frombuffer(raw_bytes, dtype=np.uint64)[0]
##        unpacked_event = unpack_rawdata(raw_word)
##        unpacked_events.append(unpacked_event)
##        print(f"Event {i+1}: {unpacked_event}")
##
###convert to DataFrame for comparison
##df_unpacked = pd.DataFrame(unpacked_events)
##print(df_unpacked)
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
