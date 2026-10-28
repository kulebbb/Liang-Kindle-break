# 01 · WinterBreak2 越狱（实测 Kindle 8 / KT3 / 5.16.2.1.1）

## 适用性

| 项 | 值 |
| --- | --- |
| 支持固件 | 5.6.1.1 – 5.16.3（KindleModding wizard 数据，2026-10） |
| 实测机型 | Kindle 8th gen（代号 KT3），固件 5.16.2.1.1 |
| 是否要求注册 Amazon | 否（对国区停服设备友好） |
| 是否要求无广告版 | 不强制 |
| 官方指南 | https://kindlemodding.org/jailbreaking/WinterBreak2/ |

WinterBreak 原始版（商城 Mesquite 路径）在 5.18.1+ 被修复；本文的 WinterBreak2 走实验性浏览器路径，兼容上限 5.16.3。

## 原理（简述）

1. 实验性浏览器下载 `/wb2p` 返回的 0 字节 "mobi"，其 `Content-Disposition` 文件名里注入了 `<script>`；
2. 下载确认弹窗渲染文件名时执行脚本，通过 `com.lab126.pillow` 的 `customDialog` 打开 Kindle 根目录下的 `winterbreak2/dialoger.html`；
3. `dialoger.html` 用 `nativeBridge` 调起 `com.lab126.transfer` 的 `request_upload`，`source_command` 用 curl 拉取 `jb.sh` 并执行，完成越狱、装 KPM、封锁 OTA。

因此**必须**先把 `winterbreak2/dialoger.html` 放到 Kindle 根目录，且 Kindle 浏览器能访问外网。

## 实际步骤（含现象）

1. 清理 Kindle 根目录里遗留的 `*.bin` 更新文件（本次有一个 `._update_kindle_8th_5.11.2.bin`，删除）；
2. 数据线连接电脑，运行 `scripts/Prime-Kindle.ps1`（等价于把 `assets/wb2.zip` 解压到 Kindle 根目录）；
   校验：根目录出现 `winterbreak2\dialoger.html`（627 字节）；
3. 安全弹出，Kindle 连 Wi-Fi；
4. 打开实验性浏览器：`菜单 → 实验性浏览器`（部分固件在 设置 → 设备选项 → 高级）；
5. 访问 `https://penguins184.xyz/wb2`，点 **Jailbreak**；
6. 现象：浏览器下载了一个 `Winterbreak2.mobi`；随后屏幕出现黑色日志文字并自动重启；
7. 验证：主页搜索框输入 `;kpm` 回车，出现：
   ```
   kindle package manager v0.2.4
   ```
   即越狱成功（同时 OTA 已自动封锁）。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 只下载 mobi、没日志没重启 | 确认 `winterbreak2` 在根目录且完整；重启 Kindle 后重试；确认 Wi-Fi 可访问外网 |
| 浏览器打不开 penguins184.xyz | 换网络（手机热点）、重启；注意该页由社区托管，国内访问可能不稳 |
| 点 Jailbreak 没反应 | 检查是否被当成普通搜索；重进页面；确认 `;kpm` 无输出 |
| 越狱后仍提示更新 | 删除根目录 `*.bin`；填满存储可临时阻止 OTA |

## 风险与回退

- 风险：失去保修；极小概率变砖（可恢复）；越狱本身不改变分区与固件。
- 回退步骤：
  1. 运行卸载 scriptlet：<https://kindlemodding.org/jailbreaking/ota.sh>
  2. 恢复出厂设置；
  3. 从 <https://ftvdb.com/kindle/firmware/> 下载对应机型/固件版本的 `update_*.bin`，放根目录，`设置 → 更新你的 Kindle` 推送同版本固件。
  4. 详细说明：<https://kindlemodding.org/jailbreaking/unjailbreaking.html>

## 参考

- <https://kindlemodding.org/jailbreaking/WinterBreak2/>
- <https://kindlemodding.org/jailbreak-wizard.html>（按序列号+固件判断该用哪个越狱）
- 机制解读：<https://blindwith.science/2026/09/489.html/>