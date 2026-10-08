# -*- coding: utf-8 -*-
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
src = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\parse_pandoc.py', encoding='utf-8').read()
ns = {}
exec(src[:src.index('walk(doc[')], ns)
inlines_text, table_rows, split_pairs = ns['inlines_text'], ns['table_rows'], ns['split_pairs']
doc = ns['doc']

state = {'in5': False, 'cat': ''}
seq = []
def walk(x):
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            if not state['in5']:
                return
            for cells in table_rows(x):
                joined = ''.join(cells).strip()
                if re.match(r'^[一二三四五]\s*、', joined):
                    state['cat'] = joined
                    continue
                for c in cells:
                    for ln in c.split('\n'):
                        ln = ln.strip(' ;')
                        if ln:
                            for w_, m_ in split_pairs(ln):
                                seq.append((w_, state['cat']))
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c']).strip()
            m = re.match(r'^PART\s*(\d)', txt)
            if m:
                state['in5'] = m.group(1) == '5'
                return
            if not state['in5'] or not txt:
                return
            if re.match(r'^[一二三四五]\s*、', txt) and re.search(r'动词|名词|形容词|副词', txt):
                state['cat'] = txt
                return
            for w_, mm in split_pairs(txt):
                seq.append((w_, state['cat']))
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])
from collections import Counter
cnt = Counter(w_ for w_, c in seq)
dups = {k: v for k, v in cnt.items() if v > 1}
print('源文档内重复出现的词:', dups)
for k in dups:
    print(' ', k, '->', [c[:12] for w_, c in seq if w_ == k])
