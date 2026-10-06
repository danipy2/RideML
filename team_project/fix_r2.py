import re

# Read the file
with open('presentation/team_qiyas_slides.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Update "88%" -> "88.6%" in the R² metric card
# The hero metric card shows R2 = 88%
old = '<div class="val">88%</div><div class="lbl">R? explained</div>'
new = '<div class="val">88.6%</div><div class="lbl">R\u00b2 explained</div>'

if old in content:
    content = content.replace(old, new, 1)
    print("Updated R2 card to 88.6%")
else:
    print("Pattern not found - trying direct search")
    idx = content.find('88%')
    if idx >= 0:
        print(f"Found 88% at {idx}: {repr(content[idx-100:idx+100])}")

# Also ensure the R2 label shows proper R^2 symbol
# Check what the actual encoding looks like
idx = content.find('R? explained')
if idx >= 0:
    print(f"Found 'R? explained' - will fix encoding")
    # The ? is from encoding issue - fix the R2 label
    content = content.replace('R? explained', 'R\u00b2 explained')
    print("Fixed R2 label encoding")

# Write back
with open('presentation/team_qiyas_slides.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Written successfully")

# Verify
with open('presentation/team_qiyas_slides.html', 'r', encoding='utf-8') as f:
    content2 = f.read()
    
for needle in ['88.6%', '88%', 'R\u00b2 explained']:
    if needle in content2:
        idx = content2.find(needle)
        print(f'  VERIFIED: "{needle}" found at pos {idx}')
