# -*- coding: utf-8 -*-
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']')+1])
pat = [x['w'] for x in w if re.search(r"\s+'|'\s+[A-Za-z]", x['w'])]
print('撇号周围有空格的词条 (%d):' % len(pat))
for p in pat:
    print('  ', repr(p))
print()
ap = [x['w'] for x in w if re.search(r"([a-z])'([A-Z])", x['w'])]
print('小写-撇号-大写模式 (%d):' % len(ap), ap)
