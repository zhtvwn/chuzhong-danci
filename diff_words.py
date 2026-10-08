# -*- coding: utf-8 -*-
"""比对 HEAD 与工作区 words.js 的词条差异"""
import json, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

def load(text):
    m = re.search(r'const\s+WORDS\s*=\s*(\[.*\])', text, re.S)
    return json.loads(m.group(1))

git = r'C:\Program Files\Git\cmd\git.exe'
head = subprocess.run([git, 'show', 'HEAD:words.js'], capture_output=True).stdout.decode('utf-8')
cur = open('words.js', encoding='utf-8').read()

a, b = load(head), load(cur)
print(f'HEAD: {len(a)} 条 | 工作区: {len(b)} 条')

ka = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in a}
kb = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in b}
for x in sorted(ka - kb): print('  删除/变更前:', x[:200])
for x in sorted(kb - ka): print('  新增/变更后:', x[:200])
