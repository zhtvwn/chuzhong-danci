# -*- coding: utf-8 -*-
"""地理名称表全量对账：AST 提取所有格 -> 词库 cat=地理名称 比对"""
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
    return [x.strip() for x in lines if x.strip()]

label = ''
geo = []
def walk(x):
    global label
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            if label == '部分地理名称及相关信息':
                c = x['c']
                rows = list(c[3][1])
                for body in c[4]:
                    rows += body[2] + body[3]
                for r in rows:
                    cells = r[1] if isinstance(r, list) else r['c'][1]
                    for cell in cells:
                        for ln in cell_text(cell):
                            w = re.sub(r'●|增加|删减|变化', '', ln).strip()
                            mm = re.match(r'^[（(]([A-Za-z][A-Za-z. ]*)[）)]$', w)
                            if mm:
                                w = mm.group(1).strip()
                            if w and w != '/' and re.search(r'[A-Za-z]', w):
                                geo.append(w)
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            if txt.startswith('部分地理名称'):
                label = txt
            elif txt and label and not txt.startswith('部分地理'):
                label = txt  # 后续新标题覆盖
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])
print('源文档地理表全部格词 (%d):' % len(geo))
print(' ', geo)

s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']')+1])
allm = {x['w'] for x in w}
catg = [x['w'] for x in w if x.get('cat') == '地理名称']
print()
print('词库 cat=地理名称 (%d)' % len(catg))
print('源表有但词库完全没有的:', [g for g in geo if g not in allm])
ing = set(catg)
print('源表有但 cat 不是地理名称的:', [(g, next(x.get('cat') for x in w if x['w']==g)) for g in geo if g in allm and g not in ing])
