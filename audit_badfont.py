# -*- coding: utf-8 -*-
"""统计坏字体音标的污染范围：词库里音标为空/含乱码的词条，回查原文档音标文本"""
import io, json, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with io.open(r"c:\Users\wnok\CodeBuddy\初中单词\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])

GOOD = set("abcdefghijklmnopqrstuvwxyzəɪʊæɒʌɑɜɔθðʃʒŋʤʧɹʰ'ˌˈː()/.,:; +")
empty = [x for x in words if not x['p']]
print('音标为空的词条数:', len(empty), '/', len(words))
print()
print('--- 音标为空的词条（前60个）---')
for x in empty[:60]:
    print('  %-24s %s' % (x['w'], x['m'][:30]))

# 回查原文档里这些词的音标原文
xml = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx").read('word/document.xml').decode('utf-8')
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)
print()
print('--- 原文档中这些词的单词格原文（含乱码字符）---')
targets = {x['w'].split(' / ')[0].split('/')[0].split('（')[0].strip() for x in empty}
shown = 0
badchars = {}
for tr in rows:
    cs = re.split(r'</w:tc>', tr)
    if len(cs) < 3:
        continue
    wtxt = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cs[1]))
    key = wtxt.split('（')[0].split('/')[0].strip()
    if key and key in targets and '/' in wtxt:
        phon = wtxt[wtxt.index('/'):]
        garbage = [c for c in phon if c not in GOOD and c not in '增加删减● \n']
        for c in garbage:
            badchars[c] = badchars.get(c, 0) + 1
        if garbage and shown < 25:
            print('  %-26r %s' % (wtxt[:40], [hex(ord(c)) for c in set(garbage)]))
            shown += 1
print()
print('乱码字符统计:', {('%s U+%04X' % (k, ord(k))): v for k, v in sorted(badchars.items(), key=lambda kv: -kv[1])})
