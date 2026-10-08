# -*- coding: utf-8 -*-
"""按顺序列出含'缩写'标题之后的所有段落（直到下一个标题），并查词库覆盖"""
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

seq = []   # (kind, text)
def walk(x):
    if isinstance(x, dict):
        t = x.get('t')
        if t in ('Para', 'Plain'):
            seq.append(('p', inlines_text(x['c'])))
            return
        if t == 'Header':
            seq.append(('h', inlines_text(x['c'][2])))
            return
        if t == 'Table':
            seq.append(('t', '<TABLE>'))
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])

# 找 '缩写' 标题（段落形式）
idx = None
for i, (k, txt) in enumerate(seq):
    if '缩写' in txt and len(txt) < 40:
        idx = i
        print('标题行 [%s]: %r' % (k, txt))
if idx is None:
    print('!!! 未找到 缩写 标题，搜索相关段落:')
    for i, (k, txt) in enumerate(seq):
        if 'UNESCO' in txt or '组织' in txt and len(txt) < 50:
            print(i, k, repr(txt[:60]))
else:
    print('--- 之后的块序列 ---')
    for k, txt in seq[idx:idx + 45]:
        print(' [%s] %s' % (k, (txt or '').replace('\n', ' ⏎ ')[:120]))
