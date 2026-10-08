# -*- coding: utf-8 -*-
"""行级终审: 遍历所有表格的数字序号行(含位移行), 词格提取的词必须存在于词库"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r"c:\Users\wnok\CodeBuddy\初中单词"
doc = json.load(io.open(BASE + r"\words_ast.json", encoding='utf-8'))

def txt(nodes):
    out = []
    for n in nodes:
        if not isinstance(n, dict) or 't' not in n: continue
        t, c = n['t'], n.get('c')
        if t == 'Str': out.append(c if isinstance(c, str) else str(c))
        elif t == 'Space': out.append(' ')
        elif t in ('SoftBreak', 'LineBreak'): out.append('\n')
        elif isinstance(c, list): out.append(txt(c[-1]) if t == 'Link' else txt(c))
    return ''.join(out)

def blocks_text(blocks):
    lines = []
    def flat(bs):
        for b in bs:
            if not isinstance(b, dict): continue
            t = b['t']
            if t in ('Para', 'Plain'): lines.append(txt(b['c']))
            elif t == 'BlockQuote': flat(b['c'])
            elif t == 'Div': flat(b['c'][-1])
    flat(blocks)
    return '\n'.join(x.strip() for x in lines if x.strip())

def cell_text(cell):
    if isinstance(cell, dict): cell = cell['c']
    content = cell[4]
    if content and isinstance(content[0], list): blocks = [b for sub in content for b in sub]
    else: blocks = content
    return blocks_text(blocks)

def table_rows(x):
    c = x['c']
    rows = list(c[3][1])
    for body in c[4]: rows += body[2] + body[3]
    out = []
    for row in rows:
        cells = row[1] if isinstance(row, list) else row['c'][1]
        if isinstance(cells, list): out.append([cell_text(cl) for cl in cells])
    return out

def norm_key(w):
    w = w.replace('\u2011', '-').replace('’', "'")
    return re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', re.sub(r'\s+', ' ', re.sub(r'●|增加|删减', '', w)).strip().lower())

with io.open(BASE + r"\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])
have = set()
have_p = set()
for x in words:
    have.add(norm_key(x['w']))
    have_p.add(norm_key(re.sub(r'[（(][^（）()]*[）)]', ' ', x['w'])))

def word_of(cell):
    """词格第一行的词(三规则音标剥离, 同 audit_final)"""
    ln = cell.split('\n')[0].strip()
    ln = re.sub(r'●|增加|删减', '', ln).strip(' ;')
    if not ln: return ''
    # a. 成对斜杠: "bed /bed/"
    m = re.match(r'^(.+?)\s+/([^ /]{1,24}/)', ln)
    if m: return m.group(1).strip(' ;. ')
    # b. 斜杠后 7 字符内 IPA/旧字体
    m = re.match(r"^(.+?)\s+/(?=[^ ]{0,7}[əɪʊæɒʌɑɜɔθðʃʒŋɡːˈˌ:9IΛ况了巧∫δσ])", ln)
    if m: return m.group(1).strip(' ;. ')
    # c. 斜杠后紧跟撇号/旧字体(跨行音标前半)
    m = re.match(r"^(.+?)\s+/[':9IΛ况了巧∫δσ]", ln)
    if m: return m.group(1).strip(' ;. ')
    # d. 无空格斜杠+撇号: "instrument/'ɪnstrəmənt/"
    m = re.match(r"^(.+?)/(?=[':9IΛ况了巧∫δσ])", ln)
    if m: return m.group(1).strip(' ;. ')
    # e. 行尾残缺音标: "job /d"
    m = re.match(r'^([A-Za-z][A-Za-z\'./-]*)\s+/\S{0,3}$', ln)
    if m: return m.group(1).strip(' ;. ')
    return ln.strip(' ;. ')

SHIFT = {'P30-33', 'W P58 61', '-'}
total = miss = 0
missing_rows = []
def walk(x):
    global total, miss
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            for cells in table_rows(x):
                if len(cells) < 3: continue
                c0 = ' '.join(cells[0].split())
                wc = None
                if re.match(r'^\d+$', c0):
                    wc = cells[1]
                elif c0 in SHIFT and len(cells) > 2 and re.match(r'^\d+$', cells[1].strip()):
                    wc = cells[2]
                if wc is None: continue
                w = word_of(wc)
                if not w or not re.search(r'[A-Za-z]', w): continue
                total += 1
                k = norm_key(w)
                if k not in have and k not in have_p:
                    miss += 1
                    missing_rows.append((c0, w, ' | '.join(c.replace('\n', '⏎')[:36] for c in cells[:4])))
            return
        for v in x.values(): walk(v)
    elif isinstance(x, list):
        for v in x: walk(v)

walk(doc['blocks'])
print('数字序号行总数:', total, '| 词库未收录:', miss)
for idx, w, ctx in missing_rows:
    print('  缺[%s] %s :: %s' % (idx, w, ctx))
