# -*- coding: utf-8 -*-
"""PART2 精确比对：309 序号行（修复粘连后）vs 词库 308，找差异"""
import io, json, re, sys
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
            parts.append('\n')
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
            elif b['t'] == 'BlockQuote':
                flat(b['c'])
            elif b['t'] == 'Div':
                flat(b['c'][-1])
    flat(blocks)
    return '\n'.join(x.strip() for x in lines if x.strip())

def cell_text(cell):
    if isinstance(cell, dict):
        cell = cell['c']
    content = cell[4]
    if content and isinstance(content[0], list):
        blocks = [b for sub in content for b in sub]
    else:
        blocks = content
    return blocks_text(blocks)

GLUE = {'getup': 'get up', 'lookup': 'look up', 'pickup': 'pick up',
        'setup': 'set up', 'speedup': 'speed up', 'goodtime': 'good time'}

part = 1
num = []
def walk(x):
    global part
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            if part == 2:
                c = x['c']
                rows = list(c[3][1])
                for body in c[4]:
                    rows += body[2] + body[3]
                for r in rows:
                    cells = r[1] if isinstance(r, list) else r['c'][1]
                    if not isinstance(cells, list) or len(cells) < 3:
                        continue
                    idx = cell_text(cells[0]).strip()
                    if re.match(r'^\d+$', idx):
                        ph = cell_text(cells[1]).replace('\n', ' ').strip()
                        num.append((int(idx), ph, cell_text(cells[2])))
            return
        if t in ('Para', 'Plain', 'Header'):
            txt = inlines_text(x['c'] if t != 'Header' else x['c'][2]).strip()
            m = re.match(r'^PART\s*(\d)', txt)
            if m:
                part = int(m.group(1))
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])

def norm(ph):
    ph = ph.replace('’', "'")
    ph = re.sub(r"\s*'\s*(?=[A-Za-z])", "'", ph)
    ph = GLUE.get(ph, ph)
    return ph

src = [(i, norm(p), orig) for i, p, orig in ((i, p, p) for i, p, m in num)]
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']')+1])
p2 = [x['w'] for x in w if x['part'] == 2]
lib = set(p2)

print('序号行 309（规范化后）去重: %d' % len(set(p for _, p, _ in src)))
from collections import Counter
cnt = Counter(p for _, p, _ in src)
print('源表内重复的短语:', {k: v for k, v in cnt.items() if v > 1})
print()
miss = [(i, p) for i, p, _ in src if p not in lib]
print('规范化后词库仍缺 (%d):' % len(miss))
for i, p in miss:
    print('  #%d %r' % (i, p))
    row = next(r for r in num if r[0] == i)
    print('     原行:', [c.replace('\n', '⏎')[:70] for c in row[:3]])
print()
extra = [x for x in p2 if x not in set(p for _, p, _ in src)]
print('词库多出的 (%d):' % len(extra), extra)
