# -*- coding: utf-8 -*-
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']')+1])
print('cat统计:', {c: sum(1 for x in w if x.get('cat') == c)
                  for c in ['部分国家、重要组织机构名称缩写', '节日、专有名词']})
print()
print('== 缩写 ==')
for x in w:
    if x.get('cat') == '部分国家、重要组织机构名称缩写':
        print('  %-30s %-16s t=%s' % (x['w'][:30], x['m'][:16], x['t']))
print()
print('== 节日/文化修复点 ==')
m = {x['w']: x for x in w}
for t in ['Mount Qomolangma', 'Beijing opera（Peking opera）', 'The Changjiang River（The Yangtze River）',
          'Traditional Chinese Medicine（TCM）', "Children's Day", "Teachers' Day", "Tian'anmen Square"]:
    e = m.get(t)
    print('  %-42s ->' % t, (e['m'] + ' t=' + str(e['t'])) if e else 'MISSING')
print()
bad = [x['w'] for x in w if re.search(r"\s+'|'\s+[A-Za-z]", x['w'])]
print('撇号空格残留:', len(bad), bad[:6])
print()
fest = [x['w'] for x in w if x.get('cat') == '节日、专有名词']
print('节日专有名词全部 %d 条:' % len(fest))
for f in fest:
    print('  ', f)
