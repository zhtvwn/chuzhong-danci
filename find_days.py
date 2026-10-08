# -*- coding: utf-8 -*-
"""在原文 XML 中搜索所有 第N天 标签及其上下文，确认 37-43 天的位置"""
import io, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

xml = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx").read('word/document.xml').decode('utf-8')

for n in range(33, 44):
    pats = ['第%s天' % n, '第 %s 天' % n, '第 %s天' % n, '第%s 天' % n]
    found = None
    for p in pats:
        i = xml.find(p)
        if i >= 0:
            found = (p, i)
            break
    if found:
        p, i = found
        ctx = xml[max(0, i - 300):i]
        ts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', ctx)
        print('第%d天: 找到 %r  前文: %s' % (n, p, ''.join(ts)[-40:]))
    else:
        print('第%d天: 未找到' % n)

# PART 3/4/5 之间的表格行样本
print()
print('--- PART 3 不规则动词表样本 ---')
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)
shown = 0
for tr in rows:
    ts = [t.strip() for t in re.findall(r'<w:t[^>]*>([^<]*)</w:t>', tr) if t.strip()]
    if re.search(r'过去式|不规则', ''.join(ts)) or (len(ts) >= 3 and ts[0] and re.match(r'^[a-z]+$', ts[0])
            and any(re.match(r'^[a-z]+$', t) for t in ts[1:]) and shown < 60):
        if re.match(r'^[a-z]+$', ts[0]):
            print('  ', ts[:8])
            shown += 1
