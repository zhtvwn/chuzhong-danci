# -*- coding: utf-8 -*-
"""找出含 D/A/E 等待定乱码字符的音标，确定映射"""
import io, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

xml = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx").read('word/document.xml').decode('utf-8')
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)

for tr in rows:
    cs = re.split(r'</w:tc>', tr)
    if len(cs) < 3:
        continue
    wtxt = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cs[1]))
    if '/' not in wtxt:
        continue
    phon = wtxt[wtxt.index('/'):]
    # 待定字符: D A E；顺带展示所有含非白名单字符的
    if re.search(r"[DAE]", phon) or re.search(r'[^\x00-\x7f]', phon) and any(
            c in phon for c in 'DAE'):
        print('%-38r' % wtxt[:46])
