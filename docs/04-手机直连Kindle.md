# 手机直连 Kindle 传书（不需要电脑）

已为手机生成专用私钥并加入 Kindle 的 SSH 白名单（实测可登录），Kindle 不需要电脑中转。

## 一次性准备

1. 把 **`phone_sftp_key.pem`** 发送到手机：微信「文件传输助手」、QQ、或数据线拷贝都行。
2. 手机安装一个支持「SFTP + 私钥」的文件管理 App：
   - **Android**：Material Files（开源）、FE File Explorer、Solid Explorer、Termius 等
   - **iOS**：Secure ShellFish、Termius、Documents 等（看版本是否支持私钥）

## 配置连接

在 App 里新建 SFTP 连接：

| 项目 | 值 |
| --- | --- |
| 主机 / Host | `192.168.1.3` |
| 端口 / Port | `2222` |
| 用户名 | `root` |
| 认证方式 | 私钥（选择 `phone_sftp_key.pem`，无口令） |
| 初始目录 | `/mnt/us/documents/books` |

> Kindle 的 IP 可能会变：在 KOReader 里打开 **工具 → 传书地址 / 手机 SFTP 信息**，第二行显示的就是当前 `SSH: root@IP -p 2222`（电脑端 Bookdrop 启动时会自动同步）。

连上后把电子书上传到 `/mnt/us/documents/books/`，KOReader 文件浏览器刷新即可看到。

## 前提条件

- Kindle 亮屏、KOReader 正在运行；
- KOReader 里 SSH 服务已启动（工具 → SSH server）；建议打开 **"Start SSH server with KOReader"**，以后一开 KOReader 就自动可用；
- 手机与 Kindle 连接同一个 Wi-Fi；
- Kindle 睡眠会断 Wi-Fi，先点亮屏幕。

## 备用方案：App 不支持私钥时

KOReader → 工具 → SSH → 打开 **"Login without password (DANGEROUS)"**，然后在 App 里用“用户名 + 密码”方式连接：用户名 `root`，密码随便填（如 `kindle`）。

⚠️ 这会让同一局域网内任何人都能 SSH 登录 Kindle，仅在完全信任的家庭网络里临时使用；用完记得关掉。

## 安全与撤销

- `phone_sftp_key.pem` 相当于手机登录 Kindle 的钥匙，别发到公开场合；
- 私钥泄露时：在电脑上运行下面命令删除对应的公钥授权即可（需要 Kindle 的 SSH 在线）：
  ```powershell
  cd D:\coding\kindle\tools
  .\Kindle-Push.ps1 -Status   # 确认在线
  ```
  或者让我帮你重写 `authorized_keys`（保留电脑端密钥、删除手机端密钥）。
- 电脑端仍保留自己的密钥，用于 Bookdrop 推送，二者互不影响。
