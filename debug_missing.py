# -*- coding: utf-8 -*-
"""查看词汇表中14个缺失词条所在 XML 行的完整文本，确认单词/音标的位置"""
import io, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with zipfile.ZipFile(r"C:\Users\wnok\Desktop\《考纲词汇》早读材料.docx") as z:
    xml = z.read('word/document.xml').decode('utf-8')

rows = re.findall(r'<w:tr\b.*?</w:tr>', xml, re.S)

targets = {
    'brush': '刷净', 'cheap': '便宜的；廉价', 'check': '检查；审查', 'chess': '国际象棋',
    'chicken': '鸡；鸡肉', 'China': 'n. 中国', 'Chinese': '中国人的', 'chip': '炸薯条',
    'choice': '选择；挑选', 'choose': '选择做', 'English': '英格兰的', 'especially': '尤其',
    'kitchen': '厨房', 'question': '表示疑问',
}
for word, key in targets.items():
    for tr in rows:
        if key in tr and word not in tr[:200]:  # 找到含释义关键词的行
            ts = [t.strip() for t in re.findall(r'<w:t[^>]*>([^<]*)</w:t>', tr) if t.strip()]
            print(f'--- {word} 行（{len(ts)} 个文本片段）---')
            print('  ', ts[:14])
            break
