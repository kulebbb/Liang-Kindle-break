# assets 说明

| 文件 | 版本/来源 | 用途 | 许可 |
| --- | --- | --- | --- |
| wb2.zip | KindleModding/Winterbreak2 最新 release | WinterBreak2 浏览器越狱载荷（解压后为 winterbreak2/dialoger.html） | 社区项目 |
| koreader-kindlepw2-v2026.07.1.zip | KOReader 官方 release（固件 <5.16.3 用 pw2 包） | 离线安装 KOReader | GPLv3 |
| weread.koplugin-v1.6.0.zip | finlater/weread.koplugin release | KOReader 微信读书插件 | AGPL-3.0 |

## 更新方式

- 越狱包：<https://github.com/KindleModding/Winterbreak2/releases/latest>
- KOReader：<https://github.com/koreader/koreader/releases>（4 个 Kindle 包：固件 ≥5.16.3 用 kindlehf，其余触屏机用 kindlepw2）
- 微信读书插件：<https://github.com/finlater/weread.koplugin/releases>（需 KOReader ≥ 2026.03）

## 校验

```powershell
Get-FileHash assets\*.zip -Algorithm SHA256
```

下载后建议核对 GitHub release 页面公布的校验值（若有）。