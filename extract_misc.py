# -*- coding: utf-8 -*-
"""导出若干普通词条行中的图片，确认其内容"""
import io, os, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOCX = r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx"
OUT = r"c:\Users\wnok\CodeBuddy\初中单词\imgs"
z = zipfile.ZipFile(DOCX)
xml = z.read('word/document.xml').decode('utf-8')
rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
rid2file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="media/([^"]+)"', rels))
rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)

want = {'9': 'accident', '11': 'account', '46': 'alarm', '12': 'ache', '21': 'actually'}
done = set()
for tr in rows:
    m = re.search(r'<w:t[^>]*>(\d+)</w:t>', tr)
    if not m or m.group(1) not in want or m.group(1) in done:
        continue
    idx = m.group(1)
    done.add(idx)
    rids = [r for pair in re.findall(r'r:embed="(rId\d+)"|r:id="(rId\d+)"', tr) for r in pair if r]
    files = [rid2file.get(r, '?') for r in rids]
    print(idx, want[idx], files)
    for f in set(files):
        data = z.read('word/media/' + f)
        out = os.path.join(OUT, '%s_%s' % (want[idx], f))
        io.open(out, 'wb').write(data)
        print('  导出:', out, len(data), 'B')
