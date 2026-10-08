# -*- coding: utf-8 -*-
"""从原始 document.xml 找回文本框中丢失的'2022新增'标记（严格版）
规则：
1. 只处理规范词汇行（<w:tr> 且首格为纯数字序号）
2. 只检测 单词格(cell[1]) 和 注释格(cell[3+]) 中的'增加'，跳过释义格(cell[2])，避免 'increase v.增加' 误标
3. 候选词取单词格第一个 <w:t>
"""
import io, json, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORDS_JS = r"c:\Users\wnok\CodeBuddy\初中单词\words.js"

with zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx") as z:
    xml = z.read('word/document.xml').decode('utf-8')

def cell_first_text(cell_xml):
    m = re.search(r'<w:t[^>]*>([^<]+)</w:t>', cell_xml)
    return m.group(1).strip() if m else ''

def cell_has_mark(cells):
    # cell[1]（单词格）与 cell[3:]（注释格，含文本框）含'增加'
    for i, c in enumerate(cells):
        if i == 0 or i == 2:   # 跳过序号格和释义格
            continue
        if '增' in c and '加' in c:
            return True
    return False

rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)
print('规范 <w:tr> 行数:', len(rows))

cands = set()
for tr in rows:
    cells = re.split(r'</w:tc>', tr)
    if len(cells) < 4:
        continue
    if not re.match(r'^\d+$', cell_first_text(cells[0]) or ''):
        continue
    if not cell_has_mark(cells):
        continue
    w = cell_first_text(cells[1])
    if w:
        cands.add(w)

print('含新增标记的候选词:', len(cands))
print(sorted(cands)[:12], '...')

with io.open(WORDS_JS, encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])

words_map = {}
for x in words:
    words_map.setdefault(x['w'], []).append(x)

changed, unmatched = 0, []
for cand in cands:
    hit = []
    if cand in words_map:
        hit = words_map[cand]
    else:
        pref = [x for x in words if x['w'].startswith(cand)]
        if pref:
            best = min(pref, key=lambda x: len(x['w']))
            hit = [best]
    if not hit:
        unmatched.append(cand)
        continue
    for x in hit:
        if not x['t']:
            x['t'] = True
            changed += 1

print('补充标记:', changed, ' 未匹配候选:', len(unmatched), unmatched[:12])
print('最终 2022新增标记:', sum(1 for x in words if x['t']), '/', len(words))

data = json.dumps(words, ensure_ascii=False, separators=(',', ':'))
with io.open(WORDS_JS, 'w', encoding='utf-8') as f:
    f.write('const WORDS=' + data + ';')
print('words.js 已更新')
