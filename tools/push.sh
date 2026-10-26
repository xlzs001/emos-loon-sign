#!/usr/bin/env bash
# 一条命令完成：校验 token → 建仓库 → 写入 raw 地址 → 推送 → 打印订阅链接
#
# 用法：
#   ./tools/push.sh <GitHub用户名> <PersonalAccessToken> [仓库名]
#
# PAT 要求（classic token）：勾 repo + workflow
#   repo      —— 建仓库、推代码
#   workflow  —— 仓库里有 .github/workflows/*.yml，少了这个会被拒
#
# 推送完成后 origin 会被改写成不含 token 的干净地址，凭据不会留在 .git/config 里。
#
set -euo pipefail

OWNER="${1:-}"
TOKEN="${2:-}"
REPO="${3:-emos-loon-sign}"
BRANCH="main"

if [ -z "$OWNER" ] || [ -z "$TOKEN" ]; then
  cat >&2 <<'EOF'
用法: ./tools/push.sh <GitHub用户名> <PersonalAccessToken> [仓库名]

PAT 在哪建：
  https://github.com/settings/tokens  →  Generate new token (classic)
  勾选 repo + workflow，有效期选 7 天即可，用完可以立刻 Revoke

  懒人直达（勾好两个权限）：
  https://github.com/settings/tokens/new?scopes=repo,workflow&description=emos-loon-sign
EOF
  exit 1
fi

case "$TOKEN" in
  ghp_*|github_pat_*|gho_*) : ;;
  *) echo "! token 不像 GitHub PAT（通常以 ghp_ 或 github_pat_ 开头），继续尝试…" >&2 ;;
esac

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── 1. 校验 token ────────────────────────────────────────────────
echo "→ 校验 token"
WHO="$(curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/user)"
LOGIN="$(printf '%s' "$WHO" | sed -n 's/.*"login"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"

if [ -z "$LOGIN" ]; then
  echo "  ✗ token 无效或已过期：" >&2
  printf '%s\n' "$WHO" | head -c 300 >&2; echo >&2
  exit 1
fi
echo "  登录身份：$LOGIN"

if [ "$LOGIN" != "$OWNER" ]; then
  echo "  ! token 属于 ${LOGIN}，但命令里写的是 $OWNER —— 推送会 403，建议改成：" >&2
  echo "    ./tools/push.sh $LOGIN <token>" >&2
  exit 1
fi

SCOPES="$(curl -s -I -H "Authorization: Bearer $TOKEN" https://api.github.com/user \
  | tr -d '\r' | sed -n 's/^[Xx]-[Oo][Aa]uth-[Ss]copes:[[:space:]]*\(.*\)$/\1/p' | head -1)"
if [ -n "$SCOPES" ]; then
  echo "  权限范围：$SCOPES"
  # GitHub 返回的是 "repo, workflow"（逗号后有空格），先去掉空格再匹配
  SCOPES_N="$(printf '%s' "$SCOPES" | tr -d ' ')"
  case ",$SCOPES_N," in *,repo,*) : ;; *) echo "  ! 缺少 repo 权限，无法建仓/推送" >&2; exit 1 ;; esac
  case ",$SCOPES_N," in
    *,workflow,*) : ;;
    *) echo "  ! 缺少 workflow 权限：仓库含 .github/workflows，推送会被拒。在 token 页面补勾 workflow 后重试" >&2 ;;
  esac
else
  echo "  权限范围：细粒度 token（无 scopes 响应头）"
  echo "  请确认 Contents / Workflows / Administration 均为 Read and write"
fi

# ── 2. 建仓库 ────────────────────────────────────────────────────
echo "→ 检查仓库 $OWNER/$REPO"
CODE="$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO")"

if [ "$CODE" = "404" ]; then
  echo "→ 创建仓库"
  BODY="{\"name\":\"$REPO\",\"description\":\"emos token 登录 + Loon 自动签到\",\"private\":false,\"has_issues\":true,\"has_wiki\":false}"
  RES="$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github+json" -d "$BODY" "https://api.github.com/user/repos")"
  case "$RES" in
    *'"full_name"'*) echo "  已创建 $OWNER/$REPO" ;;
    *) echo "  创建失败：$(printf '%s' "$RES" | head -c 300)" >&2; exit 1 ;;
  esac
elif [ "$CODE" = "200" ]; then
  echo "  仓库已存在，直接推送"
else
  echo "  无法访问（HTTP ${CODE}），请检查 token 权限" >&2
  exit 1
fi

# ── 3. 写入地址 ─────────────────────────────────────────────────
echo "→ 写入脚本 raw 地址"
./tools/render.sh "$OWNER" "$REPO" "$BRANCH" >/dev/null

git add -A
git diff --cached --quiet || git commit -q -m "chore: 写入 raw 地址（$OWNER/${REPO}）"

# ── 4. 推送 ─────────────────────────────────────────────────────
echo "→ 推送代码"
PUSH_URL="https://$OWNER:$TOKEN@github.com/$OWNER/$REPO.git"

if ! ERR="$(git push "$PUSH_URL" "$BRANCH:$BRANCH" --force-with-lease 2>&1)"; then
  if ! ERR="$(git push "$PUSH_URL" "$BRANCH:$BRANCH" 2>&1)"; then
    # 别把 token 打到屏幕上
    printf '%s\n' "$ERR" | sed "s|$TOKEN|***|g" | sed 's/^/    /' >&2
    case "$ERR" in
      *workflow*) echo "  → 原因是缺 workflow 权限：https://github.com/settings/tokens 补勾后重跑" >&2 ;;
      *Authentication*|*403*) echo "  → 认证/权限失败：确认 token 未过期、勾了 repo" >&2 ;;
      *rejected*) echo "  → 远端有你本地没有的提交，先 git pull --rebase 再推" >&2 ;;
    esac
    exit 1
  fi
fi

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$OWNER/${REPO}.git"
git fetch -q origin "$BRANCH" 2>/dev/null || true
git branch --set-upstream-to="origin/$BRANCH" "$BRANCH" >/dev/null 2>&1 || true

cat <<EOF

✓ 完成。仓库：https://github.com/$OWNER/$REPO

Loon 插件（配置 → 插件 → 添加）：
  https://raw.githubusercontent.com/$OWNER/$REPO/$BRANCH/loon/emos-sign.plugin
  （Loon < 983 用 loon/emos-sign-compat.plugin）

BoxJS 订阅（BoxJS → 订阅 → 添加）：
  https://raw.githubusercontent.com/$OWNER/$REPO/$BRANCH/boxjs/emos.boxjs.json

国内 raw 不通就换 CDN：
  https://cdn.jsdelivr.net/gh/$OWNER/$REPO@$BRANCH/loon/emos-sign.plugin

下一步：
  1. Loon 导入插件 → 插件设置里填 Token（可视化）
  2. 运行「emos立即签到」验证一次
  3. 完事记得去 https://github.com/settings/tokens 把这个 PAT 撤销
EOF
