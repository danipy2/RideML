
# Read the file in binary
with open('presentation/team_qiyas_slides.html', 'rb') as f:
    raw = f.read()

# Find and replace: b'>88%</div><div class="lbl">R\xc2\xb2 explained'
old_bytes = b'>88%</div><div class="lbl">R\xc2\xb2 explained'
new_bytes = b'>88.6%</div><div class="lbl">R\xc2\xb2 explained'

if old_bytes in raw:
    raw = raw.replace(old_bytes, new_bytes, 1)
    print("Updated 88% -> 88.6% successfully")
else:
    print("Pattern not found, checking...")
    idx = raw.find(b'88%')
    if idx >= 0:
        print(f"Found 88% at byte {idx}: {raw[idx-10:idx+40]}")

# Write back
with open('presentation/team_qiyas_slides.html', 'wb') as f:
    f.write(raw)
print("File written back")

# Verify
with open('presentation/team_qiyas_slides.html', 'rb') as f:
    content = f.read()
if b'88.6%' in content:
    print("VERIFIED: 88.6% is now in the slides")
else:
    print("WARNING: 88.6% not found")
