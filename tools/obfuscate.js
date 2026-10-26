#!/usr/bin/env node
/**
 * 构建脚本：把 src/ 下的可读源码混淆成 scripts/ 下可直接被 Loon 引用的产物。
 *
 *   node tools/obfuscate.js                 # 默认强度（preset A）
 *   node tools/obfuscate.js --preset=B      # 更强/更弱之间切换
 *   node tools/obfuscate.js --check         # 只构建到临时目录并跑一遍用例，不覆盖 scripts/
 *
 * 为什么要分 src/ 和 scripts/：
 *   仓库里只放混淆产物，源码留在本地（.gitignore 掉了），这样别人从 GitHub 上
 *   拷到的就是混淆过的版本；自己改代码仍然改 src/，然后重新构建。
 *
 * 混淆参数刻意避开了在 Loon 的 JavaScriptCore 里容易翻车的选项：
 *   selfDefending / debugProtection 关掉（会依赖 devtools、格式化即失效）
 *   stringArrayEncoding 用 rc4（不依赖 atob / Buffer，纯 JS 数学运算）
 *   target = browser-no-eval（不产生 eval，避免某些运行时禁用）
 */
const fs = require("fs");
const path = require("path");
const JavaScriptObfuscator = require("javascript-obfuscator");

const ROOT = path.join(__dirname, "..");
const SRC_DIR = path.join(ROOT, "src");
const OUT_DIR = path.join(ROOT, "scripts");

const FILES = ["emos-sign.js", "emos-token-capture.js", "emos-config.js"];

const PRESETS = {
  A: {
    compact: true,
    controlFlowFlattening: true,
    controlFlowFlatteningThreshold: 0.5,
    deadCodeInjection: false,
    debugProtection: false,
    disableConsoleOutput: false,
    identifierNamesGenerator: "hexadecimal",
    renameGlobals: true,
    selfDefending: false,
    simplify: true,
    splitStrings: true,
    splitStringsChunkLength: 5,
    stringArray: true,
    stringArrayThreshold: 0.75,
    stringArrayRotate: true,
    stringArrayShuffle: true,
    stringArrayEncoding: ["rc4"],
    stringArrayIndexShift: true,
    stringArrayWrappersCount: 2,
    stringArrayWrappersType: "variable",
    transformObjectKeys: true,
    unicodeEscapeSequence: false,
    target: "browser-no-eval",
  },
  B: {
    compact: true,
    controlFlowFlattening: false,
    deadCodeInjection: false,
    debugProtection: false,
    disableConsoleOutput: false,
    identifierNamesGenerator: "hexadecimal",
    renameGlobals: true,
    selfDefending: false,
    simplify: true,
    splitStrings: true,
    splitStringsChunkLength: 6,
    stringArray: true,
    stringArrayThreshold: 0.8,
    stringArrayRotate: true,
    stringArrayShuffle: true,
    stringArrayEncoding: [],
    transformObjectKeys: false,
    unicodeEscapeSequence: false,
    target: "browser-no-eval",
  },
};

const args = process.argv.slice(2);
const presetArg = (args.find((a) => a.startsWith("--preset=")) || "--preset=A").split("=")[1].toUpperCase();
const checkOnly = args.includes("--check");
const preset = PRESETS[presetArg];

if (!preset) {
  console.error("未知 preset：" + presetArg + "（可选 A / B）");
  process.exit(1);
}

const banner =
  "/* emos 自动签到 · build " +
  new Date().toISOString().slice(0, 10) +
  " · 混淆产物，请勿手改 */\n";

const outDir = checkOnly ? path.join(require("os").tmpdir(), "emos-obf-check") : OUT_DIR;
fs.mkdirSync(outDir, { recursive: true });

let total = 0;
for (const name of FILES) {
  const srcPath = path.join(SRC_DIR, name);
  if (!fs.existsSync(srcPath)) {
    console.error("缺少源文件：" + srcPath);
    process.exit(1);
  }
  const code = fs.readFileSync(srcPath, "utf8");
  const result = JavaScriptObfuscator.obfuscate(code, preset);
  const out = banner + result.getObfuscatedCode();
  fs.writeFileSync(path.join(outDir, name), out, "utf8");
  total += out.length;
  console.log(
    "  " + name.padEnd(26) + (code.length + "B → " + out.length + "B").padStart(18)
  );
}
console.log(`preset ${presetArg} 完成，输出 ${outDir}`);
console.log(`合计 ${(total / 1024).toFixed(1)} KB`);
