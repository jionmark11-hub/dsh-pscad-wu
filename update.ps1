# update.ps1 — dah-PSCAD-WU 更新脚本(已安装过的机器)
# 用法: powershell -ExecutionPolicy Bypass -File .\update.ps1
# 等效: git -C "$HOME\.dsh\.agent-presets\dah-pscad-wu" pull

[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $HOME '.dsh\.agent-presets')
)

$ErrorActionPreference = 'Stop'
$dst = Join-Path $InstallRoot 'dah-pscad-wu'

if (-not (Test-Path (Join-Path $dst '.git'))) {
    throw "未找到已安装的插件仓库: $dst`n若尚未安装请先运行 install.ps1。"
}

Write-Host '正在拉取更新...' -ForegroundColor Yellow
git -C $dst pull
if ($LASTEXITCODE -ne 0) { throw 'git pull 失败。' }

Write-Host ''
Write-Host '✔ 更新完成。重启 DSH 后,新会话选择 dah-PSCAD-WU 即使用最新技能。' -ForegroundColor Green
Write-Host '(提示: 只改了 skills 时,可顺带让 agent.cordis.yml 产生一次修改,新会话才会换到新组装;直接重启 DSH 最稳妥)' -ForegroundColor DarkGray
