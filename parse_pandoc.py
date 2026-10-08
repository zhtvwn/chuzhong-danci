# -*- coding: utf-8 -*-
"""按原文档结构（PART 1-5 / 第1-43天 / 分类）完整解析《考纲词汇》，生成 words.js
- PART 1 (第1-32天): 课标词汇表 + 数词表 + 地理名称 + 节日/机构等专有名词
- PART 2 (第33-36天): 中考常考短语
- PART 3 (第37天): 不规则动词的过去式与过去分词
- PART 4 (第38-41天): 完形填空高频短语（段落式）
- PART 5 (第42-43天): 高频单词分类记
"""
import io, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AST = r"c:\Users\wnok\CodeBuddy\初中单词\words_ast.json"
OUT = r"c:\Users\wnok\CodeBuddy\初中单词\words.js"

# ---------------- AST 工具 ----------------
def inlines_text(nodes):
    parts = []
    for n in nodes:
        if not isinstance(n, dict) or 't' not in n:
            continue
        t, c = n['t'], n.get('c')
        if t == 'Str':
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, list) and c:
                parts.append(c[0] if isinstance(c[0], str) else str(c[0][0]))
        elif t == 'Space':
            parts.append(' ')
        elif t in ('SoftBreak', 'LineBreak'):
            parts.append('\n')
        elif t == 'RawInline':
            pass
        elif isinstance(c, list):
            parts.append(inlines_text(c[-1]) if t == 'Link' else inlines_text(c))
    return ''.join(parts)

def blocks_text(blocks):
    lines = []
    def flat(bs):
        for b in bs:
            if not isinstance(b, dict):
                continue
            t = b['t']
            if t in ('Para', 'Plain'):
                lines.append(inlines_text(b['c']))
            elif t == 'BlockQuote':
                flat(b['c'])
            elif t == 'Div':
                flat(b['c'][-1])
    flat(blocks)
    return '\n'.join(x.strip() for x in lines if x.strip())

def cell_text(cell):
    if isinstance(cell, dict):
        cell = cell['c']
    content = cell[4]
    if content and isinstance(content[0], list):
        blocks = [b for sub in content for b in sub]
    else:
        blocks = content
    return blocks_text(blocks)

def table_rows(x):
    """返回表格全部行，每行是单元格文本列表"""
    c = x['c']
    rows = list(c[3][1])
    for body in c[4]:
        rows += body[2] + body[3]
    out = []
    for row in rows:
        cells = row[1] if isinstance(row, list) else row['c'][1]
        if not isinstance(cells, list):
            continue
        out.append([cell_text(cl) for cl in cells])
    return out

# ---------------- 清洗规则 ----------------
CJK = '\u4e00-\u9fff（）、；：'

def clean_text(s):
    if not s:
        return ''
    s = s.replace('（', '(').replace('）', ')')
    s = re.sub(r'(…\s*)+', '……', s)
    s = s.replace('●', '')
    s = re.sub(r'增加|删减', '', s)
    s = re.sub(r'(?<=[%s])\s+(?=[%s])' % (CJK, CJK), '', s)
    s = re.sub(r'\s+……', '……', s)
    s = re.sub(r'……\s+', '……', s)
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip()

PHON_OK = re.compile(r"^[a-zɡəɪʊæɒʌɑɜɔθðʃʒŋʤʧɹʰ'ˌˈː()/.,:; +-]+$")

def valid_phonetic(p):
    if not p:
        return False
    if re.search(r'[A-Z\u4e00-\u9fff]', p):
        return False
    return bool(PHON_OK.match(p))

# 旧音标字体 -> 标准 IPA（详见审计）
FONT_MAP = [('I', 'ɪ'), ('D', 'ɒ'), ('9', 'ɒ'), ('3', 'ɜ'), ('Λ', 'ʌ'), ('况', 'æ'),
            ('了', 'ʒ'), ('巧', 'ŋ'), ('∫', 'ʃ'), ('δ', 'ð'), ('σ', 'ʊ')]
LEGACY_MARK = re.compile(r'[ID93Λ况了巧∫δσ]')

def normalize_font(p):
    if not p:
        return p
    p = re.sub(r'\s*([（）:])\s*', r'\1', p)
    p = re.sub(r'/\s*（[^）]*）?\s*[^/]*$', '/', p)
    p = re.sub(r'（\s*([A-Za-z])\s*）', '\x01\\1\x02', p)
    p = p.replace('）', 'ə')
    if LEGACY_MARK.search(p):
        for k, v in FONT_MAP:
            p = p.replace(k, v)
        p = p.replace('g', 'ə').replace('a:', 'ɑ:').replace(')', 'ə')
        p = re.sub(r',(?=\S)', 'ˌ', p)
    p = p.replace('（', '(').replace('\x01', '(').replace('\x02', ')')
    PH = 'A-Za-zəɪʊæɒʌɑɜɔθðʃʒŋːˈˌː'
    p = re.sub(r'(?<=[/%s])，(?=[%s])' % (PH, PH), 'ˌ', p)
    p = p.replace('，', ', ').replace('；', '; ')
    return p

# PART 1 中 14 个单词格丢失的词条（图片渲染）: idx -> (单词, 音标, 2022新增)
RECOVER = {
    '197':  ('brush',      '/brʌʃ/',        False),
    '255':  ('cheap',      '/tʃi:p/',       False),
    '257':  ('check',      '/tʃek/',        False),
    '261':  ('chess',      '/tʃes/',        False),
    '262':  ('chicken',    '/ˈtʃɪkɪn/',     False),
    '264':  ('China',      '/ˈtʃaɪnə/',     False),
    '265':  ('Chinese',    '/tʃaɪˈni:z/',   False),
    '266':  ('chip',       '/tʃɪp/',        True),
    '268':  ('choice',     '/tʃɔɪs/',       False),
    '269':  ('choose',     '/tʃu:z/',       False),
    '467':  ('English',    '/ˈɪŋɡlɪʃ/',     False),
    '474':  ('especially', '/ɪˈspeʃəli/',   False),
    '772':  ('kitchen',    '/ˈkɪtʃɪn/',     False),
    '1153': ('question',   '/ˈkwestʃən/',   False),
}
SHIFT = {'P30-33', 'W P58 61'}

SPACE_FIX = {'getup': 'get up', 'lookup': 'look up', 'pickup': 'pick up',
             'setup': 'set up', 'speedup': 'speed up', 'goodtime': 'good time'}

# 数词表: 序数词 -> 中文
ORD_CN = {
    'first': '第一', 'second': '第二', 'third': '第三', 'fourth': '第四', 'fifth': '第五',
    'sixth': '第六', 'seventh': '第七', 'eighth': '第八', 'ninth': '第九', 'tenth': '第十',
    'eleventh': '第十一', 'twelfth': '第十二', 'thirteenth': '第十三', 'fourteenth': '第十四',
    'fifteenth': '第十五', 'sixteenth': '第十六', 'seventeenth': '第十七', 'eighteenth': '第十八',
    'nineteenth': '第十九', 'twentieth': '第二十', 'twenty-first': '第二十一',
    'twenty-second': '第二十二', 'twenty-third': '第二十三', 'thirtieth': '第三十',
    'fortieth': '第四十', 'fiftieth': '第五十', 'sixtieth': '第六十', 'seventieth': '第七十',
    'eightieth': '第八十', 'ninetieth': '第九十', 'hundredth': '第一百',
    'thousandth': '第一千', 'millionth': '第一百万',
}

# 数词表: 基数词 -> 中文
NUM_CN = {
    'one': '一', 'two': '二', 'three': '三', 'four': '四', 'five': '五',
    'six': '六', 'seven': '七', 'eight': '八', 'nine': '九', 'ten': '十',
    'eleven': '十一', 'twelve': '十二', 'thirteen': '十三', 'fourteen': '十四',
    'fifteen': '十五', 'sixteen': '十六', 'seventeen': '十七', 'eighteen': '十八',
    'nineteen': '十九', 'twenty': '二十', 'thirty': '三十', 'forty': '四十',
    'fifty': '五十', 'sixty': '六十', 'seventy': '七十', 'eighty': '八十',
    'ninety': '九十', 'hundred': '百', 'thousand': '千', 'million': '百万',
}

# 月份、星期词汇表（原文档无中文，补注）
MONTH_CN = {
    'January': 'n. 一月', 'February': 'n. 二月', 'March': 'n. 三月',
    'April': 'n. 四月', 'May': 'n. 五月', 'June': 'n. 六月',
    'July': 'n. 七月', 'August': 'n. 八月', 'September': 'n. 九月',
    'October': 'n. 十月', 'November': 'n. 十一月', 'December': 'n. 十二月',
    'Monday': 'n. 星期一', 'Tuesday': 'n. 星期二', 'Wednesday': 'n. 星期三',
    'Thursday': 'n. 星期四', 'Friday': 'n. 星期五', 'Saturday': 'n. 星期六',
    'Sunday': 'n. 星期日',
}

# 地理名称表（原文无中文释义，补注）
GEO_CN = {
    'Africa': '非洲', 'African': '非洲人；非洲的', 'America': '美国；美洲',
    'American': '美国人；美国的', 'Antarctica': '南极洲', 'Asia': '亚洲',
    'Asian': '亚洲人；亚洲的', 'Australia': '澳大利亚', 'Australian': '澳大利亚人；澳大利亚的',
    'Britain': '英国；不列颠', 'British': '英国的；英国人', 'Canada': '加拿大',
    'Canadian': '加拿大人；加拿大的', 'England': '英格兰', 'English': '英国的；英语；英国人',
    'Europe': '欧洲', 'European': '欧洲人；欧洲的', 'France': '法国',
    'French': '法国的；法语；法国人', 'Germany': '德国', 'German': '德国的；德语；德国人',
    'India': '印度', 'Indian': '印度人；印度的', 'Italy': '意大利',
    'Italian': '意大利人；意大利语；意大利的', 'Japan': '日本',
    'Japanese': '日本人；日语；日本的', 'Oceania': '大洋洲', 'Russia': '俄罗斯',
    'Russian': '俄罗斯人；俄语；俄罗斯的', 'China': '中国', 'Chinese': '中国人；汉语；中国的',
    'The Pacific Ocean': '太平洋', 'The Atlantic Ocean': '大西洋',
    'The Indian Ocean': '印度洋', 'The United Kingdom（UK）': '英国',
    'The United States of America': '美国（全称，缩写 USA）', 'UK': '英国', 'USA': '美国',
    'London': '伦敦', 'New York': '纽约', 'Paris': '巴黎',
    'New Zealand': '新西兰', 'New Zealander': '新西兰人；新西兰的',
    'Singapore': '新加坡', 'Singaporean': '新加坡人；新加坡的',
    'South Africa': '南非', 'South African': '南非人；南非的',
}

# 噪声段落（页眉页脚）
NOISE = re.compile(
    r'^(打卡|时间：|完成：|【注|课标词汇速查默写\s*\d*|义务教育英语课程标准词汇表\d*|'
    r'中考常考短语\s*\d*|\d+\s*中考常考短语|完形填空高频短语\s*\d*|\d+\s*完形填空高频短语|'
    r'不规则动词的过去式与过去分词\s*\d*|\d+\s*不规则动词的过去式与过去分词|'
    r'高频单词分类记\s*\d*|\d+\s*高频单词分类记|扫一扫.*|方法指导.*|写出词性及中文意思。)$')

# ---------------- 解析 ----------------
with io.open(AST, encoding='utf-8') as f:
    doc = json.load(f)

words = []
seen = set()          # (part, w) 去重

def add(w, p, m, n, t, part, day, cat=''):
    w = w.replace('’', "'").strip()
    w = re.sub(r"\s*'\s*(?=[A-Za-z])", "'", w)        # Children 's -> Children's
    w = re.sub(r"([a-z])'([A-Z][a-z])", r"\1' \2", w)  # Teachers'Day -> Teachers' Day
    if not w:
        return
    key = (part, w)
    if key in seen:
        return
    seen.add(key)
    words.append({'w': w, 'p': p or '', 'm': m or '', 'n': n or '',
                  't': bool(t), 'part': part, 'day': day or 0, 'cat': cat or ''})

state = {'part': 1, 'day': 0, 'cat': '', 'catnew': False}
PART_FIRST_DAY = {3: 37, 4: 38, 5: 42}
geo_adopt = set()      # 主表已有、但归类应属地理表的词

def split_pair(txt):
    """'word 中文' -> (word, 中文)；word 须含拉丁字母且不含中文"""
    m = re.match(r'^([^一-鿿]*?)\s*([一-鿿].*)$', txt.strip())
    if not m:
        return None
    w, meaning = m.group(1).strip(' ;'), m.group(2).strip()
    mm = re.match(r'^(.*?)[（(]\s*$', w)      # 尾部悬空括号归释义: break out（ -> break out
    if mm and mm.group(1).strip():
        w = mm.group(1).strip()
        meaning = '（' + meaning
    w = re.sub(r'●|增加|删减', '', w).strip()   # 去掉残留标记
    w = re.sub(r'^[（(][^（）()]*[）)](?=\s*[A-Za-z])', '', w)   # （dis）agree with -> agree with
    mm = re.match(r'^[（(](.+)[）)]$', w)        # 整体被括号包裹: （The Yangtze River） -> The Yangtze River
    if mm:
        w = mm.group(1).strip()
    if re.search(r'[A-Za-z]', w) and w:
        return w, meaning
    return None

def split_pairs(txt):
    """一行多个 'word 中文' 对：在 中文->拉丁 边界切分（括号不算边界）"""
    out = []
    for seg in re.split(r'(?<=[一-鿿；。，、])(?=\s*[A-Za-z])', txt):
        seg = seg.strip()
        if seg:
            pr = split_pair(seg)
            if pr:
                out.append(pr)
    return out

# 分类名归一化：源标题全角/半角括号混用，统一为全角
def norm_cat(c):
    return c.replace('(', '（').replace(')', '）')

def handle_para(txt):
    txt = txt.strip()
    if not txt or NOISE.match(txt):
        return
    m = re.match(r'^PART\s*(\d)', txt)
    if m:
        newp = int(m.group(1))
        # 文档怪癖：'一、动词（中考高频、易错）'标题位于 PART 5 标题之前，
        # 已被设为 cat，进入 PART 5 时须保留，否则 164 个动词失去分类
        keep = state['cat'] if (newp == 5 and state['cat'].startswith('一、动词')) else ''
        state['part'] = newp
        state['day'] = PART_FIRST_DAY.get(state['part'], 0)
        state['cat'] = keep
        state['catnew'] = False
        state['frag'] = None
        return
    m = re.match(r'^第\s*(\d+)\s*天', txt)
    if m:
        state['day'] = int(m.group(1))
        state['frag'] = None
        return
    part, cat = state['part'], state['cat']
    # 分类标签
    if part == 3 and re.match(r'^[一二三四五六][、.]|^\d+\.', txt):
        state['cat'] = norm_cat(clean_text(txt))
        return
    if part == 4:
        if re.match(r'^\S{1,10}\s*短语$', txt) or re.match(r'^[（(][一二三四五六]', txt) \
                or re.match(r'^[一二三四]、', txt) or txt in ('动词短语', '短语荟萃', 'v.-ing 的使用'):
            state['cat'] = norm_cat(clean_text(txt))
            state['frag'] = None
            state.pop('note', None)
            return
        if re.match(r'^(常见的接|既可接)', txt):   # 动词列表知识点标题
            state['frag'] = None
            state['note'] = txt
            state['notebuf'] = []
            return
        if state.get('note'):                      # 动词列表正文，累积至"等"结尾
            state['notebuf'].append(txt)
            if txt.endswith('等'):
                title = state.pop('note')
                buf = state.pop('notebuf')
                lst = clean_text(' '.join(buf)).replace('’', "'")
                lst = re.sub(r"\s*'\s*(?=[A-Za-z])", "'", lst)   # can 't -> can't
                lst = re.sub(r'\s+,', ',', lst)
                lst = re.sub(r'\s{2,}', ' ', lst).strip().rstrip('，').rstrip()
                if not lst.endswith('等'):
                    lst += ' 等'
                if '又可接' in title:
                    w_ = '既可接 to do 又可接 v.-ing 的动词'
                elif 'v.-ing' in title:
                    w_ = '常见接 v.-ing 作宾语的动词'
                else:
                    w_ = '常见接 to do 作宾语的动词'
                add(w_, '', lst, '', False, 4, state['day'], state['cat'])
            return
    if re.match(r'^[一二三四五]\s*、', txt) and re.search(r'动词|名词|形容词|副词', txt):
        state['cat'] = norm_cat(clean_text(txt))
        return
    if part == 1 and (txt.startswith('数词表') or txt.startswith('月份、星期词汇表')
                       or txt.startswith('部分地理名称及相关信息')
                       or txt.startswith('部分国家、重要组织机构名称缩写')
                       or txt.startswith('部分重要节日名称、中国文化专有名词')):
        state['cat'] = norm_cat(txt.replace('●', '').replace('增加', '').strip())
        state['catnew'] = '增加' in txt      # 标题带●增加 => 整表 2022 新增
        return
    # PART 4: 短语段落（可能一行多对）
    if part == 4:
        # 先切段；释义中的单个大写字母(A/B)切段并回前一段，避免被当成独立短语
        segs = re.split(r'(?<=[一-鿿；。，、])(?=\s*[A-Za-z])', txt)
        buf = []
        for seg in segs:
            s_ = seg.strip()
            if not s_:
                continue
            if buf and re.match(r'^[A-Z](\s|$)', s_):
                buf[-1] += ' ' + s_
            else:
                buf.append(s_)
        pairs = []
        for seg in buf:
            pr = split_pair(seg)
            if pr:
                pairs.append(pr)
        merged = list(pairs)
        # 过滤语法说明产生的伪短语（"be used to 等"、"to do 作宾语的动词有："等）
        merged = [(w_, m_) for w_, m_ in merged
                  if m_ not in ('等', '又可接') and not m_.endswith('有：')]
        if merged:
            state['frag'] = None
            for w_, m_ in merged:
                before = len(words)
                add(w_, '', clean_text(m_), '', '增加' in txt, 4, state['day'], state['cat'])
                state['frag'] = words[-1] if len(words) > before else None
        else:
            ref = state.get('frag')
            state['frag'] = None
            # 分页截断的释义碎片（纯中文短片段）拼回上一词条
            if ref and len(txt) <= 8 and not re.search(r'[A-Za-z]', txt):
                ref['m'] = clean_text(ref['m'] + txt)
        return
    # PART 5: 段落式词条（形容词表等部分词条为独立段落，如 'afraid 恐惧的'）
    if part == 5:
        for w_, m_ in split_pairs(txt):
            add(w_, '', clean_text(m_), '', '增' in txt, 5, state['day'], state['cat'])
        return
    # PART 1: 机构缩写等段落（标题带●增加 => 整组 2022 新增）
    if part == 1 and cat in ('部分国家、重要组织机构名称缩写', '部分重要节日名称、中国文化专有名词'):
        for w_, m_ in split_pairs(txt):
            add(w_, '', clean_text(m_), '', state.get('catnew', False), 1, state['day'], cat)

def parse_digit_row(cells, part, day):
    """PART 1/2 的序号行 -> 词条"""
    idx = cells[0].strip()
    if ' '.join(idx.split()) in SHIFT:
        cells = cells[1:]
        idx = cells[0].strip()
    if not re.match(r'^\d+$', idx):
        return
    word_cell = cells[1].replace('goodtime', 'good time')
    recovered = None
    if not word_cell.strip() and idx in RECOVER:
        recovered = RECOVER[idx]
        word_cell = recovered[0]
    elif not word_cell.strip():
        return
    rest = [c.strip() for c in cells[2:] if c.strip()]
    raw_rest = ' '.join(c.strip() for c in cells[2:])
    meaning = clean_text(rest[0].replace('\n', ' ')) if len(rest) >= 1 else ''
    note = clean_text(' '.join(rest[1:]).replace('\n', ' ')) if len(rest) >= 2 else ''
    wl = [x.strip() for x in word_cell.split('\n') if x.strip()]
    if not wl:
        return
    word, phonetic = '', ''
    m = re.match(r'^([A-Za-z]+)\s*/\s*([A-Za-z]+)\s+(/.+)$', wl[0])
    if m:
        word = m.group(1) + ' / ' + m.group(2)
        phonetic = m.group(3).strip()
    else:
        m = re.match(r'^(.+?)\s+(/.*)$', wl[0])
        if not m:
            m = re.match(r'^(.+?)\s*(/.*/.*)$', wl[0])
            if m and not re.search(r"[əɪʊæɒʌɑɜɔθðʃʒŋːˈˌ:（）]", m.group(2)):
                m = None
        if m:
            word, phonetic = m.group(1).strip(), m.group(2).strip()
        else:
            word = wl[0]
    tag = bool(re.search(r'增\s*加', word_cell + ' ' + raw_rest))
    extra = ''
    for ln in wl[1:]:
        if re.match(r'^[A-Za-z][A-Za-z/-]*$', ln) and not phonetic:
            word += ' ' + ln
        elif ln.startswith('/'):
            phonetic = (phonetic + ' ' + ln).strip()
        else:
            mp = re.match(r'^(.*?)\s*(/.*/.*)$', ln)
            if mp and not phonetic and re.search(r"[əɪʊæɒʌɑɜɔθðʃʒŋːˈˌ:（）]", mp.group(2)):
                phonetic = mp.group(2).strip()
                if mp.group(1).strip():
                    extra = (extra + ' ' + mp.group(1).strip()).strip()
            else:
                extra = (extra + ' ' + ln).strip()
    phonetic = normalize_font(phonetic)
    phonetic = clean_text(phonetic)
    phonetic = re.sub(r'\s*,\s*', ', ', phonetic).strip(' ,')
    phonetic = re.sub(r'\s+ː', 'ː', phonetic).strip()
    if not valid_phonetic(phonetic):
        phonetic = ''
    elif not (phonetic.startswith('/') and phonetic.endswith('/') and phonetic.count('/') >= 2):
        phonetic = ''
    note = clean_text((note + ' ' + extra).strip())
    word = word.strip()
    if recovered:
        phonetic = recovered[1]
        tag = tag or recovered[2]
    word = SPACE_FIX.get(word, word)
    add(word, phonetic, meaning, note, tag, part, day, '')

def handle_table(x):
    rows = table_rows(x)
    # 天标记表（单行含 第N天）
    flat = ' '.join(c for r in rows for c in r)
    m = re.search(r'第\s*(\d+)\s*天', flat)
    if m and len(rows) <= 2:
        state['day'] = int(m.group(1))
        return
    part, cat = state['part'], state['cat']
    # PART 3: 情态动词表之后的大表是 ABB 式的续表
    if part == 3 and len(rows) > 10 and '情态动词' in cat:
        state['cat'] = '二、过去式与过去分词形式相同（ABB 式）'
        cat = state['cat']
    for cells in rows:
        idx = cells[0].strip()
        if re.match(r'^\d+$', idx) and len(cells) >= 3 and part in (1, 2):
            parse_digit_row(cells, part, state['day'])
            continue
        if part == 3 and len(cells) >= 3:
            # 不规则动词表 [原形, 过去式, 过去分词]（含若干变体布局）
            c0 = cells[0].strip()
            if c0 == '原形' or not re.search(r'[A-Za-z]', c0):
                continue
            tag = '增' in ''.join(cells)
            base = re.sub(r'●|增加|删减', '', c0).strip()
            note = ''
            mm = re.match(r'^([A-Za-z][A-Za-z（() ]*?)\s*（([^）]*)）\s*$', base)
            if mm:
                base = mm.group(1).strip()
                note = mm.group(2)
            latin = [re.match(r'^[A-Za-z]+$', c.strip()) for c in cells]
            if len(cells) == 4 and latin[1] and latin[2]:
                # 情态动词双列: [原形, 过去式, 原形, 过去式]
                for a, b in ((cells[0], cells[1]), (cells[2], cells[3])):
                    add(a.strip(), '', '过去式 %s（情态动词，无过去分词）' % b.strip(),
                        note, tag, 3, state['day'], state['cat'])
            elif len(cells) >= 5 and cells[1].strip() == '/' and latin[0]:
                # am / is / was / been（原形含斜杠）
                w = cells[0].strip() + ' / ' + cells[2].strip()
                add(w, '', '过去式 %s；过去分词 %s' % (cells[3].strip(), cells[4].strip()),
                    note, tag, 3, state['day'], state['cat'])
            elif len(cells) == 5 and latin[1] and latin[2] and latin[3] and latin[4]:
                # 双变体: burn burnt burned burnt burned
                add(base, '', '过去式 %s/%s；过去分词 %s/%s' % (
                    cells[1].strip(), cells[2].strip(), cells[3].strip(), cells[4].strip()),
                    note, tag, 3, state['day'], state['cat'])
            else:
                past = cells[1].strip().replace('\n', '/')
                pp = '/'.join(c.strip().replace('\n', '/') for c in cells[2:]
                              if c.strip() and c.strip() != '/')
                meaning = '过去式 %s' % past + ('；过去分词 %s' % pp if pp else '')
                add(base, '', clean_text(meaning).replace('\n', ' '), note, tag, 3, state['day'], state['cat'])
            continue
        if part == 1 and cat == '数词表' and len(cells) >= 3:
            # [基数词, 自测, 序数词, 自测]
            base = re.sub(r'●|增加|删减', '', cells[0]).strip()
            ordinal = re.sub(r'●|增加|删减', '', cells[2]).strip()
            has_ord = re.match(r'^[A-Za-z-]+$', ordinal) is not None
            # 基数词（主词表不含数词）；●增加标记在哪个格就归哪个词
            if base and re.match(r'^[A-Za-z]+$', base):
                cn = NUM_CN.get(base, '')
                m_ = 'num. ' + cn if cn else ''
                if has_ord:
                    m_ = (m_ + '；序数词 ' + ordinal) if m_ else ('序数词 ' + ordinal)
                add(base, '', m_, '', '增' in cells[0], 1, state['day'], '数词表')
            # 序数词
            if has_ord:
                ocn = ORD_CN.get(ordinal, '')
                m_ = (ocn + '（%s 的序数词）' % base) if ocn else ('%s 的序数词' % base)
                add(ordinal, '', m_, '', '增' in cells[2], 1, state['day'], '数词表')
            continue
        if part == 1 and cat == '月份、星期词汇表':
            for c in cells:
                for ln in c.split('\n'):
                    w_ = re.sub(r'●|增加|删减', '', ln).strip()
                    if w_ in MONTH_CN:
                        add(w_, '', MONTH_CN[w_], '', '增' in ln, 1, state['day'], '月份、星期')
            continue
        if part == 1 and cat == '部分地理名称及相关信息':
            # 布局 [词, 词性, 自测] x2；意大利行等存在错位，逐格扫描
            for c in cells:
                for ln in c.split('\n'):
                    w_ = re.sub(r'●|增加|删减|变化', '', ln).strip()
                    if re.match(r'^[nadj., ]+$', w_):       # 词性格 n. / n., adj.
                        continue
                    if w_ in MONTH_CN:
                        continue                             # 无关表防御
                    mm = re.match(r'^[（(]([A-Za-z][A-Za-z. ]*)[）)]$', w_)  # （USA）缩写并入全称条
                    if mm:
                        continue
                    if not w_ or w_ == '/' or not re.search(r'[A-Za-z]', w_):
                        continue
                    cn = GEO_CN.get(w_, '')
                    if (1, w_) in seen:                     # 主词汇表已有(China/Chinese/English)
                        geo_adopt.add(w_)                    # 归类转移为地理名称
                        continue
                    if cn or len(w_) > 2:
                        add(w_, '', clean_text(cn or '(地理名称)'), '', '增' in ln, 1, state['day'], '地理名称')
            continue
        if part == 1 and cat == '部分重要节日名称、中国文化专有名词':
            for c in cells:
                # cell 内的换行是排版折行（Mount Qomolangma⏎珠穆朗玛峰），合并后再切分
                txt = re.sub(r'\s*\n\s*', ' ', c).strip()
                txt = re.sub(r'\s+（', '（', txt)
                pr = split_pair(txt)
                if pr:
                    add(pr[0], '', clean_text(pr[1]), '', state.get('catnew', False), 1, state['day'], '节日、专有名词')
            continue
        if part == 5:
            # 一格一词: 'word 中文'，跳过分类标记行
            joined = ''.join(cells).strip()
            if re.match(r'^[一二三四五]\s*、', joined):
                state['cat'] = norm_cat(clean_text(joined))
                continue
            for c in cells:
                for ln in c.split('\n'):
                    ln = ln.strip(' ;')
                    if not ln:
                        continue
                    for w_, m_ in split_pairs(ln):
                        add(w_, '', clean_text(m_), '', '增' in ln, 5, state['day'], state['cat'])
            continue
        # PART 4 表格内也含短语（补充段落遗漏）
        if part == 4:
            for c in cells:
                for ln in c.split('\n'):
                    for w_, m_ in split_pairs(ln):
                        add(w_, '', clean_text(m_), '', '增' in ln, 4, state['day'], state['cat'])

def walk(x):
    if isinstance(x, dict):
        t = x.get('t')
        if t == 'Table':
            handle_table(x)
            return
        if t in ('Para', 'Plain'):
            handle_para(inlines_text(x['c']))
            return
        if t == 'Header':
            handle_para(inlines_text(x['c'][2]))
            return
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)

walk(doc['blocks'])

# 主词汇表已有、但地理表再次列出的词（China/Chinese/English），归类转移为地理名称
for x in words:
    if x['part'] == 1 and x['w'] in geo_adopt:
        x['cat'] = '地理名称'

# ---------------- 统计输出 ----------------
print('词条总数:', len(words))
from collections import Counter
pc = Counter(x['part'] for x in words)
dc = Counter(x['day'] for x in words)
print('按 PART:', dict(sorted(pc.items())))
missing_day = [x['w'] for x in words if not x['day']]
print('无天编号的词条:', len(missing_day), missing_day[:10])
print('音标:', sum(1 for x in words if x['p']), ' 2022新增:', sum(1 for x in words if x['t']),
      ' 重复:', len(words) - len(seen))

data = json.dumps(words, ensure_ascii=False, separators=(',', ':'))
with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('const WORDS=' + data + ';')
print('已写出 words.js:', len(data), '字符')
