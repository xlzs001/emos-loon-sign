#!/usr/bin/env node
/**
 * 本地模拟 Loon 运行时，跑一遍脚本逻辑（不需要真机、不需要真 token）
 *
 *   node tools/test-local.js
 *
 * 全部用例使用模拟响应，不发真实网络请求。
 */

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.join(__dirname, "..");
// 默认测仓库里发布的混淆产物；加 --dir=src 可以直接测可读源码
const DIR = (process.argv.find((a) => a.startsWith("--dir=")) || "--dir=scripts").split("=")[1];
const TOKEN_A = "11_akjo2udokinqmkou";
const TOKEN_B = "11_bbbb2222cccc3333";

function makeRuntime(opts) {
  const store = Object.assign({}, opts.store || {});
  const notes = [];
  const logs = [];
  let donePayload = null;

  const sandbox = {
    console: { log: (v) => logs.push(typeof v === "string" ? v : JSON.stringify(v)) },
    setTimeout: (fn) => setTimeout(fn, 0),
    setInterval: (fn) => setTimeout(fn, 0),
    Math,
    JSON,
    String,
    Number,
    Object,
    Array,
    Date,
    encodeURIComponent,
    decodeURIComponent,
    $script: { name: "emos-test", startTime: new Date() },
    $persistentStore: {
      read: (k) => (store[k] === undefined ? null : store[k]),
      write: (v, k) => {
        if (v === undefined || v === null) delete store[k];
        else store[k] = String(v);
        return true;
      },
      remove: () => Object.keys(store).forEach((k) => delete store[k]),
    },
    $notification: {
      post: (title, subtitle, content) => notes.push({ title, subtitle, content }),
    },
    $httpClient: {},
    $done: (payload) => {
      donePayload = payload === undefined ? {} : payload;
    },
  };

  if (opts.now) {
    const fixed = new Date(opts.now).getTime();
    class FakeDate extends Date {
      constructor(...a) {
        if (a.length === 0) super(fixed);
        else super(...a);
      }
      static now() {
        return fixed;
      }
    }
    sandbox.Date = FakeDate;
  }

  ["get", "post", "put", "delete", "head", "patch", "options"].forEach((m) => {
    sandbox.$httpClient[m] = (o, cb) => {
      const url = typeof o === "string" ? o : o.url;
      const headers = (typeof o === "object" && o.headers) || {};
      const r = opts.handler(m.toUpperCase(), url, headers);
      if (r && r.hang) return;
      cb(r && r.error, { status: (r && r.status) || 200 }, (r && r.body) || "");
    };
  });

  if (opts.request) sandbox.$request = opts.request;
  if (opts.response) sandbox.$response = opts.response;
  if (opts.argument !== undefined) sandbox.$argument = opts.argument;

  return { sandbox, store, notes, logs, getDone: () => donePayload };
}

function run(file, opts) {
  const rel = file.startsWith("scripts/") ? path.join(DIR, file.slice("scripts/".length)) : file;
  const rt = makeRuntime(opts);
  vm.createContext(rt.sandbox);
  vm.runInContext(fs.readFileSync(path.join(ROOT, rel), "utf8"), rt.sandbox, { filename: rel });
  return rt;
}

const wait = (ms = 140) => new Promise((r) => setTimeout(r, ms));

const results = [];
function check(name, cond, detail) {
  results.push({ name, ok: !!cond });
  console.log(`${cond ? "PASS" : "FAIL"}  ${name}${detail ? "  → " + detail : ""}`);
}

/* 常用模拟后端 */
function backend(overrides = {}) {
  return (method, url) => {
    if (overrides[method + " " + url.split("?")[0]]) return overrides[method + " " + url.split("?")[0]];
    if (url.endsWith("/api/sign/check")) return { status: 200, body: '{"is_sign":false,"user_id":null}' };
    if (url.includes("/api/user/sign")) {
      return { status: 200, body: '{"sign_index":17,"earn_point":3,"continuous_days":5}' };
    }
    if (url.endsWith("/api/user")) return { status: 200, body: '{"user_id":"eABCs","username":"苹果"}' };
    return { status: 404, body: "{}" };
  };
}

const ARG = (extra = {}) =>
  Object.assign({ tokens: TOKEN_A, remark: "主号", time: "00:00", content: "", enabled: true }, extra);

(async function main() {
  console.log("=== 1. 插件参数里填 Token → 签到成功 ===");
  {
    const rt = run("scripts/emos-sign.js", { store: {}, argument: ARG(), handler: backend() });
    await wait();
    const n = rt.notes[0] || {};
    check("发出通知", !!n.title, n.title);
    check("解析出萝卜/名次/连签", /\+3/.test(n.content) && /第17位/.test(n.content) && /连签5天/.test(n.content), n.content);
    check("账号写回本地（纯文本）", rt.store.emos_tokens === "主号," + TOKEN_A, rt.store.emos_tokens);
    check("写入今日完成标记", !!rt.store["emos_done_" + new Date().toISOString().slice(0, 10)]);
  }

  console.log("\n=== 2. 今日已签 → 跳过且不再发签到请求 ===");
  {
    let putCount = 0;
    const rt = run("scripts/emos-sign.js", {
      store: { emos_tokens: "11_akjo2udokinqmkou" },
      argument: ARG({ tokens: "" }),
      handler: (m, url) => {
        if (m === "PUT") putCount++;
        if (url.endsWith("/api/sign/check")) return { status: 200, body: '{"is_sign":true}' };
        return { status: 200, body: '{"username":"苹果"}' };
      },
    });
    await wait();
    check("识别为已签到", /今日已签到/.test(rt.notes[0].content), rt.notes[0].content);
    check("没有发 PUT", putCount === 0);
  }

  console.log("\n=== 3. token 失效（401） ===");
  {
    const rt = run("scripts/emos-sign.js", {
      store: {},
      argument: ARG(),
      handler: (m, url, h) => {
        if ((h.Authorization || "").indexOf("dead") > -1) return { status: 401, body: '{"message":"Unauthenticated."}' };
        return { status: 401, body: '{"message":"Unauthenticated."}' };
      },
    });
    await wait();
    check("提示 Token 失效", /Token 失效/.test(rt.notes[0].content), rt.notes[0].content);
    check("标题标记异常", /异常/.test(rt.notes[0].title), rt.notes[0].title);
  }

  console.log("\n=== 4. 没有任何 token ===");
  {
    const rt = run("scripts/emos-sign.js", { store: {}, argument: ARG({ tokens: "" }), handler: backend() });
    await wait();
    check("给出配置引导", /未配置 token/.test(rt.notes[0].subtitle || ""), rt.notes[0].subtitle);
    check("正常结束", !!rt.getDone());
  }

  console.log("\n=== 5. 主站挂了自动切 api.emos.best ===");
  {
    const seen = [];
    const rt = run("scripts/emos-sign.js", {
      store: {},
      argument: ARG(),
      handler: (m, url) => {
        seen.push(url);
        if (url.indexOf("https://emos.best/") === 0) return { error: "timeout" };
        if (url.indexOf("api.emos.best") > -1 && url.endsWith("/api/sign/check")) return { status: 200, body: '{"is_sign":true}' };
        return { status: 200, body: '{"username":"备用"}' };
      },
    });
    await wait();
    check("回落到备用域名", seen.some((u) => u.indexOf("api.emos.best") > -1));
    check("备用域名下正常出结果", /今日已签到/.test(rt.notes[0].content));
  }

  console.log("\n=== 6. 时间门禁：没到点不发请求 ===");
  {
    let calls = 0;
    const rt = run("scripts/emos-sign.js", {
      store: {},
      argument: ARG({ time: "23:59" }),
      now: "2026-10-26T08:05:00+08:00",
      handler: (m, url) => {
        calls++;
        return backend()(m, url);
      },
    });
    await wait(60);
    check("零请求", calls === 0, "calls=" + calls);
    check("零通知", rt.notes.length === 0);
  }

  console.log("\n=== 7. 时间门禁：过点后自动补签 ===");
  {
    const rt = run("scripts/emos-sign.js", {
      store: {},
      argument: ARG({ time: "08:05" }),
      now: "2026-10-26T13:05:00+08:00",
      handler: backend(),
    });
    await wait();
    check("补签成功", /签到成功/.test(rt.notes[0].content || ""), rt.notes[0].content);
  }

  console.log("\n=== 8. 「立即签到」绕过门禁 ===");
  {
    const rt = run("scripts/emos-sign.js", {
      store: { emos_tokens: TOKEN_A },
      argument: "manual",
      now: "2026-10-26T01:00:00+08:00",
      handler: backend(),
    });
    await wait();
    check("手动可立即签到", /签到成功/.test(rt.notes[0].content || ""), rt.notes[0].content);

    // 插件里的「立即签到」按钮：带 token 不带 time
    const rt2 = run("scripts/emos-sign.js", {
      store: {},
      argument: { tokens: TOKEN_A, remark: "主号", content: "", enabled: true },
      now: "2026-10-26T01:00:00+08:00",
      handler: backend(),
    });
    await wait();
    check("不带 time 即视为手动", /签到成功/.test(rt2.notes[0].content || ""), rt2.notes[0].content);
  }

  console.log("\n=== 9. 面板关闭自动签到 ===");
  {
    let calls = 0;
    const rt = run("scripts/emos-sign.js", {
      store: { emos_auto_sign: "false", emos_tokens: TOKEN_A },
      handler: (m, url) => {
        calls++;
        return backend()(m, url);
      },
    });
    await wait(60);
    check("不请求接口", calls === 0);
    check("不打扰用户", rt.notes.length === 0);
  }

  console.log("\n=== 10. 面板里填的纯文本多账号（备注,token） ===");
  {
    const seen = [];
    const rt = run("scripts/emos-sign.js", {
      store: { emos_tokens: "主号,11_akjo2udokinqmkou\n小号 " + TOKEN_B, emos_time: "00:00" },
      handler: (m, url, h) => {
        seen.push(h.Authorization);
        return backend()(m, url);
      },
    });
    await wait(300);
    check("两个账号都签到", (rt.notes[0].content || "").split("\n").length === 2, rt.notes[0].content);
    check("备注被识别", /主号/.test(rt.notes[0].content) && /小号/.test(rt.notes[0].content));
    check("两个 token 都发了请求", seen.filter((s) => /11_/.test(s)).length >= 2);
  }

  console.log("\n=== 11. 自定义签到留言 ===");
  {
    let signedUrl = "";
    const rt = run("scripts/emos-sign.js", {
      store: {},
      argument: ARG({ content: "今日打卡" }),
      handler: (m, url) => {
        if (m === "PUT") signedUrl = url;
        return backend()(m, url);
      },
    });
    await wait();
    check("使用面板自定义留言", decodeURIComponent(signedUrl).indexOf("content=今日打卡") > -1, signedUrl);
  }

  console.log("\n=== 12. 抓取 token（http-request） ===");
  {
    const rt = run("scripts/emos-token-capture.js", {
      store: {},
      request: { url: "https://emos.best/api/user", headers: { Authorization: "Bearer " + TOKEN_B } },
      handler: () => ({ status: 200, body: "{}" }),
    });
    check("写入纯文本", rt.store.emos_tokens === TOKEN_B, rt.store.emos_tokens);
    check("首次抓取发通知", /已抓取登录密钥/.test(rt.notes[0].subtitle || ""));
  }

  console.log("\n=== 13. 抓取去重 / 过滤测试服 token ===");
  {
    const rt = run("scripts/emos-token-capture.js", {
      store: { emos_tokens: "主号," + TOKEN_B },
      request: { url: "https://api.emos.best/api/user", headers: { Authorization: "Bearer " + TOKEN_B } },
      handler: () => ({ status: 200, body: "{}" }),
    });
    check("不重复入库", (rt.store.emos_tokens.match(/11_/g) || []).length === 1);
    check("不打扰用户", rt.notes.length === 0);

    const rt2 = run("scripts/emos-token-capture.js", {
      store: {},
      request: { url: "https://test.emos.best/api/user", headers: { Authorization: "Bearer 11_test-token" } },
      handler: () => ({ status: 200, body: "{}" }),
    });
    check("过滤测试 token", !rt2.store.emos_tokens);
  }

  console.log("\n=== 14. 重置密钥自动同步 ===");
  {
    const rt = run("scripts/emos-token-capture.js", {
      store: { emos_tokens: "主号,11_oldoldoldoldold" },
      request: { url: "https://emos.best/api/user/resetToken", headers: { Authorization: "Bearer 11_oldoldoldoldold" } },
      response: { status: 200, headers: {}, body: '{"token":"11_newnewnewnewnew"}' },
      handler: () => ({ status: 200, body: "{}" }),
    });
    check("换成新 token", rt.store.emos_tokens === "主号,11_newnewnewnewnew", rt.store.emos_tokens);
    check("通知已更新", /密钥已更新/.test(rt.notes[0].subtitle || ""));
  }

  console.log("\n=== 15. 插件「保存Token」按钮 ===");
  {
    const rt = run("scripts/emos-config.js", {
      store: {},
      argument: { tokens: TOKEN_A + "," + TOKEN_B, remark: "小号" },
      handler: () => ({ status: 200, body: "{}" }),
    });
    check("两个 token 都落库", /11_akjo/.test(rt.store.emos_tokens) && /11_bbbb/.test(rt.store.emos_tokens));
    check("备注写入", /小号/.test(rt.store.emos_tokens), rt.store.emos_tokens.split("\n")[0]);
    check("给出确认", /已保存 2/.test(rt.getDone().title), rt.getDone().title);
  }

  console.log("\n=== 16. 查看账号（脱敏） ===");
  {
    const rt = run("scripts/emos-config.js", {
      store: { emos_tokens: "主号," + TOKEN_A, "emos_done_2026-10-26": "1" },
      argument: "list",
      handler: () => ({ status: 200, body: "{}" }),
    });
    const d = rt.getDone() || {};
    check("列出账号数", /1/.test(d.title), d.title);
    check("脱敏显示", /…/.test(d.content || ""), d.content);
  }

  console.log("\n=== 17. 纯失败一天只通知一次 ===");
  {
    const store = {};
    const boom = () => ({ status: 500, body: "{}" });
    const first = run("scripts/emos-sign.js", { store, argument: ARG(), handler: boom });
    await wait();
    check("首次失败有通知", first.notes.length === 1, (first.notes[0] || {}).subtitle);
    const carry = Object.assign({}, first.store);
    const second = run("scripts/emos-sign.js", { store: carry, argument: ARG(), handler: boom });
    await wait();
    check("第二次失败保持安静", second.notes.length === 0);
  }

  console.log("\n=== 18. 成功后同一天不再重复请求 ===");
  {
    const store = {};
    const first = run("scripts/emos-sign.js", { store, argument: ARG(), handler: backend() });
    await wait();
    let calls = 0;
    const second = run("scripts/emos-sign.js", {
      store: Object.assign({}, first.store),
      argument: ARG(),
      handler: (m, url) => {
        calls++;
        return backend()(m, url);
      },
    });
    await wait(60);
    check("第二次零请求", calls === 0, "calls=" + calls);
    check("第二次零通知", second.notes.length === 0);
  }

  const failed = results.filter((r) => !r.ok);
  console.log("\n----------------------------------------");
  console.log(`${results.length - failed.length}/${results.length} 通过`);
  process.exit(failed.length ? 1 : 0);
})();
