# Troubleshooting

## `gh auth login` connects to `127.0.0.1:443`

If GitHub CLI shows an error like:

```text
dial tcp 127.0.0.1:443: connectex: No connection could be made because the target machine actively refused it.
```

check whether `github.com` is blocked in the Windows hosts file:

```powershell
Resolve-DnsName github.com
Select-String -Path C:\Windows\System32\drivers\etc\hosts -Pattern github
```

If `github.com` resolves to `127.0.0.1`, open Notepad as Administrator and edit:

```text
C:\Windows\System32\drivers\etc\hosts
```

Comment out GitHub-related lines, for example:

```text
# 127.0.0.1 github.com
# 127.0.0.1 api.github.com
# 127.0.0.1 githubusercontent.com
```

Then flush DNS:

```powershell
ipconfig /flushdns
```

Verify:

```powershell
Resolve-DnsName github.com
gh auth login
```

Only remove or comment lines you understand. Keep a backup of the hosts file before changing it.

## `github.com` resolves to `198.18.x.x` but cannot connect

`198.18.x.x` is often a Clash fake-ip range. If `Test-NetConnection github.com -Port 443` fails, open Clash Verge and try one of these:

- turn on System Proxy;
- turn on or restart TUN mode;
- switch DNS/fake-ip mode off if you do not want TUN.

The publish script also tries common local proxy ports such as `7897`, `7898`, and `7899` and sets `HTTP_PROXY` / `HTTPS_PROXY` for the current run when one is found.

## Browser says authorization succeeded, but `gh auth status` still says not logged in

This project uses a local GitHub CLI config directory:

```text
.gh-config
```

The folder is ignored by Git and Docker because it may contain authentication data. Use `login_github_cli.bat` from this project folder so login and publishing read the same config directory.

The helper uses `gh auth login --insecure-storage` so the token can be written into the project-local `.gh-config` directory instead of Windows Credential Manager. Do not commit or share `.gh-config`.

If device login still does not finish locally, use `login_github_with_token.bat`. Create a classic token with `repo`, `read:org`, and `gist` scopes, then paste it only into the local script window.
