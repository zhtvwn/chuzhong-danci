# -*- coding: utf-8 -*-
"""审计：国家/组织机构缩写表 + 节日/中国文化专有名词表 与词库对账"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AST = r"c:\Users\wnok\CodeBuddy\初中单词\words_ast.json"

with io.open(AST, encoding='utf-8') as f:
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

# 关注的分类标题（原文档中的表述）
TARGETS = None   # 动态设定：最近一个匹配标题之后的表
KEEP = re.compile(r'(缩写|节日|文化|组织|机构|国家)')

tables = []          # (title, rows)
cur_title = ''

def walk(x):
    global cur_title, TARGETS
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            if TARGETS:
                c = x['c']
                rows = list(c[3][1])
                for body in c[4]:
                    rows += body[2] + body[3]
                out = []
                for r in rows:
                    cells = r[1] if isinstance(r, list) else r['c'][1]
                    if not isinstance(cells, list):
                        continue
                    out.append([cell_text(cl) for cl in cells])
                tables.append((cur_title, out))
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            if txt and KEEP.search(txt) and len(txt) < 40:
                cur_title = txt
                TARGETS = txt
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])

for title, rows in tables:
    print('=' * 70)
    print('### %s  (%d 行)' % (title, len(rows)))
    for r in rows:
        print('   ', ' ; '.join((c or '·').replace('\n', '⏎') for c in r))
