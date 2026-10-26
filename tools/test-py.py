#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
python/emos_sign.py 的离线回归测试（不打真实网络，mock 掉 urllib）。

    python3 tools/test-py.py              # 测仓库里的混淆产物
    python3 tools/test-py.py --src        # 测 src/ 里的可读源码

覆盖：没配 token / 签到成功 / 今日已签 / token 失效 / 主站超时切备用域名。
"""

import contextlib
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "scripts", "..", "python", "emos_sign.py")

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL") + "  " + name + (("  → " + str(detail)) if detail else ""))


class FakeResp:
    def __init__(self, status, body):
        self.status = status
        self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def run_case(routes, env_tokens, path):
    """routes: (url, method) -> (status, body)；返回 (退出码, 输出文本, 访问过的 URL)"""
    seen = []

    def fake_urlopen(req, timeout=None):
        url = req.full_url
        method = req.get_method() if hasattr(req, "get_method") else "GET"
        seen.append(method + " " + url)
        for key, val in routes.items():
            if key in url and (key.endswith("*") or True):
                return FakeResp(*val)
        return FakeResp(404, "{}")

    real_open = urllib.request.urlopen
    urllib.request.urlopen = fake_urlopen
    os.environ.pop("EMOS_TOKENS", None)
    if env_tokens is not None:
        os.environ["EMOS_TOKENS"] = env_tokens

    code = open(path, encoding="utf-8").read()
    buf = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(buf):
            try:
                exec(compile(code, path, "exec"), {"__name__": "__main__", "__file__": path})
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else 1
    finally:
        urllib.request.urlopen = real_open
        os.environ.pop("EMOS_TOKENS", None)
    return exit_code, buf.getvalue(), seen


def main():
    path = os.path.join(ROOT, "src", "emos_sign.py") if "--src" in sys.argv else os.path.join(ROOT, "python", "emos_sign.py")
    if not os.path.exists(path):
        print("找不到目标：" + path)
        return 1
    print("被测文件：" + os.path.relpath(path, ROOT))

    OK = {
        "/api/sign/check": (200, '{"is_sign":false,"user_id":null}'),
        "/api/user/sign": (200, '{"sign_index":7,"earn_point":4,"continuous_days":3}'),
        "/api/user": (200, '{"user_id":"eABCs","username":"测试号"}'),
    }

    code, out, _ = run_case({}, None, path)
    check("没配 token 直接报错退出", code == 1 and "EMOS_TOKENS" in out, out.strip()[:60])

    code, out, _ = run_case(OK, "11_abcdefgh1234", path)
    check("签到成功退出码 0", code == 0, code)
    check("解析出萝卜/名次/连签", "签到成功" in out and "+4" in out and "第7位" in out and "连签3天" in out, out.splitlines()[-2] if out else "")

    signed = dict(OK)
    signed["/api/sign/check"] = (200, '{"is_sign":true,"user_id":"eABCs"}')
    code, out, seen = run_case(signed, "11_abcdefgh1234", path)
    check("今日已签不发 PUT", code == 0 and not any(s.startswith("PUT") for s in seen), out.splitlines()[-2] if out else "")
    check("提示今日已签到", "今日已签到" in out)

    dead = {"/api/sign/check": (401, '{"message":"Unauthenticated."}')}
    code, out, _ = run_case(dead, "11_abcdefgh1234", path)
    check("token 失效退出码 1", code == 1, code)
    check("提示 Token 失效", "Token 失效" in out, out.splitlines()[-2] if out else "")

    # 主站全挂 → 应回落到 api.emos.best
    fallback_seen = []

    def fake(req, timeout=None):
        url = req.full_url
        fallback_seen.append(url)
        if url.startswith("https://emos.best/"):
            raise urllib.error.URLError("timeout")
        if url.endswith("/api/sign/check"):
            return FakeResp(200, '{"is_sign":true}')
        return FakeResp(200, '{"username":"备用"}')

    real = urllib.request.urlopen
    urllib.request.urlopen = fake
    os.environ["EMOS_TOKENS"] = "11_abcdefgh1234"
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            try:
                exec(compile(open(path, encoding="utf-8").read(), path, "exec"),
                     {"__name__": "__main__", "__file__": path})
            except SystemExit:
                pass
    finally:
        urllib.request.urlopen = real
        os.environ.pop("EMOS_TOKENS", None)
    check("主站失败切到 api.emos.best", any("api.emos.best" in u for u in fallback_seen))

    failed = [n for n, ok in results if not ok]
    print("\n" + "-" * 40)
    print("%d/%d 通过" % (len(results) - len(failed), len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
