# -*- coding: utf-8 -*-
"""彻底核对：文档中所有带序号的行到底有多少，边缘情况全部列出"""
import io, json, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with io.open(r"c:\Users\wnok\CodeBuddy\初中单词\words_ast.json", encoding='utf-8') as f:
    doc = json.load(f)

def inlines_text(nodes):
    parts = []
    for n in nodes:
        if not isinstance(n, dict) or 't' not in n:
            continue
        t, c = n['t'], n.get('c')
        if t == 'Str':
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, list) and c:
                parts.append(c[0] if isinstance(c[0], str) else str(c[0][0]))
        elif t == 'Space':
            parts.append(' ')
        elif t in ('SoftBreak', 'LineBreak'):
            parts.append(' / ')
        elif isinstance(c, list):
            parts.append(inlines_text(c[-1]) if t == 'Link' else inlines_text(c))
    return ''.join(parts)

def blocks_text(blocks):
    lines = []
    def flat(bs):
        for b in bs:
            if not isinstance(b, dict):
                continue
            t = b['t']
            if t in ('Para', 'Plain'):
                lines.append(inlines_text(b['c']))
            elif t == 'BlockQuote':
                flat(b['c'])
            elif t == 'Div':
                flat(b['c'][-1])
    flat(blocks)
    return ' '.join(x.strip() for x in lines if x.strip())

def iter_rows(x):
    if isinstance(x, dict):
        if x.get('t') == 'Table':
            c = x['c']
            for row in c[3][1]:
                yield ('head', row)
            for body in c[4]:
                for row in body[2] + body[3]:
                    yield ('body', row)
            return
        for v in x.values():
            yield from iter_rows(v)
    elif isinstance(x, list):
        for v in x:
            yield from iter_rows(v)

def cell_text(cell):
    if isinstance(cell, dict):
        cell = cell['c']
    content = cell[4]
    if content and isinstance(content[0], list):
        blocks = [b for sub in content for b in sub]
    else:
        blocks = content
    return blocks_text(blocks)

cats = {'pure_digit': 0, 'digit_not_pure': 0, 'less3cells': 0, 'no_digit': 0}
not_pure_samples, less3_samples = [], []
pure_rows = []
for kind, row in iter_rows(doc):
    cells = row[1] if isinstance(row, list) else row['c'][1]
    if not isinstance(cells, list) or len(cells) < 2:
        cats['no_digit'] += 1
        continue
    idx = cell_text(cells[0]).strip()
    if re.match(r'^\d+$', idx):
        if len(cells) < 3:
            cats['less3cells'] += 1
            if len(less3_samples) < 10:
                less3_samples.append((idx, len(cells), [cell_text(c)[:30] for c in cells]))
        else:
            cats['pure_digit'] += 1
            pure_rows.append((idx, [cell_text(c)[:40] for c in cells]))
    elif re.search(r'\d', idx):
        cats['digit_not_pure'] += 1
        if len(not_pure_samples) < 20:
            not_pure_samples.append((idx, [cell_text(c)[:30] for c in cells]))
    else:
        cats['no_digit'] += 1

print('AST 行分类:', cats, '合计:', sum(cats.values()))
print()
print('--- 序号含数字但非纯数字的行 (%d) ---' % cats['digit_not_pure'])
for s in not_pure_samples:
    print('  ', repr(s[0]), s[1])
print()
print('--- 纯数字序号但单元格<3的行 (%d) ---' % cats['less3cells'])
for s in less3_samples:
    print('  ', s)
print()

# 词库对照
with io.open(r"c:\Users\wnok\CodeBuddy\初中单词\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])

# 纯数字行中：与词库匹配情况（按 行文本前几个词 匹配词库 w）
wset = {x['w'] for x in words}
matched, unmatched = 0, []
for idx, cells in pure_rows:
    word = cells[1].strip()
    # 14 个还原词 + position 修复词，它们的行内单词格是空的
    if not word:
        continue
    if word in wset:
        matched += 1
    else:
        unmatched.append((idx, word, cells[2] if len(cells) > 2 else ''))
print('纯数字序号行总数:', cats['pure_digit'])
print('其中单词能对上词库的:', matched)
print('对不上的（前 30 个）:')
for u in unmatched[:30]:
    print('  ', u)
print('对不上总数:', len(unmatched))
