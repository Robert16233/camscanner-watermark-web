# 部署清单

## 最小可上线版本

- Dockerfile 构建通过。
- `/healthz` 返回 `{"status":"ok"}`。
- 上传 PDF 后能下载处理结果。
- 平台已开启 HTTPS。
- 页面包含授权使用提示。

## Fly.io 示例

```bash
copy fly.toml.example fly.toml
fly launch
fly deploy
```

如果平台询问端口，填：

```text
8000
```

## Railway / Render 示例

选择从 GitHub 仓库部署，构建方式选择 Dockerfile。Render 也可以使用仓库内的 `render.yaml` 创建 Blueprint。环境变量按需要配置：

```text
MAX_UPLOAD_BYTES=52428800
MAX_FILES=10
RATE_LIMIT_PER_MINUTE=20
```

## VPS 示例

```bash
docker build -t camscanner-watermark-web .
docker run -d --name camscanner-watermark-web --restart unless-stopped -p 8000:8000 camscanner-watermark-web
```

或者：

```bash
docker compose up -d --build
```

然后用 Nginx 或 Caddy 反向代理到 `127.0.0.1:8000`，并配置 HTTPS。

## 上线前建议

- 开启访问日志脱敏，不记录上传文件名。
- 配置服务器磁盘空间监控。
- 反向代理层增加请求体大小限制。
- 面向公众时加入验证码或账号配额。

## 建议的上线顺序

1. 先部署到 Render 或 Railway 的免费/低配环境，验证上传和下载。
2. 绑定一个测试子域名，例如 `pdf.example.com`。
3. 加上 `PRIVACY.md` 中的隐私说明页面或页脚链接。
4. 等使用量稳定后，再迁移到 VPS 或 Fly.io 并加验证码/登录。
