#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端联调测试：Bookdrop 网页上传 → scp 推送到 mock Kindle（无需真实设备）。"""
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[1]
sys.path.insert(0, str(TESTS))
from mock_kindle import MockKindle  # noqa: E402


def load_bookdrop():
    spec = importlib.util.spec_from_file_location("bookdrop", ROOT / "tools" / "bookdrop.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    bd = load_bookdrop()
    key = Path(os.environ.get("LOCALAPPDATA", "")) / "KindleBookdrop" / "kindle_ed25519"
    if not key.exists():
        print("SKIP: 缺少 SSH 密钥，先运行 tools\\Setup-KindleSsh.ps1")
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="mockkindle-"))
    mk = MockKindle(tmp / "kindle-docs")
    cfg = dict(bd.DEFAULT_CONFIG)
    cfg.update({
        "kindle_ip": "127.0.0.1",
        "ssh_port": mk.port,
        "ssh_key": str(key),
        "remote_dir": "/mnt/us/documents/books",
        "http_port": 18999,
        "auto_push": True,
        "watch_library": False,
    })
    known_hosts = tmp / "known_hosts.txt"
    known_hosts.write_text("", encoding="utf-8")
    orig_base = bd.ssh_base

    def patched_base(c, port_flag="-p"):
        return orig_base(c, port_flag) + ["-o", "UserKnownHostsFile=" + str(known_hosts)]

    bd.ssh_base = patched_base
    server = bd.run_server(cfg, 18999)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    name = "测试 电子书.epub"
    try:
        payload = ("EPUB-TEST-CONTENT-" * 5000).encode("utf-8")
        req = Request("http://127.0.0.1:18999/upload?name=" + quote(name), data=payload, method="POST")
        with urlopen(req, timeout=60) as resp:
            up = json.loads(resp.read().decode("utf-8"))
        print("upload ->", up)
        assert up.get("ok"), up
        target = mk.root / name
        deadline = time.time() + 20
        while time.time() < deadline and not target.exists():
            time.sleep(0.2)
        assert target.exists(), "文件未出现在 mock Kindle: %s" % list(mk.root.rglob("*"))
        assert target.read_bytes() == payload, "推送内容不一致"
        with urlopen("http://127.0.0.1:18999/api/status", timeout=10) as resp:
            status = json.loads(resp.read().decode("utf-8"))
        assert status["kindle"]["reachable"], status
        print("STATUS ->", status["kindle"], "| last_push:", status["last_push"])
        print("PUSH E2E PASSED")
        return 0
    finally:
        server.shutdown()
        mk.stop()
        bd.ssh_base = orig_base
        lib_file = bd.LIB / name
        if lib_file.exists():
            lib_file.unlink()


if __name__ == "__main__":
    sys.exit(main())
