# -*- coding: utf-8 -*-
"""完整导出数词表与月份星期表的全部行内容"""
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
        elif isinstance(c, list):
            parts.append(inlines_text(c[-1]) if t == 'Link' else inlines_text(c))
    return ''.join(parts)

def cell_text(cell):
    if isinstance(cell, dict):
        cell = cell['c']
    content = cell[4]
    if content and isinstance(content[0], list):
        blocks = [b for sub in content for b in sub]
    else:
        blocks = content
    lines = []
    def flat(bs):
        for b in bs:
            if not isinstance(b, dict):
                continue
            if b['t'] in ('Para', 'Plain'):
                lines.append(inlines_text(b['c']))
            elif b['t'] == 'BlockQuote':
                flat(b['c'])
            elif b['t'] == 'Div':
                flat(b['c'][-1])
    flat(blocks)
    return ' | '.join(x.strip() for x in lines if x.strip())

label = ''
tno = 0
def walk(x):
    global label, tno
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            tno += 1
            if label in ('数词表', '月份、星期词汇表'):
                c = x['c']
                rows = list(c[3][1])
                for body in c[4]:
                    rows += body[2] + body[3]
                print('=== %s (TABLE#%d, %d 行) ===' % (label, tno, len(rows)))
                for r in rows:
                    cells = r[1] if isinstance(r, list) else r['c'][1]
                    print('  ', ' ; '.join(cell_text(cl) or '·' for cl in cells))
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            if txt in ('数词表', '月份、星期词汇表'):
                label = txt
                tno = 0
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])
