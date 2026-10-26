# 不推 GitHub 也能用：本地脚本安装

Loon 支持 `script("本地文件名")`，所以脚本完全可以放在手机本地，不需要任何远程仓库。
适合：现在就想跑一次、不想动 GitHub、或者 raw 域名被墙。

> 本地模式下没有插件参数面板（那是插件的功能），Token 请用下面第 3 步的两种方式之一：
> **BoxJS 面板** 或 **脚本参数**，也可以靠 MitM 自动抓取。

## 1. 把三个文件放进 Loon 的脚本目录

把 `scripts/` 下的三个文件传到手机：

- `emos-sign.js`
- `emos-token-capture.js`
- `emos-config.js`

放到 **iCloud 云盘 → Loon → Script**（没有这个目录就先在 Loon 里点一次「配置 → 添加脚本 → 从 URL 下载」，目录会被自动创建）。

传法任选：AirDrop → 存储到「文件」；iCloud 云盘网页版上传；隔空投送到 iPhone 后用「文件」App 移动。

> Loon 设置里要打开 **自动同步**，否则本地文件列表可能不刷新。

## 2. 添加脚本（UI 操作）

**配置 → 添加脚本 → 右上角 +**，按下表加三条：

| # | 脚本类型 | 别名 | 表达式 | 脚本位置 | 脚本名称 |
|---|---|---|---|---|---|
| 1 | `http-request` | emos抓密钥 | `^https?:\/\/(api\.)?emos\.best\/api\/` | Local | `emos-token-capture.js` |
| 2 | `http-response` | emos同步密钥 | `^https?:\/\/(api\.)?emos\.best\/api\/user\/resetToken` | Local | `emos-token-capture.js` |
| 3 | `generic`（手动运行） | emos立即签到 | 留空 | Local | `emos-sign.js` |

再加定时任务。**cron 类型在部分版本的 UI 里没有入口**，直接编辑配置最稳：

配置 → 选中当前配置 → 右上角「编辑」→ 在 `[Script]` 段末尾粘一行：

```ini
cron "5 * * * *" script-path=emos-sign.js, tag=emos自动签到, timeout=300, enable=true
```

这里刻意用**每小时一次**：脚本内部会读 `emos_time`（默认 `08:05`），没到点就直接退出、不联网；
如果 08:05 手机没网，下一个整点会自动补签。

（Loon ≥ 983 的新语法写法，效果一样，二选一：）

```ini
cron "5 * * * *" then script("emos-sign.js") with tag="emos自动签到", timeout=300
```

> 本地脚本用**文件名**即可，不用写路径。若提示找不到脚本，改成 `script("Loon/Script/emos-sign.js")` 试一次。

## 3. 填 Token：二选一

**A. BoxJS 面板（推荐，可视化）**

BoxJS → 订阅 → 添加：

```
https://raw.githubusercontent.com/<你的用户名>/emos-loon-sign/main/boxjs/emos.boxjs.json
```

然后在「emos 签到」里填 Token / 时间 / 留言。脚本读的就是这几个 key，本地脚本一样生效。

**B. 脚本参数**

把「emos立即签到」那条改一下，或在配置里加一条一次性脚本：

```ini
generic script-path=emos-config.js, tag=emos填Token, timeout=30, argument="token=11_你的密钥&remark=主号", enable=true
```

运行一次即写入本地，之后可把 argument 改回 `list`。

## 4. 打开 MitM（只有「抓密钥」需要）

设置 → MitM → 生成证书并安装 → 到 iOS「设置 → 通用 → VPN与设备管理」信任；
然后 MitM 的 **主机名** 里加上：`emos.best`、`api.emos.best`。

不想装证书就跳过，用第 3 步的 A 或 B 手动填。

## 5. 跑通

1. Loon 保持运行 → 浏览器打开 `https://emos.best` 登录一次 → 收到「已抓取登录密钥」
2. 配置 → 脚本 → **emos立即签到** → 运行 → 收到签到结果通知
3. 完成。之后每天到点自动跑，**过点也会补签**。

## 6. 整段粘贴版

```ini
[Script]
http-request ^https?:\/\/(api\.)?emos\.best\/api\/ script-path=emos-token-capture.js, tag=emos抓密钥, timeout=30, enable=true
http-response ^https?:\/\/(api\.)?emos\.best\/api\/user\/resetToken script-path=emos-token-capture.js, tag=emos同步密钥, requires-body=true, timeout=30, enable=true
cron "5 * * * *" script-path=emos-sign.js, tag=emos自动签到, timeout=300, enable=true
generic script-path=emos-sign.js, tag=emos立即签到, timeout=300, enable=true
generic script-path=emos-config.js, tag=emos查看账号, timeout=30, argument="list", enable=true

[MitM]
hostname = %APPEND% emos.best, api.emos.best
```

贴进主配置，把三个 js 放进 `Loon/Script`，重启 Loon 生效。
