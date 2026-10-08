# -*- coding: utf-8 -*-
"""检查音标中 ASCII g 的使用情况：是否全部出现在旧字体行"""
import io, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

xml = zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx").read('word/document.xml').decode('utf-8')
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)

n_g, n_ɡ, samples = 0, 0, []
for tr in rows:
    cs = re.split(r'</w:tc>', tr)
    if len(cs) < 3:
        continue
    wtxt = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cs[1]))
    if '/' not in wtxt:
        continue
    phon = wtxt[wtxt.index('/'):]
    if 'ɡ' in phon:
        n_ɡ += 1
    elif re.search(r'g', phon.split('（')[0]):
        n_g += 1
        legacy = bool(re.search(r'[ID93Λ况了巧∫δσ）]', phon))
        if len(samples) < 15:
            samples.append((wtxt[:44], legacy))

print('音标含标准 ɡ(U+0261) 的行数:', n_ɡ)
print('音标含 ASCII g 的行数:', n_g, '（其中旧字体痕迹行已标注）')
for s, legacy in samples:
    print('  %-46r 旧字体痕迹=%s' % (s, legacy))
