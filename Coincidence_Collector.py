# import os
# import numpy as np
# # RAW_PATH   = "/Users/2025/Documents/David/raw_files/center_ps.raw"
# # OUT_COINC  = "/Users/2025/Documents/David/raw_files/center.u8"  # uint64 words
# RAW_PATH   = "/Users/2025/Documents/David/raw_files/vertical_ps.raw"
# OUT_COINC  = "/Users/2025/Documents/David/raw_files/vertical.u8"  # uint64 words
# N_EVENTS   = 100_000_000
# BYTESWAP   = False

# # How many uint64 words to read per chunk (tune if needed)
# CHUNK_WORDS = 2_000_000

# def get_bits_u64(x: np.ndarray, lo: int, hi: int) -> np.ndarray:
#     width = hi - lo + 1
#     mask = (np.uint64(1) << np.uint64(width)) - np.uint64(1)
#     return (x >> np.uint64(lo)) & mask

# def main():
#     total_words = os.path.getsize(RAW_PATH) // 8
#     print(f"RAW file: {RAW_PATH}")
#     print(f"Total words (uint64): {total_words:,}")
#     print(f"Target coincidences: {N_EVENTS:,}")
#     print(f"Chunk words: {CHUNK_WORDS:,}")
#     print(f"BYTESWAP: {BYTESWAP}")

#     found = 0
#     with open(RAW_PATH, "rb") as f_in, open(OUT_COINC, "wb") as f_out:
#         while found < N_EVENTS:
#             w = np.fromfile(f_in, dtype=np.uint64, count=CHUNK_WORDS)
#             if w.size == 0:
#                 break

#             if BYTESWAP:
#                 w = w.byteswap()

#             bit31 = get_bits_u64(w, 31, 31)
#             bit63 = get_bits_u64(w, 63, 63)
#             bit4  = get_bits_u64(w,  4,  4)

#             is_coinc = (bit31 == 0) & (bit63 == 1) & (bit4 == 1)
#             c = w[is_coinc]
#             if c.size == 0:
#                 continue

#             need = N_EVENTS - found
#             if c.size > need:
#                 c = c[:need]

#             c.tofile(f_out)
#             found += c.size

#             print(f"  wrote {c.size:,} | total {found:,}/{N_EVENTS:,}")

#     if found == 0:
#         raise RuntimeError("No coincidences found. Try BYTESWAP=True or confirm bit rules.")

#     print(f"\nDone. Wrote {found:,} coincidence uint64 words to:")
#     print(f"  {OUT_COINC}")

# if __name__ == "__main__":
#     main()




###############################################
###############MODULE SELECTION################
###############################################

import os
import numpy as np

RAW_PATH   = "/Users/2025/Documents/David/raw_files/center_ps.raw"
OUT_COINC  = "/Users/2025/Documents/David/raw_files/center_3.u8"  # uint64 words
# RAW_PATH   = "/Users/2025/Documents/David/raw_files/offset_ps.raw"
# OUT_COINC  = "/Users/2025/Documents/David/raw_files/offset_3.u8"  # uint64 words

N_EVENTS   = 1_000_000
BYTESWAP   = False


MODULE_1 = 0
MODULE_2 = 11

# How many uint64 words to read per chunk
CHUNK_WORDS = 2_000_000



# bit extraction
def get_bits_u64(x: np.ndarray, lo: int, hi: int) -> np.ndarray:
    width = hi - lo + 1
    mask = (np.uint64(1) << np.uint64(width)) - np.uint64(1)
    return (x >> np.uint64(lo)) & mask


#table 7
def build_pair_lut():
    """
    Return dict: pair_index -> (module_low, module_high)
    Based on uMI-550 Table 7
    """
    lut = {}
    base = [20, 39, 57, 74, 90, 105, 119, 132, 144,
            155, 165, 174, 182, 189, 195, 200, 204, 207, 209]

    for i in range(22):          # higher module index
        for j in range(i):       # lower module index
            if i >= j + 2:
                if j == 0:
                    code = i - 1
                else:
                    code = base[j - 1] + (i - j - 1)
                lut[code] = (j, i)

    return lut


PAIR_LUT = build_pair_lut()



def main():
    total_words = os.path.getsize(RAW_PATH) // 8
    print(f"RAW file: {RAW_PATH}")
    print(f"Total words (uint64): {total_words:,}")
    print(f"Target coincidences: {N_EVENTS:,}")
    print(f"Chunk words: {CHUNK_WORDS:,}")
    print(f"Filtering modules: {MODULE_1} & {MODULE_2}")
    print(f"BYTESWAP: {BYTESWAP}")

    found = 0

    with open(RAW_PATH, "rb") as f_in, open(OUT_COINC, "wb") as f_out:
        while found < N_EVENTS:
            w = np.fromfile(f_in, dtype=np.uint64, count=CHUNK_WORDS)
            if w.size == 0:
                break

            if BYTESWAP:
                w = w.byteswap()

            # --- coincidence word filter ---
            bit31 = get_bits_u64(w, 31, 31)
            bit63 = get_bits_u64(w, 63, 63)
            bit4  = get_bits_u64(w,  4,  4)
            is_coinc = (bit31 == 0) & (bit63 == 1) & (bit4 == 1)
            w = w[is_coinc]
            if w.size == 0:
                continue

            mod_pair_A = get_bits_u64(w,  0,  3)
            mod_pair_B = get_bits_u64(w, 32, 35)

            # Full pair index (Table 7)
            pair_code = mod_pair_A | (mod_pair_B << np.uint64(4))


            # unique_pairs, counts = np.unique(pair_code, return_counts=True)
            # print("Top pair codes:", list(zip(unique_pairs[:10], counts[:10])))

            # decode module numbers
            decoded = np.array(
                [PAIR_LUT.get(int(c), (-1, -1)) for c in pair_code],
                dtype=np.int16
            )
            mod_lo = decoded[:, 0]
            mod_hi = decoded[:, 1]

            #filter to desired module pair
            keep = (
                ((mod_lo == MODULE_1) & (mod_hi == MODULE_2)) |
                ((mod_lo == MODULE_2) & (mod_hi == MODULE_1))
            )

            w = w[keep]
            if w.size == 0:
                continue

            need = N_EVENTS - found
            if w.size > need:
                w = w[:need]

            w.tofile(f_out)
            found += w.size

            print(f"  wrote {w.size:,} | total {found:,}/{N_EVENTS:,}")

    if found == 0:
        raise RuntimeError("No coincidences found for selected module pair.")

    print(f"\nDone.")
    print(f"Wrote {found:,} coincidence words to:")
    print(f"  {OUT_COINC}")


if __name__ == "__main__":
    main()
