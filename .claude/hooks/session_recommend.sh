#!/usr/bin/env bash
# SessionStart 훅: 새 세션이 열릴 때 지금까지의 작업 내역을 모아 Claude에게 넘기고,
# 첫 응답에서 "다음에 해보면 좋을 3가지"를 추천하도록 지시한다.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" 2>/dev/null || exit 0

echo "=== [자동 추천용 작업 내역] ==="
echo "## 최근 커밋 (최신순)"
git log -n 15 --date=short --pretty='- %ad %s' 2>/dev/null
echo
echo "## 아직 커밋 안 된 변경"
git status --short 2>/dev/null | head -20
echo
echo "## README 요약"
head -n 12 README.md 2>/dev/null
echo
echo "## 결과물(output/)"
ls -1 output 2>/dev/null
echo
cat <<'MSG'
=== [지시] ===
사용자의 이번 세션 첫 메시지에 답할 때, 답변 맨 앞에 "💡 이어서 해보면 좋을 3가지"를 먼저 보여줘.
- 위 작업 내역을 분석해서, 이미 한 것을 보완·발전·재활용할 수 있는 구체적인 제안 3개.
- 각 제안: 한 줄 제목 + 왜 좋은지 1문장 + 바로 실행할 첫 단계 1개.
- 이미 한 작업을 그대로 반복하는 제안은 빼고, 서로 다른 방향(예: 품질 개선 / 새 콘텐츠 / 자동화·배포)으로 고르기.
- 그 다음 사용자의 실제 요청에 답해. 사용자가 바로 구체적인 작업을 지시했다면 추천은 3줄 이내로 짧게.
- 추천은 세션당 한 번만.
MSG
