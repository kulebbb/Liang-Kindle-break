#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小化 SSH/SFTP 服务器，模拟 Kindle 上 KOReader 的 SSH 服务，用于本地联调测试。

它不是完整实现，只支持：publickey 认证、sftp 子系统（读/写/stat/列表）、拒绝 exec。
用于验证 Bookdrop/Kindle-Push 的 scp 推送链路，不依赖真实设备。
"""
import os
import socket
import threading
from pathlib import Path

import paramiko
from paramiko import (
    AUTH_FAILED,
    AUTH_SUCCESSFUL,
    OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED,
    OPEN_SUCCEEDED,
)
from paramiko.sftp import SFTP_FAILURE, SFTP_FLAG_APPEND, SFTP_FLAG_READ, SFTP_FLAG_WRITE, SFTP_OK, SFTP_NO_SUCH_FILE
from paramiko.sftp_handle import SFTPHandle
from paramiko.sftp_server import SFTPServer

VIRTUAL_ROOT = "/mnt/us/documents/books"


class _Handle(SFTPHandle):
    def __init__(self, flags, fobj):
        super().__init__(flags)
        self.fobj = fobj

    def read(self, offset, length):
        try:
            self.fobj.seek(offset)
            return self.fobj.read(length)
        except OSError:
            return SFTP_FAILURE

    def write(self, offset, data):
        try:
            self.fobj.seek(offset)
            self.fobj.write(data)
            return SFTP_OK
        except OSError:
            return SFTP_FAILURE

    def close(self):
        try:
            self.fobj.close()
        except OSError:
            pass
        return SFTP_OK

    def stat(self):
        try:
            return paramiko.SFTPAttributes.from_stat(os.fstat(self.fobj.fileno()))
        except OSError:
            return SFTP_FAILURE

    def chattr(self, attr):
        # scp 上传完成后会 fsetstat 设置权限/时间，接受即可
        return SFTP_OK


class LocalFS(paramiko.SFTPServerInterface):
    def __init__(self, server, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _map(self, path):
        p = (path or "/").replace("\\", "/").lstrip("/")
        if p == VIRTUAL_ROOT.lstrip("/"):
            p = ""
        elif p.startswith(VIRTUAL_ROOT.lstrip("/") + "/"):
            p = p[len(VIRTUAL_ROOT.lstrip("/")) + 1:]
        else:
            for prefix in ("/mnt/us/documents", "/mnt/us", ""):
                pre = prefix.lstrip("/")
                if pre and (p == pre or p.startswith(pre + "/")):
                    p = p[len(pre):].lstrip("/")
                    break
        target = (self.root / p).resolve()
        if target != self.root and self.root not in target.parents:
            raise OSError("path escape")
        return target

    def _virtual(self, local):
        local = Path(local).resolve()
        if local == self.root:
            return VIRTUAL_ROOT
        return VIRTUAL_ROOT + "/" + str(local.relative_to(self.root)).replace("\\", "/")

    def canonicalize(self, path):
        return self._virtual(self._map(path))

    def stat(self, path):
        try:
            return paramiko.SFTPAttributes.from_stat(self._map(path).stat())
        except OSError:
            return SFTP_NO_SUCH_FILE

    def lstat(self, path):
        return self.stat(path)

    def list_folder(self, path):
        try:
            local = self._map(path)
            return [paramiko.SFTPAttributes.from_stat((local / n).stat(), n) for n in os.listdir(local)]
        except OSError:
            return SFTP_NO_SUCH_FILE

    def open(self, path, flags, attr):
        try:
            local = self._map(path)
            local.parent.mkdir(parents=True, exist_ok=True)
            # 兼容 paramiko >= 5（服务端传入的是 os.open 标志）与旧版（SFTP 标志）
            os_flag_bits = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            if flags & os_flag_bits:
                writing = bool(flags & (os.O_WRONLY | os.O_RDWR))
                reading = bool(flags & os.O_RDWR)
                appending = bool(flags & os.O_APPEND)
            else:
                writing = bool(flags & SFTP_FLAG_WRITE)
                reading = bool(flags & SFTP_FLAG_READ)
                appending = bool(flags & SFTP_FLAG_APPEND)
            if writing:
                if reading:
                    mode = "r+b" if local.exists() else "w+b"
                elif appending:
                    mode = "ab"
                else:
                    mode = "wb"
            else:
                mode = "rb"
            return _Handle(flags, open(local, mode))
        except OSError:
            return SFTP_FAILURE

    def mkdir(self, path, attr):
        try:
            self._map(path).mkdir(parents=True, exist_ok=True)
            return SFTP_OK
        except OSError:
            return SFTP_FAILURE

    def remove(self, path):
        try:
            self._map(path).unlink()
            return SFTP_OK
        except OSError:
            return SFTP_FAILURE

    def rename(self, oldpath, newpath):
        try:
            self._map(oldpath).rename(self._map(newpath))
            return SFTP_OK
        except OSError:
            return SFTP_FAILURE

    def chattr(self, path, attr):
        return SFTP_OK


class _Server(paramiko.ServerInterface):
    def check_auth_publickey(self, username, key):
        return AUTH_SUCCESSFUL

    def check_auth_none(self, username):
        return AUTH_FAILED

    def get_allowed_auths(self, username):
        return "publickey"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return OPEN_SUCCEEDED
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_exec_request(self, channel, command):
        # 不支持 exec（真实设备支持 mkdir -p，这里只用于验证 scp）
        return False


class MockKindle:
    def __init__(self, root, port=0):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(10)
        self.port = self.sock.getsockname()[1]
        self.host_key = paramiko.RSAKey.generate(2048)
        self.transports = []
        self._stop = False
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while not self._stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            try:
                t = paramiko.Transport(conn)
                t.add_server_key(self.host_key)
                t.set_subsystem_handler("sftp", SFTPServer, LocalFS, str(self.root))
                t.start_server(server=_Server())
                self.transports.append(t)
            except Exception:
                try:
                    conn.close()
                except OSError:
                    pass

    def stop(self):
        self._stop = True
        try:
            self.sock.close()
        except OSError:
            pass
        for t in self.transports:
            try:
                t.close()
            except Exception:
                pass
