<#
.SYNOPSIS
  识别已连接的 Kindle：USB 存储模式，或局域网中开启了 SSH 的 Kindle（KOReader）。
.EXAMPLE
  .\Find-Kindle.ps1
#>
Write-Host "=== 1) USB 存储检查 ===" -ForegroundColor Cyan
$found = $false
foreach ($v in Get-Volume -ErrorAction SilentlyContinue) {
    if (-not $v.DriveLetter) { continue }
    $root = "$($v.DriveLetter):\"
    if ((Test-Path (Join-Path $root 'documents')) -and (Test-Path (Join-Path $root 'system'))) {
        $found = $true
        Write-Host ("Kindle 已连接：{0}  标签={1}" -f $root, $v.FileSystemLabel) -ForegroundColor Green
        Write-Host "根目录："
        Get-ChildItem $root -Force -ErrorAction SilentlyContinue | Select-Object -First 20 Mode, Name | Format-Table -AutoSize
        Write-Host "固件版本（system\version.txt）：" -ForegroundColor Cyan
        if (Test-Path (Join-Path $root 'system\version.txt')) { Get-Content (Join-Path $root 'system\version.txt') }
    }
}
if (-not $found) {
    Write-Host "未发现 Kindle 盘。常见原因：" -ForegroundColor Yellow
    Write-Host "  - 用了只在充电的 micro-USB 线（必须用数据线）"
    Write-Host "  - 插在扩展坞/充电口/坏 USB 口上，改直插笔记本"
    Write-Host "  - Kindle 未解锁或电量过低"
}

Write-Host "=== 2) 局域网扫描（KOReader SSH 默认端口 2222）===" -ForegroundColor Cyan
$arpText = (arp -a) | Out-String
$cands = [regex]::Matches($arpText, '(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})\s+dynamic') | ForEach-Object {
    [pscustomobject]@{ IP = $_.Groups[1].Value; MAC = $_.Groups[2].Value }
}
if (-not $cands) { Write-Host "ARP 表为空，先让设备连一次网络。"; exit }

$hits = 0
foreach ($c in $cands) {
    foreach ($port in 2222, 22, 8080) {
        $open = $false
        try {
            $tc = New-Object System.Net.Sockets.TcpClient
            $ar = $tc.BeginConnect($c.IP, $port, $null, $null)
            $open = $ar.AsyncWaitHandle.WaitOne(250) -and $tc.Connected
            if ($open) { $tc.EndConnect($ar) }
            $tc.Close()
        } catch { $open = $false }
        if ($open) {
            $hits++
            $tag = if ($port -eq 2222) { 'KOReader SSH' } elseif ($port -eq 22) { 'SSH' } else { 'HTTP' }
            Write-Host ("  {0}  端口 {1} 开放 ({2})  MAC={3}" -f $c.IP, $port, $tag, $c.MAC) -ForegroundColor Green
        }
    }
}
if ($hits -eq 0) { Write-Host "  没有发现开放端口的设备（Kindle 需亮屏并运行 KOReader、SSH 已启动）。" -ForegroundColor Yellow }
Write-Host "  认出 Kindle IP 后，可运行: .\Kindle-Push.ps1 -Discover"
