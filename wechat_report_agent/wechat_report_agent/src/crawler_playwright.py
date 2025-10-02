from playwright.sync_api import sync_playwright

def crawl_one(url: str):
    def clean_content(text: str) -> str:
        """去除常见无关内容"""
        import re
        # 去除“请在微信内打开”等反爬提示
        patterns = [
            r"请在微信内打开",
            r"长按识别二维码",
            r"关注我们",
            r"点击蓝字.*关注",
            r"NEWS TODAY",
            r"写留言",
            r"赞[\d]*",
            r"在看[\d]*",
            r"AI瞭望星球",
        ]
        for pat in patterns:
            text = re.sub(pat, '', text, flags=re.IGNORECASE)
        # 去除多余空行
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.0")
        page.goto(url, timeout=30000)
        try:
            page.wait_for_selector('#activity-name', timeout=8000)
        except Exception:
            pass
        # 标题：只用#activity-name，不降级正文
        try:
            raw_title = page.query_selector('#activity-name').inner_text().strip()
        except Exception:
            raw_title = ''
        # 日期
        try:
            date = page.query_selector('#publish_time').inner_text().strip()
        except Exception:
            date = ''
        # 正文
        try:
            page.wait_for_selector('#js_content', timeout=8000)
            content = page.query_selector('#js_content').inner_text().strip()
        except Exception:
            content = ''
        browser.close()
        # 反爬检测：如正文或标题含反爬提示，直接返回None
        anti_spider_keywords = ["请在微信内打开", "长按识别二维码", "关注公众号", "微信扫一扫"]
        if any(k in (raw_title or '') for k in anti_spider_keywords) or any(k in (content or '') for k in anti_spider_keywords):
            return None
        # 清洗正文
        content = clean_content(content)
        # 标题为空直接返回None
        if not raw_title or not content:
            return None
        return {"title": raw_title, "date": date, "content": content}
