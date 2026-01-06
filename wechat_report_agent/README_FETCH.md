# 使用 Playwright 持久化登录并抓取微信文章（快速上手）

本文档说明如何在本地使用项目自带的脚本：

- `save_wechat_state.py`：交互式打开浏览器登录并保存 Playwright 的 `storage_state`（登录态）。
- `fetch_with_state.py`：使用保存的登录态以 headless 模式抓取指定微信文章并尝试入库，同时生成调试产物（HTML / PNG）。

目录：`wechat_report_agent/scripts/`

## 前提

- 在项目根目录下操作（即包含 `wechat_report_agent/` 的目录）。
- 已激活虚拟环境（示例使用 `venv311`）。
- 已安装依赖并安装 Playwright 浏览器：

```bash
pip install -r requirements.txt
# 若未安装 playwright，请执行：
pip install playwright
playwright install
```

## 保存登录态（交互式）

1. 运行脚本，脚本会以 headful 模式打开 Chromium：

```bash
# 在项目根目录下
python3 wechat_report_agent/scripts/save_wechat_state.py wechat_state.json
```

2. 在打开的浏览器窗口中完成微信扫码或账号登录。登录完成后回到终端按回车，脚本会把登录态写入你指定的 `wechat_state.json`（示例路径：项目根目录下）。

注意：该文件包含有效会话信息，请妥善保管并限制访问权限。

## 使用保存的登录态抓取文章

示例：抓取一篇文章并尝试入库

```bash
python3 wechat_report_agent/scripts/fetch_with_state.py "https://mp.weixin.qq.com/s/XXXXXXXXXXXX" --state "/path/to/wechat_state.json"
```

替换 URL 与 `--state` 值（如你刚保存的 `wechat_state.json`）。脚本会：

- 使用 headless Playwright + 已保存的 `storage_state` 加载页面
- 做滚动 / 点击 等交互尝试触发正文加载
- 提取 `#js_content` 或段落文本作为正文
- 保存调试产物到 `/tmp/wechat_fetch_state_debug_<ts>.html` 和 `/tmp/wechat_fetch_state_debug_<ts>.png`（便于人工查看）
- 若能提取到正文，会尝试调用项目的 DB helper 将文章写入 `已采集文章` 表（要求从项目根目录运行以便正确导入模块）
- 脚本执行完成后会把使用的 `storage_state` 文件复制到项目实例目录：`wechat_report_agent/instance/wechat_state.json`（便于后续服务化使用与备份）。

示例输出（成功）会包含调试文件路径和提取内容长度。

## 常见问题与排查

- 无法提取正文或只得到“参数错误”：
  - 原因：服务器在无会话/被检测为自动化时降级返回占位页。
  - 处理：确保使用保存的 `wechat_state.json`，并从项目根目录运行脚本；必要时在 headful 模式下手动打开页面确认。

- 脚本提示 `DB helper not available; skipping DB insert`：
  - 说明脚本未能导入项目内的 DB helper（可能因当前工作目录或 PYTHONPATH 不对）。
  - 解决：从项目根目录运行脚本，或在运行前设置 `PYTHONPATH=. `；例如：

```bash
cd /path/to/project/root
python3 wechat_report_agent/scripts/fetch_with_state.py <URL> --state wechat_state.json
# 或
PYTHONPATH=. python3 wechat_report_agent/scripts/fetch_with_state.py <URL> --state wechat_state.json
```

- 若需要把脚本集成到后端 API：请在后端路由中调用相同逻辑（注意权限、并发控制与登录态保密）。

## 调试产物位置

- HTML / PNG：`/tmp/wechat_fetch_state_debug_<ts>.html`、`/tmp/wechat_fetch_state_debug_<ts>.png`。
- headful 保存的登录态示例位置：`/Users/yourname/新闻智能体/wechat_state.json`（按运行时路径而定）。

## 安全与合规提醒

- `wechat_state.json` 包含登录会话信息，请仅在受信任的环境中保存并限制访问。若项目托管在服务器，请不要保存非必要的长期会话文件。
- 抓取与使用文章请遵守版权和平台规则，必要时获得原作者或公众号授权。

## 下一步（可选）

- 将 `fetch_with_state.py` 的入库逻辑切换为后端 API 调用并增加任务队列（如 celery）以做并发控制与重试。
- 增加自动脱敏与最小化存储策略以降低合规风险。

如需，我可以把抓取流程集成到后端路由并演示一次完整的前端触发到写库流程。
