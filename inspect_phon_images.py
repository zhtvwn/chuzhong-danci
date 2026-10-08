# -*- coding: utf-8 -*-
"""提取若干词条音标中夹带的图片，确认它们是什么符号"""
import io, os, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOCX = r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx"
OUT = r"c:\Users\wnok\CodeBuddy\初中单词\imgs"
z = zipfile.ZipFile(DOCX)
xml = z.read('word/document.xml').decode('utf-8')
rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
rid2file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="media/([^"]+)"', rels))

rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)
# 找 alarm / about / able 等行，取其单词格里的图片
seen_rows = 0
for tr in rows:
    m = re.search(r'<w:t[^>]*>(\d+)</w:t>', tr)
    if not m:
        continue
    ts = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', tr))
    if not re.search(r"alarm|about|able|apple|adventure", ts[:60]):
        continue
    seen_rows += 1
    word = re.search(r'([a-zA-Z.]+)', ts[1:])
    print('---', ts[:50])
    # 逐格查看：第2格(单词+音标)里图片的位置
    cs = re.split(r'</w:tc>', tr)
    if len(cs) > 2:
        cell2 = cs[1]
        # 按文档顺序输出 文本/图片 序列
        seq = re.findall(r'<w:t[^>]*>([^<]*)</w:t>|r:embed="(rId\d+)"', cell2)
        line = []
        for t, r in seq:
            line.append(t if t else '[' + rid2file.get(r, r) + ']')
        print('   单词格序列:', ' '.join(line))
    if seen_rows >= 6:
        break
