import argparse
import yaml
from pathlib import Path
def crawl_one_with_fallback(url: str):
    """
    优先用playwright采集，失败时降级用selenium采集。
    """
    import traceback
    try:
        from wechat_report_agent.src.crawler_playwright import crawl_one as crawl_one_playwright
        result = crawl_one_playwright(url)
        if result and result.get("content"):
            print(f"[采集] Playwright采集成功: url={url}, title={result.get('title','')}")
            return result
        else:
            print(f"[采集] Playwright采集无内容: url={url}, result={result}")
    except Exception as e:
        print(f"[采集] Playwright采集异常: url={url}, error={e}\n{traceback.format_exc()}")
    # 降级用selenium
    try:
        from wechat_report_agent.src.crawler import crawl_one as crawl_one_selenium
        result = crawl_one_selenium(url)
        if result and result.get("content"):
            print(f"[采集] Selenium采集成功: url={url}, title={result.get('title','')}")
            return result
        else:
            print(f"[采集] Selenium采集无内容: url={url}, result={result}")
    except Exception as e:
        print(f"[采集] Selenium采集异常: url={url}, error={e}\n{traceback.format_exc()}")
    return None

from wechat_report_agent.src.summarize import summarize_text
from wechat_report_agent.src.report import build_report

def run_from_config(config_path: str):
    """原来的批量模式"""
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    meta = cfg["report"]
    urls = cfg["sources"]

    items = []
    for u in urls:
        art = crawl_one_with_fallback(u["url"])
        if not art or not art.get("title"):
            continue
        summary = summarize_text(art["title"], art["date"], art["content"])
        items.append({
            "title": art["title"],
            "date": art["date"],
            "content": art["content"],
            "summary": summary,
            "category": u.get("category", "")
        })

    build_report(meta, items, meta["output"])
    print(f"报告生成成功: {meta['output']}")

def run_from_url(url: str, report_meta: dict = None):
    """智能体模式：单个 URL"""
    art = crawl_one_with_fallback(url)
    if not art or not art.get("title"):
        print("抓取失败或文章没有标题")
        return
    summary = summarize_text(art["title"], art["date"], art["content"])
    items = [{
        "title": art["title"],
        "date": art["date"],
        "content": art["content"],
        "summary": summary,
        "category": ""
    }]
    meta = report_meta or {
        "title": "智能体生成报告",
        "date": art["date"],
        "output": "output/report.docx"
    }
    build_report(meta, items, meta["output"])
    print(f"报告生成成功: {meta['output']}")

def run_from_urls(urls: list, report_meta: dict = None):
    """支持一次性处理多个 URL"""
    items = []
    for url in urls:
        art = crawl_one_with_fallback(url)
        if not art or not art.get("title"):
            print(f"抓取失败: {url}")
            continue
        summary = summarize_text(art["title"], art["date"], art["content"])
        items.append({
            "title": art["title"],
            "date": art["date"],
            "content": art["content"],
            "summary": summary,
            "category": ""
        })

    if not items:
        print("没有成功生成报告内容")
        return

    meta = report_meta or {
        "title": "智能体生成报告",
        "date": items[0]["date"],
        "output": "output/report.docx"
    }
    build_report(meta, items, meta["output"])
    print(f"报告生成成功: {meta['output']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None, help="配置文件路径")
    parser.add_argument("--url", default=None, help="单个或多个文章 URL，逗号分隔")

    args = parser.parse_args()

    if args.url:
        urls = [u.strip() for u in args.url.split(",") if u.strip()]
        if len(urls) == 1:
            run_from_url(urls[0])
        else:
            run_from_urls(urls)
    elif args.config:
        run_from_config(args.config)
    else:
        print("请提供 --config <配置文件> 或 --url <文章链接>")