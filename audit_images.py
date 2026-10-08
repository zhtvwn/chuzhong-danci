# -*- coding: utf-8 -*-
"""审计 docx 中的图片：媒体文件、在 document.xml 中的位置（哪一行的哪个格）"""
import io, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOCX = r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx"
z = zipfile.ZipFile(DOCX)

# 1. 媒体文件清单
media = [(n, z.getinfo(n).file_size) for n in z.namelist()
         if n.startswith('word/media/')]
print('媒体文件数:', len(media))
for n, sz in sorted(media, key=lambda x: -x[1])[:40]:
    print('  %-40s %8d B' % (n, sz))

# 2. document.xml 中图片引用的分布
xml = z.read('word/document.xml').decode('utf-8')
drawings = len(re.findall(r'<w:drawing>', xml))
picts = len(re.findall(r'<w:pict>|<v:imagedata', xml))
print()
print('document.xml: <w:drawing> =', drawings, ', w:pict/v:imagedata =', picts)

# 3. 图片出现在哪些表格行（按序号定位）
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)
img_rows = []
for i, tr in enumerate(rows):
    n_img = len(re.findall(r'<w:drawing>|<v:imagedata', tr))
    if not n_img:
        continue
    idx = (re.search(r'<w:t[^>]*>([^<]+)</w:t>', tr) or [None, '?'])[1]
    ts = [t.strip() for t in re.findall(r'<w:t[^>]*>([^<]*)</w:t>', tr) if t.strip()]
    img_rows.append((i, idx, n_img, ts[:8]))
print('含图片的表格行数:', len(img_rows))
for i, idx, n, ts in img_rows[:30]:
    print('  行#%d 序号=%s 图片%d个: %s' % (i, idx, n, ts))
