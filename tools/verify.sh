#!/usr/bin/env bash
# 用你的真实 token 走一遍脚本的同一条链路，判断「到底能不能用」。
# 不发钱、不改文件，只发 2~3 个请求：校验 token → 查状态 →（没签则）签到。
#
#   ./tools/verify.sh 11_你的密钥
#   ./tools/verify.sh 11_你的密钥 --check-only    # 只看状态，不签到
#
set -uo pipefail

TOKEN="${1:-}"
MODE="${2:-}"
BASES=("https://emos.best" "https://api.emos.best")

if [ -z "$TOKEN" ]; then
  echo "用法: ./tools/verify.sh <token> [--check-only]" >&2
  echo "token 在 emos.best 首页 → 点左上「欢迎」→ 弹窗里「当前密钥」" >&2
  exit 1
fi

if [ "${#TOKEN}" -lt 8 ] || [ "$TOKEN" = "11_test-token" ]; then
  echo "✗ token 格式不像密钥（应形如 11_AkJO2UdOKinqmKOU）" >&2
  exit 1
fi

field() { # field <file> <key>
  sed -n "s/.*\"$2\"[[:space:]]*:[[:space:]]*\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" "$1" | head -1
}

BASE="https://emos.best"
echo "① 探测可用域名"
for b in "${BASES[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "$b/api/sign/check")
  printf "   %-26s HTTP %s\n" "$b" "$code"
  if [ "$code" = "200" ] || [ "$code" = "401" ]; then BASE="$b"; fi
done
echo "   使用 $BASE"

echo
echo "② 校验 token（GET /api/user）"
CODE=$(curl -s -m 20 -o /tmp/emos_u.json -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" "$BASE/api/user")
if [ "$CODE" = "401" ]; then
  echo "   ✗ 401 —— token 无效或已被重置，去 emos.best 重新取一次"
  exit 1
elif [ "$CODE" != "200" ]; then
  echo "   ! HTTP $CODE：$(head -c 200 /tmp/emos_u.json)"
else
  echo "   ✓ 有效：用户 $(field /tmp/emos_u.json username) / ID $(field /tmp/emos_u.json user_id)"
fi

echo
echo "③ 查询今日签到状态（GET /api/sign/check）"
curl -s -m 20 -o /tmp/emos_c.json -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" "$BASE/api/sign/check"
echo "   $(head -c 300 /tmp/emos_c.json)"

if grep -q '"is_sign"[[:space:]]*:[[:space:]]*true' /tmp/emos_c.json; then IS_SIGN=1; else IS_SIGN=0; fi

if [ "$MODE" = "--check-only" ]; then
  echo
  echo "（--check-only，未执行签到）"
  exit 0
fi

if [ "$IS_SIGN" = "1" ]; then
  echo
  echo "✓ 今天已经签过了，脚本今天会跳过它 —— 判断逻辑是通的"
  exit 0
fi

echo
echo "④ 执行签到（PUT /api/user/sign?content=签到）"
CODE=$(curl -s -m 25 -o /tmp/emos_s.json -w "%{http_code}" -X PUT \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
  -H "Referer: https://emos.best/" \
  --get --data-urlencode "content=签到" "$BASE/api/user/sign")

echo "   HTTP $CODE"
case "$CODE" in
  200)
    echo "   ✓ 签到成功，接口返回："
    cat /tmp/emos_s.json; echo
    echo
    echo "→ 脚本解析的就是这份 JSON 的 sign_index / earn_point / continuous_days。"
    ;;
  401) echo "   ✗ token 失效，重新取密钥" ;;
  409|429) echo "   ✓ 已签过（服务端判重），脚本会按「今日已签到」处理" ;;
  400) echo "   ! 参数被拒：$(cat /tmp/emos_s.json)" ;;
  *)   echo "   ! 未知响应：$(cat /tmp/emos_s.json)" ;;
esac
