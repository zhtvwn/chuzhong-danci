# -*- coding: utf-8 -*-
"""找回 14 个单词格为空但释义存在的词条：
1. 从原始 XML 提取这些行的英文单词、音标、增加标记
2. 从 AST 取释义/注释
3. 补进 words.js
"""
import io, json, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MISSING_IDX = {'197', '255', '257', '261', '262', '264', '265', '266', '268', '269',
               '467', '474', '772', '1153'}

# ---------- 1. 原始 XML 提取 ----------
with zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx") as z:
    xml = z.read('word/document.xml').decode('utf-8')

def cell_first_text(cell_xml):
    m = re.search(r'<w:t[^>]*>([^<]+)</w:t>', cell_xml)
    return m.group(1).strip() if m else ''

found = {}
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)
for tr in rows:
    cells = re.split(r'</w:tc>', tr)
    if len(cells) < 4:
        continue
    idx = cell_first_text(cells[0])
    if idx not in MISSING_IDX:
        continue
    # 行内全部 <w:t>
    ts = [t.strip() for t in re.findall(r'<w:t[^>]*>([^<]*)</w:t>', tr) if t.strip()]
    # 单词 = 第一个纯英文文本（跳过序号）
    word = ''
    for t in ts:
        if re.match(r"^[A-Za-z][A-Za-z .,'\-/]*$", t) and t != idx:
            word = t
            break
    # 音标 = 第一个 /.../ 形式文本
    phon = ''
    for t in ts:
        if re.match(r"^/[^/]+/", t) or (t.startswith('/') and t.count('/') >= 2):
            phon = t
            break
    mark = ('增' in tr and '加' in tr)
    # 释义格 = 第三个单元格
    meaning = ''
    mts = [t for t in re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cells[2]) if t.strip()]
    if mts:
        meaning = ''.join(mts).strip()
    found[idx] = {'w': word, 'p': phon, 'm': meaning, 't': mark}

print('XML 中找回:')
for k in sorted(found, key=int):
    print('  ', k, found[k]['w'], '|', found[k]['p'][:30], '|', found[k]['m'][:24], '| mark:', found[k]['t'])

# ---------- 2. 写入 words.js ----------
WORDS_JS = r"c:\Users\wnok\CodeBuddy\初中单词\words.js"
with io.open(WORDS_JS, encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])
have = {x['w'] for x in words}

added = 0
for idx, info in sorted(found.items(), key=lambda kv: int(kv[0])):
    if not info['w'] or info['w'] in have:
        continue
    words.append({'w': info['w'], 'p': info['p'], 'm': info['m'], 'n': '', 't': info['t']})
    have.add(info['w'])
    added += 1

print('补充词条数:', added)
print('词条总数:', len(words), '| 重复检查:', len(words) - len(have))

data = json.dumps(words, ensure_ascii=False, separators=(',', ':'))
with io.open(WORDS_JS, 'w', encoding='utf-8') as f:
    f.write('const WORDS=' + data + ';')
print('words.js 已更新')
