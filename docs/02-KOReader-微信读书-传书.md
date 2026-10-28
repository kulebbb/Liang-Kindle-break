# KOReader / 微信读书 / 局域网传书

## 1. 安装 KOReader（越狱后）

在 Kindle 主页搜索框依次执行：

1. ;kpm update — 更新软件源；
2. ;kpm install koreader — 安装 KOReader；
3. 回到主页点击新出现的 KOReader 小册子（书签图标）启动，或搜索框执行 ;kpm launch koreader。

参考：https://kindlemodding.org/jailbreaking/whats-next/getting-koreader/

> KOReader 直接支持 EPUB/PDF/MOBI/AZW3，微信读书导出的 EPUB 不需要转换即可阅读。

## 2. 微信读书插件（KOReader 内直连）

插件：https://github.com/finlater/weread.koplugin

前提：微信读书 App 中已开通 Skill（我 → 设置 → 微信读书 Skill → 获取 API Key）。

安装：

1. 下载 Releases 中最新的 weread.koplugin-vX.Y.Z.zip；
2. 解压得到 weread.koplugin 文件夹；
3. 放到 Kindle 上的 koreader/plugins/（USB 或 SFTP 均可）；
4. 重启 KOReader，菜单出现 工具 → 微信读书；
5. 工具 → 微信读书 → 微信扫码登录，用手机微信扫码并确认（如出现四位验证码，在 KOReader 输入）。

能力：微信读书书架、公众号、搜索、章节/全书下载、阅读进度同步、阅读时长统计、划线想法查看。
注意：非官方插件，存在账号风控/协议变化风险，仅用于个人阅读。

备选：PC 端用 weread-exporter（https://github.com/drunkdream/weread-exporter）按书籍 ID 导出 EPUB，再按第 3 节传入 Kindle。

## 3. 局域网传书

### 方案 A（推荐）：KOReader SSH/SFTP + PC 拖拽页

KOReader 内置 SSH 服务器（Kindle 机型支持）：

1. Kindle：KOReader 工具 → SSH server（不同版本可能叫 SSH 服务器）启动；
2. PC：运行 tools 下的拖拽上传页（待实现），浏览器把书拖进页面即可推送到 Kindle；
3. Kindle：KOReader 文件浏览器刷新目录，书立即出现。

### 方案 B（兜底，无需 SSH）：Kindle 浏览器下载

PC 起本地 HTTP 服务（Python 自带即可），Kindle 实验性浏览器打开 http://电脑IP:端口，点书下载。

### 方案 C：Calibre 无线

PC 安装 Calibre，KOReader 里启用 Calibre 插件连接无线设备，从 Calibre 书库推送。

## 4. 书库目录约定

建议统一放 Kindle 上的 /mnt/us/documents/books/，按分类分子目录；KOReader 文件浏览器默认能看到 documents。

## 5. 可选：把 KOReader 做成"自己的系统"

- 自定义屏保：KOReader 设置 → 屏保，指定图片文件夹；
- 自定义界面：安装 ZenUI / SimpleUI 插件，把首页做成自己的书架/底栏；
- 开机直达：KPM/KUAL 脚本或 KOReader 启动器方式，待真机联调后补充。

## 6. PC 端工具（已实现，位于 tools\）

### 6.1 一次性准备

0. 生成并保存密钥（放在 NTFS 盘 `%LOCALAPPDATA%\KindleBookdrop`，exFAT 盘上的私钥会被 OpenSSH 拒绝）。

1. 在电脑上运行：

```powershell
cd D:\coding\kindle\tools
.\Setup-KindleSsh.ps1        # 生成密钥，得到 authorized_keys 文件
```

2. 首次 USB 连接 Kindle 时（KOReader 已装好），运行 `tools\Deploy-KindleExtras.ps1` 自动部署（它会把公钥复制到下面路径，同时把微信读书插件解压到 `koreader\plugins`）。手动方式：把 `tools\authorized_keys` 复制到 Kindle 的：

```
koreader/settings/SSH/authorized_keys
```

3. Kindle 上：KOReader → 工具 → SSH（或"SSH 服务器"），端口确认 2222，启动。
   - 若菜单里有"允许无密码连接"，也可以直接打开，省去密钥步骤（仅限家里局域网）。

### 6.2 日常传书

方式一：双击 `tools\Start-Bookdrop.cmd`

- 浏览器自动打开 http://127.0.0.1:8765 （手机用页面打印的局域网地址）；
- 把书拖进页面即上传，脚本立即通过 scp 推到 Kindle；
- 也可以直接把书复制进 `library\` 文件夹，监视器几秒内自动推送。

方式二：命令行

```powershell
.\Kindle-Push.ps1 -File "D:\books\三体.epub"
.\Kindle-Push.ps1 -Path "D:\books\*.epub"
.\Kindle-Push.ps1 -Status        # 看 Kindle 是否在线
.\Kindle-Push.ps1 -Discover      # 自动找 Kindle IP 并写入配置
```

配置文件：`tools\kindle-config.json`（Kindle IP、端口 2222、远程目录 /mnt/us/documents/books）。

### 6.3 兜底：Kindle 浏览器下载

Bookdrop 页面上的"下载"链接在 Kindle 实验性浏览器里打开即可下载（适合 SSH 未启动时）。

### 6.4 注意事项

- Kindle 需亮屏、KOReader 运行中、与电脑同一 Wi-Fi；Kindle 睡眠会断 Wi-Fi，可在 KOReader 里开"保持唤醒/Keep alive"。
- KOReader 菜单里的 SSH 插件支持开机自启（autostart），装好后建议打开。
- 远程目录不存在时脚本会自动 `mkdir -p`；推送失败会自动重试 legacy scp 模式（`scp -O`）。


## 7. 实际使用（2026-10-29 已联调通过）

### Wi-Fi 传书（推荐）

前提：Kindle 亮屏且 KOReader 运行中，`工具 → SSH` 已启动（建议 autostart），同一 Wi-Fi。

1. 双击 `tools\Start-Bookdrop.cmd`（自动打开浏览器 http://127.0.0.1:8765）；
2. 把书拖进页面，几秒后提示「已推送 1 个文件」；
3. Kindle 的 KOReader 文件浏览器进入 `/mnt/us/documents/books/` 查看。

其他方式：
- 把书拷进 `library\` 文件夹，启动 Bookdrop 后自动推送新文件；
- 命令行 `.\Kindle-Push.ps1 -File 某本书.epub`；
- 手机浏览器打开页面显示的局域网地址，同样可拖拽上传（电脑需开机）。

已验证：中文文件名、含空格的 EPUB/TXT 均能正常推送。

### 微信读书

书架、下载、进度同步均正常；登录走 Cookie 绕行方案，见 `docs/03-微信读书登录绕行.md`。
