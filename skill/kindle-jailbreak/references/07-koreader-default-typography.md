# 07 · 统一版式：Profiles 自动套用（字号/行距/边距）

## 问题

KOReader 的版式设置默认**按书保存**（存在 `书.sdr/metadata.*.lua` 里），所以每本书都要重设字号、行距、页边距。
「文档设置 → 保存文档设置为默认」只影响**之后新打开**的书，已经读过的书仍各自带旧设置。

## 方案：Profiles + ReaderReady 自动执行

创建一个 Profile「统一版式」，并把它挂到 `ReaderReady` 事件上；每次打开文档时自动套用。

### 一键脚本

前置：**退出 KOReader**（KOReader 运行时会屏蔽 USB 存储，且 SSH 也会随 KOReader 退出而停止），
再插数据线让 Kindle 以 USB 盘符出现。

```powershell
cd skill\kindle-jailbreak\scripts
.\Install-KoreaderProfile.ps1
# 自定义参数示例：
.\Install-KoreaderProfile.ps1 -FontSize 24 -LineSpacing 120 -HMargin 10 -TopMargin 50 -BottomMargin 50
```

脚本会：
1. 备份 `koreader/settings/profiles.lua` 与 `koreader/settings.reader.lua`（`.bak-时间戳`）；
2. 生成 Profile（默认名「统一版式」）：`font_size` / `line_spacing` / `h_page_margins` / `t_page_margin` / `b_page_margin`；
3. 把 `settings.reader.lua` 里的 `["profiles_autoexec"] = {}` 替换为：

```lua
["profiles_autoexec"] = {
    ["ReaderReady"] = {
        ["统一版式"] = true,
    },
},
```

4. 如果 `profiles_autoexec` 已经非空（有其他自动执行配置），脚本不会覆盖，会提示你到
   `工具 → Profiles → Auto-execute` 手动勾选。

### 生成的 profiles.lua 结构（供手写/排查参考）

```lua
return {
    ["统一版式"] = {
        ["b_page_margin"] = 50,
        ["font_size"] = 28,
        ["h_page_margins"] = { [1] = 20, [2] = 20 },
        ["line_spacing"] = 115,
        ["settings"] = {
            ["name"] = "统一版式",
            ["order"] = {
                "font_size", "line_spacing", "h_page_margins",
                "t_page_margin", "b_page_margin",
            },
        },
        ["t_page_margin"] = 50,
    },
}
```

要点：
- `settings.order` 决定 Dispatcher 执行顺序，必须包含所有要执行的项；
- 名字不带 `copt_` 前缀（Profile 用 document.configurable 的名字）；
- 只对 **EPUB 等滚动排版文档**（`copt_*`）有效；PDF（`kopt_*`）需要另建 Profile。

## 验证

1. 拔线，打开 KOReader，打开任意一本书；
2. 点顶部 → 字体（Aa）→ 字号应为 28；行距/边距同步变化；
3. 或进 排版 → 文档设置 查看当前值。

如未生效，检查：
- `koreader/crash.log` 是否有 Profiles/Dispatcher 报错；
- `settings.reader.lua` 里 `profiles_autoexec` 是否包含 `ReaderReady`；
- Profiles 插件是否被禁用（`plugins_disabled`）。

## 调整 / 关闭 / 回滚

- 调整：KOReader → 工具 → Profiles → 「统一版式」可编辑，或重跑脚本换参数；
- 关闭自动执行：Profiles → Auto-execute → 取消 `ReaderReady` 下的勾选（仍可手动执行 Profile）；
- 回滚：把 `koreader/settings.reader.lua.bak-*`、`koreader/settings/profiles.lua.bak-*` 覆盖回去。

## 注意

- 自动执行会在**每次打开书**时套用，会覆盖你之前对单本书的手动调整（这正是「统一」的目的）；
- 只覆盖档位类设置（字号/行距/边距等），不影响阅读进度、标注、书签。
