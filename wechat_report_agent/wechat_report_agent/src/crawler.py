from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def refine_title(raw_title: str, content: str) -> str:
    """
    优化标题:
    - 如果是“资讯/动态/速递”这种笼统标题，就从正文第一句取一个当标题
    - 否则直接返回原始标题
    """
    bad_words = ["资讯", "动态", "速递", "简报", "日报", "周报", "月报", "最新消息"]
    if any(bad in raw_title for bad in bad_words) or not raw_title or raw_title == "无标题":
        first_sent = content.strip().split("。")[0] if content else ""
        if len(first_sent) > 6:   # 避免太短
            return first_sent
    return raw_title or "（未命名）"


def crawl_one(url: str):
    options = Options()
    options.add_argument("--headless")  # 无界面模式
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # 等页面加载

    # 标题
    try:
        raw_title = driver.find_element("id", "activity-name").text.strip()
    except:
        raw_title = ""

    # 日期
    try:
        date = driver.find_element("id", "publish_time").text.strip()
    except:
        date = ""

    # 正文
    try:
        content = driver.find_element("id", "js_content").text.strip()
    except:
        content = ""

    driver.quit()

    # 重新生成一个优化后的标题
    title = refine_title(raw_title, content)

    # 如果正文抓不到，整篇文章就直接丢弃（避免生成“无标题”空块）
    if not content:
        return None

    return {"title": title, "date": date, "content": content}
