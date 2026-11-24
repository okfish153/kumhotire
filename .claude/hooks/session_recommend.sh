#!/usr/bin/env bash
# SessionStart 훅: 세션이 열리자마자 .claude/next_ideas.md의 추천 3줄을 화면에 바로 보여주고,
# 작업 내역을 Claude에게 넘겨 작업이 끝날 때마다 추천을 새로 고치게 한다.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" 2>/dev/null || exit 0
python3 - <<'PY'
import json, subprocess
def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
    except Exception: return ""
try: ideas = open(".claude/next_ideas.md", encoding="utf-8").read().strip()
except Exception: ideas = ""
ctx = f"""[최근 커밋]
{sh("git log -n 15 --date=short --pretty='- %ad %s'")}
[커밋 안 된 변경]
{sh("git status --short | head -20")}
[지시] 이 세션에서 의미 있는 작업을 마칠 때마다, 지금까지의 작업 내역을 보고 '이어서 해보면 좋을 3가지'를
각각 한 문장으로 .claude/next_ideas.md에 새로 써서 작업과 함께 커밋해라(번호 1~3, 세 줄만, 이미 한 일 반복 금지,
서로 다른 방향, 한 줄은 20자 안팎으로 짧게). 다음 세션 시작 때 이 파일이 사용자에게 자동으로 보인다.
[지시] 사용자가 숫자 하나(1, 2, 3)만 보내거나 '1번'처럼 고르면, .claude/next_ideas.md의 그 번호 아이디어를
자세히 설명해라: 무엇을 하는지, 왜 좋은지, 예상 결과물, 작업 단계 3~5개, 걸리는 시간. 끝에 '바로 시작할까요?'로 묻기."""
out = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}
if ideas: out["systemMessage"] = "💡 오늘의 아이디어 (번호를 보내면 자세히 설명)\n" + ideas
print(json.dumps(out, ensure_ascii=False))
PY
