# -*- coding: utf-8 -*-
import io, json, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']')+1])
p3 = [x for x in w if x['part'] == 3]
print('part=3 词条:', len(p3), '| 去重:', len(set(x['w'] for x in p3)))
m = {x['w']: x for x in p3}
print()
tests = ['do', 'go', 'bear', 'burn', 'get', 'must', 'am / is', 'lie（躺）', 'hang（悬挂）',
         'have(has)', 'mistake', 'awake', 'freeze', 'shoot', 'sweep', 'bleed', 'deal',
         'understand', 'cost', 'become']
for t in tests:
    e = m.get(t)
    if e:
        info = (e['w'] + ' : ' + e['m'] + ' | ' + e['n'])[:90]
        print('  %-14s -> %s' % (t, info))
    else:
        print('  %-14s -> MISSING' % t)
print()
print('cat分布:')
for c, n in Counter(x['cat'] for x in p3).most_common():
    print('  %-44s %d' % (c, n))
print('day分布:', dict(sorted(Counter(x['day'] for x in p3).items())))
