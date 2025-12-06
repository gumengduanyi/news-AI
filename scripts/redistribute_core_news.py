#!/usr/bin/env python3
"""
后处理脚本：读取上次模型输出（或直接调用模型），将 core_news 中短要点按规则分配到四个栏目
（技术前沿/产业动态/政策法规/应用实例），并在必要时进行模型补写以保证每个栏目至少 N 条。
生成审计日志并渲染最终 DOCX。
"""
import os, sys, json, re
sys.path.append(os.getcwd())
from wechat_report_agent import prompt_qdrant_api as api
from importlib.machinery import SourceFileLoader

OUTDIR = os.path.join('wechat_report_agent','output')
RAW_PATH = os.path.join(OUTDIR,'ai_raw_user_prompt_deepseek.txt')
POST_JSON = os.path.join(OUTDIR,'ai_content_postprocess.json')
AUDIT_LOG = os.path.join(OUTDIR,'redistribute_audit.log')
DOCX_OUT = os.path.join(OUTDIR,'report_postprocess.docx')
MIN_PER_SECTION = 2
MODEL_NAME = 'DeepSeek-R1'

# keyword map: keyword -> category
KEYWORDS = {
    '产业动态': ['融资','投','并购','上市','融资轮','估值','发布产品','合作','扩张','市场','收购','并购','资本'],
    '技术前沿': ['模型','架构','基座','多模态','tokens','性能','benchmark','推理','算法','鲁棒','权重','微调','架构','优化','具身'],
    '政策法规': ['签证','政策','法','法规','监管','指南','标准','合规','安全策略','政策变动','税收'],
    '应用实例': ['落地','部署','案例','应用','场景','示例','视频','演示','表格','助理','机器人','产品']
}

# helper scoring by keyword occurrences
def score_by_keywords(text, category):
    s = 0
    for kw in KEYWORDS.get(category,[]):
        if kw in text:
            s += 1
    return s

# fallback simple overlap score
def overlap_score(a, b):
    aset = set(re.findall(r'\w+', a))
    bset = set(re.findall(r'\w+', b))
    if not aset or not bset:
        return 0
    return len(aset & bset) / max(1, len(aset))

# load raw AI response
raw = None
if os.path.exists(RAW_PATH):
    with open(RAW_PATH,'r',encoding='utf-8') as f:
        raw = f.read()
else:
    print('Raw AI file not found at', RAW_PATH)
    # attempt to trigger model run via api? for now abort
    sys.exit(1)

# normalize via ensure_structured_ai_response
ai_content = api.ensure_structured_ai_response(MODEL_NAME, raw)
# ensure keys
for k in ['core_news','技术前沿','产业动态','政策法规','应用实例']:
    if k not in ai_content:
        ai_content[k] = []

audit = []

# If core_news is a list of strings, redistribute
core_items = ai_content.get('core_news') or []
if isinstance(core_items, list) and all(isinstance(x,str) for x in core_items):
    audit.append(f'Found {len(core_items)} core_news items to redistribute')
    leftovers = []
    for item in core_items:
        # try keyword scoring
        scores = {cat: score_by_keywords(item, cat) for cat in KEYWORDS}
        best = max(scores.items(), key=lambda x: x[1])
        if best[1] > 0:
            ai_content[best[0]].append({'title': item[:12], 'summary': item, 'source_fragment': ''})
            audit.append(f'Assigned core_news "{item}" -> {best[0]} by keyword match')
            continue
        # fallback: similarity with existing summaries' concatenation
        best_cat = None
        best_score = 0
        for cat in ['技术前沿','产业动态','政策法规','应用实例']:
            concat = ' '.join([ (x.get('title','')+' '+x.get('summary','')) if isinstance(x,dict) else str(x) for x in ai_content.get(cat,[]) ])
            sc = overlap_score(item, concat)
            if sc > best_score:
                best_score = sc
                best_cat = cat
        if best_score > 0.05 and best_cat:
            ai_content[best_cat].append({'title': item[:12], 'summary': item, 'source_fragment': ''})
            audit.append(f'Assigned core_news "{item}" -> {best_cat} by overlap score {best_score:.3f}')
        else:
            leftovers.append(item)
            audit.append(f'Could not confidently assign core_news "{item}" -> kept as leftover')
    # replace core_news with leftovers (or empty)
    ai_content['core_news'] = leftovers
else:
    audit.append('No core_news string-list found to redistribute (core_news may already be structured)')

# Ensure min per section
for cat in ['技术前沿','产业动态','政策法规','应用实例']:
    arr = ai_content.get(cat) or []
    if len(arr) < MIN_PER_SECTION:
        need = MIN_PER_SECTION - len(arr)
        audit.append(f'Category {cat} needs {need} items to reach min {MIN_PER_SECTION}')
        # try to pull from leftovers
        pulled = 0
        leftovers = ai_content.get('core_news', [])
        while pulled < need and leftovers:
            itm = leftovers.pop(0)
            if isinstance(itm, str):
                ai_content[cat].append({'title': itm[:12], 'summary': itm, 'source_fragment': ''})
            else:
                ai_content[cat].append(itm)
            pulled += 1
            audit.append(f'Pulled leftover into {cat}: "{str(itm)[:60]}"')
        # if still need, try to reallocate from other categories that have surplus
        if pulled < need:
            for donor in ['技术前沿','产业动态','政策法规','应用实例']:
                if donor==cat: continue
                donor_arr = ai_content.get(donor) or []
                while pulled < need and len(donor_arr) > MIN_PER_SECTION:
                    moved = donor_arr.pop()
                    ai_content[cat].append(moved)
                    pulled += 1
                    audit.append(f'Moved item from {donor} to {cat}: "{str(moved)[:60]}"')
                if pulled >= need:
                    break
        # if still short, ask model to synthesize missing entries based on combined_material
        if pulled < need:
            num = need - pulled
            # build a safe prompt asking the model to synthesize missing items; do not use unescaped f-strings with braces
            synth_prompt = (
                "请基于之前提供的材料，为栏目 {cat} 生成 {num} 条对象数组，格式为 JSON，例："
                "[{{\"title\":\"\", \"summary\":\"\", \"source_fragment\":\"\"}}]。"
                "只使用材料里的信息，不要加入外部事实。"
            ).format(cat=cat, num=num)
            try:
                audit.append(f'Requesting model to synthesize {need-pulled} items for {cat}')
                conv = api.call_ai(MODEL_NAME, synth_prompt)
                # try to parse conv as JSON array
                if isinstance(conv, str):
                    try:
                        parsed = json.loads(conv)
                    except Exception:
                        # try extract json substring
                        m = re.search(r'(\[\s*\{[\s\S]*\}\s*\])', conv)
                        if m:
                            parsed = json.loads(m.group(1))
                        else:
                            parsed = []
                else:
                    parsed = conv
                if isinstance(parsed, list):
                    for p in parsed:
                        if isinstance(p, dict):
                            ai_content[cat].append(p)
                            pulled += 1
                            audit.append(f'Model-synthesized item for {cat}: {p.get("title","")[:60]}')
                        if pulled >= need:
                            break
                else:
                    audit.append(f'Model synthesis returned non-list: {type(parsed)}')
            except Exception as e:
                audit.append('Model synthesis failed: '+str(e))

# final audit summary counts
audit.append('Final counts:')
for k in ['core_news','技术前沿','产业动态','政策法规','应用实例']:
    audit.append(f'{k}: {len(ai_content.get(k) or [])}')

# save ai_content and audit
with open(POST_JSON,'w',encoding='utf-8') as f:
    json.dump(ai_content, f, ensure_ascii=False, indent=2)
with open(AUDIT_LOG,'w',encoding='utf-8') as f:
    f.write('\n'.join(audit))

# render using render_word_report
rw_path = os.path.join(os.getcwd(),'wechat_report_agent','wechat_report_agent','src','render_word_report.py')
if not os.path.exists(rw_path):
    rw_path = os.path.join(os.getcwd(),'wechat_report_agent','src','render_word_report.py')
r = SourceFileLoader('render_word_report', rw_path).load_module()
try:
    r.generate_ai_report(ai_content, DOCX_OUT, combined_material='', meta={'title':'后处理分配报告','issue':'postprocess'}, include_sources=True)
    print('Rendered', DOCX_OUT)
except Exception as e:
    print('Render failed', e)

print('Saved postprocess JSON to', POST_JSON)
print('Saved audit log to', AUDIT_LOG)
print('Done')
