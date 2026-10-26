# -*- coding: utf-8 -*-
# 混淆产物 · 源码不在本仓库，请勿手改
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
_a = ['https://emos.best', 'https://api.emos.best']
_b = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
_c = 20
_d = ['签到', '打卡', '今日份到', '来签个到', '顺手签到', '准点冒泡', '今天也在', '醒来签到', '梦里签到', '路过一下', '悄悄签到', '照常营业', '保持热爱', '平安喜乐', '万事顺意', '元气在线', '好运敲门', '认真生活', '慢慢变好', '继续发光', '今日达成', '任务完成', '签到打卡', '我又来了']

def _e(_f):
    if not _f:
        return []
    _g = re.split('[\\s,;]+', _f.strip())
    return [_h for _h in _g if _h and '_' in _h and (_h != '11_test-token')]

def _i(_j):
    return _j[:4] + '…' + _j[-3:] if len(_j) > 8 else _j

def _k(_l, _m, _j, _n='https://emos.best'):
    _o = _n + _m
    _p = urllib.request.Request(_o, method=_l)
    _p.add_header('Authorization', 'Bearer ' + _j)
    _p.add_header('Accept', 'application/json, text/plain, */*')
    _p.add_header('Referer', 'https://emos.best/')
    _p.add_header('User-Agent', _b)
    try:
        with urllib.request.urlopen(_p, timeout=_c) as _q:
            return (_q.status, _q.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as _r:
        return (_r.code, _r.read().decode('utf-8', 'replace'))
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
    raise RuntimeError(str(_t) if _t else 'network error')

def _u(_v):
    try:
        return json.loads(_v)
    except Exception:
        return {}

def _w(_j):
    _x = {'token': _j, 'name': '', 'ok': False, 'msg': '', 'point': None, 'days': None, 'rank': None}
    _y, _z = _s('GET', '/api/sign/check', _j)
    if _y in (401, 403):
        _x['msg'] = 'Token 失效'
        return _x
    if _y != 200:
        _x['msg'] = '查询失败 HTTP %s' % _y
        return _x
    if _u(_z).get('is_sign') is True:
        _x['msg'] = '今日已签到'
        _x['ok'] = True
        return _x
    _aa = random.choice(_d)
    _m = '/api/user/sign?content=' + urllib.parse.quote(_aa)
    _y, _z = _s('PUT', _m, _j)
    if _y == 200:
        _ab = _u(_z)
        _x['ok'] = True
        _x['msg'] = '签到成功'
        _x['point'] = _ab.get('earn_point')
        _x['days'] = _ab.get('continuous_days')
        _x['rank'] = _ab.get('sign_index')
    elif _y in (409, 429):
        _x['ok'] = True
        _x['msg'] = '今日已签到'
    elif _y in (401, 403):
        _x['msg'] = 'Token 失效'
    else:
        _ac = _u(_z)
        _ad = _ac.get('message') if isinstance(_ac, dict) else ''
        _x['msg'] = '签到失败 HTTP %s%s' % (_y, '：' + _ad if _ad else '')
    return _x

def _ae(_x):
    try:
        _y, _z = _s('GET', '/api/user', _x['token'])
        if _y == 200:
            _ab = _u(_z)
            if isinstance(_ab.get('data'), dict):
                _ab = _ab['data']
            _x['name'] = _ab.get('username') or _ab.get('name') or _ab.get('user_id') or ''
    except Exception:
        pass

def _af():
    _f = os.getenv('EMOS_TOKENS') or os.getenv('EMOS_TOKEN') or ''
    _ag = _e(_f)
    if not _ag:
        print('::error::未配置 EMOS_TOKENS（仓库 Settings → Secrets → Actions）')
        return 1
    if os.getenv('EMOS_BASE'):
        _a.insert(0, os.environ['EMOS_BASE'].rstrip('/'))
    print('共 %d 个账号，开始签到 %s' % (len(_ag), time.strftime('%Y-%m-%d %H:%M:%S')))
    print('-' * 56)
    _ah = 0
    _ai = 0
    for _aj, _j in enumerate(_ag, 1):
        try:
            _ak = _w(_j)
        except Exception as _r:
            _ak = {'token': _j, 'name': '', 'ok': False, 'msg': '网络异常：%s' % _r, 'point': None, 'days': None, 'rank': None}
        if _ak['ok']:
            _ah += 1
        else:
            _ai += 1
        if not _ak['name']:
            _ae(_ak)
        _al = '%-2d %-18s %s' % (_aj, (_ak['name'] or _i(_j))[:18], _ak['msg'])
        if _ak['point'] is not None:
            _al += ' +%s萝卜' % _ak['point']
        if _ak['rank'] is not None:
            _al += ' 第%s位' % _ak['rank']
        if _ak['days'] is not None:
            _al += ' 连签%s天' % _ak['days']
        print(_al)
        if _aj != len(_ag):
            time.sleep(1)
    print('-' * 56)
    print('完成：成功 %d / 失败 %d' % (_ah, _ai))
    return 0 if _ai == 0 else 1
if __name__ == '__main__':
    sys.exit(_af())
