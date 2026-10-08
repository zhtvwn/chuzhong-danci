# -*- coding: utf-8 -*-
"""检查 PART 1 第31/32天的附加表格（数词表/月份星期/地理名称）格式 + PART 4 短语段落统计"""
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

state = {'part': 1, 'label': '', 'p4': [], 'p4cat': ''}
out = []
table_no = [0]

def walk(x):
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            table_no[0] += 1
            c = x['c']
            rows = list(c[3][1])
            for body in c[4]:
                rows += body[2] + body[3]
            # 关注第31/32天的表格（在数词表事件之后）
            if state['label'] in ('数词表', '月份、星期词汇表', '部分地理名称及相关信息'):
                out.append('TABLE#%d rows=%d [after %s]' % (table_no[0], len(rows), state['label']))
                for r in rows[:4]:
                    cells = r[1] if isinstance(r, list) else r['c'][1]
                    out.append('   ' + ' ; '.join(cell_text(cl)[:30] for cl in cells))
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            if not txt:
                return
            if txt in ('数词表', '月份、星期词汇表', '部分地理名称及相关信息'):
                state['label'] = txt
                out.append('===== %s =====' % txt)
                return
            if re.match(r'^PART\s*(\d)', txt):
                state['part'] = int(re.match(r'^PART\s*(\d)', txt).group(1))
                out.append('===== %s =====' % txt)
                return
            if state['part'] == 4:
                state['p4'].append(txt)
                if len(txt) < 22 and ('短语' in txt or re.match(r'^[（一二三四五六]、]', txt) or re.match(r'^(动词|介词|其他)短语$', txt)):
                    state['p4cat'] = txt
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])
print('\n'.join(out[:60]))
print()
p4 = state['p4']
print('PART 4 段落总数:', len(p4))
# 短语段落 = 以英文开头且含中文的
phrase_paras = [t for t in p4 if re.match(r"^[a-zA-Z(]", t) and re.search(r'[\u4e00-\u9fff]', t)]
label_paras = [t for t in p4 if t not in phrase_paras]
print('其中短语段:', len(phrase_paras), ' 标签段:', len(label_paras))
print('标签:', label_paras)
print()
print('短语段样例:', phrase_paras[:6], '...', phrase_paras[-4:])
