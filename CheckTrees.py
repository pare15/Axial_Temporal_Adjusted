import uproot
import pandas as pd

file = uproot.open("C:/Users/david/OneDrive/Documents/Python/VaskaData/Hoffman_test.root")

print("Branches and file types")
print(file.classnames())
print()
print("\nContext of each branch:")
for key in file.keys():
    print(key, file[key].all_members)
    print()
