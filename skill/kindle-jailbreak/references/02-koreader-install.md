# 02 · KOReader 安装与 Kindle 端配置

## 选哪个包

| 固件 | 包 |
| --- | --- |
| ≥ 5.16.3 | `koreader-kindlehf-*.zip` |
| < 5.16.3（含 KT3/5.16.2.1.1） | `koreader-kindlepw2-*.zip`（本 skill 的 assets 里就是它） |

来源：<https://github.com/koreader/koreader/releases>

## 安装方式 A：KPM（在线）

Kindle 主页搜索框：

```
;kpm update
;kpm install koreader
```

完成后主页出现 KOReader 启动条目（scriptlet），点开即可；也可 `;kpm launch koreader`。

> 实测国内网络容易在下载 40MB 包时卡住；卡住就改用方式 B。

## 安装方式 B：离线（推荐兜底）

1. **先退出 KOReader**（它运行时会 `killall -STOP volumd` 屏蔽 USB 存储，插线不挂载）；
2. 插 USB，电脑运行：

```powershell
.\Install-KOReaderOffline.ps1
```

脚本会：
- 清理旧的 `koreader/` 与 `extensions/koreader/`；
- 把 `assets/koreader-kindlepw2-v2026.07.1.zip` 解压到 Kindle 根目录；
- 在 `documents/KOReader.sh` 写一个 scriptlet：
  ```sh
  #!/bin/sh
  # Name: KOReader
  # Author: Bookdrop
  /mnt/us/koreader/koreader.sh
  ```

3. 安全弹出 → Kindle 书库出现名为 **KOReader** 的条目 → 点开启动；首次会问语言。

### scriptlet 机制

Universal Hotfix 引入的 SH_Integration 会把 `documents/` 下任意 `.sh` 当作书索引，点开以 root 执行。
可用 `# Name:`、`# Author:`、`# Icon:`（绝对路径或 base64）自定义显示。
`# DontUseFBInk` 可关闭屏幕输出。参考：<https://kindlemodding.org/kindle-dev/scriptlets.html>

## 部署微信读书插件与 SSH 公钥

KOReader 装好后，USB 连接（同样先退出 KOReader），运行：

```powershell
.\Deploy-KindleExtras.ps1
```

- 解压 `assets/weread.koplugin-v1.6.0.zip` 到 `koreader/plugins/`；
- 把 `authorized_keys` 写到 `koreader/settings/SSH/authorized_keys`。

重启 KOReader 生效。

## SSH 服务（KOReader 自带插件）

- 菜单：工具 → SSH（`SSH server`）；
- 默认端口 **2222**；密钥认证读取 `koreader/settings/SSH/authorized_keys`（每行一个公钥）；
- 建议打开 **"Start SSH server with KOReader"** 实现自启动；
- 应急可开 **"Login without password (DANGEROUS)"**（局域网内无密码，慎用）。

## 验证

- KOReader 主界面可进入；
- 工具菜单出现「微信读书」；
- 工具 → SSH 启动后，电脑 `ssh -p 2222 -i <key> root@<kindle-ip>` 能登录。