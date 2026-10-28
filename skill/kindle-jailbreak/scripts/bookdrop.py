#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bookdrop — 局域网传书工具（Kindle + KOReader SSH）。

用法:
  python tools/bookdrop.py                # 启动上传页 + 监视 library/ 自动推送
  python tools/bookdrop.py --no-push      # 只当 HTTP 文件页（Kindle 浏览器下载用）
  python tools/bookdrop.py --selftest     # 自检（不需要 Kindle）

工作原理:
  1. 浏览器/资源管理器把书放进 library/（网页拖拽或直接拷贝）
  2. 脚本检测到新文件，用 scp 通过 KOReader 的 SSH 服务推到 Kindle
  3. Kindle 的 KOReader 刷新目录即可看到
"""
import argparse
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "scripts"
CONFIG_PATH = TOOLS / "kindle-config.json"
LIB = ROOT / "library"
LOGS = ROOT / "logs"

DEFAULT_CONFIG = {
    "kindle_ip": "",
    "ssh_port": 2222,
    "ssh_user": "root",
    "ssh_key": str(Path(os.environ.get("LOCALAPPDATA", "")) / "KindleBookdrop" / "kindle_ed25519"),
    "remote_dir": "/mnt/us/documents/books",
    "http_port": 8765,
    "auto_push": True,
    "watch_library": True,
}

STATE = {"pushed": set(), "last_push": "", "last_error": "", "qr_url": ""}


def log(msg):
    LOGS.mkdir(parents=True, exist_ok=True)
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg)
    print(line, flush=True)
    try:
        with open(LOGS / "bookdrop.log", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def cfg_load():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig")))
        except ValueError:
            log("配置 JSON 解析失败，使用默认配置")
    return cfg


def cfg_save(cfg):
    TOOLS.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def ssh_open(ip, port, timeout=0.35):
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def discover_ip(cfg):
    if cfg.get("kindle_ip"):
        return cfg["kindle_ip"]
    try:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=6).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    port = int(cfg.get("ssh_port", 2222))
    for ip in re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+[0-9a-fA-F-]{17}\s+dynamic", out):
        if ssh_open(ip, port):
            cfg["kindle_ip"] = ip
            cfg_save(cfg)
            log("自动发现 Kindle: " + ip)
            return ip
    return ""


def ssh_base(cfg, port_flag="-p"):
    key = Path(cfg.get("ssh_key") or "")
    if str(key) in ("", "."):
        local = os.environ.get("LOCALAPPDATA", "")
        key = (Path(local) / "KindleBookdrop" / "kindle_ed25519") if local else Path("/nonexistent")
    elif not key.is_absolute():
        key = ROOT / key
    cmd = [port_flag, str(cfg["ssh_port"]), "-o", "StrictHostKeyChecking=accept-new",
           "-o", "BatchMode=yes", "-o", "ConnectTimeout=6"]
    if key.exists():
        cmd += ["-i", str(key), "-o", "IdentitiesOnly=yes"]
    return cmd


def scp_cmd(cfg, sources, legacy=False):
    cmd = ["scp"] + (["-O"] if legacy else []) + ssh_base(cfg, "-P") + ["-r"]
    cmd += [str(Path(s)) for s in sources]
    cmd.append("%s@%s:%s/" % (cfg["ssh_user"], cfg["kindle_ip"], cfg["remote_dir"].rstrip("/")))
    return cmd


def ensure_remote_dir(cfg):
    try:
        subprocess.run(["ssh"] + ssh_base(cfg) + ["%s@%s" % (cfg["ssh_user"], cfg["kindle_ip"]),
                                                   "mkdir -p " + cfg["remote_dir"]],
                       capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        pass


def push_files(cfg, files):
    files = [f for f in files if Path(f).exists()]
    if not files:
        return False, "没有可推送的文件"
    if not cfg.get("kindle_ip"):
        ip = discover_ip(cfg)
        if not ip:
            STATE["last_error"] = "找不到 Kindle（KOReader 的 SSH 服务没开，或不在同一网络）"
            return False, STATE["last_error"]
    ensure_remote_dir(cfg)
    last_err = ""
    for legacy in (False, True):
        cmd = scp_cmd(cfg, files, legacy)
        log("推送: " + " ".join(cmd))
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except (OSError, subprocess.SubprocessError) as exc:
            last_err = str(exc)
            continue
        if res.returncode == 0:
            STATE["pushed"].update(str(Path(f).resolve()) for f in files)
            STATE["last_push"] = time.strftime("%H:%M:%S") + " " + ", ".join(Path(f).name for f in files)
            STATE["last_error"] = ""
            return True, "已推送 %d 个文件" % len(files)
        last_err = (res.stderr or res.stdout).strip()[-400:]
    STATE["last_error"] = last_err or "推送失败"
    return False, STATE["last_error"]


def library_files():
    LIB.mkdir(parents=True, exist_ok=True)
    items = []
    for f in sorted(LIB.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.is_file() and not f.name.startswith("."):
            st = f.stat()
            items.append({"name": f.name, "size": st.st_size, "mtime": time.strftime("%m-%d %H:%M", time.localtime(st.st_mtime))})
    return items


def lan_ips():
    ips = []
    try:
        out = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=6).stdout
        for ip in re.findall(r"IPv4[^:]*:\s*((?:\d{1,3}\.){3}\d{1,3})", out):
            if not ip.startswith(("127.", "169.254.")):
                ips.append(ip)
    except (OSError, subprocess.SubprocessError):
        pass
    return ips


def shq(text):
    return "'" + str(text).replace("'", "'\\''") + "'"


def local_url(cfg):
    for ip in lan_ips():
        if not ip.startswith("127."):
            return "http://%s:%d" % (ip, int(cfg.get("http_port", 8765)))
    return ""


def sync_url_to_kindle(cfg, url=None):
    url = url or local_url(cfg)
    if not url:
        return False, "没有可用的局域网地址"
    if not cfg.get("kindle_ip"):
        discover_ip(cfg)
    if not cfg.get("kindle_ip"):
        return False, "找不到 Kindle（请先在 KOReader 里启动 SSH）"
    ssh_info = "SSH: %s@%s -p %s" % (cfg["ssh_user"], cfg["kindle_ip"], cfg["ssh_port"])
    cmd = ["ssh"] + ssh_base(cfg) + [
        "%s@%s" % (cfg["ssh_user"], cfg["kindle_ip"]),
        "echo " + shq(url) + " > /mnt/us/koreader/bookdrop_url.txt && echo "
        + shq(ssh_info) + " >> /mnt/us/koreader/bookdrop_url.txt",
    ]
    log("同步二维码地址: " + url)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    if res.returncode != 0:
        return False, (res.stderr or res.stdout).strip()[-200:]
    STATE["qr_url"] = url
    return True, url


def page_html():
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bookdrop · 局域网传书</title>
<style>
 body{font-family:system-ui,-apple-system,'Microsoft YaHei',sans-serif;margin:0;background:#f5f6f8;color:#222}
 header{background:#1f2937;color:#fff;padding:16px 24px}
 header h1{margin:0;font-size:20px}
 main{max-width:820px;margin:24px auto;padding:0 16px}
 #drop{border:3px dashed #94a3b8;border-radius:14px;background:#fff;padding:48px 16px;text-align:center;color:#64748b;cursor:pointer;transition:.2s}
 #drop.hover{border-color:#3b82f6;background:#eff6ff;color:#2563eb}
 #drop b{color:#1f2937}
 #meta{margin:14px 0;color:#475569;font-size:14px}
 .card{background:#fff;border-radius:12px;padding:16px 20px;margin-top:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .card h2{font-size:16px;margin:0 0 12px}
 ul{list-style:none;margin:0;padding:0}
 li{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9;font-size:14px}
 li:last-child{border-bottom:none}
 li a{color:#2563eb;text-decoration:none}
 .muted{color:#94a3b8;font-size:12px}
 .err{color:#dc2626;font-size:13px;white-space:pre-wrap}
 .ok{color:#16a34a}
 #log{font-size:13px;color:#475569;white-space:pre-wrap;min-height:20px}
 button{border:0;border-radius:8px;padding:8px 14px;background:#2563eb;color:#fff;font-size:14px;cursor:pointer}
 button.ghost{background:#e2e8f0;color:#1f2937}
 input[type=text]{padding:8px;border:1px solid #cbd5e1;border-radius:8px;width:200px}
</style></head><body>
<header><h1>📚 Bookdrop — 局域网传书</h1></header>
<main>
 <div id="drop">把电子书拖到这里，或 <b>点击选择文件</b><br><span class="muted">EPUB / MOBI / AZW3 / PDF / TXT 都行；保存后会自动推送到 Kindle</span></div>
 <div id="meta">状态：<span id="status">连接中…</span></div>
 <div id="log"></div>
 <div class="card"><h2>Kindle 连接</h2>
   <div id="kindleinfo" class="muted"></div>
   <div style="margin-top:10px">Kindle IP：<input type="text" id="ip" placeholder="自动发现">
     <button id="saveip" class="ghost">保存</button>
     <button id="pushall">推送全部</button> <button id="syncqr" class="ghost">同步二维码</button></div>
 </div>
 <div class="card"><h2>书库（Kindle 浏览器也可直接下载）</h2><ul id="files"></ul></div>
</main>
<script>
const $=s=>document.querySelector(s);
async function refresh(){
  try{
    const r=await fetch('/api/status'); const j=await r.json();
    $('#status').innerHTML = j.kindle.reachable ? '<span class="ok">Kindle 在线 '+(j.kindle.ip||'')+'</span>' : '<span class="err">Kindle 离线（KOReader SSH 未开启？）</span>';
    $('#kindleinfo').textContent = '目标目录 '+j.config.remote_dir+' · 端口 '+j.config.ssh_port+(j.last_push?' · 上次推送 '+j.last_push:'');
    $('#ip').value = j.config.kindle_ip||'';
    $('#files').innerHTML = j.files.length ? j.files.map(f=>'<li><span>'+f.name+'</span><span class="muted">'+f.mtime+' · '+(f.size/1024).toFixed(0)+' KB · <a href="/files/'+encodeURIComponent(f.name)+'">下载</a></span></li>').join('') : '<li class="muted">还没有书</li>';
    if(j.last_error) $('#log').textContent = '⚠ '+j.last_error;
  }catch(e){ $('#status').textContent='服务未响应'; }
}
const drop=$('#drop');
drop.addEventListener('click',()=>{const i=document.createElement('input');i.type='file';i.multiple=true;i.onchange=()=>upload(i.files);i.click()});
['dragenter','dragover'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('hover')}));
['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('hover')}));
drop.addEventListener('drop',e=>upload(e.dataTransfer.files));
async function upload(files){
  $('#log').textContent='';
  for(const f of files){
    $('#log').textContent='上传 '+f.name+' …';
    const r=await fetch('/upload?name='+encodeURIComponent(f.name),{method:'POST',body:f});
    const j=await r.json();
    $('#log').textContent = j.ok ? ('✓ '+f.name+' 已保存'+(j.push?'，'+j.push:'')) : ('✗ '+f.name+'：'+j.error);
  }
  refresh();
}
$('#saveip').onclick=async()=>{await fetch('/api/config',{method:'POST',body:JSON.stringify({kindle_ip:$('#ip').value.trim()})});refresh()};
$('#pushall').onclick=async()=>{await fetch('/api/push',{method:'POST'});refresh()};
$('#syncqr').onclick=async()=>{const r=await fetch('/api/sync',{method:'POST'});const j=await r.json();$('#log').textContent=j.ok?('二维码地址已同步到 Kindle: '+j.message):('同步失败: '+j.message);refresh()};
refresh(); setInterval(refresh,4000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "Bookdrop/1.0"

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, page_html(), "text/html; charset=utf-8")
        elif path == "/api/status":
            cfg = self.server.cfg
            ip = cfg.get("kindle_ip") or ""
            reachable = bool(ip) and ssh_open(ip, int(cfg["ssh_port"]))
            if not reachable:
                found = discover_ip(cfg)
                reachable = bool(found) and ssh_open(found, int(cfg["ssh_port"]))
                ip = found or ip
            self._json(200, {"ok": True, "config": cfg, "kindle": {"ip": ip, "reachable": reachable},
                             "files": library_files(), "last_push": STATE["last_push"],
                             "last_error": STATE["last_error"], "qr_url": STATE.get("qr_url", "")})
        elif path.startswith("/files/"):
            name = unquote(path[len("/files/"):])
            target = LIB / name
            if target.is_file() and target.parent == LIB:
                self._send(200, target.read_bytes(), "application/octet-stream")
            else:
                self._send(404, "not found", "text/plain; charset=utf-8")
        else:
            self._send(404, "not found", "text/plain; charset=utf-8")

    def do_POST(self):
        parsed = urlparse(self.path)
        cfg = self.server.cfg
        if parsed.path == "/upload":
            name = Path(unquote(parsed.query.split("name=")[-1])).name if "name=" in parsed.query else "unnamed"
            length = int(self.headers.get("Content-Length") or 0)
            LIB.mkdir(parents=True, exist_ok=True)
            target = LIB / name
            remaining = length
            with open(target, "wb") as fh:
                while remaining > 0:
                    chunk = self.rfile.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    fh.write(chunk)
                    remaining -= len(chunk)
            log("收到文件: %s (%d bytes)" % (name, target.stat().st_size))
            push_msg = ""
            if cfg.get("auto_push", True):
                ok, msg = push_files(cfg, [target])
                push_msg = msg
                log("推送结果: " + msg)
            self._json(200, {"ok": True, "saved": name, "push": push_msg})
        elif parsed.path == "/api/sync":
            ok, msg = sync_url_to_kindle(cfg)
            self._json(200, {"ok": ok, "message": msg})
        elif parsed.path == "/api/push":
            files = [str(p) for p in LIB.iterdir() if p.is_file()] if LIB.exists() else []
            ok, msg = push_files(cfg, files)
            self._json(200, {"ok": ok, "message": msg})
        elif parsed.path == "/api/config":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                body = {}
            for k in ("kindle_ip", "ssh_port", "ssh_user", "remote_dir", "auto_push"):
                if k in body:
                    cfg[k] = body[k]
            cfg_save(cfg)
            self._json(200, {"ok": True, "config": cfg})
        else:
            self._send(404, "not found", "text/plain; charset=utf-8")

    def log_message(self, fmt, *args):
        pass


def watch_loop(server):
    cfg = server.cfg
    seen = set()
    if LIB.exists():
        for existing in LIB.iterdir():
            if existing.is_file():
                seen.add(str(existing.resolve()))
    while True:
        try:
            if LIB.exists():
                for f in LIB.iterdir():
                    if not f.is_file() or f.name.startswith("."):
                        continue
                    key = str(f.resolve())
                    if key in seen:
                        continue
                    seen.add(key)
                    if cfg.get("watch_library", True) and cfg.get("auto_push", True):
                        ok, msg = push_files(cfg, [f])
                        log("监视到新文件 %s -> %s" % (f.name, msg))
        except OSError:
            pass
        time.sleep(4)


def run_server(cfg, port):
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.cfg = cfg
    threading.Thread(target=watch_loop, args=(server,), daemon=True).start()
    return server


def selftest():
    import tempfile
    from urllib.request import urlopen, Request
    LIB.mkdir(parents=True, exist_ok=True)
    test_name = "selftest-%d.epub" % int(time.time())
    port = 18765
    selftest_cfg = cfg_load()
    selftest_cfg.update({"auto_push": False, "watch_library": False})
    server = run_server(selftest_cfg, port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        payload = b"BOOKDROP-SELFTEST" * 1000
        req = Request("http://127.0.0.1:%d/upload?name=%s" % (port, quote(test_name)), data=payload, method="POST")
        with urlopen(req, timeout=10) as resp:
            up = json.loads(resp.read().decode("utf-8"))
        print("upload:", up)
        assert up.get("ok")
        with urlopen("http://127.0.0.1:%d/api/status" % port, timeout=10) as resp:
            st = json.loads(resp.read().decode("utf-8"))
        names = [f["name"] for f in st["files"]]
        assert test_name in names, names
        with urlopen("http://127.0.0.1:%d/files/%s" % (port, quote(test_name)), timeout=10) as resp:
            data = resp.read()
        assert data == payload
        print("status/library/download: OK")
        with urlopen("http://127.0.0.1:%d/" % port, timeout=10) as resp:
            html = resp.read()
        assert b"Bookdrop" in html, "page html broken"
        (LIB / test_name).unlink()
        print("SELFTEST PASSED")
    finally:
        server.shutdown()


def main():
    ap = argparse.ArgumentParser(description="Bookdrop 局域网传书")
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--no-watch", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    LIB.mkdir(parents=True, exist_ok=True)
    if args.selftest:
        selftest()
        return
    cfg = cfg_load()
    if args.port:
        cfg["http_port"] = args.port
    if args.no_push:
        cfg["auto_push"] = False
    if args.no_watch:
        cfg["watch_library"] = False
    port = int(cfg["http_port"])
    server = run_server(cfg, port)
    log("Bookdrop 启动，端口 %d" % port)
    threading.Thread(target=lambda: log("二维码同步: " + str(sync_url_to_kindle(cfg))), daemon=True).start()
    print("本机访问: http://127.0.0.1:%d" % port)
    for ip in lan_ips():
        print("手机/Kindle 访问: http://%s:%d" % (ip, port))
    try:
        import webbrowser
        webbrowser.open("http://127.0.0.1:%d" % port)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("用户中断，退出")


if __name__ == "__main__":
    main()
