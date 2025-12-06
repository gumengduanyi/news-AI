#!/usr/bin/env python3
# Run a structured-AI dry run: use local_call_ai_fallback or real call_ai (if configured) to generate
# the structured JSON (core_news + sections with title+summary+source_fragment), then render a docx.
import os, sys, json
sys.path.append(os.getcwd())
from wechat_report_agent import prompt_qdrant_api as api
# dynamic load of render_word_report (module file located under wechat_report_agent/wechat_report_agent/src)
from importlib.machinery import SourceFileLoader
rw_path = os.path.join(os.getcwd(), 'wechat_report_agent', 'wechat_report_agent', 'src', 'render_word_report.py')
if not os.path.exists(rw_path):
    # alternate path (older layout)
    rw_path = os.path.join(os.getcwd(), 'wechat_report_agent', 'src', 'render_word_report.py')
r = SourceFileLoader('render_word_report', rw_path).load_module()

# build combined_material from DB (same as other scripts)
conn = api.get_db_conn()
c = conn.cursor()
# determine available columns
c.execute("PRAGMA table_info(collected_article)")
cols = [r[1] for r in c.fetchall()]
sel = ['id']
for opt in ('title','date','content','summary','create_time','name'):
    if opt in cols:
        sel.append(opt)
q = f"SELECT {', '.join(sel)} FROM collected_article ORDER BY id DESC"
c.execute(q)
rows = c.fetchall()
parts = []
for row in rows:
    keys = list(row.keys())
    title = row['title'] if 'title' in keys and row['title'] else (row.get('name') or '')
    datev = row['date'] if 'date' in keys and row['date'] else (row.get('create_time') or '')
    content = row['content'] if 'content' in keys and row['content'] else (row.get('summary') or '')
    parts.append(f"{title}\n{datev}\n{content}")
combined_material = '\n\n'.join(parts)

# Build strict payload (same wording as in api)
schema_example = {'core_news': [], '技术前沿': [], '产业动态': [], '政策法规': [], '应用实例': []}
schema_text = (
    "请严格返回 JSON，格式示例：\n" + json.dumps(schema_example, ensure_ascii=False, indent=2) + "\n\n"
    "约束：\n"
    "1) 必须仅基于下方提供的材料（'材料' 字段），不得补充外部信息或凭空臆造事实；\n"
    "2) core_news：只返回若干短要点（每条一行，简短句子），不要为 core_news 提供正文或来源；\n"
    "3) 对于每个非 core 的栏目（技术前沿/产业动态/政策法规/应用实例），返回一个对象数组，\n"
    "   每个对象包含 'title'（小标题，1-10 字）和 'summary'（基于材料的正文描述，50-300 字），summary 必须严格依据材料并在文末标注来源片段（用字段 'source_fragment' 表示）；\n"
    "4) 如果材料不足以支撑某条要点，请返回空数组或在对应位置返回 {\n"
    "   \"title\": \"(材料不足)\", \"summary\": \"(材料不足)\", \"source_fragment\": \"\"\n"
    "   }；\n"
    "5) 请不要返回任何解释、注释或额外文本——仅返回纯 JSON。\n\n"
)
payload = schema_text + "材料：\n" + (combined_material or '')

print('---payload preview---')
print(payload[:2000])

# choose AI caller: real call_ai if present, else local fallback
ai_res = None
if api.call_ai:
    try:
        ai_res = api.call_ai('local-model', payload)
    except Exception as e:
        print('call_ai failed:', e)
        ai_res = None

if ai_res is None:
    if hasattr(api, 'local_call_ai_fallback'):
        print('Using local_call_ai_fallback to simulate AI response')
        ai_res = api.local_call_ai_fallback('local-model', payload)
    else:
        raise RuntimeError('No AI provider available and no local fallback')

print('\n---AI raw response preview (first 2000 chars)---')
print(str(ai_res)[:2000])

# normalize via ensure_structured_ai_response
ai_content = api.ensure_structured_ai_response('local-model', ai_res)
print('\n---Parsed ai_content keys and counts---')
for k in ai_content:
    print(k, len(ai_content[k]))

# render a docx to inspect
out = os.path.join('wechat_report_agent', 'output', 'report_structured_ai_test.docx')
try:
    r.generate_ai_report(ai_content, out, combined_material=combined_material, meta={'title':'测试AI结构化生成','issue':'测试'}, include_sources=True)
    print('\nGenerated report:', out)
except Exception as e:
    print('render failed:', e)

conn.close()
