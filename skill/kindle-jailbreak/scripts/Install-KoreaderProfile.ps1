<#
.SYNOPSIS
  为 KOReader 创建「统一版式」Profile，并开启打开文档时自动套用。
  需要先退出 KOReader，让 Kindle 以 USB 存储方式挂载（KOReader 运行时会屏蔽 USB）。
.EXAMPLE
  .\Install-KoreaderProfile.ps1
  .\Install-KoreaderProfile.ps1 -FontSize 24 -LineSpacing 120 -HMargin 10 -TopMargin 50 -BottomMargin 50
#>
param(
    [string]$Root,
    [string]$ProfileName = "统一版式",
    [int]$FontSize = 28,
    [int]$LineSpacing = 115,
    [int]$HMargin = 20,
    [int]$TopMargin = 50,
    [int]$BottomMargin = 50,
    [switch]$Eject
)
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot 'patch_koreader_profile.py'

function Find-KindleRoot {
    foreach ($v in Get-Volume -ErrorAction SilentlyContinue) {
        if (-not $v.DriveLetter) { continue }
        $r = "$($v.DriveLetter):\"
        if ((Test-Path (Join-Path $r 'documents')) -and (Test-Path (Join-Path $r 'system')) -and (Test-Path (Join-Path $r 'koreader'))) { return $r }
    }
    return $null
}

if (-not $Root) { $Root = Find-KindleRoot }
if (-not $Root) { throw '没找到 Kindle USB 盘。请先退出 KOReader，再插数据线。' }
if (-not (Test-Path (Join-Path $Root 'koreader\settings'))) { throw "该盘不像已装 KOReader 的 Kindle: $Root" }

$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$settingsDir = Join-Path $Root 'koreader\settings'
foreach ($p in @((Join-Path $settingsDir 'profiles.lua'), (Join-Path $Root 'koreader\settings.reader.lua'))) {
    if (Test-Path $p) { Copy-Item $p ("$p.bak-$stamp") -Force }
}
Write-Host "已备份原配置（后缀 .bak-$stamp）" -ForegroundColor DarkGray

& python $python $Root $ProfileName $FontSize $LineSpacing $HMargin $TopMargin $BottomMargin
if ($LASTEXITCODE -ne 0) { throw '写入 Profile 失败' }

Write-Host ""
Write-Host "完成。拔线后打开 KOReader，打开任意一本书即自动套用：" -ForegroundColor Green
Write-Host ("  {0}：字号 {1} / 行距 {2}% / 左右边距 {3} / 上下边距 {4}" -f $ProfileName, $FontSize, $LineSpacing, $HMargin, $TopMargin)
Write-Host "如未生效：关掉 profiles_autoexec 里的自动执行后，在 工具 → Profiles 里手动执行一次。" -ForegroundColor DarkGray

if ($Eject) {
    try {
        $shell = New-Object -ComObject Shell.Application
        $vol = $shell.NameSpace(17).ParseName($Root)
        if ($vol) { $vol.InvokeVerb('Eject'); Write-Host '已请求安全弹出。' -ForegroundColor Green }
    } catch { Write-Host '自动弹出失败，请手动弹出。' -ForegroundColor Yellow }
}
