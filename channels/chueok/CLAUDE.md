# 채널 규칙: 추억을 읽는 시간

> 이 파일은 「추억을 읽는 시간」 세션에서만 따른다. 공통 규칙은 저장소 루트 `CLAUDE.md`.
> 작업은 **`channels/chueok/` 안에서만** 한다 (대본 `docs/`, 사진·음성 `assets/`, 결과 `output/`, 코드 `*.py`).
> 「차를 읽는 시간」의 `docs/`·`output/`·`ep*.py`·드라이브는 읽거나 고치지 않는다(예외: `HANDOFF.md` 6번의 완성 예시는 구조 참고용으로 **읽기만**). 공통 도구(`tools/`, `video.py`, `audio.py`)는 가져다 쓰기만 한다.

## 채널

- **한 줄:** 매일 아침 5시 주요 이슈를 받아, 그 이슈와 이어지는 **그 시절 추억**(물건·가격·음식·놀이·가전·방송·사건·거리 풍경)을 1분 쇼츠로 읽어 주는 채널
- **주 시청자:** 30대 후반~60대
- **말투:** 존댓말 + 편한 수다체. 시그니처 "그 시절엔 말이죠"
- **특기:** 그 시절 값을 짜장면 값·신입 월급·버스 요금 같은 생활 물가로 바꿔 보는 '그 시절 vs 지금'. 환산은 방법을 밝힌다("물가 환산이 아니라 ○○값 환산")
- **훅의 출발점:** 오늘 이슈 → "그 시절에는?" (예: 오늘 라면값 인상 → 1980년대 라면 한 봉지 값)
- **캐릭터:** **꼬망** (2026-11-26 확정). 손녀·손자 같은 귀여운 분위기의 해설자. 가족 역할로 고정하지 않고, 이야기에 따라 할아버지·할머니·엄마·아빠·삼촌·이모를 소품만 바꿔 연기. 설정서 `docs/character_kkomang.md`. 기준 그림 한 장(`assets/character/kkomang_base.png`)을 고정해 그 그림만 움직인다
- **목소리 (꼬망):** 구글 TTS `ko-KR-Chirp3-HD-Leda`, 속도 1.05 → 높이 4음 올림(asetrate 방식, 떨림 없음). 반드시 `python3 channels/chueok/kkomang_voice.py <대본.md> <음성 폴더>`로 만든다(카운트다운 `count.wav` 포함). 견본 `assets/voice/samples/꼬망_인사.mp3`
- **해시태그 마지막:** `#추억을읽는시간`

## 위치

| 무엇 | 어디 |
|---|---|
| 인수인계 | `channels/chueok/HANDOFF.md` |
| 콘텐츠 목록(중복 확인) | `channels/chueok/content_registry.csv` = 드라이브 `00_채널 기본/콘텐츠 목록` 시트 |
| 템플릿 | `channels/chueok/docs/templates.md` (대본·근거·장면·업로드 글·블로그) |
| 교훈·체크리스트 | `channels/chueok/docs/lessons.md` |
| 드라이브 최상위 | 「추억을 읽는 시간」 1qXkcZSBmAca0fHF8-9Asc7sUE7jhY7hb |
| 드라이브 하위 | 00_채널 기본 1OHuZc5ZjMqSN3UqW-C7xoK4MD1gEUT_Y · 01_캐릭터 1NjLFIxYWCT702bAjemE60onnl8udd9ZG · 03_에피소드 1BoroJ3JqwTAmF-u7azdDCHCQ39SvKpwN · 04_완성 영상 모음 1w68zf3WvXNklY5FrYy-SHgTrI96RXZuL · 05_롱폼·블로그 1gZ12hJHTAMiu5NamySZhUhAV6EH3oJPa · 99_자료 출처 1bef7pbdGCTHsyWig5R-6ZKE7aWSvIm7g |
| 아침 브리핑 | 예약 작업 「[추억] 추억 아침 브리핑」 trig_01TLVx5X2vut4cUJANGsSctj (매일 4:41 시작, 휴대폰 푸시) |

## 파일 이름

- 대본·근거: `docs/m001_<소재>_script.md`, 업로드 글: `docs/m001_<소재>_upload.md`
- 영상 코드: `m001_<소재>.py` → `output/m001_<소재>_1min.mp4`
- 음성: `assets/voice/m001/line_XX.wav`, 사진: `assets/images/<소재>_<저작자>.jpg`
- 드라이브 에피소드 폴더: `03_에피소드/M001_<소재>/`
- 번호는 `M001`부터 (차 채널 EP 번호와 겹치지 않게)

## 만드는 순서

1. 콘텐츠 목록으로 중복 확인 → "중복 없음/있음"만 알림
2. 오늘 이슈 기사 + 그 시절 1차 자료(당시 신문, 통계청, 한국은행, 한국소비자원 참가격 등)로 근거 표
3. 대본(11문장 안팎): 훅(오늘 이슈 × 그 시절) / 정체 / 미끼 / 퀴즈+하나둘셋 / 정답 / "그 시절엔 말이죠" / 비교 / 미끼 회수 / 흥미로운 사실 / 끝 문장(쉼표로 첫 문장에 이어짐) → 사용자 확인
4. 사진(Commons) · 그 시절 풍경은 일러스트(사용자가 제미나이에서 만들어 올림, 초록 배경이면 `tools/green_key.py`)
5. 음성 `python3 channels/chueok/kkomang_voice.py channels/chueok/docs/m001_…_script.md channels/chueok/assets/voice/m001`
6. 영상: 차 채널의 `ep04_grandeur_tg.py` 구조를 복사해 `channels/chueok/m001_….py`로 (경로만 이 폴더로)
7. 업로드 글 5종 → 드라이브 에피소드 폴더, 콘텐츠 목록에 한 줄 + 시트 교체, 커밋 메시지 `[추억] …`
