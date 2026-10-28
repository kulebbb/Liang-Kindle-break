#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 Chrome/Edge 的 DevTools 协议读取 weread.qq.com 的登录 Cookie。

用法（由 weread-login.ps1 调用，也可手动）:
  python tools/cdp_cookies.py --port 9222 --timeout 300 --out cookies.json

前提：浏览器以 --remote-debugging-port=9222 启动，且用户已在其中登录 https://weread.qq.com
"""
import argparse
import json
import sys
import time
import urllib.request

try:
    import websocket
except ImportError:
    print("缺少 websocket-client：python -m pip install websocket-client", file=sys.stderr)
    sys.exit(3)

WANTED = ("wr_vid", "wr_gid", "wr_skey", "wr_rt", "wr_ql", "wr_fp")


def http_json(url, timeout=3):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_page(port):
    targets = http_json("http://127.0.0.1:%d/json/list" % port)
    for t in targets:
        if t.get("type") == "page" and "weread.qq.com" in (t.get("url") or ""):
            return t
    for t in targets:
        if t.get("type") == "page":
            return t
    return None


def rpc(ws, msg_id, method, params=None):
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    deadline = time.time() + 5
    while time.time() < deadline:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id:
            return data
    return None


def fetch_cookies(port):
    page = find_page(port)
    if not page:
        return None
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=5)
    try:
        rpc(ws, 1, "Network.enable")
        resp = rpc(ws, 2, "Network.getCookies", {
            "urls": ["https://weread.qq.com/", "https://i.weread.qq.com/"]
        })
        cookies = (resp or {}).get("result", {}).get("cookies", [])
        return {c["name"]: c["value"] for c in cookies}
    finally:
        ws.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    deadline = time.time() + args.timeout
    last = {}
    while time.time() < deadline:
        try:
            cookies = fetch_cookies(args.port)
        except Exception as exc:  # 浏览器还没起好/页面还没打开
            last = {"error": str(exc)}
            time.sleep(2)
            continue
        if cookies is None:
            time.sleep(2)
            continue
        got = {k: v for k, v in cookies.items() if k in WANTED and v}
        last = got
        if got.get("wr_vid") and (got.get("wr_skey") or got.get("wr_gid")):
            out = {"ok": True, "cookies": got, "all_wr": {k: v for k, v in cookies.items() if k.startswith("wr_")}}
            text = json.dumps(out, ensure_ascii=False, indent=2)
            if args.out:
                open(args.out, "w", encoding="utf-8").write(text)
            print(text)
            return 0
        time.sleep(2)
    print(json.dumps({"ok": False, "last": last}, ensure_ascii=False), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
