# -*- coding: utf-8 -*-
"""跟踪 afraid 等词在解析器路径下的处理"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

src = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\parse_pandoc.py', encoding='utf-8').read()
prefix = src[:src.index('walk(doc[')]
ns = {}
exec(prefix, ns)
inlines_text, blocks_text, cell_text, table_rows = ns['inlines_text'], ns['blocks_text'], ns['cell_text'], ns['table_rows']
split_pairs, norm_cat, clean_text = ns['split_pairs'], ns['norm_cat'], ns['clean_text']
NOISE = ns['NOISE']
doc = ns['doc']

TARGETS = {'afraid', 'asleep', 'beautiful', 'bright', 'certain', 'clever', 'common',
           'correct', 'cruel', 'daily', 'dear', 'embarrassed', 'excited', 'famous',
           'fit', 'free', 'hard', 'honest', 'impossible', 'knowledgeable'}

state = {'part': 0, 'day': 0, 'cat': ''}
tno = 0

def walk(x):
    global tno
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            tno += 1
            rows = table_rows(x)
            if state['part'] == 5:
                print('表格#%d (%d行)' % (tno, len(rows)))
                for cells in rows:
                    joined = ''.join(cells).strip()
                    if re.match(r'^[一二三四五]\s*、', joined):
                        print('  [分类行]', joined[:30])
                        continue
                    for c in cells:
                        for ln in c.split('\n'):
                            ln2 = ln.strip(' ;')
                            if not ln2:
                                continue
                            prs = split_pairs(ln2)
                            if any(w_ in TARGETS for w_, m_ in prs):
                                print('  !! 含目标词: 行=%r -> pairs=%r' % (ln2[:70], [(w_, m_[:20]) for w_, m_ in prs]))
                            if not prs and re.search(r'[A-Za-z]', ln2) and not NOISE.match(ln2) and '天' not in ln2[:6]:
                                print('  ?? 未切出: %r' % ln2[:70])
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            m = re.match(r'^PART\s*(\d)', txt)
            if m:
                state['part'] = int(m.group(1))
                print('===== PART %d =====' % state['part'])
                return
            if state['part'] == 5 and txt and 'afraid' in txt:
                print('  [段落含afraid]', txt[:80])
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])
