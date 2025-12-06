#!/usr/bin/env python3
# 从本地 SQLite 数据库读取 collected_article 表的素材，构造 ai_content 并调用 render_word_report.generate_ai_report 生成 DOCX 测试
import os, sys, sqlite3, datetime
sys.path.append('wechat_report_agent')
try:
    import prompt_qdrant_api as pq
except Exception as e:
    print('无法导入 prompt_qdrant_api:', e)
    pq = None

try:
    from wechat_report_agent.src import render_word_report as r
except Exception as e:
    print('无法导入 render_word_report:', e)
    raise

DB_CONN = None
if pq:
    try:
        DB_CONN = pq.get_db_conn()
    except Exception as e:
        print('使用 prompt_qdrant_api.get_db_conn 失败，回退读取常见 DB 路径：', e)

if DB_CONN is None:
    # 尝试常见路径
    CAND = [
        os.path.join(os.getcwd(), 'prompt_templates.db'),
        os.path.join(os.getcwd(), 'instance', 'prompt_templates.db'),
        os.path.join(os.getcwd(), 'wechat_report_agent', 'prompt_templates.db'),
    ]
    dbp = None
    for p in CAND:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            dbp = p; break
    if not dbp:
        print('未找到可用的 SQLite DB（prompt_templates.db）路径，脚本结束')
        sys.exit(1)
    DB_CONN = sqlite3.connect(dbp)
    DB_CONN.row_factory = sqlite3.Row

c = DB_CONN.cursor()
# 检查表是否存在
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='collected_article'")
if not c.fetchone():
    print('数据库中没有表 collected_article，脚本结束')
    sys.exit(1)

LIMIT = 12
# select all columns and handle schema variations gracefully
c.execute('SELECT * FROM collected_article ORDER BY id DESC LIMIT ?', (LIMIT,))
rows = c.fetchall()
if not rows:
    print('collected_article 表中没有数据，脚本结束')
    sys.exit(1)

parts = []
for rrow in rows:
    keys = list(rrow.keys())
    # title can be in 'title' or 'name'
    title = ''
    if 'title' in keys and rrow['title']:
        title = rrow['title']
    elif 'name' in keys and rrow['name']:
        title = rrow['name']
    elif 'task_name' in keys and rrow['task_name']:
        title = rrow['task_name']

    # date can be 'date' or 'create_time'
    date = ''
    if 'date' in keys and rrow['date']:
        date = rrow['date']
    elif 'create_time' in keys and rrow['create_time']:
        date = rrow['create_time']

    # content can be 'content' or 'summary'
    content = ''
    if 'content' in keys and rrow['content']:
        content = rrow['content']
    elif 'summary' in keys and rrow['summary']:
        content = rrow['summary']

    parts.append(f"{title}\n{date}\n{content}")

combined_material = '\n\n'.join(parts)

# 构造简单的 ai_content：把前3标题作为 core_news，其余均匀分配到四个栏目
titles = [ (r['title'] or '').strip() for r in rows ]
core_news = [t for t in titles[:3] if t]
sections = {'技术前沿': [], '产业动态': [], '政策法规': [], '应用实例': []}
sec_keys = list(sections.keys())
for i, row in enumerate(rows):
    title = (row['title'] or '').strip() or f'文档_{row[0]}'
    summary = (row['content'] or '').strip()
    if len(summary) > 600:
        summary = summary[:600] + '...'
    sec = sec_keys[(i) % len(sec_keys)]
    sections[sec].append({'title': title, 'summary': summary, 'source': title})

ai_content = {'core_news': core_news}
ai_content.update(sections)

out = os.path.join('wechat_report_agent', 'output', f'report_from_db_{datetime.date.today().isoformat()}.docx')
meta = {'title':'人工智能技术跟踪周报告（DB素材测试）','issue':'测试','org':'新闻智能体','date':datetime.date.today().strftime('%Y年%m月%d日')}

print('读取到 article 行数:', len(rows))
print('生成 combined_material 长度:', len(combined_material))

try:
    r.generate_ai_report(ai_content, out, combined_material=combined_material, meta=meta, include_sources=True)
    print('已生成报告:', out)
except Exception as e:
    print('生成报告失败:', e)
    raise

# --- Dry-run: show the strict prompt that backend will send to the AI when combined_material is present
try:
    import prompt_qdrant_api as pq
    example_full_prompt = pq.__dict__.get('full_prompt', None)
except Exception:
    example_full_prompt = None

from wechat_report_agent import prompt_qdrant_api as pq_mod
schema_example = {'core_news': [], '技术前沿': [], '产业动态': [], '政策法规': [], '应用实例': []}
schema_text = (
    "请严格返回 JSON，格式示例：\n" + __import__('json').dumps(schema_example, ensure_ascii=False, indent=2) + "\n\n"
    "约束见后端实现（core_news 只要短要点；栏目返回 title 与 summary，summary 必须基于传入材料）。\n"
)
payload = schema_text + "材料：\n" + combined_material[:4000]
print('\n--- Dry-run prompt preview (first 4000 chars of material) ---')
print(payload[:4000])
