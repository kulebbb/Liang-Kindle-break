#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 weread.lua 中写坏的 cookies 段（从现有内容里的 Python 字典字符串恢复）。"""
import re
import sys


def lua_str(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    src, api_key, out = sys.argv[1:4]
    text = open(src, encoding='utf-8').read()
    pairs = {}
    for m in re.finditer(r"'wr_(\w+)': '([^']*)'", text):
        pairs['wr_' + m.group(1)] = m.group(2)
    if 'wr_vid' not in pairs or not ('wr_skey' in pairs or 'wr_gid' in pairs):
        raise SystemExit('没有找到可恢复的 wr_* cookie 值')
    start = text.index('["cookies"] = {') + len('["cookies"] = {')
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    block = '["cookies"] = {\n' + '\n'.join(
        '        [%s] = %s,' % (lua_str(k), lua_str(v)) for k, v in pairs.items()
    ) + '\n    }'
    text = text[:start - len('["cookies"] = {')] + block + text[i:]
    text = re.sub(r'\["api_key"\] = "[^"]*",', lambda m: '["api_key"] = ' + lua_str(api_key) + ',', text)
    text = re.sub(r'\["user_vid"\] = "[^"]*",', lambda m: '["user_vid"] = ' + lua_str(pairs['wr_vid']) + ',', text)
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    print('fixed ->', out, 'cookies=', ','.join(pairs))


if __name__ == '__main__':
    main()
