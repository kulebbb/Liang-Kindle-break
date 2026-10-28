# 04 · 传书：Bookdrop / Kindle 二维码 / 手机直连

统一前提：Kindle 亮屏、KOReader 正在运行、KOReader 的 SSH 服务已启动（端口 2222），
Kindle 与电脑/手机在同一局域网。Kindle 睡眠会断 Wi-Fi。

## 4.1 Bookdrop（电脑网页）

```powershell
cd <skill>\scripts
.\Start-Bookdrop.cmd        # 等价：python bookdrop.py
```

- 打开页面：`http://127.0.0.1:<http_port>`（默认 8765），并自动同步到 Kindle；
- **拖拽上传**：浏览器把文件 POST 到 `/upload?name=...`，服务保存到 `library\`，然后 `scp` 推到 Kindle；
- **文件夹自动推送**：放进 `library\` 的新文件会被监视线程推送；
- **兜底下拉**：页面里每本书有下载链接，Kindle 浏览器也能直接下载；
- 启动时自动把「网页地址 + SSH 信息」写入 Kindle 的
  `/mnt/us/koreader/bookdrop_url.txt`（两行）。

配置 `scripts\kindle-config.json`：

```json
{
  "kindle_ip": "192.168.1.3",
  "ssh_port": 2222,
  "ssh_user": "root",
  "ssh_key": "%LOCALAPPDATA%\\KindleBookdrop\\kindle_ed25519",
  "remote_dir": "/mnt/us/documents/books",
  "http_port": 8765,
  "auto_push": true,
  "watch_library": true
}
```

`kindle_ip` 留空时自动在 ARP 表里找开放 2222 端口的主机。

常见参数：`--no-push`（只当网页文件服务器）、`--port 9000`、`--selftest`（自检，不需要 Kindle）。

## 4.2 Kindle 端「传书二维码」插件（本项目自写）

位置：`scripts/plugins/bookdrop.koplugin/`（main.lua + _meta.lua）。

部署（KOReader 已安装、SSH 在线即可，不用插线）：

```powershell
scp -P 2222 -i <key> -r scripts/plugins/bookdrop.koplugin root@<kindle-ip>:/mnt/us/koreader/plugins/
```

重启 KOReader 后，工具菜单出现：
- **传书二维码（手机扫码）**：显示 `/mnt/us/koreader/bookdrop_url.txt` 第一行（网页地址）的二维码；
- **传书地址 / 手机 SFTP 信息**：显示网页地址 + `SSH: root@<ip> -p 2222`（供手机 SFTP 使用）。

文件由电脑端 Bookdrop 每次启动时同步，因此 IP 变化后重启 Bookdrop 即可。

## 4.3 手机直连 Kindle（SFTP，不需要电脑）

1. 生成手机专用密钥（RSA + PEM，兼容大多数手机 App）：

```powershell
ssh-keygen -t rsa -b 3072 -m PEM -f phone_sftp_key -N ""
```

2. 把 `phone_sftp_key.pub` 追加到 Kindle `koreader/settings/SSH/authorized_keys`（每行一个，末尾要有换行）；
3. `phone_sftp_key` 发送到手机（微信文件传输助手等）；
4. 手机 App 新建 SFTP：主机 `<kindle-ip>`、端口 `2222`、用户 `root`、认证=私钥、目录 `/mnt/us/documents/books`；
5. 上传后 KOReader 文件浏览器刷新可见。

### 撤销手机授权

从 `authorized_keys` 删除对应行（保留电脑端那行）后，dropbear 下一次认证即拒绝。
可用 PowerShell 通过 ssh 重写该文件。

### 备用：App 不支持私钥

KOReader → 工具 → SSH → 打开 **"Login without password (DANGEROUS)"**，
App 里用「root + 任意密码」连接。仅限信任的家庭局域网，用完关闭。

## 4.4 排障

| 现象 | 处理 |
| --- | --- |
| 手机打不开网页 | 同一 Wi-Fi？关 VPN/代理；用手机浏览器直接输入 `http://<pc-ip>:8765`；微信扫码被拦时点「在浏览器中打开」 |
| 电脑本机能开、手机不行 | 路由器访客网络/AP 隔离；Windows 防火墙需放行 python.exe（Public 网络）或临时允许 |
| 推书报 SSH 连接失败 | Kindle 睡眠/KOReader 退出/SSH 未启动；点亮屏幕、工具→SSH 重新启动 |
| 推送卡住或超时 | 大文件走 Wi-Fi 较慢；确认信号；Kindle 保持亮屏 |
| IP 变了 | 重启 Bookdrop 重新同步；或工具→传书地址查看；`Kindle-Push.ps1 -Discover` 自动找 |
| 文件名中文/空格 | 已测试可用；scp 通过参数传文件名，无需引号处理 |