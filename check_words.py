# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with io.open(r"c:\Users\wnok\CodeBuddy\初中单词\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])
m = {x['w']: x for x in words}

print('词条总数:', len(words), '| 音标:', sum(1 for x in words if x['p']),
      '| 2022新增:', sum(1 for x in words if x['t']),
      '| 重复:', len(words) - len(m), '| 缺释义:', sum(1 for x in words if not x['m']))
print()
print('--- 14 个还原词条抽查 ---')
for w in ['brush', 'cheap', 'check', 'chess', 'chicken', 'China', 'Chinese',
          'chip', 'choice', 'choose', 'English', 'especially', 'kitchen', 'question']:
    x = m.get(w)
    print(' ', (w + ' ' * 12)[:12], '->', (x['p'] or '无音标').ljust(16), '|', x['m'][:22],
          '| t=' + str(x['t']), '|', (x['n'] or '')[:20])
