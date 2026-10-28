<#
.SYNOPSIS
  生成 Bookdrop 使用的 SSH 密钥（放在 NTFS 盘并收紧权限），并更新 Kindle 推送配置。
.EXAMPLE
  .\Setup-KindleSsh.ps1
#>
$ErrorActionPreference = 'Stop'
$configPath = Join-Path $PSScriptRoot 'kindle-config.json'
$keyDir = Join-Path $env:LOCALAPPDATA 'KindleBookdrop'
$key = Join-Path $keyDir 'kindle_ed25519'
New-Item -ItemType Directory -Force -Path $keyDir | Out-Null

if (-not (Test-Path $key)) {
    Write-Host "生成 ed25519 密钥（空口令）: $key" -ForegroundColor Cyan
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'ssh-keygen'
    $psi.Arguments = '-t ed25519 -f "' + $key + '" -N "" -C "bookdrop@kindle"'
    $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { throw "ssh-keygen 失败（退出码 $($p.ExitCode)）" }
} else {
    Write-Host "密钥已存在: $key" -ForegroundColor DarkGray
}

# 收紧 ACL：只允许当前用户访问（OpenSSH 拒绝权限过宽的私钥）
& icacls $key /inheritance:r /grant:r "$($env:USERNAME):F" | Out-Null
$check = cmd /c "ssh-keygen -y -f `"$key`" 2>nul"
if ($LASTEXITCODE -ne 0) { throw "密钥验证失败，请检查 $key 的权限。" }

$pub = (Get-Content "$key.pub" -Raw).Trim()
Write-Host ""
Write-Host "=== 公钥（写到 Kindle 的 koreader/settings/SSH/authorized_keys）===" -ForegroundColor Yellow
Write-Host $pub
Write-Host ""

$dest = Join-Path $PSScriptRoot 'authorized_keys'
Set-Content -Path $dest -Value $pub -Encoding ascii -NoNewline

if (-not (Test-Path $configPath)) { Copy-Item (Join-Path $PSScriptRoot 'kindle-config.template.json') $configPath }
$cfg = Get-Content $configPath -Raw -Encoding utf8 | ConvertFrom-Json
$cfg.ssh_key = $key
$cfg | ConvertTo-Json | Set-Content -Path $configPath -Encoding utf8
Write-Host "已更新配置: $configPath（ssh_key 指向 $key）" -ForegroundColor Green
Write-Host "已生成公钥文件: $dest"
Write-Host ""
Write-Host "步骤（首次 USB 连接、KOReader 已装好之后）：" -ForegroundColor Cyan
Write-Host "  1) 把 authorized_keys 复制到 Kindle 的 koreader/settings/SSH/ 目录（没有该目录就自己建）"
Write-Host "  2) Kindle 上打开 KOReader → 工具 → SSH，确认端口为 2222 并启动"
Write-Host "  3) 回电脑运行: .\Kindle-Push.ps1 -Status 或 .\Kindle-Push.ps1 -File 某本书.epub"
Write-Host ""
Write-Host "如果 KOReader 的 SSH 菜单里有「允许无密码连接」，也可以直接打开，跳过密钥步骤。" -ForegroundColor DarkGray
