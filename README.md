# 新闻智能体 — 项目说明

本文件包含本项目的依赖、安装与运行步骤，以及 `openclaw` web bridge 的 SSH 隧道使用说明（含安全建议）。

## 前提环境
- macOS / Linux
- Python 3.10 推荐（仓库中 Dockerfile 使用 Python 3.9）
- Node.js 18+ 和 npm
- Git
- Docker（可选，用于构建镜像）

## 快速安装（后端）
1. 使用 pyenv 安装并切换 Python（示例）：

```bash
pyenv install 3.10.20
pyenv local 3.10.20
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r fastnews-main/backend/requirements.txt
```

2. Playwright 额外步骤（若项目使用浏览器自动化）：

```bash
pip install playwright
playwright install
```

3. PaddlePaddle / PaddleOCR 注意事项：
- 若需要 GPU 支持，按官方说明安装匹配 CUDA/cuDNN 的 PaddlePaddle。
- CPU 版可直接通过 pip 安装，但可能需要额外系统依赖。

## 快速安装（前端）

```bash
cd fastnews-main/frontend
npm install
npm run dev
```

根目录还包含一个简单 `package.json`（`markdown-it`），按需安装。

## 使用 Docker 构建后端镜像

```bash
cd fastnews-main/backend
docker build -t fastnews-backend .
docker run -p 8000:8000 fastnews-backend
```

## `openclaw` web bridge 与 SSH 隧道

脚本位置：`fastnews-main/backend/openclaw/start-web-bridge-local.sh`。

功能：建立本地端口到远端主机的 SSH 隧道（本地：`LOCAL_PORT` -> 远端 `REMOTE_PORT`），然后启动 web bridge（`npm start`）。

环境变量配置：在同目录放置 `.env`，支持以下变量（有默认值）：
- `OPENCLAW_HOST`（默认示例：43.160.192.130）
- `OPENCLAW_USER`（默认：root）
- `OPENCLAW_PASSWORD`（若使用密码认证）
- `OPENCLAW_LOCAL_GATEWAY_PORT`（默认：10720）
- `OPENCLAW_REMOTE_GATEWAY_PORT`（默认：10720）

运行脚本：

```bash
cd fastnews-main/backend/openclaw
./start-web-bridge-local.sh
```

脚本行为与依赖：
- 脚本会优先尝试使用 `autossh`（若可用）以维护持久隧道。否则使用 `ssh`。
- 若 `.env` 中提供 `OPENCLAW_PASSWORD`，脚本会使用 `sshpass` 传递密码；若未提供，会尝试使用密钥认证（请确保本地 `~/.ssh` 有有效私钥，并且远端 `authorized_keys` 已配置）。

安全与可靠性建议：
- 强烈建议使用 SSH 公钥认证，避免在文件中保存明文密码或使用 `sshpass`。
- 在 macOS 安装 `sshpass`（若确实需要密码回退）：

```bash
brew install hudochenkov/sshpass/sshpass
```

- 如需持久重连，安装 `autossh`：

```bash
brew install autossh
```

若需要，我可以把 `start-web-bridge-local.sh` 改为：
- 优先使用密钥认证（检测本地私钥），仅在显式 `--use-password` 时回退到 `sshpass`；或
- 增加 `--help` / CLI 选项并改进日志。你希望我实现哪种？

## 主要依赖汇总（简洁）

- Python: `fastapi`, `uvicorn`, `pandas`, `bcrypt`, `transformers`, `openai`, `python-multipart`, `python-dotenv`, `python-docx`, `itsdangerous`, `docker`, `sqlalchemy`, `httpx`, `python-jose[cryptography]`, `passlib[bcrypt]`, `tencentcloud-sdk-python`, `playwright`, `paddleocr`, `paddlepaddle`, `requests`, `beautifulsoup4`, `lxml`。
- 前端（fastnews-main/frontend）: `axios`, `highlight.js`, `html2pdf.js`, `katex`, `marked`, `marked-highlight`, `vue`, `vue-router`；dev: `vite`, `@vitejs/plugin-vue`。
- openclaw bridge: `cors`, `dotenv`, `express`, `http-proxy-middleware`, `ws`。

## 其他运行/调试提示
- 若端口冲突，修改 `.env` 中的 `OPENCLAW_LOCAL_GATEWAY_PORT`。
- 若在 CI 或容器中运行，无交互安装 `playwright` 时需显式安装浏览器二进制。

---

如果你确认，我会把这个 `README.md` 写入仓库（现在正在写入）。接下来我可以：
- 把 `start-web-bridge-local.sh` 改为优先密钥认证并支持 `--use-password`（自动回退），或
- 生成一个专门的 `openclaw/README.md`，详细说明 `.env` 字段与示例。

请选择下一步。
