#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 API Key + 登录 Cookie 写入 Kindle 的 weread.lua（微信读书插件配置）。

用法：
  python patch_weread_settings.py <原werad.lua> <api_key> <cookies.json> <输出路径>
"""
import json
import re
import sys
import time


def lua_str(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    src, api_key, cookies_path, out = sys.argv[1:5]
    data = json.load(open(cookies_path, encoding='utf-8-sig'))
    cookies = data.get('cookies', data) if isinstance(data, dict) else {}
    if not isinstance(cookies, dict) or not cookies:
        raise SystemExit('cookies JSON 格式不对')
    text = open(src, encoding='utf-8').read()

    if '"cookies"' not in text or '"api_key"' not in text:
        raise SystemExit('输入文件不像 weread.lua')

    cookie_lines = "\n".join(
        '        [%s] = %s,' % (lua_str(k), lua_str(v)) for k, v in cookies.items() if v
    )
    text = re.sub(
        r'\["cookies"\] = \{[^}]*\},',
        lambda m: '["cookies"] = {\n' + cookie_lines + '\n    },',
        text,
    )
    text = re.sub(
        r'\["api_key"\] = "[^"]*",',
        lambda m: '["api_key"] = ' + lua_str(api_key) + ',',
        text,
    )
    text = re.sub(
        r'\["user_vid"\] = "[^"]*",',
        lambda m: '["user_vid"] = ' + lua_str(cookies.get('wr_vid', '')) + ',',
        text,
    )
    text = re.sub(r'\["login_method"\] = "[^"]*",', lambda m: '["login_method"] = "qr",', text)
    text = re.sub(
        r'\["login_time"\] = \d+,',
        lambda m: '["login_time"] = %d,' % int(time.time()),
        text,
    )
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    print('patched ->', out)


if __name__ == '__main__':
    main()


