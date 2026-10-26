# emos 自动签到（Loon / BoxJS）

<img src="assets/icon.png" width="88" align="right" alt="emos 自动签到图标">

作者：**xlzs001** · 图标：`assets/icon.png`（由 `tools/make-icon.py` 生成，改参数可重跑）

用 **Token 登录 + 每天定时签到** 替你在 emos 领萝卜。
Token 有三种填法，**两种是可视化面板**：Loon 插件设置里直接填，或在 BoxJS 网页面板里填。

> 接口全部来自官方开放 API（`https://wiki.emos.best/api/use`、Postman `somebyteorg/emos`），
> 没有模拟点击、没有绕登录，就是拿你本人的 token 调它自己的接口。

---

## 一、它到底做了什么

```
            ┌── Loon 插件设置面板（tokens / time / content / enabled）
配置来源 ───┼── BoxJS 网页面板（同一批 key，改哪边都生效）
            └── 自动抓取（开着 Loon 打开一次 emos.best，Bearer token 自动入库）

cron 每小时 :05 触发
   │
   ├─ 面板关了？            → 直接退出，不联网
   ├─ 还没到设定时间？       → 直接退出，不联网
   ├─ 今天已经搞定？         → 直接退出，不联网
   └─ 否则
        GET  /api/sign/check       今天签过没？
             ├─ is_sign = true  → 记「今日已签到」
             └─ is_sign = false → PUT /api/user/sign?content=<留言>
                                     └─ 拿到 sign_index / earn_point / continuous_days
                                          → 汇总成一条通知
```

几个刻意的设计：

- **每小时复查一次，而不是死等 08:05**：08:05 手机没网、Loon 没开，晚点开也会自动补签，不会漏签。
- **先查再签**：`is_sign=true` 就直接跳过，绝不会重复签到把自己搞成负分名次。
- **纯失败一天只吵你一次**：网络抖动导致的失败不会每小时弹一次通知。
- **多账号**：`主号,11_xxx` 一行一个，逐个串行签，账号之间留 800ms 间隔。
- **掉线自愈**：主站被 Cloudflare 拦时切 `api.emos.best`；你在网页点「重置密钥」后，脚本抓响应里的新 key 自动替换旧的。

### 先用 30 秒确认能用

不用装 Loon，拿你自己的 token 直接打一次真实接口：

```bash
./tools/verify.sh 11_你的密钥
```

打印：可用域名 → token 有效性 → 今日是否已签 →（没签就）真签一次并回显 JSON。
只想看状态不签到，加 `--check-only`。

---

## 二、三种填 Token 的方式

密钥在哪拿：登录 `https://emos.best` → 点左上角「欢迎」→ 弹窗里那行 **当前密钥**，
形如 `11_AkJO2UdOKinqmKOU`。**只有你手动点「重置密钥」它才会失效。**

### 方式 1：Loon 插件设置面板（推荐，最直观）

装好插件（见第四节）后，进 **Loon → 配置 → 插件 → emos 自动签到 → 设置**，会看到 5 个可视化控件：

| 控件 | 类型 | 说明 |
| --- | --- | --- |
| **Token 密钥** | 输入框 | 形如 `11_xxx`；多个账号用逗号分隔：`11_aaa,11_bbb`；留空则用自动抓取/BoxJS 里存的 |
| **账号备注** | 输入框 | 只影响通知里的显示名，填「主号」之类 |
| 签到时间 | 输入框 | 24 小时制 `HH:mm`，默认 `08:05`；过点未签会自动补签 |
| 签到留言 | 输入框 | 留空则每次从 30 句里随机挑一句（接口的 `content` 参数） |
| 启用自动签到 | 开关 | 关掉后定时任务完全不联网，手动「立即签到」仍可用 |

填完直接生效，**不用重启、不用改配置文件**。想在通知里区分多账号，
把 Token 框写成 `11_aaa` 并在备注写「主号」，需要再加号就点插件里的 **「emos保存Token」** 按钮把它落到本地。

> 这个面板依赖 Loon 3.5.1(983) 的插件参数功能。版本低的话用 `loon/emos-sign-compat.plugin`，
> 它没有面板，Token 靠方式 2 或方式 3。

### 方式 2：BoxJS 网页面板

BoxJS 是社区通用的脚本配置面板，好处是**在浏览器里改、多设备同步、还能看到历史记录**。

1. 先装 BoxJS 主程序（Loon 需要它的插件来提供 `boxjs.com` 页面与存储桥接）；
2. BoxJS → **订阅** → 添加订阅地址：

   ```
   https://raw.githubusercontent.com/<你的用户名>/emos-loon-sign/main/boxjs/emos.boxjs.json
   ```

3. 回到 BoxJS 首页 → 底部「应用」→ 找到 **emos 签到**，四个字段：

   | 字段 | 类型 | key |
   | --- | --- | --- |
   | 自动签到 | 开关 | `emos_auto_sign` |
   | Token 密钥 | 多行文本框（每行一个，`备注,11_xxx`） | `emos_tokens` |
   | 签到时间 | 文本 `HH:mm` | `emos_time` |
   | 签到留言 | 文本 | `emos_content` |

4. 填完点「保存」。**它和 Loon 插件读的是同一份数据**（同一个 `$persistentStore` key），
   所以两边改哪边都生效，不用二选一。

> 优先级：Loon 插件面板填了值 > BoxJS > 内置默认。想统一管理就把插件里的 Token 框留空，只用 BoxJS。

### 方式 3：自动抓取（完全不用手抄）

开着 Loon 打开一次 `https://emos.best` 并登录，脚本截获请求头里的
`Authorization: Bearer xxx_xxx` 直接入库，收到通知「已抓取登录密钥」即成。

前提：MitM 已开启、证书已信任（见第四节第 4 步）。
抓到的 token 也是写进 `emos_tokens`，跟前面两种方式共存。

---

## 三、目录结构

```
emos-loon-sign/
├── assets/icon.png                 图标（512 / 256 / 128 三档，生成脚本见 tools/make-icon.py）
├── loon/
│   ├── emos-sign.plugin            Loon 插件：可视化参数 + 抓 token + 定时签到（Loon ≥ 983）
│   ├── emos-sign-compat.plugin     旧版 Loon（< 983）用的无面板版本
│   └── local-install.md            不推 GitHub、用本地脚本的装法
├── boxjs/emos.boxjs.json           BoxJS 订阅（4 个可视化字段）
├── scripts/                        ★ 混淆后的运行文件（Loon 直接拉这几个）
│   ├── emos-sign.js                签到主脚本（时间门禁 + 多账号 + 切备用域名）
│   ├── emos-token-capture.js       截获 / 同步 token
│   └── emos-config.js              手动保存 / 查看账号
├── python/emos_sign.py             ★ 混淆后的 Actions / crontab 版本
├── .github/workflows/              Actions 定时签到 + 脚本自检
├── tools/
│   ├── push.sh                     一条命令建仓库 + 推送 + 输出订阅链接
│   ├── render.sh                   把 {{RAW}}/{{REPO}} 换成本仓库地址
│   ├── verify.sh                   用真实 token 打一次线上接口，验证能不能用
│   ├── make-icon.py                重新生成图标（Pillow 绘制，非 AI 生成）
│   ├── obfuscate.js                src/*.js → scripts/*.js（javascript-obfuscator）
│   ├── obfuscate-py.py             src/emos_sign.py → python/emos_sign.py（ast 改名）
│   └── test-local.js               模拟 Loon 运行时跑 39 项用例（无需真机）
└── docs/API.md                     接口与机制备忘（含来源链接）
```

改脚本前先跑自检（默认测的就是 `scripts/` 里的混淆产物，不是源码）：

```bash
node tools/test-local.js       # 39/39（JS，模拟 Loon 运行时）
python3 tools/test-py.py       # 8/8（Python，mock 网络）
```

---

## 四、装 Loon 插件

### 1. 推到你的 GitHub

```bash
./tools/push.sh <GitHub用户名> <你的PersonalAccessToken>    # 建仓 + 写地址 + 推送 + 打链接
```

PAT 在 <https://github.com/settings/tokens> → **Generate new token (classic)**，
勾 **repo** 和 **workflow** 两项（`workflow` 是推 `.github/workflows` 必需的，少勾会被拒）。
懒人直达（权限已预勾）：<https://github.com/settings/tokens/new?scopes=repo,workflow&description=emos-loon-sign>

脚本会先校验 token 身份和权限，再动手；推完记得把 token Revoke 掉。

不想给 token 就手动：

```bash
git remote add origin https://github.com/<你的用户名>/emos-loon-sign.git
git push -u origin main
./tools/render.sh <你的用户名>
git add -A && git commit -m "chore: 写入订阅地址" && git push
```

`render.sh` 会同时把插件里的脚本地址和 BoxJS JSON 里的 repo 地址换成你的。

### 2. Loon 导入

**配置 → 插件 → 右上角 + → 粘贴插件地址**：

```
https://raw.githubusercontent.com/<你的用户名>/emos-loon-sign/main/loon/emos-sign.plugin
```

raw 域名不通就换 CDN：`https://cdn.jsdelivr.net/gh/<你的用户名>/emos-loon-sign@main/loon/emos-sign.plugin`

导入后点进插件就是第二节说的设置面板，填 Token 即可。

### 3. 只想要可视化面板、不想给 MitM 权限？

完全可以。MitM 只影响「方式 3 自动抓取」。不装证书就在面板/BoxJS 里手填 Token，
其余功能（定时签到、通知、切备用域名）都不受影响。

### 4. 要用自动抓取才需要 MitM

插件已写好 `[MitM] hostname = %APPEND% emos.best, api.emos.best`，你只需：

1. Loon → 设置 → MitM → 生成并安装证书；
2. iOS **设置 → 通用 → VPN与设备管理** 信任该证书；
3. 确认 Loon 处于运行状态。

### 5. 验证

Loon → 脚本 → **emos立即签到** → 运行。通知应为「签到成功 +N🥕 第X位 连签Y天」或「今日已签到」。

---

## 五、不推 GitHub：本地脚本

Loon 支持引用本地文件。把 `scripts/` 三个 js 丢进 **iCloud 云盘 → Loon → Script**，
在 Loon 里「配置 → 添加脚本」按文件名引用，完全不经过 GitHub。

逐步说明（含每条脚本的表达式与可整段粘贴的配置）见 **[loon/local-install.md](loon/local-install.md)**。

---

## 六、GitHub Actions 兜底

手机不在线也有一次签到机会。

1. 仓库 **Settings → Secrets and variables → Actions** → New secret
   - Name：`EMOS_TOKENS`，Value：`11_xxx,11_yyy`
2. **Actions → emos 自动签到 → Run workflow** 跑一次看日志；
3. 默认每天 `UTC 00:05`（北京 08:05）自动执行。

> Actions 的 cron 高峰期可能延迟几十分钟，**抢名次还是用 Loon**。

---

## 七、签到能拿多少（摘自社区 Wiki）

| 项目 | 萝卜 |
| --- | --- |
| 每日签到 | +1 ~ +5 |
| 当天第 3 / 11 / 59 / 311 / 457 位 | +3 / +2 / +2 / +1 / +2 |
| 当天第 9 / 26 / 89 / 113 / 199 位 | −2 / −1 / −3 / −2 / −2 |
| 连续 7 / 30 / 365 天 | +10 / +30 / +3000 |

来源 `https://emos.dpdns.org/carrot`，以实际到账为准。所以越早签越划算，
但脚本无论如何一天只签一次。

---

## 八、常见问题

**Q：改了面板设置没反应？**
Loon 插件参数改动后配置会重载；若没生效，把开关关掉再打开一次，或重启 Loon。
BoxJS 里改完记得点「保存」。

**Q：通知说「Token 失效」**
网页「欢迎」弹窗里点重置密钥，按第二节重新填一次；开着 MitM 的话新 key 会被自动同步。

**Q：403 / Cloudflare 拦截**
脚本已内置 `api.emos.best` 备用域名；两个都不通一般是本地网络环境问题，换节点再试。

**Q：抓不到 token**
① MitM 没开或证书没信任；② Loon 没在运行；③ 只在静态页面停留不会产生 `/api/` 请求，刷新一下或点头像/片单。

**Q：会不会签两次、抢到负分名次**
不会。每次先 `/api/sign/check`，`is_sign=true` 直接跳过；签到后当天不再请求。

**Q：数据存在哪**
只在 Loon 本地 `$persistentStore`：`emos_tokens`（纯文本，一行一账号）、`emos_time`、
`emos_content`、`emos_auto_sign`、`emos_done_<日期>`、`emos_last_result`。
除 `emos.best` / `api.emos.best` 外不发任何请求，也没有第三方服务器。

**Q：怎么彻底删掉**
Loon 删插件 → 再删 `iCloud/Loon/Script` 里的三个 js → 可选清 BoxJS 里对应应用的本地存储。

---

## 九、能不能把仓库设成私有？

**可以设，但设了插件就拉不到了。** `raw.githubusercontent.com` 对私有仓库的匿名请求一律 404，
Loon 导入插件、脚本下载都会失败 —— 这是 GitHub 的机制，没有开关可以绕。

三条路，按推荐度排：

| 做法 | 插件能否远程更新 | 说明 |
| --- | --- | --- |
| **保持 public**（当前） | ✅ | 仓库里**没有任何密钥**：token 只存在你手机本地 `$persistentStore`，源码里也没有别的私人信息。公开的风险基本等于零 |
| 私有 + 本地脚本 | ✅ 但需手动 | 把 `scripts/` 三个 js 丢进 iCloud 的 `Loon/Script`，按 [loon/local-install.md](loon/local-install.md) 用本地文件名引用，**完全不经过 GitHub**。仓库可以随便设私有 |
| 私有 + 双仓库 | ✅ | 一个私有仓库存完整项目，再用 Actions 把 `scripts/`、`loon/`、`boxjs/` 同步到另一个公开仓库。等于把「源码」和「运行文件」分开 |

另外说明一点：GitHub 没有「不公开但可访问」这种中间态（unlisted）。`#!author` 写了你的 ID、
仓库又是公开的，两者本来就是配套的 —— 真想低调，就把作者名改成昵称，或者走第二种做法。

## 十、代码混淆与二次开发

仓库里 **`scripts/` 和 `python/` 全部是混淆产物**，可读源码不在仓库里（`.gitignore` 掉了 `src/`），
所以别人从 GitHub 拷到的是混淆版。行为完全一致 —— 每次构建后我都用同一套 39 项用例回归过。

| 文件 | 处理方式 | 产物大小 |
| --- | --- | --- |
| `scripts/*.js` | javascript-obfuscator：标识符改名、字符串数组 + rc4、控制流平坦化、字符串拆分 | 5~13KB → 13~40KB |
| `python/emos_sign.py` | ast 改名 + 去注释/文档字符串，压成短名（`_a` `_b` `_c`…） | 5.4KB → 4.8KB |
| `tools/*.sh`、`tools/*.js`、`tools/make-icon.py` | **故意不混淆** | — |

用 Bash 写的东西没法真正混淆（`shc` 之类编译成二进制会带来一堆兼容问题），
而且这几个是你自己用的构建/推送工具，混淆只会让你自己也没法改。

### 自己改代码

源码在本地 `src/`（未入库），改完重新构建：

```bash
# 需要一次：npm i -g javascript-obfuscator   或装到任意 node_modules 里
NODE_PATH=/path/to/node_modules node tools/obfuscate.js --preset=A
python3 tools/obfuscate-py.py
node tools/test-local.js        # 39/39
python3 tools/test-py.py        # 8/8 才算通过
```

混淆参数刻意避开了在 Loon 的 JavaScriptCore 里容易翻车的选项：`selfDefending`、`debugProtection`
关闭，`stringArrayEncoding` 用 rc4（不依赖 `atob`/`Buffer`），`target=browser-no-eval`。
产物里搜不到 `eval` / `atob` / `window` / `document` / `require`。

> 公平地说：混淆只能提高"随手抄走"的成本，代码逻辑在 README 里已经写得比较清楚了，
> 真要防逆向得靠服务端，不是靠混淆。

## 十一、说明

- 只使用你本人账号的 token 调用 emos 官方开放接口，等价于你手动点一次签到；
- 请遵守社区规则（`https://emos.dpdns.org/carrot`），别批量注册小号刷萝卜；
- 接口由官方维护，字段若有调整，改 `docs/API.md` 和脚本里集中的那几处即可。

MIT License
