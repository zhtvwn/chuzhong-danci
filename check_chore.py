# -*- coding: utf-8 -*-
"""核对 chore 词条：源文档行内容 + 图片"""
import io, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

xml = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx").read('word/document.xml').decode('utf-8')
rels = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx").read('word/_rels/document.xml.rels').decode('utf-8')
rid2file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="media/([^"]+)"', rels))
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)

hits = [tr for tr in rows if '杂务' in tr]
print('含"杂务"的行数:', len(hits))
for tr in hits:
    ts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', tr)
    print('  文本:', ts)
    rids = re.findall(r'r:embed="(rId\d+)"', tr)
    print('  图片:', [(r, rid2file.get(r)) for r in rids])
    if rids:
        z = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx")
        for r in rids:
            f = rid2file.get(r)
            if f:
                io.open(r'c:\Users\wnok\CodeBuddy\初中单词\imgs\chore_' + f, 'wb').write(z.read('word/media/' + f))
                print('  已导出: imgs/chore_' + f)
