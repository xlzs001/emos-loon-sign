# emos 接口备忘

> 全部来自官方公开资料，抓取时间 2026-10-26。字段可能随官方迭代变化，以 Postman 为准。

## 资料来源

| 内容 | 地址 |
| --- | --- |
| 官方 Wiki · API 使用 | https://wiki.emos.best/api/use |
| 官方 Wiki · 授权连接（OAuth） | https://wiki.emos.best/api/link |
| 官方 Wiki · 接口变更记录 | https://wiki.emos.best/api/changelog |
| 官方 Postman 接口文档 | https://www.postman.com/somebyteorg/emos |
| 社区 Wiki（萝卜规则补充） | https://emos.dpdns.org/carrot |
| 社区 Wiki · 网站导航 | https://emos.dpdns.org/links |
| 前端源码（登录/密钥实现） | https://github.com/somebyteorg/emos_home |

## 域名

| 用途 | 地址 |
| --- | --- |
| 主站 | `https://emos.best` |
| 备用（CF 403 时） | `https://api.emos.best` |
| 统一账号（somebyte） | `https://account.somebyte.org` |
| 测试服 | `https://test.emos.best`，token `11_test-token` |
| 资源站 | `https://files.emos.best` |

## 鉴权

```http
Authorization: Bearer <token>
Accept: application/json
```

- token 形如 `11_AkJO2UdOKinqmKOU`（`前缀_随机串`），**只有用户手动重置时才会失效**
- 网页里「当前密钥」即此 token：登录 `https://emos.best` → 点左上角「欢迎」→ 弹窗
- 快捷登录：`https://emos.best/#/sign?token=xxx_xxx`（前端 `web/views/sign.vue` 直接把它写进 store）
- 重置：`PUT /api/user/resetToken`，响应体 `{"token": "新密钥"}`

## OAuth 授权（给第三方应用拿 token）

```
用户点击登录 → https://emos.best/link?uuid=[uuid]&name=[应用名]&url=[回调地址]
用户授权后   → [url]?user_id=..&username=..&avatar=..&token=..
```

- `uuid` 自己生成，`url` 为回调地址
- 另有「网页授权 V2」需申请：跳 `https://emos.best/api/sign?state=[应用名]`，回调 `[url][token]`
- 机器人授权：`https://t.me/emospg_bot?start=link_[用户ID]-[机器人name]`

## 签到相关（本项目用到的三个）

### 1. 查询今日是否已签到

```http
GET /api/sign/check
Authorization: Bearer <token>
```

响应（未登录/未签）：

```json
{ "is_sign": false, "user_id": null }
```

已签时为 `true` 并带上 `user_id`。注意：**该接口在无 token 时也返回 200**，
所以不能拿它当「token 有效性」的唯一判据，要配合下面的接口看状态码。

### 2. 执行签到

```http
PUT /api/user/sign?content=<签到留言>
Authorization: Bearer <token>
```

- `content` 为签到留言（手动签到时输入的那句话），社区实践 ≤10 个字
- 成功 `200`，响应体：

```json
{
  "sign_index": 17,          // 今日第几位签到
  "earn_point": 3,           // 本次获得萝卜
  "continuous_days": 5       // 连续签到天数
}
```

状态码语义：

| 状态码 | 含义 | 处理 |
| --- | --- | --- |
| 200 | 签到成功 | 读上面的字段 |
| 401 / 403 | token 失效 / 无权限 | 重新拿密钥 |
| 409 / 429 | 今天已经签过 | 视为成功跳过 |
| 400 | 参数错误（content 不合规等） | 换留言重试 |

### 3. 用户信息

```http
GET /api/user
Authorization: Bearer <token>
```

返回 `user_id`（形如 `eXXXXXXXXs`）、`username`、`roles`、`telegram_user_id`、
`server_*` 服务端字段、`slot_remaining` 等。前端用它渲染首页「欢迎」弹窗。

## 已实测的响应（2026-10-26）

```bash
$ curl -s https://emos.best/api/sign/check
{"is_sign":false,"user_id":null}          # 200

$ curl -s https://emos.best/api/user
{"message":"Unauthenticated."}            # 401

$ curl -s -X PUT "https://emos.best/api/user/sign?content=test"
{"message":"Unauthenticated."}            # 401
```

`api.emos.best` 结果一致，可作为备用域名。

## 其他接口（同一套鉴权，摘录）

| 接口 | 说明 |
| --- | --- |
| `POST /api/redPacket/create` | 发红包（2026-05-15 调整 `type` / `receive`） |
| `GET /api/watch` / `POST /api/watch` | 片单，`type` 必填（`video` / `music`） |
| `POST /api/watch/slot` | 兑换片单卡槽 |
| `GET /api/upload/getUploadToken` | 上传 token（图片/字幕走 `tusd`） |
| `GET /api/user/passwordTemporary` | 一次性登录密码（原 `/api/emya/getLoginPassword`） |
| `PUT /api/user/passwordReset` | 重置永久密码 |
| `GET /api/user/server/videoHistory` | 登录设备列表 |
| `POST /api/user/server/videoLogout` | 退出指定设备 |
| `GET /api/live/list` | 直播列表 |
| `POST /api/shop/order/user/create` | 商城下单（`buy_number` 必填） |

> 错误字段自 2026-06-21 起统一为 `{"message": "..."}`（原为 `error`）。

## 萝卜规则（签到部分）

- 每次签到 +1 ~ +5
- 按当天签到顺位有浮动：第 3 位 +3、第 11 位 +2、第 59 位 +2、第 311 位 +1、第 457 位 +2；
  第 9 位 −2、第 26 位 −1、第 89 位 −3、第 113 位 −2、第 199 位 −2
- 连续签到：一周 +10、一月 +30、一年 +3000

所以「越早签越划算」，但每日一次即可，重复请求只会拿到 409/429。

## 参考实现

- 社区同类项目：`gaoqifan2/emos-sign-bot`（Go/Node，Telegram Bot 管理多账号）
  —— 本项目的接口路径与状态码语义参考了它的实现，再用官方 Wiki 校对。
