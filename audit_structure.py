# -*- coding: utf-8 -*-
"""探查文档结构：按文档顺序记录 PART/第N天 标题与表格行序号"""
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

def cell_first(cell):
    if isinstance(cell, dict):
        cell = cell['c']
    content = cell[4]
    blocks = [b for sub in content for b in sub] if content and isinstance(content[0], list) else content
    txt = []
    def flat(bs):
        for b in bs:
            if not isinstance(b, dict):
                continue
            if b['t'] in ('Para', 'Plain'):
                txt.append(inlines_text(b['c']))
            elif b['t'] == 'BlockQuote':
                flat(b['c'])
            elif b['t'] == 'Div':
                flat(b['c'][-1])
    flat(blocks)
    return ' '.join(txt).strip()

events = []

def walk(x):
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            c = x['c']
            rows = list(c[3][1])
            for body in c[4]:
                rows += body[2] + body[3]
            for row in rows:
                cells = row[1] if isinstance(row, list) else row['c'][1]
                if not isinstance(cells, list) or len(cells) < 2:
                    continue
                idx = cell_first(cells[0])
                if re.match(r'^\d+$', idx):
                    events.append(('ROW', idx))
            return
        if t == 'Header':
            events.append(('HDR', inlines_text(x['c'][2])))
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c'])
            if re.search(r'PART|第\s*\d+\s*天|短语|不规则', txt):
                events.append(('TXT', txt))
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])
print('事件总数:', len(events), ' 其中行事件:', sum(1 for k, _ in events if k == 'ROW'))
print()
prev_row = None
for i, (k, t) in enumerate(events):
    if k != 'ROW':
        nxt = next((x[1] for x in events[i + 1:] if x[0] == 'ROW'), None)
        print('[%-3s] 前行=%-5s 后行=%-5s  %s' % (k, prev_row, nxt, t[:64]))
    else:
        prev_row = t
