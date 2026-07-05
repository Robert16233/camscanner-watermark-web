from __future__ import annotations

import io
import os
import tempfile
import time
import zipfile
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from app.watermark import remove_camscanner_watermark


MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
MAX_FILES = int(os.getenv("MAX_FILES", "10"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
OUTPUT_SUFFIX = "_去水印"

app = FastAPI(
    title="CamScanner Watermark Remover",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

_requests_by_ip: dict[str, deque[float]] = defaultdict(deque)


PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>扫描全能王 PDF 去水印</title>
  <style>
    :root {
      --ink: #172033;
      --muted: #667085;
      --line: #d8dee8;
      --panel: #fff;
      --bg: #f5f7fa;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --danger: #b42318;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 28px;
    }
    main {
      width: min(780px, 100%);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 28px;
      box-shadow: 0 20px 60px rgba(23, 32, 51, .08);
    }
    h1 {
      margin: 0 0 8px;
      font-size: 25px;
      line-height: 1.25;
      letter-spacing: 0;
    }
    .lead {
      margin: 0 0 22px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.7;
    }
    .drop {
      min-height: 220px;
      border: 2px dashed var(--line);
      border-radius: 8px;
      background: #fbfcfe;
      display: grid;
      place-items: center;
      padding: 24px;
      text-align: center;
      transition: background .15s, border-color .15s;
      cursor: pointer;
    }
    .drop.drag {
      background: #eefaf8;
      border-color: var(--accent);
    }
    .drop strong {
      display: block;
      font-size: 18px;
      margin-bottom: 8px;
    }
    .drop span {
      display: block;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
      word-break: break-word;
    }
    .actions {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-top: 16px;
      flex-wrap: wrap;
    }
    button {
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      padding: 12px 20px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
    }
    button:hover { background: var(--accent-strong); }
    button:disabled { opacity: .65; cursor: wait; }
    .status {
      min-height: 24px;
      color: var(--accent-strong);
      font-size: 14px;
      font-weight: 700;
    }
    .status.error { color: var(--danger); }
    .meta {
      margin: 16px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.7;
    }
    .links {
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      margin-top: 12px;
      font-size: 13px;
    }
    .links a {
      color: var(--accent-strong);
      text-decoration: none;
      font-weight: 700;
    }
    .links a:hover { text-decoration: underline; }
    @media (max-width: 560px) {
      body { padding: 16px; align-items: stretch; }
      main { padding: 20px; }
      h1 { font-size: 21px; }
      .drop { min-height: 170px; }
      button { width: 100%; }
      .actions { align-items: stretch; }
    }
  </style>
</head>
<body>
  <main>
    <h1>扫描全能王 PDF 去水印</h1>
    <p class="lead">选择 PDF 后自动返回处理结果。文件只在服务器临时目录中处理，响应结束后删除。</p>
    <form id="form">
      <label class="drop" id="drop">
        <input id="files" name="files" type="file" accept="application/pdf,.pdf" multiple hidden>
        <div>
          <strong>拖入 PDF，或点击选择文件</strong>
          <span id="fileText">最多 10 个文件，单次总大小上限 50 MB</span>
        </div>
      </label>
      <div class="actions">
        <button id="submit" type="submit">开始处理</button>
        <div class="status" id="status"></div>
      </div>
      <p class="meta">请只处理你本人拥有权利或获得授权处理的 PDF。当前版本针对右下角“扫描全能王”独立图片水印。</p>
      <nav class="links" aria-label="站点说明">
        <a href="/privacy" target="_blank">隐私说明</a>
        <a href="/terms" target="_blank">使用条款</a>
        <a href="/security" target="_blank">安全建议</a>
      </nav>
    </form>
  </main>
  <script>
    const form = document.querySelector('#form');
    const drop = document.querySelector('#drop');
    const files = document.querySelector('#files');
    const submit = document.querySelector('#submit');
    const statusBox = document.querySelector('#status');
    const fileText = document.querySelector('#fileText');

    function setStatus(text, isError = false) {
      statusBox.textContent = text;
      statusBox.classList.toggle('error', isError);
    }

    function updateFileText() {
      const selected = Array.from(files.files || []);
      fileText.textContent = selected.length
        ? selected.map(file => file.name).join('、')
        : '最多 10 个文件，单次总大小上限 50 MB';
    }

    function downloadBlob(blob, filename) {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || 'cleaned.pdf';
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }

    drop.addEventListener('dragover', event => {
      event.preventDefault();
      drop.classList.add('drag');
    });
    drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
    drop.addEventListener('drop', event => {
      event.preventDefault();
      drop.classList.remove('drag');
      files.files = event.dataTransfer.files;
      updateFileText();
    });
    files.addEventListener('change', updateFileText);

    form.addEventListener('submit', async event => {
      event.preventDefault();
      const selected = Array.from(files.files || []);
      if (!selected.length) {
        setStatus('请先选择 PDF。', true);
        return;
      }
      const data = new FormData();
      selected.forEach(file => data.append('files', file));
      submit.disabled = true;
      setStatus('正在处理...');
      try {
        const response = await fetch('/api/remove', { method: 'POST', body: data });
        if (!response.ok) {
          let message = '处理失败。';
          try {
            const payload = await response.json();
            message = payload.detail || message;
          } catch (_) {}
          throw new Error(message);
        }
        const blob = await response.blob();
        const filename = response.headers.get('x-download-filename') || 'cleaned.pdf';
        downloadBlob(blob, decodeURIComponent(filename));
        setStatus('处理完成，下载已开始。');
      } catch (error) {
        setStatus(error.message || '处理失败。', true);
      } finally {
        submit.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


INFO_STYLE = """
<style>
  body {
    margin: 0;
    background: #f5f7fa;
    color: #172033;
    font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    line-height: 1.75;
    padding: 28px;
  }
  main {
    max-width: 820px;
    margin: 0 auto;
    background: #fff;
    border: 1px solid #d8dee8;
    border-radius: 8px;
    padding: 28px;
  }
  h1 { margin-top: 0; font-size: 24px; letter-spacing: 0; }
  h2 { font-size: 18px; margin-top: 24px; }
  a { color: #115e59; font-weight: 700; }
  li { margin: 6px 0; }
</style>
"""


def info_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  {INFO_STYLE}
</head>
<body>
  <main>
    <h1>{title}</h1>
    {body}
    <p><a href="/">返回首页</a></p>
  </main>
</body>
</html>
"""


@app.middleware("http")
async def request_guard(request: Request, call_next):
    if request.url.path == "/api/remove":
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = _requests_by_ip[client_ip]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse({"detail": "请求过于频繁，请稍后再试。"}, status_code=429)
        bucket.append(now)

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_UPLOAD_BYTES:
            return JSONResponse({"detail": "单次上传总大小超过限制。"}, status_code=413)
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return PAGE


@app.get("/privacy", response_class=HTMLResponse)
async def privacy() -> str:
    return info_page(
        "隐私说明",
        """
        <p>本服务用于处理 PDF 中右下角“扫描全能王”独立图片水印。</p>
        <h2>文件处理</h2>
        <ul>
          <li>上传文件只用于本次去水印处理。</li>
          <li>文件保存在服务器临时目录中。</li>
          <li>处理完成并返回结果后，临时目录会自动删除。</li>
          <li>默认不保存原 PDF、处理后的 PDF 或上传文件名。</li>
        </ul>
        <h2>敏感文件</h2>
        <p>身份证、诉讼材料、合同、病历、工资流水等敏感文件，建议优先使用本地版工具处理。</p>
        """,
    )


@app.get("/terms", response_class=HTMLResponse)
async def terms() -> str:
    return info_page(
        "使用条款",
        """
        <ul>
          <li>你应仅上传本人拥有权利或已获得授权处理的 PDF 文件。</li>
          <li>请勿使用本服务处理违法、侵权或未经授权的文件。</li>
          <li>当前版本只针对右下角“扫描全能王”独立图片水印，不保证适用于所有 PDF。</li>
          <li>公开部署时，站点运营者应根据当地法律完善正式条款和隐私政策。</li>
        </ul>
        """,
    )


@app.get("/security", response_class=HTMLResponse)
async def security() -> str:
    return info_page(
        "安全建议",
        """
        <ul>
          <li>公开上线前请启用 HTTPS。</li>
          <li>建议增加验证码、登录或额度限制，防止批量滥用。</li>
          <li>反向代理层应限制请求体大小。</li>
          <li>不要把临时目录挂载到持久磁盘。</li>
          <li>不要在访问日志中记录上传文件名或文档元数据。</li>
        </ul>
        """,
    )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


def _safe_filename(name: str) -> str:
    cleaned = Path(name).name.replace("\x00", "").strip()
    return cleaned or "upload.pdf"


def _download_name(source_name: str) -> str:
    path = Path(_safe_filename(source_name))
    return f"{path.stem}{OUTPUT_SUFFIX}.pdf"


async def _read_upload(upload: UploadFile) -> bytes:
    name = _safe_filename(upload.filename or "")
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"{name} 不是 PDF 文件。")
    data = await upload.read()
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail=f"{name} 不是有效 PDF。")
    return data


def _content_disposition(filename: str) -> str:
    return f"attachment; filename=cleaned.pdf; filename*=UTF-8''{quote(filename)}"


@app.post("/api/remove")
async def remove(files: list[UploadFile] = File(...)) -> Response:
    if not files:
        raise HTTPException(status_code=400, detail="请上传 PDF 文件。")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"最多一次上传 {MAX_FILES} 个文件。")

    uploads: list[tuple[str, bytes]] = []
    total_size = 0
    for upload in files:
        data = await _read_upload(upload)
        total_size += len(data)
        if total_size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="单次上传总大小超过限制。")
        uploads.append((_safe_filename(upload.filename or "upload.pdf"), data))

    with tempfile.TemporaryDirectory(prefix="camscanner-watermark-") as tmp:
        tmp_dir = Path(tmp)
        outputs: list[tuple[str, bytes, int]] = []
        for index, (filename, data) in enumerate(uploads, 1):
            source = tmp_dir / f"source-{index}.pdf"
            destination = tmp_dir / f"clean-{index}.pdf"
            source.write_bytes(data)
            removed = remove_camscanner_watermark(source, destination)
            outputs.append((_download_name(filename), destination.read_bytes(), removed))

    if len(outputs) == 1:
        filename, payload, removed = outputs[0]
        return Response(
            content=payload,
            media_type="application/pdf",
            headers={
                "Content-Disposition": _content_disposition(filename),
                "X-Download-Filename": quote(filename),
                "X-Removed-Watermarks": str(removed),
            },
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        report_lines = []
        for filename, payload, removed in outputs:
            archive.writestr(filename, payload)
            report_lines.append(f"{filename}: removed {removed} watermark draw operations")
        archive.writestr("report.txt", "\n".join(report_lines) + "\n")

    zip_name = "去水印PDF.zip"
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=cleaned.zip; filename*=UTF-8''{quote(zip_name)}",
            "X-Download-Filename": quote(zip_name),
        },
    )
