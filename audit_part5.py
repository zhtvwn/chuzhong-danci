# -*- coding: utf-8 -*-
"""PART 5 对账 v2：复用 parse_pandoc.py 的原函数，独立跟踪分类归属"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 加载解析器中 walk 之前的全部定义（不执行解析）
src = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\parse_pandoc.py', encoding='utf-8').read()
prefix = src[:src.index('walk(doc[')]
ns = {}
exec(prefix, ns)
inlines_text, blocks_text, cell_text, table_rows = ns['inlines_text'], ns['blocks_text'], ns['cell_text'], ns['table_rows']
split_pairs, norm_cat, clean_text = ns['split_pairs'], ns['norm_cat'], ns['clean_text']
NOISE = ns['NOISE']
doc = ns['doc']

state = {'in5': False, 'cat': '(无)', 'day': 0}
seq = []          # (w, m, cat, day)
lost = []         # PART5 中没切出词条的行
cat_lines = []

CATRE = re.compile(r'^[一二三四五]\s*、')

def note_cat(txt):
    if CATRE.match(txt) and re.search(r'动词|名词|形容词|副词', txt):
        state['cat'] = norm_cat(clean_text(txt))
        cat_lines.append(('段落', txt))
        return True
    return False

def walk(x):
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            if not state['in5']:
                return
            rows = table_rows(x)
            print('  [表格 %d 行 x %d 格]' % (len(rows), len(rows[0]) if rows else 0))
            for cells in rows:
                joined = ''.join(cells).strip()
                if CATRE.match(joined):
                    state['cat'] = norm_cat(clean_text(joined))
                    cat_lines.append(('表格行', joined[:30]))
                    continue
                for c in cells:
                    for ln in c.split('\n'):
                        ln = ln.strip(' ;')
                        if not ln:
                            continue
                        prs = split_pairs(ln)
                        if not prs and ln and not NOISE.match(ln):
                            lost.append((state['cat'], ln[:60]))
                        for w_, m_ in prs:
                            seq.append((w_, m_, state['cat'], state['day']))
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            if not txt:
                return
            m = re.match(r'^PART\s*(\d)', txt)
            if m:
                state['in5'] = m.group(1) == '5'
                if state['in5']:
                    print('===== PART 5 =====')
                return
            if not state['in5']:
                return
            if re.match(r'^第\s*(\d+)\s*天', txt):
                state['day'] = int(re.match(r'^第\s*(\d+)\s*天', txt).group(1))
                print(' [第%d天]' % state['day'])
                return
            if note_cat(txt):
                return
            if NOISE.match(txt):
                return
            prs = split_pairs(txt)
            if not prs:
                lost.append((state['cat'], txt[:60]))
            for w_, m_ in prs:
                seq.append((w_, m_, state['cat'], state['day']))
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])

print()
print('识别到的分类头:')
for k, t in cat_lines:
    print('  (%s) %s' % (k, t))
print()
print('源文档提取词条:', len(seq))
cnt = {}
for w_, m_, c, d in seq:
    cnt[c] = cnt.get(c, 0) + 1
for c, n in cnt.items():
    print('  %-30s %d' % (c[:34], n))
print()
print('未切出词条的行(%d):' % len(lost))
for c, t in lost[:30]:
    print('  [%s] %s' % (c[:16], t))

s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']') + 1])
lib = [x for x in w if x['part'] == 5]
libw = set(x['w'] for x in lib)
srcw = set(x[0] for x in seq)
print()
print('词库 %d | 源 %d | 源有库无 %d | 库有源无 %d' % (
    len(lib), len(seq), len(srcw - libw), len(libw - srcw)))
if srcw - libw:
    print(' 源有库无:', sorted(srcw - libw)[:20])
if libw - srcw:
    print(' 库有源无:', sorted(libw - srcw)[:20])
