#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 KOReader Profiles「统一版式」并（可选）开启 ReaderReady 自动执行。

用法（一般由 Install-KoreaderProfile.ps1 调用）：
  python patch_koreader_profile.py <kindle根目录> [profile名] [字号] [行距%] [左右边距] [上边距] [下边距]
"""
import os
import sys


def lua_str(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def build_profiles(name, font_size, line_spacing, h_margin, t_margin, b_margin):
    return (
        "-- ./settings/profiles.lua\n"
        "return {\n"
        "    [%s] = {\n"
        "        [\"b_page_margin\"] = %d,\n"
        "        [\"font_size\"] = %d,\n"
        "        [\"h_page_margins\"] = {\n"
        "            [1] = %d,\n"
        "            [2] = %d,\n"
        "        },\n"
        "        [\"line_spacing\"] = %d,\n"
        "        [\"settings\"] = {\n"
        "            [\"name\"] = %s,\n"
        "            [\"order\"] = {\n"
        "                \"font_size\",\n"
        "                \"line_spacing\",\n"
        "                \"h_page_margins\",\n"
        "                \"t_page_margin\",\n"
        "                \"b_page_margin\",\n"
        "            },\n"
        "        },\n"
        "        [\"t_page_margin\"] = %d,\n"
        "    },\n"
        "}\n"
    ) % (lua_str(name), b_margin, font_size, h_margin, h_margin,
         line_spacing, lua_str(name), t_margin)


def patch_autoexec(settings_text, name):
    anchor = '["profiles_autoexec"] = {},'
    if anchor not in settings_text:
        return None, "settings.reader.lua 中的 profiles_autoexec 不是空表，请手动在 Profiles 菜单开启自动执行"
    block = ('["profiles_autoexec"] = {\n'
             '        ["ReaderReady"] = {\n'
             '            [%s] = true,\n'
             '        },\n'
             '    },' % lua_str(name))
    return settings_text.replace(anchor, block), "autoexec 已开启（ReaderReady）"


def main():
    root = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "统一版式"
    font_size = int(sys.argv[3]) if len(sys.argv) > 3 else 28
    line_spacing = int(sys.argv[4]) if len(sys.argv) > 4 else 115
    h_margin = int(sys.argv[5]) if len(sys.argv) > 5 else 20
    t_margin = int(sys.argv[6]) if len(sys.argv) > 6 else 50
    b_margin = int(sys.argv[7]) if len(sys.argv) > 7 else 50

    settings_dir = os.path.join(root, "koreader", "settings")
    settings_file = os.path.join(root, "koreader", "settings.reader.lua")
    profiles_file = os.path.join(settings_dir, "profiles.lua")
    if not os.path.isdir(settings_dir):
        raise SystemExit("找不到 koreader/settings 目录：%s" % settings_dir)
    if not os.path.isfile(settings_file):
        raise SystemExit("找不到 settings.reader.lua：%s" % settings_file)

    with open(profiles_file, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_profiles(name, font_size, line_spacing, h_margin, t_margin, b_margin))
    print("已写入 profiles.lua（Profile: %s）" % name)

    text = open(settings_file, encoding="utf-8-sig").read()
    patched, message = patch_autoexec(text, name)
    if patched is None:
        print("提示：" + message)
    else:
        with open(settings_file, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(patched)
        print(message)
    print("OK")


if __name__ == "__main__":
    main()
