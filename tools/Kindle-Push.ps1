<#
.SYNOPSIS
  通过 KOReader 的 SSH 服务把书推送到 Kindle（Wi-Fi，不用插线）。
.EXAMPLE
  .\Kindle-Push.ps1 -File "D:\books\三体.epub"
  .\Kindle-Push.ps1 -Path "D:\books\*.epub"
  .\Kindle-Push.ps1 -Status
  .\Kindle-Push.ps1 -Discover
#>
param(
    [string]$File,
    [string]$Path,
    [switch]$Status,
    [switch]$Discover
)
$ErrorActionPreference = 'Stop'
$configPath = Join-Path $PSScriptRoot 'kindle-config.json'
$cfg = Get-Content $configPath -Raw -Encoding utf8 | ConvertFrom-Json

function Test-SshPort([string]$ip, [int]$port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $ar = $client.BeginConnect($ip, $port, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(400)) { return $false }
        $client.EndConnect($ar)
        return $client.Connected
    } catch { return $false } finally { $client.Close() }
}

function Find-KindleIp {
    $arp = (arp -a) | Out-String
    $cands = [regex]::Matches($arp, '(\d+\.\d+\.\d+\.\d+)\s+[0-9a-fA-F-]{17}\s+dynamic') | ForEach-Object { $_.Groups[1].Value }
    foreach ($ip in $cands) { if (Test-SshPort $ip ([int]$cfg.ssh_port)) { return $ip } }
    return $null
}

function Save-Config { $cfg | ConvertTo-Json | Set-Content $configPath -Encoding utf8 }

function Get-SshArgs {
    $a = @('-p', "$($cfg.ssh_port)", '-o', 'StrictHostKeyChecking=accept-new', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=6')
    if ($cfg.ssh_key -and (Test-Path $cfg.ssh_key)) { $a += @('-i', $cfg.ssh_key, '-o', 'IdentitiesOnly=yes') }
    return $a
}

if ($Discover) {
    $ip = Find-KindleIp
    if ($ip) { $cfg.kindle_ip = $ip; Save-Config; Write-Host "发现 Kindle: $ip" -ForegroundColor Green }
    else { Write-Host "没找到开启 SSH 的 Kindle（先在 KOReader 里启动 SSH 服务，端口 2222）" -ForegroundColor Yellow }
    exit
}

if ($Status) {
    if (-not $cfg.kindle_ip) { $cfg.kindle_ip = Find-KindleIp }
    if (-not $cfg.kindle_ip) { Write-Host "尚未配置/发现 Kindle IP。先在 KOReader 里启动 SSH 服务，再运行 -Discover。" -ForegroundColor Yellow; exit 1 }
    $ok = Test-SshPort $cfg.kindle_ip ([int]$cfg.ssh_port)
    Write-Host ("Kindle {0}:{1} -> {2}" -f $cfg.kindle_ip, $cfg.ssh_port, $(if ($ok) { 'SSH 在线' } else { '离线' })) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
    if ($ok -and -not $cfg.kindle_ip) { Save-Config }
    exit $(if ($ok) { 0 } else { 1 })
}

if (-not $cfg.kindle_ip) {
    $cfg.kindle_ip = Find-KindleIp
    if (-not $cfg.kindle_ip) { throw "未配置 Kindle IP 且自动发现失败。先在 Kindle 上打开 KOReader → 工具 → SSH 服务。" }
    Save-Config
}

$files = @()
if ($File) { $files += (Resolve-Path $File).Path }
if ($Path) { $files += (Get-ChildItem $Path -File | Select-Object -ExpandProperty FullName) }
if (-not $files) { throw "用法: .\Kindle-Push.ps1 -File 某本书.epub 或 -Path 'D:\books\*.epub'" }

Write-Host ("推送 {0} 个文件到 Kindle {1} …" -f $files.Count, $cfg.kindle_ip) -ForegroundColor Cyan
$sshArgs = Get-SshArgs
& ssh @sshArgs "$($cfg.ssh_user)@$($cfg.kindle_ip)" ("mkdir -p " + $cfg.remote_dir) 2>$null | Out-Null

$scpArgs = @('-P', "$($cfg.ssh_port)") + ($sshArgs | Where-Object { $_ -ne '-p' }) + @('-r') + $files + @("$($cfg.ssh_user)@$($cfg.kindle_ip):$($cfg.remote_dir.TrimEnd('/'))/")
& scp @scpArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "scp 失败，重试 legacy 模式 (-O) …" -ForegroundColor Yellow
    $scpArgs = @('-O') + $scpArgs
    & scp @scpArgs
}
if ($LASTEXITCODE -eq 0) { Write-Host "完成。Kindle 的 KOReader 文件浏览器里刷新即可看到。" -ForegroundColor Green }
else { Write-Host "推送失败：确认 Kindle 亮屏、KOReader 的 SSH 服务已启动、与电脑同一 Wi-Fi。" -ForegroundColor Red }
