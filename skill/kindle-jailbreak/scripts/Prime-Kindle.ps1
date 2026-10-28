<#
.SYNOPSIS
  把 WinterBreak2 越狱文件拷到已连接的 Kindle 根目录（自动找盘、解压、校验）。
.EXAMPLE
  .\Prime-Kindle.ps1
  .\Prime-Kindle.ps1 -Root "E:\"   # 手动指定 Kindle 盘符
#>
param(
    [string]$Root,
    [switch]$Eject
)
$ErrorActionPreference = 'Stop'
$zip = Join-Path (Split-Path -Parent $PSScriptRoot) 'downloads\wb2.zip'
if (-not (Test-Path $zip)) { throw "找不到越狱包: $zip" }

function Find-KindleRoot {
    foreach ($v in Get-Volume -ErrorAction SilentlyContinue) {
        if (-not $v.DriveLetter) { continue }
        $r = "$($v.DriveLetter):\"
        if ((Test-Path (Join-Path $r 'documents')) -and (Test-Path (Join-Path $r 'system'))) { return $r }
    }
    return $null
}

if (-not $Root) {
    $Root = Find-KindleRoot
    if (-not $Root) { throw "没找到 Kindle 盘。请检查：数据线是否为数据线、是否直插电脑、Kindle 是否亮屏解锁。" }
}
if (-not (Test-Path $Root)) { throw "路径不存在: $Root" }

Write-Host "目标 Kindle 根目录: $Root" -ForegroundColor Cyan
if (Test-Path (Join-Path $Root 'system\version.txt')) {
    Write-Host ("固件版本: " + ((Get-Content (Join-Path $Root 'system\version.txt') -Raw).Trim()))
}
if (Test-Path (Join-Path $Root 'winterbreak2')) {
    Write-Host "检测到已存在 winterbreak2（将覆盖更新）" -ForegroundColor Yellow
}

Write-Host "解压 wb2.zip 到 Kindle 根目录 …"
Expand-Archive -Path $zip -DestinationPath $Root -Force
$payload = Join-Path $Root 'winterbreak2\dialoger.html'
if (-not (Test-Path $payload)) { throw "解压后未找到 winterbreak2\dialoger.html，请检查压缩包。" }
Write-Host "已就绪: $payload" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "  1) 安全弹出 Kindle（拔线）"
Write-Host "  2) Kindle 连 Wi-Fi，打开 实验性浏览器，访问 https://penguins184.xyz/wb2"
Write-Host "  3) 点 Jailbreak，等待完成"
Write-Host ""

if ($Eject) {
    try {
        $shell = New-Object -ComObject Shell.Application
        $volume = $shell.NameSpace(17).ParseName($Root)
        if ($volume) { $volume.InvokeVerb('Eject'); Write-Host "已请求弹出。" -ForegroundColor Green }
    } catch { Write-Host "自动弹出失败，请手动安全弹出。" -ForegroundColor Yellow }
}

