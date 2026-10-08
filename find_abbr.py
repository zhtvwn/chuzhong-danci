# -*- coding: utf-8 -*-
"""找到缩写表的原始形态并审计两类表在词库中的覆盖"""
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

# 1) 找含典型缩写词(WTO/UN/WHO)的块：显示块类型与上下文文本
hits = []
def scan(x, path=''):
    if isinstance(x, dict):
        t = x.get('t')
        if t in ('Para', 'Plain', 'Header'):
            txt = inlines_text(x['c'] if t != 'Header' else x['c'][2])
            if re.search(r'\b(WTO|WHO|UNESCO|NBA)\b', txt):
                hits.append(txt[:300])
            return
        for v in x.values():
            scan(v)
    elif isinstance(x, list):
        for v in x:
            scan(v)

scan(doc['blocks'])
print('含 WTO/WHO 等的文本块 (%d):' % len(hits))
for h in hits:
    print('  >>>', h.replace('\n', ' ⏎ ')[:280])
    print()
