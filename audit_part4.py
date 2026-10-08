# -*- coding: utf-8 -*-
"""PART 4 完形填空高频短语对账：源文档全部短语对 vs 词库 381 条"""
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

NOISE = re.compile(
    r'^(打卡|时间：|完成：|【注|课标词汇速查默写\s*\d*|义务教育英语课程标准词汇表\d*|'
    r'中考常考短语\s*\d*|\d+\s*中考常考短语|完形填空高频短语\s*\d*|\d+\s*完形填空高频短语|'
    r'不规则动词的过去式与过去分词\s*\d*|\d+\s*不规则动词的过去式与过去分词|'
    r'高频单词分类记\s*\d*|\d+\s*高频单词分类记|扫一扫.*|方法指导.*|写出词性及中文意思。)$')

def split_pair(txt):
    m = re.match(r'^([^一-鿿]*?)\s*([一-鿿].*)$', txt.strip())
    if not m:
        return None
    w, meaning = m.group(1).strip(' ;'), m.group(2).strip()
    mm = re.match(r'^(.*?)[（(]\s*$', w)
    if mm and mm.group(1).strip():
        w = mm.group(1).strip(); meaning = '（' + meaning
    w = re.sub(r'●|增加|删减', '', w).strip()
    w = re.sub(r'^[（(][^（）()]*[）)](?=\s*[A-Za-z])', '', w)
    mm = re.match(r'^[（(](.+)[）)]$', w)
    if mm:
        w = mm.group(1).strip()
    if re.search(r'[A-Za-z]', w) and w:
        return w, meaning
    return None

def split_pairs(txt):
    out = []
    for seg in re.split(r'(?<=[一-鿿；。，、])(?=\s*[A-Za-z])', txt):
        seg = seg.strip()
        if seg:
            pr = split_pair(seg)
            if pr:
                out.append(pr)
    return out

def norm_cat(c):
    return c.replace('(', '（').replace(')', '）')

state = {'part': 0, 'day': 0, 'cat': ''}
src_pairs = []          # (word, meaning, day, cat)
zero_paras = []        # 没切出任何短语的段落
table_count = 0

def handle_para(txt):
    txt = txt.strip()
    if not txt or NOISE.match(txt):
        return
    m = re.match(r'^PART\s*(\d)', txt)
    if m:
        state['part'] = int(m.group(1)); state['cat'] = ''
        print('--- PART %d ---' % state['part'])
        return
    m = re.match(r'^第\s*(\d+)\s*天', txt)
    if m:
        state['day'] = int(m.group(1)); return
    part = state['part']
    if part == 4:
        if re.match(r'^\S{1,10}\s*短语$', txt) or re.match(r'^[（(][一二三四五六]', txt) \
                or re.match(r'^[一二三四]、', txt) or txt in ('动词短语',):
            state['cat'] = norm_cat(txt)
            return
        pairs = split_pairs(txt)
        if not pairs:
            zero_paras.append((state['cat'], txt))
        for w_, m_ in pairs:
            src_pairs.append((w_, m_, state['day'], state['cat']))

def walk(x):
    global table_count
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            # PART 4 内出现的表格
            if state['part'] == 4:
                table_count += 1
                print('!! PART4 出现表格 #%d, 当前行数=%s, 当前分类=%s' % (
                    table_count, len(x['c'][3][1]), state['cat']))
                # 提取表格文本看看内容
                c = x['c']
                rows = list(c[3][1])
                for body in c[4]:
                    rows += body[2] + body[3]
                for r in rows[:5]:
                    cells = r[1] if isinstance(r, list) else r['c'][1]
                    if isinstance(cells, list):
                        print('    行:', [blocks_text(cl['c'][4] if isinstance(cl, dict) else cl[4])[:50] for cl in cells[:3]])
            return
        if t in ('Para', 'Plain'):
            handle_para(inlines_text(x['c']))
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])

print()
print('源文档 PART4 短语对总数:', len(src_pairs))
cats = {}
for w_, m_, d, c in src_pairs:
    cats[c] = cats.get(c, 0) + 1
print('源文档分类数:', len(cats))
for c, n in cats.items():
    print('  %-14s %d' % (c, n))

print()
print('未切出短语的段落(%d 个):' % len(zero_paras))
for c, t in zero_paras:
    print('  [%s] %s' % (c, t[:80]))

# 与词库比对
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']') + 1])
lib = [x for x in w if x['day'] in (38, 39, 40, 41) and x.get('cat') and '短语' in str(x.get('cat'))]
libkeys = set((x['w'], x.get('cat')) for x in lib)
srckeys = set((w_, c) for w_, m_, d, c in src_pairs)
print()
print('词库 PART4 短语数:', len(lib), '| 源文档:', len(src_pairs))
print('词库有、源没有:', [(a, b) for a, b in libkeys - srckeys][:10])
print('源有、词库没有:', [(a, b) for a, b in srckeys - libkeys][:10])
