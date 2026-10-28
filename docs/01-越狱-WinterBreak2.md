# 越狱：WinterBreak2（Kindle 8 / KT3，固件 5.16.2.1.1）

> 依据：https://kindlemodding.org/jailbreaking/WinterBreak2/
> 适用性：WinterBreak2 支持固件 5.6.1.1-5.16.3，支持机型包含 KT3（Kindle 8th gen），且不要求 Kindle 能注册 Amazon 账号。

## 风险与前提

- 越狱会失去 Amazon 保修；有极小概率设备异常（可恢复）。
- WinterBreak2 是浏览器型越狱，不刷固件、不改分区，风险相对低。
- 开始前：
  - Kindle 电量 > 50%，连好家里 Wi-Fi（SSID：恭禧发财）；
  - 电脑装好 7-Zip 或系统自带解压；
  - 先"填满设备"防止自动更新：在 Kindle 根目录放几个大文件（如 1GB 的视频/压缩包），把可用空间占满，完成后删除。参考 https://kindlemodding.org/jailbreaking/prevent-auto-update/

## 步骤

1. 下载：https://github.com/KindleModding/Winterbreak2/releases/latest/download/wb2.zip
   - 国内直连 GitHub 可能慢，可让电脑用代理下载好再拷过去。
2. 解压到 Kindle 根目录：USB 数据线连接电脑，把 wb2.zip 解压到 Kindle 根目录，完成后根目录应出现 winterbreak2 文件夹。
   - 电脑认不出 Kindle 时先排查线材/接口（充电线通常没有数据线芯）。
3. 弹出并联网：安全弹出 Kindle，确认 Kindle 已连 Wi-Fi 且能上网。
4. 打开实验性浏览器：菜单 → 实验性浏览器（部分固件在 设置 → 设备选项 → 高级 → 实验性浏览器）。
5. 访问越狱页：在地址栏输入 https://penguins184.xyz/wb2（要带 https）。
   - 打不开时：先确认 Kindle 能打开其他网站；重启后再试。该页由社区托管，国内网络可能不稳定。
6. 执行：点击页面上的 Jailbreak 按钮，等待流程跑完（会弹窗提示）。完成后越狱会自动封锁系统更新。
7. 收尾：删除 Kindle 根目录里的 *.bin 更新文件（如果有），删除填满空间用的临时文件。

## 验证越狱成功

- 回到主页，搜索框输入 ;kpm 后回车，屏幕上应出现命令反馈（而不是被当成普通搜索）。
- 或按 https://kindlemodding.org/jailbreaking/whats-next/installing-homebrew.html 确认 scriptlet 可用。

## 回退 / 卸载

1. 运行卸载 scriptlet：https://kindlemodding.org/jailbreaking/ota.sh
2. 恢复出厂设置；
3. 从 https://ftvdb.com/kindle/firmware/ 下载对应固件 update_*.bin 放到 Kindle 根目录，设置 → 更新你的 Kindle 推送同一版本固件。
详细：https://kindlemodding.org/jailbreaking/unjailbreaking.html

## 故障排查

| 现象 | 处理 |
| --- | --- |
| 浏览器打不开 penguins184.xyz | 换网络（手机热点）、重启 Kindle；确认 Wi-Fi 可访问外网 |
| 点 Jailbreak 没反应 | 确认 winterbreak2 在 Kindle 根目录且完整解压；重启后重试 |
| 越狱后更新仍在推送 | 先填满设备并删除根目录 *.bin；必要时重跑流程 |

> WinterBreak2 在本地网络完全不可用时再评估离线备选 LanguageBreak（支持 <=5.16.2.1.1，需恢复出厂 + 演示模式流程）。Link: https://kindlemodding.org/jailbreaking/Legacy/LanguageBreak.html

