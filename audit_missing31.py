# -*- coding: utf-8 -*-
"""31 个疑点行的完整清单 + 导出单词图片"""
import io, json, os, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOCX = r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx"
z = zipfile.ZipFile(DOCX)
xml = z.read('word/document.xml').decode('utf-8')
rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
rid2file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="media/([^"]+)"', rels))

with io.open(r"c:\Users\wnok\CodeBuddy\初中单词\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])
wset = {x['w'] for x in words}

def cell_text(cxml):
    return ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cxml)).strip()

def cell_imgs(cxml):
    return [rid2file.get(r, r) for r in re.findall(r'r:embed="(rId\d+)"', cxml)]

rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)
suspects = []
for tr in rows:
    cs = re.split(r'</w:tc>', tr)
    if len(cs) < 4:
        continue
    idx = cell_text(cs[0])
    if not re.match(r'^\d+$', idx):
        continue
    wtxt = cell_text(cs[1])
    if not cell_imgs(cs[1]):
        continue
    letters = re.sub(r'/.*?/', ' ', wtxt)
    letters = re.sub(r'[●增加删减（）()\s]+', ' ', letters).strip()
    first = letters.split(' ')[0] if letters else ''
    hit = (wtxt in wset) or (first in wset) or any(
        x == wtxt or x.split(' / ')[0] == wtxt for x in wset)
    if not hit:
        meaning = cell_text(cs[2]) if len(cs) > 2 else ''
        imgs = cell_imgs(cs[1])
        suspects.append((idx, wtxt, meaning[:26], imgs))

out = io.open(r"c:\Users\wnok\CodeBuddy\初中单词\suspects.txt", 'w', encoding='utf-8')
for idx, wtxt, meaning, imgs in suspects:
    line = '%-5s | %-44r | %s | %s' % (idx, wtxt[:44], meaning, imgs)
    print(line)
    out.write(line + '\n')
    for f in imgs:
        sz = z.getinfo('word/media/' + f).file_size
        if sz > 400:   # 徽标图标很小，>400B 的才是单词图
            data = z.read('word/media/' + f)
            io.open(r"c:\Users\wnok\CodeBuddy\初中单词\imgs\s%s_%s" % (idx, f), 'wb').write(data)
out.close()
print()
print('共', len(suspects), '行；单词图已导出到 imgs\\s{序号}_*.png')
