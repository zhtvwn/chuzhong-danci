# -*- coding: utf-8 -*-
"""审计 PART 3 不规则动词：源表全部行 vs 词库 part=3"""
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
tables3 = []      # (标题前的最近Para, rows)
lastpara = ['']
def walk(x):
    global part, lastpara
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            if part == 3:
                c = x['c']
                rows = list(c[3][1])
                for body in c[4]:
                    rows += body[2] + body[3]
                tables3.append([cell_text(cl) for r in rows
                                for cl in (r[1] if isinstance(r, list) else r['c'][1]) if isinstance(cl, list) or True][:0] or
                               [[cell_text(cl) for cl in (r[1] if isinstance(r, list) else r['c'][1])]
                                for r in rows])
            return
        if t in ('Para', 'Plain', 'Header'):
            txt = inlines_text(x['c'] if t != 'Header' else x['c'][2]).strip()
            m = re.match(r'^PART\s*(\d)', txt)
            if m:
                part = int(m.group(1))
                lastpara = ['']
            elif part == 3 and txt:
                lastpara[0] = txt
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])

total = 0
for ti, rows in enumerate(tables3):
    print('=== 表 %d (%d 行)  上文: %r' % (ti + 1, len(rows), lastpara[0][:40]))
    for r in rows:
        cells = r
        total += 1
        print('   ', ' ; '.join((c or '·').replace('\n', '⏎')[:40] for c in cells))
print()
print('总行数:', total)
