# -*- coding: utf-8 -*-
"""1) 解析 rels 映射 rId->media 文件
2) 定位 14 个还原词条行中的图片，提取出来
3) 提取最大的 image385 及若干音标符号图片，供人工查看"""
import io, os, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOCX = r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx"
OUT = r"c:\Users\wnok\CodeBuddy\初中单词\imgs"
os.makedirs(OUT, exist_ok=True)

z = zipfile.ZipFile(DOCX)
xml = z.read('word/document.xml').decode('utf-8')
rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
rid2file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="media/([^"]+)"', rels))

rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)

def cells_of(tr):
    return re.split(r'</w:tc>', tr)

# 14 个还原词条: idx -> word
targets = {'197': 'brush', '255': 'cheap', '257': 'check', '261': 'chess', '262': 'chicken',
           '264': 'China', '265': 'Chinese', '266': 'chip', '268': 'choice', '269': 'choose',
           '467': 'English', '474': 'especially', '772': 'kitchen', '1153': 'question'}

found_imgs = []
for tr in rows:
    cs = cells_of(tr)
    m = re.search(r'<w:t[^>]*>(\d+)</w:t>', cs[0]) if cs else None
    if not m or m.group(1) not in targets:
        continue
    idx = m.group(1)
    rids = re.findall(r'r:embed="(rId\d+)"|r:id="(rId\d+)"', tr)
    flat = [r for pair in rids for r in pair if r]
    files = [rid2file.get(r, '?') for r in flat]
    print('行 %s (%s): 图片 %s' % (idx, targets[idx], files))
    for r, f in zip(flat, files):
        found_imgs.append((idx, targets[idx], r, f))

# 提取这些图片 + 最大的图
save = set(f for _, _, _, f in found_imgs)
save.add('image385.png')          # 最大 19KB
for n in z.namelist():
    if n.startswith('word/media/'):
        fn = n.split('/')[-1]
        if fn in save:
            data = z.read(n)
            with io.open(os.path.join(OUT, '%s_%s' % (idx if False else 'x', fn)), 'wb') as f:
                pass  # placeholder

for idx, word, r, f in found_imgs:
    data = z.read('word/media/' + f)
    out = os.path.join(OUT, '%s_%s' % (word, f))
    with io.open(out, 'wb') as fh:
        fh.write(data)
    print('已导出:', out, len(data), 'B')

data = z.read('word/media/image385.png')
with io.open(os.path.join(OUT, 'BIG_image385.png'), 'wb') as fh:
    fh.write(data)
print('已导出最大图: BIG_image385.png', len(data), 'B')
