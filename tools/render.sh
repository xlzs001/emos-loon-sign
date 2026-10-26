#!/usr/bin/env bash
# 把模板里的占位符换成本仓库的真实地址，并打印可直接使用的订阅链接。
#   {{RAW}}  → https://raw.githubusercontent.com/<用户名>/<仓库>/<分支>
#   {{REPO}} → https://github.com/<用户名>/<仓库>
#
# 用法：
#   ./tools/render.sh 你的GitHub用户名
#   ./tools/render.sh 你的GitHub用户名 emos-loon-sign main
#
set -euo pipefail

OWNER="${1:-}"
REPO="${2:-emos-loon-sign}"
BRANCH="${3:-main}"

if [ -z "$OWNER" ]; then
  echo "用法: ./tools/render.sh <GitHub用户名> [仓库名] [分支名]" >&2
  exit 1
fi

RAW="https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}"
JD="https://cdn.jsdelivr.net/gh/${OWNER}/${REPO}@${BRANCH}"
REPOURL="https://github.com/${OWNER}/${REPO}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILES=("$ROOT/loon/emos-sign.plugin" "$ROOT/loon/emos-sign-compat.plugin" "$ROOT/boxjs/emos.boxjs.json")

# macOS 的 sed 需要 -i ''，GNU sed 需要 -i
sed_inplace() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"
  else
    sed -i '' "$@"
  fi
}

for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  sed_inplace "s|{{RAW}}|${RAW}|g" "$f"
  sed_inplace "s|{{REPO}}|${REPOURL}|g" "$f"
done

cat <<EOF
已写入：
  脚本地址   $RAW/scripts/emos-sign.js
  插件仓库   $REPOURL

Loon 插件（配置 → 插件 → 添加）：
  $RAW/loon/emos-sign.plugin          ← 新版语法，带可视化填 Token（Loon ≥ 3.5.1(983)）
  $RAW/loon/emos-sign-compat.plugin   ← 旧版 Loon 用这个

BoxJS 订阅（BoxJS → 订阅 → 添加）：
  $RAW/boxjs/emos.boxjs.json

国内直连 raw 不通时，把上面 raw.githubusercontent.com/<用户名>/<仓库>/main
换成 cdn.jsdelivr.net/gh/<用户名>/<仓库>@main，例如：
  $JD/loon/emos-sign.plugin
EOF
