import re

# Read the file in binary to see exact bytes around the 88% position
with open('presentation/team_qiyas_slides.html', 'rb') as f:
    raw = f.read()

# Find position of "88%"
idx = raw.find(b'88%')
print(f"Position in bytes: {idx}")
print(f"Raw bytes around: {raw[idx-150:idx+150]}")

# Find and show the R2 label bytes
label_idx = raw.find(b'>R', idx-200)
print(f"\nR-label bytes at {label_idx}: {raw[label_idx:label_idx+30]}")

# Show the full metric card for R2
# find 'lbl">R'
lbl_idx = raw.find(b'lbl">R', idx-200)
if lbl_idx > 0:
    print(f"\nlbl-R bytes at {lbl_idx}: {raw[lbl_idx:lbl_idx+50]}")
