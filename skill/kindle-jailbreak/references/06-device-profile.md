# 06 · 设备与环境档案（实测记录）

## 设备

| 项 | 值 |
| --- | --- |
| 机型 | Kindle 8th Generation（代号 **KT3**，2016） |
| 固件 | **5.16.2.1.1**（`system/version.txt`: `Kindle 5.16.2.1.1 (409749 002)`） |
| USB | `VID_1949&PID_0004`，"Kindle Internal Storage"，3.04 GB FAT32 |
| 越狱 | WinterBreak2（`penguins184.xyz/wb2`），jb.sh 安装 KPM **v0.2.4** |
| KOReader | **v2026.07.1**（kindlepw2 包，离线安装） |
| 微信读书插件 | **v1.6.0**（finlater/weread.koplugin） |
| Kindle IP | 192.168.1.3（DHCP，可能变化） |
| PC | Windows，192.168.1.211，Wi-Fi「恭禧发财」，Python 3.10，PowerShell 5.1 |

## 验证证据

| 检查 | 结果 |
| --- | --- |
| `;kpm` 搜索框输出 | `kindle package manager v0.2.4` |
| KOReader 启动 | 可进入主界面（scriptlet `documents/KOReader.sh` 启动） |
| 微信读书书架 | 可加载、可下载（Cookie + API Key 绕行后） |
| Bookdrop 拖拽上传 | HTTP 200 `已推送 1 个文件`；Kindle `/mnt/us/documents/books/` 出现中文文件名文件 |
| 二维码插件 | 工具菜单出现「传书二维码」「传书地址 / 手机 SFTP 信息」 |
| 手机扫码 | 可打开 `http://192.168.1.211:8765` |
| 手机 SFTP 私钥 | `ssh -p 2222 -i phone_sftp_key root@192.168.1.3` 成功 |
| Kindle → PC HTTP | Kindle 上 wget 访问 Bookdrop 返回 HTML 200 |

## 本次实际偏差（值得记录）

1. **KPM 在线安装 KOReader 卡在约 10%** → 改用官方 kindlepw2 离线包 + scriptlet 启动条目；
2. **微信读书扫码必 401** → 用浏览器 Cookie + Skill API Key 手动写入配置；
3. **私钥放 exFAT 被 OpenSSH 拒绝** → 私钥改放 `%LOCALAPPDATA%\KindleBookdrop` 并 icacls 收紧；
4. **写文件工具在 exFAT 上硬链接失败** → 项目文件统一用 shell/Python 写入；
5. **Windows 最初完全识别不到 Kindle** → 确认是充电线，换数据线后正常。

## 时间线（2026-10-29）

- 00:1x 连接设备、确认固件；拷贝 WinterBreak2；越狱成功（日志+自动重启）；
- 00:2x 从 KPM 卡住改为离线装 KOReader；
- 00:3x 部署微信读书插件与 SSH 密钥；遇到 401，转 Cookie 绕行；
- 00:5x 传书链路验证（scp/Bookdrop）；二维码插件上线；
- 01:0x 手机直连密钥与文档完善。