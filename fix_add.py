# -*- coding: utf-8 -*-
"""修复 add 释义: '增加'被●增加标记剥离逻辑误删 (原文 23号行: v. 增添；增加)"""
import io, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
PATH = r"c:\Users\wnok\CodeBuddy\初中单词\words.js"
with io.open(PATH, encoding='utf-8') as f:
    s = f.read()
old = '"m":"v. 增添；","n":"add ... to ... 将……添加到……"'
new = '"m":"v. 增添；增加","n":"add ... to ... 将……添加到……"'
n = s.count(old)
assert n == 1, "锚点匹配 %d 次" % n
s = s.replace(old, new)
with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print('add 释义已修复')
