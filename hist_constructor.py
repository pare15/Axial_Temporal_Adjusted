# import numpy as np
# import matplotlib.pyplot as plt


# IN_TICKS = "/Users/2025/Documents/David/raw_files/offset_3.i2"


# TICK_BIN_WIDTH = 1          
# WINDOW = (-512, 512)        

# SHOW_PEAK_LINE = True

# def main():
#     dt = np.fromfile(IN_TICKS, dtype=np.int16)
#     if dt.size == 0:
#         raise RuntimeError(f"No data in {IN_TICKS}")

#     lo, hi = WINDOW
#     # build edges so bins align on integer ticks
#     edges = np.arange(lo, hi + TICK_BIN_WIDTH + 1, TICK_BIN_WIDTH)

#     plt.figure()
#     n, bins, _ = plt.hist(dt.astype(np.int32), bins=edges)
#     plt.title(f"Center Point Source (N={dt.size:,},{TICK_BIN_WIDTH})")
#     plt.xlabel("Bins")
#     plt.ylabel("Counts")

#     if SHOW_PEAK_LINE and n.size > 0:
#         peak_i = int(np.argmax(n))
#         # bin center
#         peak_center = 0.5 * (bins[peak_i] + bins[peak_i + 1])
#         plt.axvline(peak_center, linestyle="--")
#         print(f"Peak near tick: {peak_center}")

#     plt.show()

# if __name__ == "__main__":
#     main()

################################
#######SINGLE HIST ABOVE########
################################

import numpy as np
import matplotlib.pyplot as plt

IN_TICKS_CENTER = "/Users/2025/Documents/David/raw_files/center_3.i2"
IN_TICKS_SHIFT  = "/Users/2025/Documents/David/raw_files/offset_3.i2"

# Histogram controls (in ticks)
TICK_BIN_WIDTH = 1
WINDOW = (-512, 512)     # ticks shown on x-axis

SHOW_PEAK_LINES = True
LABEL_DELTA = True       # annotate Δpeak in ticks on the plot


def peak_tick_from_dt(dt: np.ndarray) -> int:
    """Return the modal tick (peak) using 1-tick bins across [-512,511]."""
    # dt is int16 ticks in [-512,511]
    shifted = dt.astype(np.int32) + 512
    counts = np.bincount(shifted, minlength=1024)
    return int(np.argmax(counts)) - 512


def main():
    dt_c = np.fromfile(IN_TICKS_CENTER, dtype=np.int16)
    dt_s = np.fromfile(IN_TICKS_SHIFT,  dtype=np.int16)

    if dt_c.size == 0:
        raise RuntimeError(f"No data in {IN_TICKS_CENTER}")
    if dt_s.size == 0:
        raise RuntimeError(f"No data in {IN_TICKS_SHIFT}")

    peak_c = peak_tick_from_dt(dt_c)
    peak_s = peak_tick_from_dt(dt_s)
    delta = peak_s - peak_c

    print("Center N:", f"{dt_c.size:,}", "peak_tick:", peak_c)
    print("Shift  N:", f"{dt_s.size:,}", "peak_tick:", peak_s)
    print("Delta bins (shift - center):", delta)

    lo, hi = WINDOW
    edges = np.arange(lo, hi + TICK_BIN_WIDTH + 1, TICK_BIN_WIDTH)

    plt.figure()
    plt.hist(dt_c.astype(np.int32), bins=edges, alpha=0.6, label=f"center (peak {peak_c})")
    plt.hist(dt_s.astype(np.int32), bins=edges, alpha=0.6, label=f"6 cm (peak {peak_s})")

    plt.title(f"Delta Bins")
    plt.xlabel("Bins")
    plt.ylabel("Counts")
    plt.xlim(-150, 150)
    plt.legend()

    if SHOW_PEAK_LINES:
        plt.axvline(peak_c, linestyle="--")
        plt.axvline(peak_s, linestyle="--")

    if LABEL_DELTA:
        # Place the label near the top of the plot, between the peaks
        ymax = plt.gca().get_ylim()[1]
        xmid = 0.5 * (peak_c + peak_s)
        plt.text(
            xmid, 0.95 * ymax,
            f"Δpeak = {delta}",
            ha="center", va="top"
        )

    plt.show()


if __name__ == "__main__":
    main()
