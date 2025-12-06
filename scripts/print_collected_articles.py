#!/usr/bin/env python3
import sys, os
sys.path.append(os.getcwd())
try:
    from wechat_report_agent import prompt_qdrant_api as pq
except Exception as e:
    print('failed import wechat_report_agent.prompt_qdrant_api:', e)
    raise

conn = pq.get_db_conn()
c = conn.cursor()
# determine available columns
c.execute("PRAGMA table_info(collected_article)")
cols = [r[1] for r in c.fetchall()]
sel = ['id']
for opt in ('title','date','content','summary','create_time','task_name','name'):
    if opt in cols:
        sel.append(opt)

q = f"SELECT {', '.join(sel)} FROM collected_article ORDER BY id DESC"
c.execute(q)
rows = c.fetchall()
print('总共行数:', len(rows))
for r in rows:
    keys = list(r.keys())
    tid = r['id']
    title = r['title'] if 'title' in keys and r['title'] else (r['name'] or r['task_name'] or '')
    datev = r['date'] if 'date' in keys and r['date'] else (r['create_time'] or '')
    content = r['content'] if 'content' in keys and r['content'] else (r['summary'] or '')
    print('---')
    print('id=', tid)
    print('title=', title)
    print('date=', datev)
    print('content preview:\n', content[:1200].replace('\n','\\n'))
conn.close()
