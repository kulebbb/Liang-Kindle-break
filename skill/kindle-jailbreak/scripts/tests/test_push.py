#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""可选：用 mock Kindle 验证 Bookdrop 的推送链路（无需真机）。

依赖：pip install paramiko
说明：mock 只实现最小 SFTP 子集；scp 在结束阶段可能报 "lost connection"，
但文件已完整写入，因此以「文件内容一致」为通过标准。
"""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[1]
sys.path.insert(0, str(TESTS))
from mock_kindle import MockKindle  # noqa: E402


def load_bookdrop():
    spec = importlib.util.spec_from_file_location("bookdrop", ROOT / "scripts" / "bookdrop.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    bd = load_bookdrop()
    key = Path(os.environ.get("LOCALAPPDATA", "")) / "KindleBookdrop" / "kindle_ed25519"
    if not key.exists():
        print("SKIP: 缺少 SSH 密钥，先运行 scripts/Setup-KindleSsh.ps1")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="mockkindle-"))
    mk = MockKindle(tmp / "kindle-docs")
    cfg = dict(bd.DEFAULT_CONFIG)
    cfg.update({
        "kindle_ip": "127.0.0.1",
        "ssh_port": mk.port,
        "ssh_key": str(key),
        "remote_dir": "/mnt/us/documents/books",
        "auto_push": True,
        "watch_library": False,
    })
    known_hosts = tmp / "known_hosts.txt"
    known_hosts.write_text("", encoding="utf-8")
    orig_base = bd.ssh_base

    def patched_base(c, port_flag="-p"):
        return orig_base(c, port_flag) + ["-o", "UserKnownHostsFile=" + str(known_hosts)]

    bd.ssh_base = patched_base
    name = "测试 电子书.epub"
    src = tmp / name
    payload = ("EPUB-TEST-CONTENT-" * 5000).encode("utf-8")
    src.write_bytes(payload)
    try:
        ok, msg = bd.push_files(cfg, [str(src)])
        print("push:", ok, msg)
        target = mk.root / name
        assert target.exists(), "目标文件不存在"
        assert target.read_bytes() == payload, "内容不一致"
        print("PUSH E2E PASSED（以文件内容为准）")
        return 0
    finally:
        mk.stop()
        bd.ssh_base = orig_base


if __name__ == "__main__":
    sys.exit(main())
