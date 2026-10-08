# -*- coding: utf-8 -*-
"""在 AST 表行中定位 add / really 的原文释义"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r"c:\Users\wnok\CodeBuddy\初中单词"
with io.open(BASE + r"\words_ast.json", encoding='utf-8') as f:
    doc = json.load(f)

def inlines_text(nodes):
    parts = []
    for n in nodes:
        if not isinstance(n, dict) or 't' not in n: continue
        t, c = n['t'], n.get('c')
        if t == 'Str':
            if isinstance(c, str): parts.append(c)
            elif isinstance(c, list) and c: parts.append(c[0] if isinstance(c[0], str) else str(c[0][0]))
        elif t == 'Space': parts.append(' ')
        elif t in ('SoftBreak', 'LineBreak'): parts.append('\n')
        elif isinstance(c, list): parts.append(inlines_text(c[-1]) if t == 'Link' else inlines_text(c))
    return ''.join(parts)

def blocks_text(blocks):
    lines = []
    def flat(bs):
        for b in bs:
            if not isinstance(b, dict): continue
            t = b['t']
            if t in ('Para', 'Plain'): lines.append(inlines_text(b['c']))
            elif t == 'BlockQuote': flat(b['c'])
            elif t == 'Div': flat(b['c'][-1])
    flat(blocks)
    return '\n'.join(x.strip() for x in lines if x.strip())

def cell_text(cell):
    if isinstance(cell, dict): cell = cell['c']
    content = cell[4]
    if content and isinstance(content[0], list): blocks = [b for sub in content for b in sub]
    else: blocks = content
    return blocks_text(blocks)

def table_rows(x):
    c = x['c']
    rows = list(c[3][1])
    for body in c[4]: rows += body[2] + body[3]
    out = []
    for row in rows:
        cells = row[1] if isinstance(row, list) else row['c'][1]
        if isinstance(cells, list): out.append([cell_text(cl) for cl in cells])
    return out

def walk(x):
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            for cells in table_rows(x):
                j = ' | '.join(cells)
                if re.search(r'\badd /', j) or re.search(r'\breally /', j):
                    print(ascii(j[:200]))
                    print('---')
            return
        if t == 'Para':
            txt = inlines_text(x['c'])
            if re.search(r'\badd\b', txt) and '增添' in txt or '真正' in txt:
                print('段:', ascii(txt[:150]))
                print('---')
            return
        if t == 'Figure': return
        for v in x.values(): walk(v)
    elif isinstance(x, list):
        for v in x: walk(v)
walk(doc['blocks'])
