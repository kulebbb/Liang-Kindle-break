<#
.SYNOPSIS
  KOReader 装好后，把 authorized_keys 和微信读书插件部署到已连接的 Kindle。
.EXAMPLE
  .\Deploy-KindleExtras.ps1
  .\Deploy-KindleExtras.ps1 -Root "E:\"
#>
param([string]$Root)
$ErrorActionPreference = 'Stop'
$tools = $PSScriptRoot
$downloads = Join-Path (Split-Path -Parent $PSScriptRoot) 'downloads'

function Find-KindleRoot {
    foreach ($v in Get-Volume -ErrorAction SilentlyContinue) {
        if (-not $v.DriveLetter) { continue }
        $r = "$($v.DriveLetter):\"
        if ((Test-Path (Join-Path $r 'documents')) -and (Test-Path (Join-Path $r 'system'))) { return $r }
    }
    return $null
}

if (-not $Root) { $Root = Find-KindleRoot }
if (-not $Root) { throw "没找到 Kindle 盘。确认数据线是数据线、直插电脑、Kindle 已亮屏解锁。" }
$koreader = Join-Path $Root 'koreader'
if (-not (Test-Path $koreader)) { throw "没找到 koreader 目录（$koreader）。请先在 Kindle 上完成 KOReader 安装。" }

$plugins = Join-Path $koreader 'plugins'
New-Item -ItemType Directory -Force -Path $plugins | Out-Null

# 1) 微信读书插件
$wereadZip = Join-Path $downloads 'weread.koplugin-v1.6.0.zip'
$wereadDir = Join-Path $plugins 'weread.koplugin'
if (Test-Path $wereadZip) {
    if (Test-Path $wereadDir) { Remove-Item $wereadDir -Recurse -Force }
    Expand-Archive -Path $wereadZip -DestinationPath $plugins -Force
    if (Test-Path $wereadDir) { Write-Host "✓ 微信读书插件已部署: $wereadDir" -ForegroundColor Green }
    else { Write-Host "! 插件解压后目录名与预期不符，请检查 $plugins" -ForegroundColor Yellow }
} else {
    Write-Host "! 未找到 $wereadZip，跳过插件" -ForegroundColor Yellow
}

# 2) SSH 公钥
$authorized = Join-Path $tools 'authorized_keys'
$sshDir = Join-Path $koreader 'settings\SSH'
if (Test-Path $authorized) {
    New-Item -ItemType Directory -Force -Path $sshDir | Out-Null
    Copy-Item $authorized (Join-Path $sshDir 'authorized_keys') -Force
    Write-Host "✓ SSH 公钥已写入: $sshDir\authorized_keys" -ForegroundColor Green
} else {
    Write-Host "! 未找到 $authorized，跳过密钥（可先运行 Setup-KindleSsh.ps1）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "完成后在 Kindle 上：" -ForegroundColor Cyan
Write-Host "  1) 重启 KOReader（或整机重启）"
Write-Host "  2) 工具 → 微信读书 → 微信扫码登录（需先在微信读书 App 开通 Skill 并获取 API Key）"
Write-Host "  3) 工具 → SSH，确认端口 2222 已启动（如有 autostart 建议打开）"
Write-Host "  4) 回电脑运行 .\Kindle-Push.ps1 -Status 验证"
