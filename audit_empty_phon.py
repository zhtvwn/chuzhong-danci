# -*- coding: utf-8 -*-
"""分析剩余空音标词条：原文档里有没有音标（文本/图片）"""
import io, json, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with io.open(r"c:\Users\wnok\CodeBuddy\初中单词\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])
empty = {x['w'].split(' / ')[0].split('（')[0].split('/')[0].strip() for x in words if not x['p']}

xml = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx").read('word/document.xml').decode('utf-8')
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)

no_speech_text, with_speech, img_only = [], [], []
for tr in rows:
    cs = re.split(r'</w:tc>', tr)
    if len(cs) < 3:
        continue
    wtxt = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cs[1])).strip()
    key = wtxt.split('（')[0].split('/')[0].strip()
    if not key or key not in empty:
        continue
    n_img = len(re.findall(r'r:embed="(rId\d+)"', cs[1]))
    if '/' in wtxt:
        with_speech.append(wtxt[:50])
    elif n_img:
        img_only.append((wtxt[:30], n_img))
    else:
        no_speech_text.append(wtxt[:50])

print('空音标词条的原文分布:')
print('  原文有音标文本(应可修复):', len(with_speech))
print('  原文无音标且无图片(源文档本来就没有):', len(no_speech_text))
print('  音标在图片里:', len(img_only))
print()
print('--- 有音标文本的（前25个，看是否还有未映射的乱码）---')
for x in with_speech[:25]:
    print('  ', repr(x))
print()
print('--- 音标在图片里的（前25个）---')
for x in img_only[:25]:
    print('  ', x)
print()
print('--- 源文档本来就没有音标的（前25个）---')
for x in no_speech_text[:25]:
    print('  ', x)
