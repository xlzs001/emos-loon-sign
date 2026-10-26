# -*- coding: utf-8 -*-
# 混淆产物 · 源码不在本仓库，请勿手改
import base64 as __emos_b64

def __emos_s(x):
    return __emos_b64.b64decode(x).decode('utf-8')
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
_a = [__emos_s('aHR0cHM6Ly9lbW9zLmJlc3Q='), __emos_s('aHR0cHM6Ly9hcGkuZW1vcy5iZXN0')]
_b = __emos_s('TW96aWxsYS81LjAgKGlQaG9uZTsgQ1BVIGlQaG9uZSBPUyAxN180IGxpa2UgTWFjIE9TIFgpIEFwcGxlV2ViS2l0LzYwNS4xLjE1IChLSFRNTCwgbGlrZSBHZWNrbykgVmVyc2lvbi8xNy40IE1vYmlsZS8xNUUxNDggU2FmYXJpLzYwNC4x')
_c = 20
_d = ['签到', '打卡', __emos_s('5LuK5pel5Lu95Yiw'), __emos_s('5p2l562+5Liq5Yiw'), __emos_s('6aG65omL562+5Yiw'), __emos_s('5YeG54K55YaS5rOh'), __emos_s('5LuK5aSp5Lmf5Zyo'), __emos_s('6YaS5p2l562+5Yiw'), __emos_s('5qKm6YeM562+5Yiw'), __emos_s('6Lev6L+H5LiA5LiL'), __emos_s('5oKE5oKE562+5Yiw'), __emos_s('54Wn5bi46JCl5Lia'), __emos_s('5L+d5oyB54Ot54ix'), __emos_s('5bmz5a6J5Zac5LmQ'), __emos_s('5LiH5LqL6aG65oSP'), __emos_s('5YWD5rCU5Zyo57q/'), __emos_s('5aW96L+Q5pWy6Zeo'), __emos_s('6K6k55yf55Sf5rS7'), __emos_s('5oWi5oWi5Y+Y5aW9'), __emos_s('57un57ut5Y+R5YWJ'), __emos_s('5LuK5pel6L6+5oiQ'), __emos_s('5Lu75Yqh5a6M5oiQ'), __emos_s('562+5Yiw5omT5Y2h'), __emos_s('5oiR5Y+I5p2l5LqG')]

def _e(_f):
    if not _f:
        return []
    _g = re.split(__emos_s('W1xzLDtdKw=='), _f.strip())
    return [_h for _h in _g if _h and '_' in _h and (_h != __emos_s('MTFfdGVzdC10b2tlbg=='))]

def _i(_j):
    return _j[:4] + '…' + _j[-3:] if len(_j) > 8 else _j

def _k(_l, _m, _j, _n=__emos_s('aHR0cHM6Ly9lbW9zLmJlc3Q=')):
    _o = _n + _m
    _p = urllib.request.Request(_o, method=_l)
    _p.add_header(__emos_s('QXV0aG9yaXphdGlvbg=='), __emos_s('QmVhcmVyIA==') + _j)
    _p.add_header(__emos_s('QWNjZXB0'), __emos_s('YXBwbGljYXRpb24vanNvbiwgdGV4dC9wbGFpbiwgKi8q'))
    _p.add_header(__emos_s('UmVmZXJlcg=='), __emos_s('aHR0cHM6Ly9lbW9zLmJlc3Qv'))
    _p.add_header(__emos_s('VXNlci1BZ2VudA=='), _b)
    try:
        with urllib.request.urlopen(_p, timeout=_c) as _q:
            return (_q.status, _q.read().decode(__emos_s('dXRmLTg='), __emos_s('cmVwbGFjZQ==')))
    except urllib.error.HTTPError as _r:
        return (_r.code, _r.read().decode(__emos_s('dXRmLTg='), __emos_s('cmVwbGFjZQ==')))
    except Exception as _r:
        raise RuntimeError(str(_r))

def _s(_l, _m, _j):
    _t = None
    for _n in _a:
        try:
            return _k(_l, _m, _j, _n)
        except RuntimeError as _r:
            _t = _r
            continue
    raise RuntimeError(str(_t) if _t else __emos_s('bmV0d29yayBlcnJvcg=='))

def _u(_v):
    try:
        return json.loads(_v)
    except Exception:
        return {}

def _w(_j):
    _x = {__emos_s('dG9rZW4='): _j, __emos_s('bmFtZQ=='): '', 'ok': False, 'msg': '', __emos_s('cG9pbnQ='): None, __emos_s('ZGF5cw=='): None, __emos_s('cmFuaw=='): None}
    _y, _z = _s('GET', __emos_s('L2FwaS9zaWduL2NoZWNr'), _j)
    if _y in (401, 403):
        _x['msg'] = __emos_s('VG9rZW4g5aSx5pWI')
        return _x
    if _y != 200:
        _x['msg'] = __emos_s('5p+l6K+i5aSx6LSlIEhUVFAgJXM=') % _y
        return _x
    if _u(_z).get(__emos_s('aXNfc2lnbg==')) is True:
        _x['msg'] = __emos_s('5LuK5pel5bey562+5Yiw')
        _x['ok'] = True
        return _x
    _aa = random.choice(_d)
    _m = __emos_s('L2FwaS91c2VyL3NpZ24/Y29udGVudD0=') + urllib.parse.quote(_aa)
    _y, _z = _s('PUT', _m, _j)
    if _y == 200:
        _ab = _u(_z)
        _x['ok'] = True
        _x['msg'] = __emos_s('562+5Yiw5oiQ5Yqf')
        _x[__emos_s('cG9pbnQ=')] = _ab.get(__emos_s('ZWFybl9wb2ludA=='))
        _x[__emos_s('ZGF5cw==')] = _ab.get(__emos_s('Y29udGludW91c19kYXlz'))
        _x[__emos_s('cmFuaw==')] = _ab.get(__emos_s('c2lnbl9pbmRleA=='))
    elif _y in (409, 429):
        _x['ok'] = True
        _x['msg'] = __emos_s('5LuK5pel5bey562+5Yiw')
    elif _y in (401, 403):
        _x['msg'] = __emos_s('VG9rZW4g5aSx5pWI')
    else:
        _ac = _u(_z)
        _ad = _ac.get(__emos_s('bWVzc2FnZQ==')) if isinstance(_ac, dict) else ''
        _x['msg'] = __emos_s('562+5Yiw5aSx6LSlIEhUVFAgJXMlcw==') % (_y, '：' + _ad if _ad else '')
    return _x

def _ae(_x):
    try:
        _y, _z = _s('GET', __emos_s('L2FwaS91c2Vy'), _x[__emos_s('dG9rZW4=')])
        if _y == 200:
            _ab = _u(_z)
            if isinstance(_ab.get(__emos_s('ZGF0YQ==')), dict):
                _ab = _ab[__emos_s('ZGF0YQ==')]
            _x[__emos_s('bmFtZQ==')] = _ab.get(__emos_s('dXNlcm5hbWU=')) or _ab.get(__emos_s('bmFtZQ==')) or _ab.get(__emos_s('dXNlcl9pZA==')) or ''
    except Exception:
        pass

def _af():
    _f = os.getenv(__emos_s('RU1PU19UT0tFTlM=')) or os.getenv(__emos_s('RU1PU19UT0tFTg==')) or ''
    _ag = _e(_f)
    if not _ag:
        print(__emos_s('OjplcnJvcjo65pyq6YWN572uIEVNT1NfVE9LRU5T77yI5LuT5bqTIFNldHRpbmdzIOKGkiBTZWNyZXRzIOKGkiBBY3Rpb25z77yJ'))
        return 1
    if os.getenv(__emos_s('RU1PU19CQVNF')):
        _a.insert(0, os.environ[__emos_s('RU1PU19CQVNF')].rstrip('/'))
    print(__emos_s('5YWxICVkIOS4qui0puWPt++8jOW8gOWni+etvuWIsCAlcw==') % (len(_ag), time.strftime(__emos_s('JVktJW0tJWQgJUg6JU06JVM='))))
    print('-' * 56)
    _ah = 0
    _ai = 0
    for _aj, _j in enumerate(_ag, 1):
        try:
            _ak = _w(_j)
        except Exception as _r:
            _ak = {__emos_s('dG9rZW4='): _j, __emos_s('bmFtZQ=='): '', 'ok': False, 'msg': __emos_s('572R57uc5byC5bi477yaJXM=') % _r, __emos_s('cG9pbnQ='): None, __emos_s('ZGF5cw=='): None, __emos_s('cmFuaw=='): None}
        if _ak['ok']:
            _ah += 1
        else:
            _ai += 1
        if not _ak[__emos_s('bmFtZQ==')]:
            _ae(_ak)
        _al = __emos_s('JS0yZCAlLTE4cyAlcw==') % (_aj, (_ak[__emos_s('bmFtZQ==')] or _i(_j))[:18], _ak['msg'])
        if _ak[__emos_s('cG9pbnQ=')] is not None:
            _al += __emos_s('ICslc+iQneWNnA==') % _ak[__emos_s('cG9pbnQ=')]
        if _ak[__emos_s('cmFuaw==')] is not None:
            _al += __emos_s('IOesrCVz5L2N') % _ak[__emos_s('cmFuaw==')]
        if _ak[__emos_s('ZGF5cw==')] is not None:
            _al += __emos_s('IOi/nuetviVz5aSp') % _ak[__emos_s('ZGF5cw==')]
        print(_al)
        if _aj != len(_ag):
            time.sleep(1)
    print('-' * 56)
    print(__emos_s('5a6M5oiQ77ya5oiQ5YqfICVkIC8g5aSx6LSlICVk') % (_ah, _ai))
    return 0 if _ai == 0 else 1
if __name__ == __emos_s('X19tYWluX18='):
    sys.exit(_af())
