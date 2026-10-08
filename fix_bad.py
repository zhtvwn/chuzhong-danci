# -*- coding: utf-8 -*-
"""修复 words.js 中 14 个坏词条（标记文本污染/音标碎片/原文缺失词）"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORDS_JS = r"c:\Users\wnok\CodeBuddy\初中单词\words.js"

# 旧 w -> (新 w, 新音标, 新 note)；None 表示保留原值
FIX = {
    'AI（= artificial ● 增加':  ('AI（= artificial intelligence）', None, ''),
    ':ns/,':                    ('chance',   '/tʃɑ:ns/',   None),
    'characteristic ● 增加':    ('characteristic', None,    None),
    ':t/ ● 增加':               ('cheat',    '/tʃi:t/',    None),
    ',':                        ('cheer',    '/tʃɪə(r)/',  None),
    ':z/ ● 增加':               ('cheese',   '/tʃi:z/',    None),
    ':（r）/ ● 增加':           ('chore',    '/tʃɔ:(r)/',  None),
    'competition ● 删减':       ('competition', None,      None),
    'confidence ● 增加':        ('confidence', None,       None),
    'disaster ● 增加':          ('disaster', None,         None),
    'donate ● 增加':            ('donate',   None,         None),
    'emergency ● 增加':         ('emergency', None,        None),
    'grandparent ● 删减':       ('grandparent', None,      None),
    'responsible ● 增加':       ('responsible', None,      None),
    '● 增加':                   ('position', '/pəˈzɪʃn/',  None),   # 原文缺失，按字母序与释义推断
}

with io.open(WORDS_JS, encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])

fixed = 0
for x in words:
    if x['w'] in FIX:
        nw, np, nn = FIX[x['w']]
        x['w'] = nw
        if np is not None:
            x['p'] = np
        if nn is not None:
            x['n'] = nn
        fixed += 1
print('修复词条数:', fixed)

# 源文档音标被截断的词条，补标准音标
PHON_FIX = {
    'pollution':   "/pə'lu:ʃn/",
    'reach':       '/ri:tʃ/',
    'chocolate':   "/'tʃɒklət/",
    'population':  "/ˌpɒpju'leɪʃn/",
}
n_phon = 0
for x in words:
    if not x['p'] and x['w'] in PHON_FIX:
        x['p'] = PHON_FIX[x['w']]
        n_phon += 1
print('补音标数:', n_phon)

# 去重检查（仅同一 PART 内算重复；跨 PART 的重复是原文档结构使然）
seen = set()
dup = [x['w'] for x in words if (x['part'], x['w']) in seen or seen.add((x['part'], x['w']))]
print('同PART内重复:', dup)

# 可疑词条复查（PART4 的中文知识点词条合法）
NOTES_OK = {'常见接 v.-ing 作宾语的动词', '常见接 to do 作宾语的动词', '既可接 to do 又可接 v.-ing 的动词'}
bad = [x for x in words if x['w'] not in NOTES_OK
       and ('●' in x['w'] or '增加' in x['w'] or '删减' in x['w'] or not re.match(r"^[A-Za-z]", x['w']))]
print('残留坏词条:', len(bad), [x['w'] for x in bad])

data = json.dumps(words, ensure_ascii=False, separators=(',', ':'))
with io.open(WORDS_JS, 'w', encoding='utf-8') as f:
    f.write('const WORDS=' + data + ';')
print('词条总数:', len(words), '| 2022新增:', sum(1 for x in words if x['t']), '| words.js 已更新')
