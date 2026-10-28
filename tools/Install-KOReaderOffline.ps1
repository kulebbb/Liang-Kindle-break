<#
.SYNOPSIS
  离线安装 KOReader（USB 手动方式，不依赖 KPM 联网下载）。
  把官方 koreader-kindlepw2 包解压到 Kindle 根目录，并创建可点击的 KOReader 启动条目（scriptlet）。
.EXAMPLE
  .\Install-KOReaderOffline.ps1
  .\Install-KOReaderOffline.ps1 -Root "E:\"
#>
param([string]$Root, [switch]$Eject)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$pkgDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'downloads'
$zip = Join-Path $pkgDir 'koreader-kindlepw2-v2026.07.1.zip'
if (-not (Test-Path $zip)) { throw "找不到离线包: $zip" }

function Find-KindleRoot {
    foreach ($v in Get-Volume -ErrorAction SilentlyContinue) {
        if (-not $v.DriveLetter) { continue }
        $r = "$($v.DriveLetter):\"
        if ((Test-Path (Join-Path $r 'documents')) -and (Test-Path (Join-Path $r 'system'))) { return $r }
    }
    return $null
}

if (-not $Root) { $Root = Find-KindleRoot }
if (-not $Root) { throw "没找到 Kindle 盘。请插数据线并解锁 Kindle。" }
if (-not (Test-Path $Root)) { throw "路径不存在: $Root" }
Write-Host "目标 Kindle: $Root" -ForegroundColor Cyan

# 清理可能残留的旧 KOReader（包括 KPM 下载到一半留下的）
foreach ($p in @((Join-Path $Root 'koreader'), (Join-Path $Root 'extensions\koreader'))) {
    if (Test-Path $p) {
        Write-Host "清理旧目录: $p" -ForegroundColor DarkGray
        Remove-Item -LiteralPath $p -Recurse -Force
    }
}

Write-Host "解压 KOReader 到 Kindle（约 40MB，需要一会儿）..." -ForegroundColor Cyan
[System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $Root)

if (-not (Test-Path (Join-Path $Root 'koreader\koreader.sh'))) { throw "解压校验失败：koreader\koreader.sh 不存在" }
if (-not (Test-Path (Join-Path $Root 'extensions\koreader\config.xml'))) { throw "解压校验失败：extensions\koreader\config.xml 不存在" }

# 创建 scriptlet：Kindle 书库里会出现一本叫 KOReader 的书，点开即启动
$scriptlet = "#!/bin/sh`n# Name: KOReader`n# Author: Bookdrop`n/mnt/us/koreader/koreader.sh`n"
$target = Join-Path $Root 'documents\KOReader.sh'
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($target, $scriptlet, $utf8)
Write-Host "已创建启动条目: $target" -ForegroundColor Green

Write-Host ""
Write-Host "完成。下一步：" -ForegroundColor Cyan
Write-Host "  1) 安全弹出 Kindle，拔线"
Write-Host "  2) 在 Kindle 书库（筛选'全部'/'文档'）里找到名为 KOReader 的条目，点击启动"
Write-Host "  3) 首次启动若提示语言/引导，按提示选择即可"
Write-Host ""

if ($Eject) {
    try {
        $shell = New-Object -ComObject Shell.Application
        $vol = $shell.NameSpace(17).ParseName($Root)
        if ($vol) { $vol.InvokeVerb('Eject'); Write-Host "已请求安全弹出。" -ForegroundColor Green }
    } catch { Write-Host "自动弹出失败，请手动安全弹出。" -ForegroundColor Yellow }
}
