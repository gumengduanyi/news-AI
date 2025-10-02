# 变更说明

请简要说明本次 PR 的改动点、关联的 issue（若有）、以及测试验证步骤。

## 变更摘要
- 增加鉴权到调试路由
- 增加 `ensure_structured_ai_response` 解析与严格 JSON 保障
- 增加 docx 轻量回退（python-docx）
- 增加本地测试 `tests/test_ai_parsing.py`
- 增加 GitHub Actions CI workflow（`.github/workflows/ci.yml`）
- 增加 `scripts/create_pr.sh` 用于本地创建分支并提交

## 验证步骤
1. 在 venv 中运行 `pytest`，所有测试应通过。
2. 启动服务并设置 `REPORT_API_TOKEN`（若启用鉴权），测试受保护的路由返回预期。

## 备注
- CI 需要在仓库 Secrets 中添加 `REPORT_API_TOKEN` 才能在 CI 环境通过鉴权相关测试。
