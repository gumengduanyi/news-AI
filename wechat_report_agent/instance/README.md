本地 instance 配置说明

目的：
- 方便在本地保存开发用的 API keys / token，避免每次启动都需要导出环境变量。请仅用于本地开发环境，切勿提交到版本控制。

位置：
- `wechat_report_agent/instance/config.json`

建议文件权限：
- 将该文件权限设为 600（仅 owner 可读写）：
  chmod 600 wechat_report_agent/instance/config.json

支持的键名（示例）：
- DEEPSEEK_API_KEY: 用于 DeepSeek API 的 key
- REPORT_API_TOKEN: 用于本地开发的鉴权 token（建议随机且足够复杂）
- QDRANT_URL / QDRANT_API_KEY: 可选的向量数据库配置

开发时的快捷配置：
- 将示例 JSON 写入 `instance/config.json`：
  {
    "REPORT_API_TOKEN": "your_local_token",
    "DEEPSEEK_API_KEY": "sk-..."
  }
- 启动后端之前可不必再在 shell 中导出这些变量。

本地回退（local fallback）策略：
- 当真实的 AI 适配器不可用时，后端可以使用一个本地回退实现 `local_call_ai_fallback` 以便开发和调试。
- 为避免在非开发环境误用，该回退仅在环境变量 `DEV_CALLAI_FALLBACK=1` 时自动启用。
  示例：
    DEV_CALLAI_FALLBACK=1 python wechat_report_agent/prompt_qdrant_api.py

日志与调试：
- 后端会在解析/转换 AI 输出时记录被掩码的片段（前 1000 字），以便在不泄露密钥的情况下进行调试。
- 如果你需要更详细的日志，可以设置环境变量 `PROMPT_QDRANT_DEBUG_ERRORS=1`（仅用于本地开发）。

安全建议：
- 请勿把 `wechat_report_agent/instance/config.json` 提交到 git。建议将其添加到 `.gitignore`。
- 在结束调试后，建议把 `REPORT_API_TOKEN` 改回强随机值并从开发浏览器中清除 localStorage 中的 token。

常见操作：
- 在浏览器 console 中设置前端 token：
  localStorage.setItem('REPORT_API_TOKEN', 'your_local_token'); location.reload();
- 以回退模式启动后端：
  DEV_CALLAI_FALLBACK=1 /path/to/venv/bin/python wechat_report_agent/prompt_qdrant_api.py

如需我替你把 README 内容扩展为更多示例或生成一个安全 token，我可以继续帮忙。