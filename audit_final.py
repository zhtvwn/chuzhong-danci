# -*- coding: utf-8 -*-
"""终审 v2: 从 words_ast.json(原文档唯一可信源)按结构化规则独立提取候选词条,
与 words.js 双向对比。噪声容忍策略: 候选若出现在词库任一词条的 释义/用法 字段中则不算遗漏。"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"c:\Users\wnok\CodeBuddy\初中单词"
AST = BASE + r"\words_ast.json"

with io.open(AST, encoding='utf-8') as f:
    doc = json.load(f)

def inlines_text(nodes):
    parts = []
    for n in nodes:
        if not isinstance(n, dict) or 't' not in n: continue
        t, c = n['t'], n.get('c')
        if t == 'Str':
            if isinstance(c, str): parts.append(c)
            elif isinstance(c, list) and c: parts.append(c[0] if isinstance(c[0], str) else str(c[0][0]))
        elif t == 'Space': parts.append(' ')
        elif t in ('SoftBreak', 'LineBreak'): parts.append('\n')
        elif isinstance(c, list): parts.append(inlines_text(c[-1]) if t == 'Link' else inlines_text(c))
    return ''.join(parts)

def blocks_text(blocks):
    lines = []
    def flat(bs):
        for b in bs:
            if not isinstance(b, dict): continue
            t = b['t']
            if t in ('Para', 'Plain'): lines.append(inlines_text(b['c']))
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

def norm(w):
    w = w.replace('’', "'").replace('\u2011', '-')
    w = re.sub(r'●|增加|删减|变化|\u200b', '', w)
    w = re.sub(r'\s+', ' ', w)
    return w.strip().lower()

def norm_key(w):
    """去标点/斜杠/空格的宽松 key, 用于变体匹配"""
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", '', norm(w))

HEADER = re.compile(r'^(第\s*\d+\s*天|PART\s*\d.*|[一二三四五六七八九]+[、.].*|\d+\s*中考.*|'
                    r'课标词汇速查默写.*|中考常考短语.*|完形填空高频短语.*|不规则动词.*|高频单词分类记.*|'
                    r'打卡|时间：.*|完成：.*|【注.*|扫一扫.*|方法指导.*|写出词性及中文意思。|原形.*|'
                    r'数词表.*|月份、星期词汇表.*|部分地理名称.*|部分国家、重要组织.*|部分重要节日名称.*|'
                    r'基数词|序数词|自测.*|单词.*|释义.*|.*短语$)$')

CJKISH = r'[一-鿿（）……]'
WORDINESS = re.compile(r'^(?:n|v|adj|adv|num|prep|pron|interj|conj|art|aux|vi|vt)\.'
                       r'(?:\s*&\s*(?:n|v|adj|adv|num|prep|pron|interj|conj|art|aux|vi|vt)\.?)?\s*$')

def word_from_line(ln):
    """从一行文本提取词候选; 返回 None 表示该行不是词条"""
    ln = ln.strip(' ;')
    if not ln or len(ln) > 70 or HEADER.match(ln):
        return None
    if not re.match(r'^[A-Za-z（(]', ln):
        return None                    # 必须字母/括号开头(滤掉音标碎片如 ":z/")
    if re.match(r'^P\d+(-\s*\d+)?(\s+\d+)?$', ln):
        return None                     # 跨页标记 P30-33 / P58 61
    # 全量剥离斜杠音标组(枚举斜杠如 go fishing/shopping/skating、by air/bus/train/ship 不受影响):
    # a. 前置空白的紧凑组: bed /bed/ -> bed
    ln2 = re.sub(r"\s+/[^ /]+?/", '', ln).strip(' ,;')
    # b. 组内含非 ASCII(音标/OCR噪声)或以重音符开头的组, 允许紧贴与含空格:
    #    instrument/'ɪnstrəmənt/ / aware /ə'weə（r）/, /ə'wer/ / student /'stju:dnt/, /'stu :dnt/
    ln2 = re.sub(r"\s*/(?=[^/]*(?:[^\x00-\x7f]|'))[^/]+?/", '', ln2).strip(' ,;')
    if ln2 != ln and ln2 and re.search(r'[A-Za-z]', ln2):
        ln = ln2
    else:
        # 斜杠后 7 字符内出现 IPA/旧字体字符(跨行音标的前半): "a.m. /eɪ 'em/"、"cabbage /'k"
        m = re.match(r"^(.+?)\s+/(?=[^ ]{0,7}[əɪʊæɒʌɑɜɔθðʃʒŋːˈˌ:9IΛ况了巧∫δσ])", ln)
        if m: ln = m.group(1)
    # 剥掉括号段(变体注释)与标记符号
    s = re.sub(r'[（(][^（）()]*[）)]', ' ', ln)
    s = re.sub(r'●|增加|删减|……', ' ', s).strip(' ;. ')
    if not s or not re.search(r'[A-Za-z]', s):
        return None                     # 整行都是括号注释/纯中文说明
    if s.startswith('/'):
        return None                     # 括号剥离后只剩音标: /'feɪvərɪt/
    # 括号不平衡的碎片行: （pl. policemen/ / po）/,
    if s.count('（') + s.count('(') != s.count('）') + s.count(')'):
        return None
    if re.search(r'[一-鿿]', s):
        # 'word 中文' 对
        m = re.match(r'^([^一-鿿]*?)\s*[，。]?\s*([一-鿿].*)$', s)
        if not m: return None
        w = m.group(1).strip(' ;. ')
    else:
        if re.fullmatch(r'[\d\s/.·,;]+', s): return None
        w = s
        if WORDINESS.fullmatch(w): return None       # 词性格 n. / adv. & n.
        if re.fullmatch(r'[nva.,&\s]*[.,&][nva.,&\s]*', w): return None  # 词性枚举 n., adj
        if len(w.split(',')) >= 3: return None       # 枚举噪声 buy, bring, catch, think, teach
    if '—' in w: return None                         # i—a— u 变化形式噪声
    # 去掉尾部词性标注: "AI n." -> "AI"
    w = re.sub(r'\s+(?:n|v|adj|adv|num|prep|pron|interj|conj|art|aux|vi|vt)\.\s*$', '', w)
    w = w.rstrip('/').strip(' ;. ')
    return w if w and re.search(r'[A-Za-z]', w) else None

cands = {}

def add_cand(w, ctx):
    if not w: return
    k = norm_key(w)
    if k: cands.setdefault(k, (w, ctx))

def walk(x, ctx):
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            for cells in table_rows(x):
                joined0 = cells[0].strip() if cells else ''
                indexed = bool(re.match(r'^\d+$', joined0))
                for ci, c in enumerate(cells):
                    if indexed and ci != 1: continue     # 序号行只取词格(cell[1])
                    if not indexed and ci == 0 and re.match(r'^[nva.]+[ ,]*$', c.strip()):
                        continue                          # 表头词性列
                    for ln in c.split('\n'):
                        w = word_from_line(ln)
                        if w: add_cand(w, '表:' + ' | '.join(cells)[:70])
            return
        if t in ('Para', 'Plain'):
            txt = inlines_text(x['c'])
            for seg in re.split(r'(?<=[一-鿿；。，、])(?=\s*[A-Za-z])', txt):
                for ln in seg.split('\n'):
                    w = word_from_line(ln)
                    if w: add_cand(w, '段:' + txt[:70])
            return
        if t == 'Figure':
            return
        for v in x.values(): walk(v, ctx)
    elif isinstance(x, list):
        for v in x: walk(v, ctx)

walk(doc['blocks'], '')

with io.open(BASE + r"\words.js", encoding='utf-8') as f:
    s = f.read()
words = json.loads(s[s.index('['): s.rindex(']') + 1])
have = {}
for x in words:
    have.setdefault(norm_key(x['w']), []).append(x)

# 容忍文本: 所有词条的 词/释义/用法 拼起来
tolerated = '\n'.join(norm(x['w']) + '\n' + norm(x['m']) + '\n' + norm(x['n']) for x in words)
tolerated += '\n' + norm('既可接 to do 又可接 v.-ing 的动词 enjoy, finish, feel like, keep, mind, practise, prefer, hate, love, begin, continue, start, stop, try, learn, forget, remember, mean, regret, go on, be used to, pay attention to, look forward to, be good at, be interested in, be busy, be worth, can\'t help, give up, pick up, stay up, keep on, insist on, succeed in, think about')

# 词库"括号变体剥离"后的 key 集: call（sb.）back -> callback / be/get used to（doing）sth. -> begetusedtosth
have_variants = set()
for x in words:
    have_variants.add(norm_key(x['w']))
    have_variants.add(norm_key(re.sub(r'[（(][^（）()]*[）)]', ' ', x['w'])))
have_variants.add(norm_key('常见接 to do 作宾语的动词'))
have_variants.add(norm_key('常见接 v.-ing 作宾语的动词'))
have_variants.add(norm_key('既可接 to do 又可接 v.-ing 的动词'))

print('AST 候选:', len(cands), '| 词库:', len(words), '| 词库去重key:', len(have))

missing = []
for k, (w, ctx) in sorted(cands.items()):
    if k in have: continue
    if k in have_variants: continue           # 括号变体剥离后可对上
    wn = norm(w)
    if wn and wn in tolerated: continue       # 出现在词库某词条的释义/用法中
    # 逗号分隔的多词列举(知识点注释), 全部词条中都有则容忍
    toks = [norm_key(t) for t in re.split(r'[,&]', w) if t.strip()]
    if len(toks) > 1 and all(t in have for t in toks): continue
    missing.append((w, ctx))
print('\n===== 原文档有、词库可能漏掉 (%d) =====' % len(missing))
for w, ctx in missing:
    print('  MISS: %-32s %s' % (w, ctx[:90]))

extra = []
for k, xs in sorted(have.items()):
    if k in cands: continue
    w0 = xs[0]['w']
    # 去掉括号变体段再比: centre（AmE center）-> centre
    base = re.sub(r'[（(][^（）()]*[）)]', ' ', w0).strip()
    if norm_key(base) and norm_key(base) in cands: continue
    # 去点号缩写再比: P.E. -> PE
    nodots = re.sub(r'[.]', '', base)
    if norm_key(nodots) != norm_key(base) and norm_key(nodots) in cands: continue
    # 知识点类特殊词条
    if w0.startswith(('常见接', '既可接')): continue
    # 词库词的所有拉丁 token 是否都在候选里(composite 词如 am / is)
    toks = [norm_key(t) for t in re.findall(r"[A-Za-z][A-Za-z'-]*", base)]
    if toks and all(t in cands or t in have for t in toks): continue
    extra.append((w0, 'P%d D%d %s' % (xs[0]['part'], xs[0]['day'], xs[0]['m'][:24])))
print('\n===== 词库有、AST 未直接命中 (%d) =====' % len(extra))
for w, m in extra:
    print('  EXTRA?: %-36s %s' % (w, m))

from collections import Counter
pc = Counter(x['part'] for x in words); dc = Counter(x['day'] for x in words)
print('\n按 PART:', dict(sorted(pc.items())))
expect_days = set(range(1, 43)) | {43}
print('缺失天数:', sorted(expect_days - set(dc)) or '无', '| 无天编号:', sum(1 for x in words if not x['day']))
print('缺释义:', sum(1 for x in words if not x['m']), '| 2022新增:', sum(1 for x in words if x['t']))
# 同 PART 内重复
seensame = Counter((x['part'], norm(x['w'])) for x in words)
dups = [(p, w, c) for (p, w), c in seensame.items() if c > 1]
print('同PART内重复词:', len(dups), dups[:15])
