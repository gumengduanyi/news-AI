from flask import Flask, request, send_file
from src.main import run_from_urls

app = Flask(__name__)

@app.route("/generate_doc", methods=["POST"])
def generate_doc_api():
    data = request.json
    urls = data.get("urls")  # 注意这里是 urls 列表
    if not urls or not isinstance(urls, list):
        return {"error": "请提供 urls 列表"}, 400

    output_path = run_from_urls(urls)
    if not output_path:
        return {"error": "抓取失败或没有有效文章"}, 500
    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(port=5000)
