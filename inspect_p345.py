# -*- coding: utf-8 -*-
"""按顺序遍历 AST：PART 3/4/5 的表格头与首行样本 + 全部行数对账"""
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
    blocks = [b for sub in content for b in sub] if content and isinstance(content[0], list) else content
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

part = None
table_no = 0
ast_row_total = 0
samples = []
last_event = ''

def walk(x):
    global part, table_no, ast_row_total, last_event
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            table_no += 1
            c = x['c']
            rows = list(c[3][1])
            for body in c[4]:
                rows += body[2] + body[3]
            ast_row_total += len(rows)
            if part and part >= 3:
                samples.append(('TABLE#%d (PART %d, after "%s") rows=%d' % (table_no, part, last_event[:20], len(rows))))
                for r in rows[:3]:
                    cells = r[1] if isinstance(r, list) else r['c'][1]
                    samples.append('   ' + ' ; '.join(cell_text(cl)[:26] for cl in cells))
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            if txt:
                last_event = txt
                if re.match(r'^PART\s*(\d)', txt):
                    part = int(re.match(r'^PART\s*(\d)', txt).group(1))
                    samples.append('===== %s =====' % txt[:40])
                elif len(samples) < 400:
                    samples.append('[P] ' + txt[:56])
            return
        if t == 'Header':
            last_event = inlines_text(x['c'][2])
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])
print('AST 总行数(含表头):', ast_row_total)
print()
for s in samples:
    print(s)
