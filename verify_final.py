# -*- coding: utf-8 -*-
"""按 JSON 解析 words.js，精确验证疑点"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

m = re.search(r'const\s+WORDS\s*=\s*(\[.*\])', open('words.js', encoding='utf-8').read(), re.S)
words = json.loads(m.group(1))
print(f'词库总数: {len(words)}')

print()
print('===== 词库中 Africa / African / AI / P.E. / UNESCO =====')
for i, w in enumerate(words):
    if re.search(r'Africa|UNESCO|artificial intel|physical edu|^AI|^P\.E\.', w['w']):
        print(f"  [{i}] w={w['w']!r} p={w.get('p','')!r} m={w.get('m','')!r} part={w.get('part')} day={w.get('day')}")

print()
print('===== 词库中 may / miss / us 全部条目 =====')
for key in ('may', 'miss', 'us'):
    hits = [(i, w) for i, w in enumerate(words) if w['w'].strip().lower() == key]
    print(f'-- {key}: {len(hits)} 条')
    for i, w in hits:
        print(f"  [{i}] w={w['w']!r} m={w.get('m','')!r} part={w.get('part')} day={w.get('day')}")

print()
print('===== 同 part 重复词原始统计（重跑 audit_final 的重复判定）====')
from collections import defaultdict
by_part = defaultdict(lambda: defaultdict(list))
for i, w in enumerate(words):
    k = re.sub(r'[（(].*?[）)]', '', w['w']).strip().rstrip('.').lower()
    by_part[w.get('part')][k].append((i, w['w']))
for part, d in sorted(by_part.items()):
    for k, lst in d.items():
        if len(lst) > 1:
            print(f'  Part{part} {k!r}: {lst}')
