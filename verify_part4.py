# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']') + 1])
m = {x['w']: x for x in w}

print('== 修复的截断释义 ==')
for k in ["with the help of sb. = with one's help",
          'have a great/difficult time（in）doing sth.',
          'have trouble/problems（in） doing sth.',
          'prefer doing A to doing B']:
    e = m.get(k)
    print(' ', k, '->', repr(e['m']) if e else 'MISSING')

for cat in ['way 短语', 'v.-ing 的使用', '短语荟萃']:
    print()
    print('== %s ==' % cat)
    for x in w:
        if x.get('cat') == cat:
            print(' ', x['w'], '|', x['m'])

print()
print('== 残留垃圾检查 ==')
bad = [x['w'] for x in w if x['w'] in ('v.-ing', 'B', 'to do', 'to do，', 'be used to',
                                       'wish, determine, afford, agree', 'remember, forget')
       or x['m'] in ('等', '又可接', '的使用', '在某人的帮', '做某事有', '做某事')]
print(' ', bad if bad else '无')

p4 = [x for x in w if x['part'] == 4]
print()
print('PART4 总数:', len(p4), '| 分类数:', len(set(x['cat'] for x in p4)))
