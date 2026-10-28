# 03 · 微信读书插件：扫码 401 与 Cookie 绕行

## 症状

```
扫码登录失败: plugins/weread.koplugin/weread/lib/qr_login.lua:114: getLoginInfo failed: HTTP 401
```

## 原因（上游 bug）

微信读书在 2026-10-22 起不再给 `GET https://weread.qq.com/r/weread-skills` 下发会话 Cookie；
插件 `_begin_protocol()` 拿不到 `wr_*` 会话，轮询 `getLoginInfo` 被服务端以 `-2013 鉴权失败` 拒绝（HTTP 401），
且 `_poll_protocol()` 把 401 当致命错误直接中断。

上游 issue：<https://github.com/finlater/weread.koplugin/issues/214>（截至 2026-10-29 未修复）。
插件其余功能（书架、下载、进度）正常，缺的只是“扫码建立会话”。

## 绕行：手动写入 Cookie + API Key

插件配置在 `/mnt/us/koreader/settings/weread.lua`，关键字段：

```lua
["api_key"] = "wrk-...",              -- 手机端 微信读书 Skill 的 API Key
["cookies"] = {
    ["wr_vid"] = "...", ["wr_gid"] = "...", ["wr_skey"] = "...",
    ["wr_rt"] = "...", ["wr_ql"] = "0", ["wr_fp"] = "...",
},
["account"] = { ["user_vid"] = "...", ["login_method"] = "qr", ["login_time"] = ... },
["auth_schema_version"] = 1,
```

插件用 `wr_skey`(≥8) 或 `wr_gid`(≥5) 判断已登录；书架/书籍信息/进度走 Skill API（Bearer api_key），
章节内容等 web 接口需要 Cookie。

## 一键流程

1. 手机微信读书 App → 我 → 设置 → 微信读书 Skill → 获取 API Key（`wrk-` 开头）；
2. Kindle：KOReader → 工具 → SSH → 启动服务；
3. 电脑：

```powershell
.\Weread-Login.ps1
```

脚本流程：
1. 用临时 Edge/Chrome 配置启动 `--remote-debugging-port`，打开 `https://weread.qq.com`；
2. 通过 DevTools 协议（`cdp_cookies.py`）轮询 `Network.getCookies`，直到拿到 `wr_vid` + `wr_skey/wr_gid`；
3. 下载 Kindle 上的 `weread.lua`，用 `patch_weread_settings.py` 写入 api_key/cookies/user_vid/login_time；
4. scp 回 Kindle 并 chmod 777。

4. Kindle 重启 KOReader → 工具 → 微信读书 → 书架。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 浏览器窗口没弹出 | 检查 Edge/Chrome 路径；手动运行 `Weread-Login.ps1 -WaitSeconds 600` |
| 扫码后没抓到 Cookie | 确认登录成功（页面进入书架）；重试 |
| Cookie 过期（书架加载失败/401） | 重跑 `Weread-Login.ps1` 重新扫码 |
| weread.lua 被写坏 | 用 `fix_weread_settings.py` 从残留的字典字符串恢复，或删掉 cookies 段重跑 |
| 提示账号未开通 Skill | 手机端完成“获取 API Key”后重扫 |

## 安全与合规

- Cookie 是账号会话凭据，只会写入本机 Kindle 配置；不要外传；
- 失效：在浏览器/微信读书退出登录，或清空 weread.lua 的 cookies；
- 仅用于个人阅读；第三方插件非官方，存在账号风控与服务条款风险。