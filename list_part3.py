# -*- coding: utf-8 -*-
"""PART3 完整词条清单 + 各种数法对账"""
import io, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
s = io.open(r'c:\Users\wnok\CodeBuddy\初中单词\words.js', encoding='utf-8').read()
w = json.loads(s[s.index('['):s.rindex(']')+1])
p3 = [x for x in w if x['part'] == 3]
i = 0
cur = None
for x in p3:
    if x['cat'] != cur:
        cur = x['cat']
        print('\n[%s]' % cur)
    i += 1
    print('%3d  %-14s %s  (n=%s)' % (i, x['w'], x['m'][:46], x['n'] or '-'))
print('\n动词条目总数:', i)
print()
print('特殊行提示:')
print('  - be 动词拆成 2 条: "am / is"(was/been) 和 "are"(were/been)')
print('  - 情态动词 5 条: can shall may will must（原文档一行放两对）')
