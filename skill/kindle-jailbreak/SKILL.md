---
name: kindle-jailbreak-koreader
description: Kindle 5.x（实测 Kindle 8/KT3，固件 5.16.2.1.1）越狱 + KOReader + 微信读书 + 局域网/手机传书的完整可回退流程。含 WinterBreak2 越狱包、KOReader 与微信读书插件离线包、自动化 PowerShell/Python 脚本和排障文档。
---

# Kindle 越狱 + KOReader + 微信读书 + 局域网传书

## 适用场景

- 2016–2022 年左右的 Kindle（固件 5.6.1.1 – 5.16.3），想越狱装 KOReader；
- 想在 Kindle 上读微信读书书架、同步进度；
- 想要不插线的传书：电脑网页拖拽、手机扫码、手机 SFTP 直传。

> 已在 **Kindle 8（KT3，固件 5.16.2.1.1）** 上完整走通。其他机型请先用
> <https://kindlemodding.org/jailbreak-wizard.html> 确认支持的越狱方式。

## 目录结构

```
kindle-jailbreak/
├── SKILL.md                    ← 本文件（步骤总览）
├── scripts/                    ← 可执行脚本
│   ├── Find-Kindle.ps1         USB 盘符 / 局域网 SSH 识别
│   ├── Prime-Kindle.ps1        把越狱包解压进 Kindle 根目录
│   ├── Install-KOReaderOffline.ps1  离线安装 KOReader + 启动条目
│   ├── Deploy-KindleExtras.ps1     部署微信读书插件 + SSH 公钥
│   ├── Setup-KindleSsh.ps1         生成 SSH 密钥并写配置
│   ├── Kindle-Push.ps1             命令行 Wi-Fi 推书
│   ├── Weread-Login.ps1            微信读书 401 绕行登录助手
│   ├── bookdrop.py                 Bookdrop 服务（网页拖拽 + 自动推送 + 二维码地址同步）
│   ├── Start-Bookdrop.cmd          双击启动 Bookdrop
│   ├── cdp_cookies.py              从浏览器读 Cookie
│   ├── patch_weread_settings.py    写 weread.lua
│   ├── fix_weread_settings.py      写坏时的恢复脚本
│   ├── kindle-config.template.json 配置模板
│   ├── plugins/bookdrop.koplugin/  Kindle 端「传书二维码」插件
│   └── tests/                      mock Kindle 端到端测试
├── assets/                     越狱包与安装包（见 assets/README.md）
├── references/                 详细文档（越狱/安装/微信读书/传书/排障/设备档案）
└── library/                    Bookdrop 待推送目录（运行时生成）
```

## 前置条件

- Windows 10/11 + PowerShell 5.1；
- Python 3.10+、OpenSSH 客户端（ssh/scp/ssh-keygen）、Edge 或 Chrome（微信读书登录助手用）；
- **micro-USB 数据线**（充电线不行——这是首次踩坑点）；
- Kindle 电量 > 50%、能连 Wi-Fi；电脑与 Kindle 在同一局域网。

## 0. 初始化

```powershell
cd <skill>\scripts
Copy-Item kindle-config.template.json kindle-config.json   # 可选，脚本会自动生成
.\Find-Kindle.ps1          # 确认能识别 Kindle 盘与固件
.\Setup-KindleSsh.ps1      # 生成 SSH 密钥（放在 NTFS 的 %LOCALAPPDATA%\KindleBookdrop）
```

> 私钥不要放在 exFAT 盘：OpenSSH 会以 "bad permissions" 拒绝加载。

## 1. 越狱（WinterBreak2，约 2 分钟）

```powershell
.\Prime-Kindle.ps1         # 自动识别 Kindle 盘，把 assets/wb2.zip 解压到根目录
```

然后在 Kindle 上：

1. 安全弹出数据线，确认 Kindle 已连 Wi-Fi；
2. 打开**实验性浏览器**，访问 `https://penguins184.xyz/wb2`；
3. 点 **Jailbreak**，屏幕出现黑色日志并自动重启 = 成功；
4. 验证：主页搜索框输入 `;kpm`，出现 `kindle package manager v0.2.4` 即越狱成功（更新已被自动封锁）。

风险、回退与失败排查见 `references/01-jailbreak-winterbreak2.md`。

## 2. 安装 KOReader

- **在线**（网络好时）：Kindle 搜索框 `;kpm update` → `;kpm install koreader`；
- **离线**（推荐兜底，KPM 下载卡住时用）：

```powershell
# 先退出 KOReader（它运行时会屏蔽 USB 存储），插 USB 后运行：
.\Install-KOReaderOffline.ps1
```

会解压官方 `koreader-kindlepw2` 包，并在 `documents/` 生成名为 KOReader 的启动条目（scriptlet）。
点它启动；首次进入会问语言。详见 `references/02-koreader-install.md`。

## 3. 微信读书

```powershell
# KOReader 已安装后，USB 连接 Kindle 运行（部署插件 + SSH 公钥）：
.\Deploy-KindleExtras.ps1
```

然后 Kindle 重启 KOReader → 工具 → 微信读书。**扫码登录会报 401**（上游 issue #214，微信读书 2026-10 改了接口），
用 Cookie 绕行：

1. 手机微信读书 App → 我 → 设置 → 微信读书 Skill → 获取 API Key；
2. Kindle：KOReader → 工具 → SSH → 启动服务；
3. 电脑：

```powershell
.\Weread-Login.ps1     # 弹出浏览器，微信扫码登录网页版，自动写 Cookie 到 Kindle
```

4. Kindle 重启 KOReader → 工具 → 微信读书 → 书架（能加载、能下载即成功）。

Cookie 过期就重跑 `Weread-Login.ps1`。详见 `references/03-weread-plugin-401.md`。

## 4. 传书（三条路）

前提：Kindle 亮屏、KOReader 运行、工具 → SSH 已启动（建议打开 "Start SSH server with KOReader"）。

**4.1 电脑网页（推荐）**

```powershell
.\Start-Bookdrop.cmd     # 自动打开 http://127.0.0.1:8765
```

把书拖进页面即可；也可以把书拷进 `library\` 目录自动推送。手机浏览器访问页面显示的局域网地址也能上传。

**4.2 Kindle 二维码 → 手机扫码**

```powershell
# 部署 Kindle 端插件（首次）：
scp -r plugins/bookdrop.koplugin root@<kindle-ip>:/mnt/us/koreader/plugins/
```

Bookdrop 启动时会自动把网页地址和 SSH 信息同步到 Kindle。Kindle：工具 → **传书二维码（手机扫码）** → 手机扫码 → 打开上传页。

**4.3 手机直连 Kindle（不需要电脑）**

- 生成手机专用密钥（RSA PEM，兼容性最好）并加入 Kindle `authorized_keys`；
- 手机 SFTP App（Android：Material Files 等）连接 `<kindle-ip>:2222`，用户 `root`，私钥登录；
- 上传到 `/mnt/us/documents/books/`。

详见 `references/04-transfer-and-qr.md`。

## 5. 验证清单

- [ ] `;kpm` 有输出（越狱成功）
- [ ] KOReader 能启动并进入主界面
- [ ] 微信读书书架能加载、能下载一本
- [ ] Bookdrop 拖拽后 Kindle `documents/books/` 出现文件
- [ ] 手机扫码能打开 Bookdrop 页面
- [ ] 手机 SFTP 能列目录

## 6. 回退

- 卸载越狱：运行 `ota.sh` scriptlet → 恢复出厂 → 推送同版本固件（见 `references/01`）；
- 只删工具：删除 `koreader/plugins/bookdrop.koplugin`、`documents/KOReader.sh` 等即可。

## 7. 常见坑（详见 references/05）

| 现象 | 原因 / 处理 |
| --- | --- |
| Windows 完全识别不到 Kindle | 用了充电线；换数据线、直插电脑 |
| KPM 安装卡住 | 改用离线安装 `Install-KOReaderOffline.ps1` |
| 微信读书扫码 401 | 上游 bug，用 `Weread-Login.ps1` 绕行 |
| SSH 私钥被拒 | 私钥放在 exFAT；移到 NTFS 并收紧 ACL |
| KOReader 运行时插 USB 没反应 | KOReader 屏蔽 USB 存储；先退出 KOReader |
| 手机打不开 Bookdrop 页面 | 不同 Wi-Fi / VPN / 微信扫码拦截；用手机浏览器直接输地址 |
| Kindle IP 变了 | 重启 Bookdrop 自动重新同步；或 `Kindle-Push.ps1 -Discover` |

## 来源与许可

- `assets/wb2.zip`：KindleModding/Winterbreak2（社区越狱工具）
- `assets/koreader-kindlepw2-v2026.07.1.zip`：KOReader 官方发布（GPLv3）
- `assets/weread.koplugin-v1.6.0.zip`：finlater/weread.koplugin（AGPL-3.0，第三方）
- `scripts/` 下脚本与插件为项目自定义；KOReader 自带 SSH 插件仅作为传输通道使用。

> 越狱有风险（失去保修、极小概率变砖），请先阅读 `references/01` 的风险与回退章节；所有涉及第三方插件的功能请遵守对应服务条款，仅用于个人使用。
## 可选：自检与 mock 测试

```powershell
# Bookdrop 自检（不需要 Kindle）
python scripts\bookdrop.py --selftest

# 用 mock Kindle 验证 scp 推送链路（需要 pip install paramiko）
python scripts\tests\test_push.py
```

mock 只实现最小 SFTP 子集，scp 结束阶段可能报 `lost connection`，以「文件内容一致」为通过标准；
真实设备上 scp 正常。