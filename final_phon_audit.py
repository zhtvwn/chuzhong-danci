# -*- coding: utf-8 -*-
"""最后核对：空音标词条中，哪些是单词（应有音标）、哪些是短语（本来就无）"""
import io, json, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with io.open(r"c:\Users\wnok\CodeBuddy\初中单词\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])

# 短语特征: 含空格/省略号/.../介词结构等
def is_phrase(w):
    core = re.sub(r'（[^）]*）', '', w)
    return bool(re.search(r'\s|\.\.\.|…', core)) and not re.match(r"^(a|an|be|Mr|Mrs|Ms|P\.E\.|a\.m\.|p\.m\.)$", core)

word_empty = [x for x in words if not x['p'] and not is_phrase(x['w'])]
phrase_empty = [x for x in words if not x['p'] and is_phrase(x['w'])]
print('空音标-单词类:', len(word_empty))
for x in word_empty:
    print('  %-28s %s' % (x['w'], x['m'][:34]))
print()
print('空音标-短语类(源文档本无音标):', len(phrase_empty))
