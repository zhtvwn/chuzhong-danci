# -*- coding: utf-8 -*-
"""终审修复: P.E. 跨行截断 / increase 释义被'增加'标记清除误伤(两处)"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r"c:\Users\wnok\CodeBuddy\初中单词"
PATH = BASE + r"\words.js"

with io.open(PATH, encoding='utf-8') as f:
    s = f.read()

fixes = [
    # 1. P.E.: w 跨行截断, education) 误入 n 字段
    ('{"w":"P.E.（=physical","p":"","m":"n. 体育","n":"education)","t":false,"part":1,"day":19,"cat":""}',
     '{"w":"P.E.（=physical education）","p":"","m":"n. 体育","n":"","t":false,"part":1,"day":19,"cat":""}'),
    # 2. increase P1: 释义 '增加' 被 ●增加 标记剥离逻辑误删(原文: v. & n. 增加；繁殖)
    ('"m":"v. & n. ；繁殖","n":"increase <> decrease"',
     '"m":"v. & n. 增加；繁殖","n":"increase <> decrease"'),
    # 3. increase P5 分类表: 原文行 'increase 增加'
    ('{"w":"increase","p":"","m":"","n":"","t":true,"part":5,"day":42,"cat":"一、动词（中考高频、易错）"}',
     '{"w":"increase","p":"","m":"增加","n":"","t":true,"part":5,"day":42,"cat":"一、动词（中考高频、易错）"}'),
]
for old, new in fixes:
    n = s.count(old)
    assert n == 1, "锚点匹配 %d 次(应为1): %s" % (n, old[:60])
    s = s.replace(old, new)

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(s)

# 校验 + 全局扫描同类损坏
with io.open(PATH, encoding='utf-8') as f:
    s2 = f.read()
words = json.loads(s2[s2.index('['): s2.rindex(']') + 1])
print('词库总数:', len(words))
for x in words:
    if x['w'] in ('P.E.（=physical education）', 'increase'):
        print(json.dumps(x, ensure_ascii=False))

print('\n--- 可疑释义扫描 (标点起头/孤立的分隔符):')
bad = 0
for x in words:
    m = x['m']
    if re.match(r'^[；;，,。.]', m) or ' ；' in m[:6] or m.endswith('；'):
        bad += 1
        print(' ', json.dumps(x, ensure_ascii=False)[:120])
if not bad: print('  无')
