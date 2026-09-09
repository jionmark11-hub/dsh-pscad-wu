# publish.ps1 — 作者端首次发布:把本地仓库推到 GitHub
# 用法(在你自己的 PowerShell 里,联网环境):
#   powershell -ExecutionPolicy Bypass -File .\publish.ps1 -RepoUrl https://github.com/<你的用户名>/dah-pscad-wu.git
#
# 前提:
#   1. 已在 github.com 网页上创建好一个【空】仓库(不要勾选 Add README),名字建议 dah-pscad-wu
#   2. push 时若弹出 Git Credential Manager 登录窗,用你的 GitHub 账号登录一次即可
# 说明: 本脚本不存储任何凭据,交给 Windows 凭据管理器(Git Credential Manager)处理。

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl
)

$ErrorActionPreference = 'Stop'
$src = Split-Path -Parent $PSScriptRoot

Write-Host ("repo  : {0}" -f $RepoUrl) -ForegroundColor Cyan
Write-Host ("source: {0}" -f $src) -ForegroundColor Cyan

# 确保 main 分支名
git -C $src branch -M main

# 设置/替换 origin
git -C $src remote remove origin 2>$null | Out-Null
git -C $src remote add origin $RepoUrl

Write-Host '首次推送中(可能需要你在弹窗里登录 GitHub)...' -ForegroundColor Yellow
git -C $src push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'push 失败,请检查仓库地址/网络/登录。' }

Write-Host ''
Write-Host '✔ 发布完成!' -ForegroundColor Green
Write-Host ''
Write-Host '【注意】请手动做一件事: 打开 install.ps1,把顶部 $RepoUrl 里的' -ForegroundColor Yellow
Write-Host '  <YOUR_GITHUB_USER> 改成你的真实用户名,然后再次运行:' -ForegroundColor Yellow
Write-Host ('  powershell -ExecutionPolicy Bypass -File "{0}\install.ps1"  # 仅用于把改动提交' -f $src) -ForegroundColor Yellow
Write-Host '  或直接执行下面两条推送这次修改:' -ForegroundColor Yellow
Write-Host ("  git -C `"{0}`" add install.ps1; git -C `"{0}`" commit -m `"set canonical repo url`"; git -C `"{0}`" push" -f $src) -ForegroundColor Yellow
Write-Host ''
Write-Host '之后其他电脑即可一键安装:' -ForegroundColor Green
Write-Host ("  git clone {0} `"`$HOME\.dsh\.agent-presets\dah-pscad-wu`"" -f $RepoUrl) -ForegroundColor Green
Write-Host ("  或  irm {0}/raw/main/install.ps1 | iex" -f ($RepoUrl -replace '\.git$','')) -ForegroundColor Green
Write-Host ''
