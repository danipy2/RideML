import re

with open('presentation/team_qiyas_slides.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find R2 references  
print("=== R2 references ===")
matches = [(m.start(), content[max(0,m.start()-100):m.end()+100]) for m in re.finditer(r'88\.', content)]
for pos, ctx in matches[:10]:
    print(f'pos {pos}: ...{repr(ctx)}...')
    print('---')

# Find RMSE hero card
print("\n=== RMSE references ===")
matches2 = [(m.start(), content[max(0,m.start()-100):m.end()+100]) for m in re.finditer(r'RMSE', content)]
for pos, ctx in matches2[:10]:
    print(f'pos {pos}: ...{repr(ctx)}...')
    print('---')
