# -*- coding: utf-8 -*-
"""审计 PART 2 中考常考短语：源表序号行 vs 词库"""
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

part = 1
rows2 = []        # (day, cells)
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
                    if not isinstance(cells, list):
                        continue
                    rows2.append([cell_text(cl) for cl in cells])
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

num = [r for r in rows2 if len(r) >= 3 and re.match(r'^\d+$', r[0].strip())]
other = [r for r in rows2 if r not in num]
print('PART2 表总行: %d  纯数字序号行: %d' % (len(rows2), len(num)))
print('序号范围: %s ~ %s' % (num[0][0].strip() if num else '-', num[-1][0].strip() if num else '-'))
# 序号完整性
ids = [int(r[0].strip()) for r in num]
miss = [i for i in range(1, max(ids) + 1) if i not in ids]
dup = sorted(set(i for i in ids if ids.count(i) > 1))
print('序号缺口:', miss if miss else '无', ' 重复序号:', dup if dup else '无')
print()
print('非序号行 (%d):' % len(other))
for r in other[:12]:
    print('  ', [c.replace('\n', '⏎')[:60] for c in r])

# 词库对账
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']')+1])
p2 = [x for x in w if x['part'] == 2]
print()
print('词库 part=2: %d 条  天分布: %s' % (len(p2), {d: sum(1 for x in p2 if x['day']==d) for d in sorted(set(x['day'] for x in p2))}))
src = {}
for r in num:
    src[int(r[0].strip())] = r[1].replace('\n', ' ').strip()
lib = {x['w'] for x in p2}
print()
print('序号行中词库没有的:')
for i, ph in sorted(src.items()):
    key = ph.replace('’', "'").replace('goodtime', 'good time')
    key = re.sub(r"\s*'\s*(?=[A-Za-z])", "'", key)
    if key not in lib:
        # 宽松再试
        loose = next((x['w'] for x in p2 if key.split('（')[0].split(' =')[0].strip() in x['w']), None)
        print('  #%d %r -> %s' % (i, ph[:60], '近似 ' + loose if loose else 'MISSING'))
