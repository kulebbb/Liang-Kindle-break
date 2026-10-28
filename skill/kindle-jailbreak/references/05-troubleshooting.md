# 05 · 排障手册

## 连接与识别

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| Windows 完全无感知（无盘符、无 USB 设备） | 用了“充电线”（只有电源线芯） | 换数据线；用同一根线接手机验证；直插电脑不用扩展坞 |
| 盘符出现但无 documents/system | 不是 Kindle 存储 | 换盘符；检查是否 MTP 设备（2024+ 机型走 MTP） |
| 固件版本不确定 | — | `Find-Kindle.ps1` 会读 `system\version.txt`；或在 设置→设备选项→设备信息 查看 |

## 越狱

| 现象 | 处理 |
| --- | --- |
| 点 Jailbreak 只下载 mobi 无日志 | 检查 `winterbreak2/dialoger.html` 是否在根目录；重启 Kindle 重试；确认外网可达 |
| 越狱后 `;kpm` 无输出 | 越狱未真正完成；重试；必要时换网络 |
| 担心被推送更新 | 根目录不要留 `*.bin`；越狱成功会自动封锁 OTA |

## KOReader

| 现象 | 处理 |
| --- | --- |
| `;kpm install koreader` 卡住 | 改用离线安装脚本（KOReader 运行时先退出，否则 USB 不挂载） |
| 书库没有 KOReader 条目 | 稍等索引；重启 Kindle；确认 `documents/KOReader.sh` 存在且为 LF 换行 |
| 启动黑屏很久 | 首次启动需要解压/初始化；等待；不行重启 KOReader |
| 插 USB 无反应 | KOReader 运行时屏蔽 USB（volumd STOP）；退出 KOReader 再插 |

## 微信读书

| 现象 | 处理 |
| --- | --- |
| 扫码 401 | 上游接口变更；用 `Weread-Login.ps1` Cookie 绕行 |
| 书架空白/加载失败 | Cookie 过期 → 重跑登录脚本；检查 api_key 是否存在 |
| 无法下载章节 | Cookie 缺失或不完整（需 wr_vid + wr_skey/wr_gid） |
| weread.lua 写坏 | `fix_weread_settings.py` 恢复，或删除 cookies 段重跑 |

## 传书 / 网络

| 现象 | 处理 |
| --- | --- |
| ssh 连接被拒 | 端口 2222 是否监听；authorized_keys 是否包含对应公钥且每行分隔 |
| 私钥 “bad permissions” | 私钥放在 exFAT 盘；移到 NTFS（`%LOCALAPPDATA%\KindleBookdrop`）并 icacls 收紧 |
| scp 连到 22 端口 | scp 用 `-P`，ssh 用 `-p`；本项目脚本已处理 |
| 手机网页打不开 | 同 Wi-Fi、关 VPN、浏览器直接输地址；路由器 AP 隔离 |
| 二维码地址过期 | 重启 Bookdrop 自动同步；工具→传书地址可查看 |

## 通用诊断命令

```powershell
# 设备
Get-Volume | Where-Object FileSystemLabel -eq 'Kindle'
.\Find-Kindle.ps1

# 网络/端口
Test-NetConnection <kindle-ip> -Port 2222
Get-NetConnectionProfile            # 看网络是否为 Public（影响防火墙规则）

# SSH 快速验证
ssh -p 2222 -i <key> root@<kindle-ip> "echo OK; ls /mnt/us/documents/books/"

# Kindle 端
; kpm      # 主页搜索框，验证越狱
```

## PowerShell 脚本编码注意

- Windows PowerShell 5.1 读取无 BOM 的 UTF-8 脚本会按 GBK 解析，导致中文/引号语法错误；
- 本项目 `.ps1` 统一保存为 **UTF-8 with BOM**；
- 在 exFAT 盘上不要存放 OpenSSH 私钥（权限校验不通过）。