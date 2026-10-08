# -*- coding: utf-8 -*-
"""审计：源文档 2335 行的完整去向分析，核对 1962 是否有遗漏"""
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
            elif t == 'BlockQuote':
                flat(b['c'])
            elif t == 'Div':
                flat(b['c'][-1])
    flat(blocks)
    return '\n'.join(x.strip() for x in lines if x.strip())

def iter_rows(x):
    if isinstance(x, dict):
        if x.get('t') == 'Table':
            c = x['c']
            for row in c[3][1]:
                yield ('head', row)
            for body in c[4]:
                for row in body[2] + body[3]:
                    yield ('body', row)
            return
        for v in x.values():
            yield from iter_rows(v)
    elif isinstance(x, list):
        for v in x:
            yield from iter_rows(v)

def cell_text(cell):
    if isinstance(cell, dict):
        cell = cell['c']
    content = cell[4]
    if content and isinstance(content[0], list):
        blocks = [b for sub in content for b in sub]
    else:
        blocks = content
    return blocks_text(blocks)

total = 0
stats = {'head_row': 0, 'no_digit_idx': 0, 'empty_word': 0, 'ok': 0}
nondigit_samples, empty_samples = [], []
idx_max = 0
for kind, row in iter_rows(doc):
    total += 1
    cells = row[1] if isinstance(row, list) else row['c'][1]
    if not isinstance(cells, list) or len(cells) < 2:
        stats[kind + '_row'] = stats.get(kind + '_row', 0) + 1
        continue
    idx = cell_text(cells[0]).strip()
    if not re.match(r'^\d+$', idx):
        stats['no_digit_idx'] += 1
        if len(nondigit_samples) < 25:
            nondigit_samples.append(' | '.join(t for t in (cell_text(c) for c in cells) if t)[:70])
        continue
    idx_max = max(idx_max, int(idx))
    if not cell_text(cells[1]).strip():
        stats['empty_word'] += 1
        if len(empty_samples) < 15:
            empty_samples.append((idx, ' | '.join(t for t in (cell_text(c) for c in cells) if t)[:60]))
        continue
    stats['ok'] += 1

print('AST 总行数(含表头):', total)
print('有效词汇行(序号为纯数字且单词非空):', stats['ok'])
print('序号非纯数字的行:', stats['no_digit_idx'])
print('序号为数字但单词为空的行:', stats['empty_word'])
print('最大序号:', idx_max)
print()
print('--- 非数字序号行样例（这些行没有变成词条）---')
for s in nondigit_samples:
    print('  ', s)
print()
print('--- 单词为空行样例 ---')
for s in empty_samples:
    print('  ', s)

# 文档说明文字里声称的词条数
print()
print('--- 文档正文段落（找声称的总数）---')
for b in doc['blocks']:
    if isinstance(b, dict) and b['t'] == 'Para':
        t = inlines_text(b['c'])
        if re.search(r'\d{3,4}|个词汇|收录', t):
            print('  ', t[:160])
