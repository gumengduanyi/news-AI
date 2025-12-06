#!/usr/bin/env python3
"""
Load ai_content_postprocess.json, normalize structure so each category is an array of objects
{'title','summary','source_fragment'}, fill core_news with up to 5 bullets (one per category top items),
then render DOCX and print summary.
"""
import os, sys, json
sys.path.append(os.getcwd())
from importlib.machinery import SourceFileLoader
from wechat_report_agent import prompt_qdrant_api as api

OUTDIR = os.path.join('wechat_report_agent','output')
POST_JSON = os.path.join(OUTDIR,'ai_content_postprocess.json')
NORM_JSON = os.path.join(OUTDIR,'ai_content_normalized.json')
DOCX_OUT = os.path.join(OUTDIR,'report_normalized.docx')

if not os.path.exists(POST_JSON):
    print('Postprocess file not found:', POST_JSON)
    sys.exit(1)

with open(POST_JSON,'r',encoding='utf-8') as f:
    ai = json.load(f)

# ensure keys
for k in ['core_news','技术前沿','产业动态','政策法规','应用实例']:
    if k not in ai:
        ai[k] = []

# normalize categories: if item is string -> convert to object
for cat in ['技术前沿','产业动态','政策法规','应用实例']:
    new = []
    for itm in ai.get(cat,[]):
        if isinstance(itm, dict):
            # ensure keys exist
            title = itm.get('title') or (itm.get('summary','')[:12])
            summary = itm.get('summary') or itm.get('title','')
            src = itm.get('source_fragment','')
            new.append({'title': title, 'summary': summary, 'source_fragment': src})
        else:
            s = str(itm)
            title = s.split('\n',1)[0][:12]
            new.append({'title': title, 'summary': s, 'source_fragment': ''})
    ai[cat] = new

# build core_news: if core_news already has string bullets, keep up to 5; else derive from categories
core = ai.get('core_news') or []
bullets = []
if isinstance(core, list) and any(isinstance(x,str) for x in core):
    for x in core:
        if isinstance(x,str) and len(bullets) < 5:
            bullets.append(x.strip())
# if we have none, derive from top items of categories (one each)
if not bullets:
    for cat in ['技术前沿','产业动态','政策法规','应用实例']:
        items = ai.get(cat,[])
        if items:
            top = items[0]
            if isinstance(top, dict):
                bullets.append(top.get('title') or top.get('summary','')[:40])
            else:
                bullets.append(str(top)[:40])
        if len(bullets) >=5:
            break
ai['core_news'] = bullets

# save normalized
with open(NORM_JSON,'w',encoding='utf-8') as f:
    json.dump(ai,f,ensure_ascii=False,indent=2)

# render
rw_path = os.path.join(os.getcwd(),'wechat_report_agent','wechat_report_agent','src','render_word_report.py')
if not os.path.exists(rw_path):
    rw_path = os.path.join(os.getcwd(),'wechat_report_agent','src','render_word_report.py')
r = SourceFileLoader('render_word_report', rw_path).load_module()
try:
    r.generate_ai_report(ai, DOCX_OUT, combined_material='', meta={'title':'Normalized Report','issue':'normalized'}, include_sources=True)
    print('Rendered', DOCX_OUT)
except Exception as e:
    print('Render failed:', e)

# print summary
print('\nSummary:')
for k in ['core_news','技术前沿','产业动态','政策法规','应用实例']:
    print(k, len(ai.get(k) or []))

print('\nCore_news (up to 5):')
for b in ai['core_news']:
    print('⚫', b)

print('\nSample item from 技术前沿:')
if ai['技术前沿']:
    print(ai['技术前沿'][0])

print('Normalized JSON saved at', NORM_JSON)
