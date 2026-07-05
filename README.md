# 扫描全能王 PDF 去水印网站

[![CI](https://github.com/Robert16233/camscanner-watermark-web/actions/workflows/ci.yml/badge.svg)](https://github.com/Robert16233/camscanner-watermark-web/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/deploy-Docker-2496ED)](Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

这是一个可部署的公开版 Web 项目。用户上传 PDF 后，服务端在临时目录中处理文件，返回去水印后的 PDF 或 zip，然后自动清理临时文件。

## 功能范围

- 当前针对右下角“扫描全能王”独立图片水印。
- 不重绘正文，只删除匹配水印图片的 PDF 绘制指令。
- 单个或批量上传 PDF。
- 默认限制：单次上传总大小 50 MB，最多 10 个文件，每 IP 每分钟 20 次请求。

## 项目结构

```text
app/
  main.py       # FastAPI 网站和上传接口
  watermark.py  # PDF 去水印核心逻辑
tests/          # 基础接口测试
Dockerfile      # Docker 部署入口
render.yaml     # Render Blueprint 示例
```

## 本地运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

浏览器打开：

```text
http://127.0.0.1:8000
```

Windows 上也可以双击 `run_local.bat`。

## 发布到 GitHub

Windows 上可以双击：

```text
publish_to_github.bat
```

如果 GitHub CLI 尚未登录，可以先双击 `login_github_cli.bat`。
如果设备码登录不能保存成功，也可以用 `login_github_with_token.bat`。

也可以按 [PUBLISHING.md](PUBLISHING.md) 手动发布。

如果 GitHub CLI 登录失败，请看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

## Docker 运行

```bash
docker build -t camscanner-watermark-web .
docker run --rm -p 8000:8000 camscanner-watermark-web
```

浏览器打开：

```text
http://127.0.0.1:8000
```

也可以用 Docker Compose：

```bash
docker compose up --build
```

## 部署到服务器

通用 Docker 平台都可以部署，例如 Fly.io、Railway、Render 或自己的 VPS。

通用流程：

1. 把本文件夹提交到 GitHub 仓库。
2. 在部署平台选择 Dockerfile 部署。
3. 设置端口为 `8000`，或使用平台自动识别。
4. 绑定域名并启用 HTTPS。

可配置环境变量：

```text
MAX_UPLOAD_BYTES=52428800
MAX_FILES=10
RATE_LIMIT_PER_MINUTE=20
```

项目内附带：

- `render.yaml`：Render Blueprint 部署配置。
- `fly.toml.example`：Fly.io 配置模板，复制为 `fly.toml` 后修改 app 名称。
- `docker-compose.yml`：VPS 或本地 Docker Compose 运行。
- `.env.example`：环境变量示例。
- `PRIVACY.md` / `SECURITY.md`：公开上线前可直接改成站点说明。
- `TERMS.md`：使用条款模板。
- `.github/workflows/ci.yml`：GitHub Actions 自动测试。

## 隐私和合规提示

- 不要保存上传文件、处理后文件或用户文件名日志。
- 建议在网页或服务条款中说明：用户只能处理自己拥有权利或已获授权处理的文件。
- 如果面向公众开放，建议加 Cloudflare Turnstile、登录、配额或更严格限流，避免被滥用。
- 法律材料、身份证、劳动仲裁材料等敏感文件，最好优先使用本地版工具。

## 健康检查

```text
GET /healthz
```

返回：

```json
{"status":"ok"}
```

## 测试

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```
