# Kindle 自建阅读系统

> 把一台 Kindle 8（KT3，固件 5.16.2.1.1）改造成：**越狱 → KOReader → 微信读书 → 局域网/手机传书** 的完整可回退方案。
> 全过程已整理成可复用的 skill：`skill/kindle-jailbreak/`（打包版 `kindle-jailbreak-skill.zip`）。

![status](https://img.shields.io/badge/status-已验证-success) ![device](https://img.shields.io/badge/device-Kindle%208%20(KT3)-blue) ![firmware](https://img.shields.io/badge/firmware-5.16.2.1.1-lightgrey)

## 特性

- **越狱**：WinterBreak2（浏览器漏洞，支持 5.6.1.1–5.16.3，无需注册 Amazon）
- **阅读器**：KOReader 2026.07.1（离线安装，书库一键启动）
- **微信读书**：weread.koplugin v1.6.0，书架/下载/进度同步可用；含上游 401 bug 的 Cookie 绕行方案
- **传书三件套**：
  1. `Bookdrop` 电脑网页拖拽 → Wi-Fi 自动推送
  2. Kindle 显示**二维码** → 手机扫码上传（自写 KOReader 插件）
  3. 手机 **SFTP 直连 Kindle**（不需要电脑）
- **可复用**：全部脚本 + 离线包 + 排障文档封装为 skill

## 目录结构

```
.
├── README.md
├── LICENSE
├── skill/kindle-jailbreak/          # ⭐ 可复用 skill（推荐从这里开始）
│   ├── SKILL.md                     #    五阶段流程总览
│   ├── scripts/                     #    自动化脚本（PowerShell / Python）
│   ├── assets/                      #    越狱包、KOReader、微信读书插件
│   └── references/                  #    越狱/安装/401/传书/排障/设备档案
├── tools/                           # 本次落地使用的脚本（与 skill/scripts 对应）
├── docs/                            # 本次操作的说明文档（中文）
├── downloads/                       # 安装包缓存（与 skill/assets 重复，不入库）
├── library/                         # Bookdrop 待推送/已上传目录（不入库）
└── logs/                            # 运行日志（不入库）
```

## 快速开始（新设备从零）

> 需要：Windows + PowerShell 5.1、Python 3.10、OpenSSH 客户端、Edge/Chrome、**micro-USB 数据线**。

```powershell
cd skill\kindle-jailbreak\scripts
Copy-Item kindle-config.template.json kindle-config.json   # 可选
.\Find-Kindle.ps1        # 1. 识别设备与固件
.\Setup-KindleSsh.ps1    # 2. 生成 SSH 密钥（NTFS 路径）
.\Prime-Kindle.ps1       # 3. 拷贝 WinterBreak2 越狱包
```

然后在 Kindle 上：连 Wi-Fi → 实验性浏览器打开 `https://penguins184.xyz/wb2` → 点 **Jailbreak** → 出现黑色日志并重启。
验证：搜索框输入 `;kpm` 出现 `kindle package manager v0.2.4`。

接着：

```powershell
.\Install-KOReaderOffline.ps1   # 4. 离线装 KOReader（先退出 KOReader 再插 USB）
.\Deploy-KindleExtras.ps1       # 5. 部署微信读书插件 + SSH 公钥
.\Weread-Login.ps1              # 6. 微信读书 401 绕行登录（浏览器扫码）
.\Start-Bookdrop.cmd            # 7. 启动传书网页
```

完整步骤、风险与回退见 [skill/kindle-jailbreak/SKILL.md](skill/kindle-jailbreak/SKILL.md)。

## 日常使用

### 传书

| 方式 | 操作 | 依赖 |
| --- | --- | --- |
| 电脑网页 | 双击 `tools\Start-Bookdrop.cmd`，拖拽文件 | Bookdrop 运行 |
| 手机扫码 | Kindle：工具 → 传书二维码（手机扫码） | Bookdrop 运行 |
| 手机直连 | SFTP App 连 `<kindle-ip>:2222`，私钥 `phone_sftp_key.pem` | 无 |

前提：Kindle 亮屏、KOReader 运行、工具 → SSH 已启动（建议开启 "Start SSH server with KOReader"）。

### 微信读书

KOReader → 工具 → 微信读书 → 书架。扫码登录因微信读书服务端改动暂不可用（上游 issue #214），
本仓库用 Cookie + Skill API Key 绕行；Cookie 过期后重跑 `Weread-Login.ps1` 即可。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| Windows 识别不到 Kindle | 换 **数据线**（充电线不行）、直插电脑 |
| `;kpm install` 卡住 | 改用离线安装脚本 |
| 微信读书扫码 401 | 用 `Weread-Login.ps1` 绕行 |
| 私钥 "bad permissions" | 私钥不能放 exFAT，移到 NTFS |
| 手机打不开传书页 | 同一 Wi-Fi、关 VPN、用手机浏览器直接打开地址 |
| KOReader 运行时插 USB 无反应 | KOReader 会屏蔽 USB 存储，先退出 |

更多见 [skill/kindle-jailbreak/references/05-troubleshooting.md](skill/kindle-jailbreak/references/05-troubleshooting.md)。

## 安全与合规

- **不要提交/公开**：`phone_sftp_key.pem`、`tools/keys/`、`kindle-config.json` 中的 IP/公钥配置、微信读书 Cookie——这些已加入 `.gitignore`；
- 越狱会失去保修、有极小概率变砖（可回退），操作前请阅读 skill 中的风险章节；
- 微信读书插件为第三方开源项目（AGPL-3.0），Cookie 注入仅用于个人设备登录，请遵守对应服务条款；
- 本项目与 Amazon、微信读书官方无关。

## 致谢与来源

- 越狱：[KindleModding/Winterbreak2](https://github.com/KindleModding/Winterbreak2)、[KindleModding Wiki](https://kindlemodding.org/)
- 阅读器：[KOReader](https://github.com/koreader/koreader)（GPLv3）
- 微信读书插件：[finlater/weread.koplugin](https://github.com/finlater/weread.koplugin)（AGPL-3.0）
- 传书/二维码/登录助手脚本：本项目自写

## 许可

本项目自写脚本与文档采用 MIT（见 [LICENSE](LICENSE)）；`assets/` 中的第三方包遵循各自许可证。