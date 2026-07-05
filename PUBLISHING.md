# GitHub 发布步骤

## 1. 新建 GitHub 仓库

建议仓库名：

```text
camscanner-watermark-web
```

## 2. 推送代码

在本项目目录中运行：

```bash
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/camscanner-watermark-web.git
git push -u origin main
```

把 `YOUR_GITHUB_USERNAME` 换成你的 GitHub 用户名或组织名。

Windows 上也可以直接双击：

```text
publish_to_github.bat
```

脚本会检查 `gh` 登录状态；如果尚未登录，会先启动 `gh auth login`。

如果想分两步做，也可以先双击：

```text
login_github_cli.bat
```

登录成功后再双击 `publish_to_github.bat`。

如果浏览器设备码登录一直显示网页成功但本地 `gh` 不保存 token，可以改用 token 登录：

```text
login_github_with_token.bat
```

创建 classic token 时勾选 `repo`、`read:org`、`gist` 权限。不要把 token 粘贴到聊天里。

如果 `gh auth login` 报错连接 `127.0.0.1:443`，说明本机 hosts 可能屏蔽了 GitHub。处理方法见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

## 3. 修正 README 徽章

打开 `README.md`，把：

```text
YOUR_GITHUB_USERNAME
```

替换成你的 GitHub 用户名或组织名。

## 4. 创建第一个 Release

Tag:

```text
v1.0.0
```

Release title:

```text
v1.0.0 - Initial release
```

Release notes 可使用 `CHANGELOG.md` 中的 1.0.0 内容。

## 5. 部署

优先选择 Render 或 Railway 验证公开访问，再按需要迁移到 VPS 或 Fly.io。
