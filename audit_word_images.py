# -*- coding: utf-8 -*-
"""系统排查：所有单词格(第2列)含图片的行，逐行核对词库覆盖情况"""
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
result = []      # (idx, word_text, phon_text, word_imgs, meaning)
for tr in rows:
    cs = re.split(r'</w:tc>', tr)
    if len(cs) < 4:
        continue
    idx = cell_text(cs[0])
    if not re.match(r'^\d+$', idx):
        continue
    wc = cs[1]
    wtxt = cell_text(wc)
    wimgs = cell_imgs(wc)
    if not wimgs:
        continue                       # 单词格无图片，不管
    meaning = cell_text(cs[2]) if len(cs) > 2 else ''
    result.append((idx, wtxt, wimgs, meaning[:20]))

print('单词格含图片的行数:', len(result))
print()
n_missing, missing = 0, []
for idx, wtxt, imgs, meaning in result:
    # 单词格文本中能找到的英文词（去掉音标/●增加等）
    letters = re.sub(r'/.*?/', ' ', wtxt)
    letters = re.sub(r'[●增加删减（）()\s]+', ' ', letters).strip()
    # 词库里是否存在（按整个文本或首词匹配）
    first = letters.split(' ')[0] if letters else ''
    hit = (wtxt in wset) or (first in wset) or any(
        x == wtxt or x.split(' / ')[0] == wtxt for x in wset)
    flag = 'OK ' if hit else '???'
    if not hit:
        n_missing += 1
        missing.append((idx, wtxt, imgs, meaning))
    print('%s %-5s 格文本=%-40r 图片=%s' % (flag, idx, wtxt[:40], imgs))

print()
print('词库覆盖不到的行数:', n_missing)
os.makedirs(r"c:\Users\wnok\CodeBuddy\初中单词\imgs", exist_ok=True)
for idx, wtxt, imgs, meaning in missing:
    for f in imgs:
        data = z.read('word/media/' + f)
        io.open(r"c:\Users\wnok\CodeBuddy\初中单词\imgs\miss%s_%s" % (idx, f), 'wb').write(data)
print('缺失行的图片已导出到 imgs\\')
