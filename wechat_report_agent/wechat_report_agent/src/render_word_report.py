# -*- coding: utf-8 -*-
"""
示例：用 docxtpl 渲染 Word 模板（支持 {{title}}、{{issue}}、{{org}}、{{date}}、{{core_titles}}、{{content}} 占位符）
"""
from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import datetime

def render_report(template_path, output_path, context):
    tpl = DocxTemplate(template_path)
    tpl.render(context)
    tpl.save(output_path)

def set_cn_font(run, name="FZFSK", size=16, bold=False, color=None):
    """统一设置中文字体为FZFSK，数字和英文为Times New Roman"""
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color

def set_title_font(run, name="FZFSK", size=28, bold=True, color=None):
    """设置大标题字体为FZFSK，28磅字"""
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color

def set_subtitle_font(run, name="方正黑体_GBK", size=16, bold=True, color=None):
    """设置小标题字体为方正黑体_GBK，三号字"""
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color

def add_red_line_cell(cell, size=6):
    """给单元格下方加红色横线"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)

    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')      # 单线
    bottom.set(qn('w:sz'), str(size))      # 粗细，单位 1/8 磅
    bottom.set(qn('w:space'), '0')
    bottom.set(qn('w:color'), 'FF0000')    # 红色
    tcBorders.append(bottom)

def generate_ai_report(ai_content, output_path):
    doc = Document()

    # ====== 封面部分 ======
    # 大标题
    p1 = doc.add_paragraph()
    run1 = p1.add_run("人工智能技术跟踪周报告")
    set_title_font(run1)
    p1.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # 期号
    p2 = doc.add_paragraph()
    run2 = p2.add_run("第12期")
    set_cn_font(run2, size=14, bold=True)
    p2.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    doc.add_paragraph("")

    # 左右分布：组织在左，日期在右
    table = doc.add_table(rows=1, cols=2)
    table.autofit = True
    row = table.rows[0]
    cell1, cell2 = row.cells

    p_left = cell1.paragraphs[0]
    run_left = p_left.add_run("新闻智能体")
    set_cn_font(run_left, size=12, bold=True)
    p_left.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    p_right = cell2.paragraphs[0]
    run_right = p_right.add_run("2025年10月2日")
    set_cn_font(run_right, size=12, bold=True)
    p_right.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    # 给整行两个单元格都加红线
    for cell in row.cells:
        add_red_line_cell(cell, size=6)

    doc.add_paragraph("")

    # ====== 本期核心要闻 ======
    p4 = doc.add_paragraph()
    run4 = p4.add_run("本期核心要闻")
    set_cn_font(run4, size=14, bold=True)
    p4.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    for item in ai_content.get("core_news", []):
        para = doc.add_paragraph()
        run = para.add_run(f"● {item}")
        set_cn_font(run, size=12, bold=False)

    # ====== 正文分章节 ======
    sections = ["技术前沿", "产业动态", "政策法规", "应用实例"]
    for sec in sections:
        sec_items = ai_content.get(sec, [])
        if not sec_items:
            continue

        # 一级标题
        h = doc.add_paragraph()
        run_h = h.add_run(sec)
        set_cn_font(run_h, size=14, bold=True)

        for idx, it in enumerate(sec_items, 1):
            if isinstance(it, str):
                it = {'title': it, 'summary': ''}  # Convert string to dictionary with default values

            # 小标题
            p_title = doc.add_paragraph()
            run_t = p_title.add_run(f"{idx}. {it['title']}")
            set_subtitle_font(run_t)

            # 摘要正文
            p_sum = doc.add_paragraph()
            run_s = p_sum.add_run(it.get('summary', ''))  # Use default value if 'summary' is missing
            set_cn_font(run_s, size=11, bold=False)

    doc.save(output_path)
    print(f"[Report] 已生成报告: {output_path}")

if __name__ == '__main__':
    context = {
        'title': 'AI 新闻周报',
        'issue': '第12期',
        'org': '新闻智能体',
        'date': datetime.date.today().strftime('%Y-%m-%d'),
        'core_titles': '1. 要闻A\n2. 要闻B',
        'content': '这里是正文内容...'
    }
    render_report('report_template.docx', 'output.docx', context)
    print('报告已生成：output.docx')
