import re

with open('presentation/team_qiyas_slides.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Check the hero metric cards - look for "9.24", "5.85", "88"
print("=== Checking displayed metrics ===")
for needle in ['9.24', '5.85', '88.56', '88%', 'R²', 'R2', '23%', '23.0%']:
    count = content.count(needle)
    if count > 0:
        idx = content.find(needle)
        snippet = content[max(0,idx-80):idx+80]
        # Clean for ASCII printing
        snippet_clean = snippet.encode('ascii', errors='replace').decode('ascii')
        print(f'  "{needle}" found {count} times. First: {snippet_clean}')
    else:
        print(f'  "{needle}" NOT FOUND')

print("\n=== Slide count ===")
slide_count = len(re.findall(r'<div class="slide', content))
print(f'  Total slides: {slide_count}')

# Check slide 4 model results  
s4_idx = content.find('id="s4"')
if s4_idx > 0:
    s4_snippet = content[s4_idx:s4_idx+500]
    s4_clean = s4_snippet.encode('ascii', errors='replace').decode('ascii')
    print(f'\nSlide 4 start: {s4_clean}')
