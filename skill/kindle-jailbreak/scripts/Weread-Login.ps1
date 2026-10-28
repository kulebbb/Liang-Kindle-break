<#
.SYNOPSIS
  微信读书登录绕行方案：浏览器扫码登录 → 自动提取 Cookie → 写入 Kindle 的 weread.lua。
  背景：微信读书 2026-10 改接口后插件扫码登录必报 401（上游 issue #214）。
.EXAMPLE
  .\Weread-Login.ps1
#>
param(
    [string]$ApiKey,
    [string]$KindleIp,
    [int]$Port = 9223,
    [int]$WaitSeconds = 300
)
$ErrorActionPreference = 'Stop'
$configPath = Join-Path $PSScriptRoot 'kindle-config.json'
$cfg = Get-Content $configPath -Raw -Encoding utf8 | ConvertFrom-Json
$keyFile = (Join-Path $env:LOCALAPPDATA 'KindleBookdrop\kindle_ed25519')
if (-not (Test-Path $keyFile)) { $keyFile = $cfg.ssh_key }
if (-not $ApiKey) { $ApiKey = $cfg.weread_api_key }
if (-not $ApiKey) { $ApiKey = Read-Host '请粘贴微信读书 Skill API Key（wrk- 开头）' }
$ApiKey = $ApiKey.Trim()

function Test-Port([string]$ip, [int]$port) {
    $tc = New-Object System.Net.Sockets.TcpClient
    try {
        $ar = $tc.BeginConnect($ip, $port, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(400)) { return $false }
        $tc.EndConnect($ar)
        return $tc.Connected
    } catch { return $false } finally { $tc.Close() }
}

if (-not $KindleIp) { $KindleIp = $cfg.kindle_ip }
if (-not $KindleIp -or -not (Test-Port $KindleIp ([int]$cfg.ssh_port))) {
    $KindleIp = $null
    $arp = (arp -a) | Out-String
    foreach ($ip in ([regex]::Matches($arp, '(\d+\.\d+\.\d+\.\d+)\s+[0-9a-fA-F-]{17}\s+dynamic') | ForEach-Object { $_.Groups[1].Value })) {
        if (Test-Port $ip ([int]$cfg.ssh_port)) { $KindleIp = $ip; break }
    }
}
if (-not $KindleIp) { throw '找不到开启 SSH 的 Kindle。请先在 KOReader 里启动 SSH 服务。' }
Write-Output ("Kindle SSH: {0}:{1}" -f $KindleIp, $cfg.ssh_port)

$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path $edge)) { $edge = 'C:\Program Files\Microsoft\Edge\Application\msedge.exe' }
if (-not (Test-Path $edge)) { $edge = 'C:\Program Files\Google\Chrome\Application\chrome.exe' }
if (-not (Test-Path $edge)) { throw '没找到 Edge/Chrome 浏览器' }

$tmp = Join-Path $env:TEMP ('weread-login-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$cookiesFile = Join-Path $tmp 'cookies.json'
$profile = Join-Path $env:TEMP ('weread-profile-' + [guid]::NewGuid().ToString('N').Substring(0, 8))

Write-Output ''
Write-Output '>>> 浏览器窗口即将打开，请用手机微信扫码登录 https://weread.qq.com <<<'
Start-Process -FilePath $edge -ArgumentList ("--user-data-dir=$profile", "--remote-debugging-port=$Port", '--no-first-run', '--no-default-browser-check', '--new-window', 'https://weread.qq.com') | Out-Null

try {
    & python (Join-Path $PSScriptRoot 'cdp_cookies.py') --port $Port --timeout $WaitSeconds --out $cookiesFile | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $cookiesFile)) { throw '等待扫码超时或读取 Cookie 失败' }
} finally {
    Get-CimInstance Win32_Process -Filter "Name='msedge.exe' OR Name='chrome.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$profile*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}

$json = Get-Content $cookiesFile -Raw -Encoding utf8 | ConvertFrom-Json
$cookies = $json.cookies
if (-not $cookies.wr_vid -or -not ($cookies.wr_skey -or $cookies.wr_gid)) { throw '没有拿到有效登录 Cookie' }
Write-Output ('已获取 Cookie: ' + (($cookies.PSObject.Properties | ForEach-Object { $_.Name }) -join ', '))

$localSettings = Join-Path $tmp 'weread.lua'
& scp -P $cfg.ssh_port -i $keyFile -o BatchMode=yes -o StrictHostKeyChecking=accept-new "root@${KindleIp}:/mnt/us/koreader/settings/weread.lua" $localSettings 2>&1 | Out-Null
if (-not (Test-Path $localSettings)) { throw '下载 Kindle 上的 weread.lua 失败' }

$patched = Join-Path $tmp 'weread.patched.lua'
& python (Join-Path $PSScriptRoot 'patch_weread_settings.py') $localSettings $ApiKey $cookiesFile $patched | Out-Null
if (-not (Test-Path $patched)) { throw '生成配置失败' }

& scp -P $cfg.ssh_port -i $keyFile -o BatchMode=yes $patched "root@${KindleIp}:/mnt/us/koreader/settings/weread.lua" 2>&1 | Out-Null
& ssh -p $cfg.ssh_port -i $keyFile -o BatchMode=yes "root@$KindleIp" "chmod 777 /mnt/us/koreader/settings/weread.lua; grep -E 'api_key|wr_vid|wr_gid|wr_skey' /mnt/us/koreader/settings/weread.lua" 2>&1 | ForEach-Object { $_ -replace '(= ").{8,}(")', '$1******$2' }

Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Output ''
Write-Output 'OK: 配置已写入 Kindle。请退出 KOReader 并重新打开，然后 工具 → 微信读书 → 书架。'
