import glob
import os

target_dir = "d:/Osool"
final_file = "nawy_final_py_1805.xlsx"
files = glob.glob(f"{target_dir}/*.xlsx")

print(f"Found {len(files)} Excel files.")

for f in files:
    fname = os.path.basename(f)
    if fname == final_file:
        print(f"✅ KEEPING: {fname}")
    else:
        try:
            os.remove(f)
            print(f"🗑️ DELETED: {fname}")
        except Exception as e:
            print(f"❌ Failed to delete {fname}: {e}")
