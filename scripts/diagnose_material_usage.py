#!/usr/bin/env python3
# Diagnose which DB materials are being used by render_word_report._extract_evidence
import os, sys
sys.path.append('wechat_report_agent')
from wechat_report_agent.src import render_word_report as r
import prompt_qdrant_api as pq
import sqlite3

conn = pq.get_db_conn()
c = conn.cursor()
# get recent rows used by previous test (we used ORDER BY id DESC LIMIT 12)
c.execute('SELECT id, title, date, content, summary FROM collected_article ORDER BY id DESC LIMIT 12')
rows = c.fetchall()
if not rows:
    print('no rows found in collected_article')
    sys.exit(0)

print('Found rows:')
for row in rows:
    keys = list(row.keys())
    title = ''
    if 'title' in keys and row['title']:
        title = row['title']
    elif 'name' in keys and row['name']:
        title = row['name']
    elif 'task_name' in keys and row['task_name']:
        title = row['task_name']
    datev = row['date'] if 'date' in keys and row['date'] else (row['create_time'] if 'create_time' in keys else '')
    print(f"- id={row['id']} title={title[:60]!r} date={datev}")

# Build combined_material as the test script did
parts = []
for rrow in rows:
    title = rrow['title'] if 'title' in rrow.keys() and rrow['title'] else (rrow.get('name') or '')
    date = rrow['date'] if 'date' in rrow.keys() and rrow['date'] else rrow.get('create_time','')
    content = rrow['content'] if 'content' in rrow.keys() and rrow['content'] else (rrow.get('summary') or '')
    parts.append(f"{title}\n{date}\n{content}")
combined_material = '\n\n'.join(parts)
print('\ncombined_material length=', len(combined_material))

# Create ai_content similar to test_generate_from_db
titles = [ (r['title'] or '').strip() for r in rows ]
core_news = [t for t in titles[:3] if t]
sections = {'技术前沿': [], '产业动态': [], '政策法规': [], '应用实例': []}
sec_keys = list(sections.keys())
for i, row in enumerate(rows):
    title = (row['title'] or '').strip() or f"文档_{row['id']}"
    summary = (row['content'] or '')[:600]
    sec = sec_keys[(i) % len(sec_keys)]
    sections[sec].append({'title': title, 'summary': summary, 'source': title})

ai_content = {'core_news': core_news}
ai_content.update(sections)

print('\nTesting evidence extraction for each generated item:\n')
for sec in ['技术前沿','产业动态','政策法规','应用实例']:
    items = ai_content.get(sec, [])
    print('Section:', sec, 'items=', len(items))
    for idx, it in enumerate(items, 1):
        title = it.get('title') if isinstance(it, dict) else str(it)
        evidence = r._extract_evidence(title, combined_material, max_sentences=2)
        print(f" {idx}. title={title[:80]!r}")
        if evidence:
            print('    -> evidence:', evidence[:200])
        else:
            print('    -> evidence: (none)')

print('\nDone')
conn.close()
