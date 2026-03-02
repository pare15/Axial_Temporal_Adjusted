import uproot
import numpy as np
import os

INPUT_ROOT_FILE = "/Users/2025/Documents/David/root_files/hoff_E_blur.root"
OUTPUT_ROOT_FILE = "/Users/2025/Documents/David/root_files/hoff_E_blur_sorted.root"
TREE_PROMPTS = "Coincidences"
TREE_DELAYED = "RandCoincidences"
SORT_COLUMN = "time1"

def main():
    if not os.path.exists(INPUT_ROOT_FILE):
        print("Error: Input file not found.")
        return

    with uproot.open(INPUT_ROOT_FILE) as f:
        # 1. Load the time1 for both prompts and delays
        print(f"Extracting sorting keys...")
        t1_p = f[TREE_PROMPTS][SORT_COLUMN].array(library="np")
        t1_d = f[TREE_DELAYED][SORT_COLUMN].array(library="np")
        
        # Keep track of which tree each entry came from 0 for prompt, 1 for delayed
        source_id = np.concatenate([np.zeros(len(t1_p)), np.ones(len(t1_d))])
        # Combine times into a single list
        combined_times = np.concatenate([t1_p, t1_d])

        # 2. O(n log n))
        # Orders indices, rows not moved yet (quicksort)
        print(f"Calculating index map...")
        sort_indices = np.argsort(combined_times, kind = 'mergesort')
        
        # Apply map
        final_source_map = source_id[sort_indices]


        # 3. Write branches
        print(f"Writing sorted branches to {os.path.basename(OUTPUT_ROOT_FILE)}...")
        # Idk internet told me to use recreate
        with uproot.recreate(OUTPUT_ROOT_FILE) as f_out:
            
            
            all_branches = f[TREE_PROMPTS].keys()
            
            data_to_write = {}
            for branch in all_branches:
                print(f"  Sorting branch: {branch}")
                # Load the full column from both trees
                arr_p = f[TREE_PROMPTS][branch].array(library="np")
                arr_d = f[TREE_DELAYED][branch].array(library="np")
                
                # Combine
                combined_arr = np.concatenate([arr_p, arr_d])   
                
                # Reorder them using map
                data_to_write[branch] = combined_arr[sort_indices]
            
            # Add delays column
            data_to_write['is_delayed'] = final_source_map
            
            f_out["SortedCoincidences"] = data_to_write

    print("\nSuccess!")

if __name__ == "__main__":
    main()
