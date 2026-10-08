# -*- coding: utf-8 -*-
"""追踪 'W P58 61' 行的解析过程"""
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
        elif t == 'RawInline':
            pass
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

def iter_rows(x):
    if isinstance(x, dict):
        if x.get('t') == 'Table':
            c = x['c']
            for row in c[3][1]:
                yield row
            for body in c[4]:
                for row in body[2] + body[3]:
                    yield row
            return
        for v in x.values():
            yield from iter_rows(v)
    elif isinstance(x, list):
        for v in x:
            yield from iter_rows(v)

for row in iter_rows(doc):
    cells = row[1] if isinstance(row, list) else row['c'][1]
    if not isinstance(cells, list) or len(cells) < 3:
        c0 = None
        try:
            c0 = cell_text(cells[0]) if cells else '?'
        except Exception:
            c0 = 'ERR'
        if c0 and 'P58' in str(c0):
            print('P58 行被 len<3 跳过, cells数:', len(cells), [cell_text(c)[:25] for c in cells])
        continue
    idx = cell_text(cells[0]).strip()
    if 'P58' in idx or 'upon' in idx:
        print('找到行: idx=', repr(idx))
        print('  cells:', [repr(cell_text(c)[:40]) for c in cells])
        print('  SHIFT 匹配:', idx in {'P30-33', 'W P58 61'})
        print('  idx 字符码:', [hex(ord(c)) for c in idx])
