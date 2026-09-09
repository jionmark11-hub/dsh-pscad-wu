# install.ps1 — DSH-PSCAD-WU 一键安装/更新脚本
# 用法(在任意装有 Git 的 Windows 电脑的 PowerShell 里):
#   irm https://raw.githubusercontent.com/<YOUR_GITHUB_USER>/dsh-pscad-wu/main/install.ps1 | iex
# 或本地:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# 行为: 没装过 -> 克隆到 <dshHome>\.agent-presets\dsh-pscad-wu
#        已装过(git 仓库) -> 拉取更新
#        目录存在但不是 git 仓库 -> 报错, 提示加 -Force 覆盖
# 参数: -InstallRoot 覆盖安装根目录(默认 $HOME\.dsh\.agent-presets)
#       -Force        覆盖重装(删除旧目录后重新克隆)

[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $HOME '.dsh\.agent-presets'),
    [switch]$Force
)

# ===== 仓库地址(创建 GitHub 仓库后改成你自己的,再 push 一次即可) =====
$RepoUrl = 'https://github.com/jionmark11-hub/dsh-pscad-wu.git'
# ========================================================================

$ErrorActionPreference = 'Stop'
$dst = Join-Path $InstallRoot 'dsh-pscad-wu'

Write-Host ''
Write-Host '== DSH-PSCAD-WU installer ==' -ForegroundColor Cyan
Write-Host ("   repo : {0}" -f $RepoUrl)
Write-Host ("   dest : {0}" -f $dst)
Write-Host ''

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw '未检测到 Git,请先安装: winget install Git.Git  或 https://git-scm.com/download/win'
}

# 确保安装根目录存在(git clone 不会创建父目录)
New-Item -ItemType Directory -Force $InstallRoot | Out-Null

if (Test-Path $dst) {
    if (Test-Path (Join-Path $dst '.git')) {
        if ($Force) {
            Write-Host '目录已存在且为 git 仓库,-Force:删除后重新克隆...' -ForegroundColor Yellow
            Remove-Item -Recurse -Force $dst
        } else {
            Write-Host '目录已存在且为 git 仓库 -> 执行 git pull 更新...' -ForegroundColor Yellow
            git -C $dst pull
            Write-Host ''
            Write-Host ('✔ 更新完成: {0}' -f $dst) -ForegroundColor Green
            Write-Host '重启 DSH 后,新会话选择 DSH-PSCAD-WU 即使用最新技能。' -ForegroundColor Green
            exit 0
        }
    } else {
        if ($Force) {
            Write-Host '目录已存在但不是 git 仓库,-Force:删除后重新克隆...' -ForegroundColor Yellow
            Remove-Item -Recurse -Force $dst
        } else {
            throw ("目录已存在但不是 git 仓库: {0}`n它不是本插件(或安装方式不同)。确认后加 -Force 覆盖。" -f $dst)
        }
    }
}

Write-Host '正在克隆...' -ForegroundColor Yellow
git clone $RepoUrl $dst
if ($LASTEXITCODE -ne 0) { throw 'git clone 失败,请检查仓库地址与网络。' }

Write-Host ''
Write-Host ('✔ 安装完成: {0}' -f $dst) -ForegroundColor Green
Write-Host '下一步: 重启 DSH -> 新建会话 -> 预设选择器选 DSH-PSCAD-WU。' -ForegroundColor Green
Write-Host ''
