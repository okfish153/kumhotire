# 인수인계: 차를 읽는 시간 (2026-11-26 정리, 새 세션 시작용)

새 세션은 **`CLAUDE.md`(작업 규칙)를 먼저** 따르고, 이 문서로 현재 상태를 이어받는다.
중복 확인은 `docs/content_registry.csv`(= 드라이브 `00_채널 기본/콘텐츠 목록 (중복 확인용)` 시트).

## 1. 한눈에 보기

| 구분 | 내용 |
|---|---|
| 채널 | 차를 읽는 시간 — 옛날 차 이야기, 1분 세로 쇼츠(+가끔 4분 가로 롱폼, 네이버 블로그 시리즈) |
| 캐릭터 | 차형 v3 (빨강·검정 레이싱 슈트, 가슴 CHAHYUNG). 기준 그림 한 장을 `tools/chahyung_motion.py`로 움직임(동작 12가지) |
| 목소리 | EP03부터 구글 클라우드 TTS `ko-KR-Chirp3-HD-Algenib` (`tools/tts_lines.py`, 퀴즈 카운트다운 `count.wav` 함께 생성). EP01·02는 사용자 녹음 |
| 저장소 | okfish153/kumhotire — 작업 브랜치 `claude/drive-docs-v2-1-ecoymf`, 기본 브랜치 `claude/youtube-shorts-reels-video-pbpz19` (2026-11-26 두 브랜치 같은 상태로 합침) |
| 드라이브 | 「차를 읽는 시간」 1EKsBRwyZf-EsKgm0J5q_4erkElSWGduQ |
| 매일 브리핑 | 예약 작업 「자동차 아침 브리핑」 trig_01BTMpMweRUxfybf4wLoX8fF — 매일 한국 시간 4:51 시작, 휴대폰 푸시. 지난 24시간 자동차 소식 + 채널 아이디어 3개(콘텐츠 목록으로 중복 표시) |

## 2. 완성된 콘텐츠 (자세한 내용은 콘텐츠 목록)

| 번호 | 형식 | 제목 | 코드 / 결과물 | 업로드 글 |
|---|---|---|---|---|
| EP01 | 쇼츠 57.8초 | 짜장면 28,000그릇 값? / 지금 짜장면 값으론 2억! (각그랜저) | `ep01_gak_grandeur.py` → `output/ep01_gak_grandeur_1min.mp4` | `docs/ep01_gak_grandeur_upload.md` |
| EP02 | 쇼츠 54.3초 | 신입 월급 5년 치 차? / 1992 회장님 차 3,490만 원 (뉴 그랜저) | `ep02_new_grandeur.py` | `docs/ep02_new_grandeur_upload.md` |
| EP03 | 쇼츠 45.8초 | 회장님 뒷자리 차에서 / 내가 직접 모는 차로? (그랜저 XG) | `ep03_grandeur_xg.py` | `docs/ep03_grandeur_xg_upload.md` |
| EP04 | 쇼츠 48.4초 | 전성기의 문을 열다 / 출시 첫날 1만 1,362대 계약 (그랜저 TG) | `ep04_grandeur_tg.py` (ep03 틀 재사용) | `docs/ep04_grandeur_tg_upload.md` |
| L01 | 롱폼 16:9 3분 53초 | 여러 번 구르고도 운전자는 살았다, 이젠 지붕 에어백까지 (제네시스) | `long01_genesis.py`, 썸네일 `tools/long01_thumbnail.py` | `docs/long01_genesis_gv90_upload.md` |
| S01 | 홍보 쇼츠 31.9초 | 여러 번 구르고도 / 운전자는 살았다? | `short01_genesis.py` (빠른 컷·펀치 줌·흔들림) | `docs/short01_genesis_promo_upload.md` |
| B01~04 | 네이버 블로그 | 제네시스 이야기 1~4편 (이미지 17장) | `docs/blog/genesis_0*.md`, 이미지 `tools/make_blog_genesis.py` → `assets/blog/genesis/` | — |

대본·근거 표: `docs/epXX_*_script.md`, `docs/long01_genesis_gv90_script.md`, `docs/short01_genesis_promo_script.md`

## 3. 제작 순서 (새 편을 만들 때)

1. 콘텐츠 목록으로 중복 확인 → 사용자에게 "중복 없음/있음"만 알림
2. 자료 조사: 숫자는 1차 자료(신문 당시 기사, 제조사 보도자료)로 확인, 근거 표 작성. 엇갈리면 쓰지 않음
3. 대본 `docs/epXX_<이름>_script.md` (표 형식, 11문장 안팎) — 훅 / 정체 / 미끼 / 퀴즈+하나둘셋 / 정답 / "그 시절엔 말이죠" / 미끼 회수 / 흥미로운 사실 / 끝 문장(쉼표로 끝나 첫 문장으로)
4. 사진: Wikimedia Commons만(저작자·라이선스를 Commons API로 확인, 번호판 흐림). 제조사 뉴스룸 사진은 약관상 불가(아래 5)
5. 음성: `python3 tools/tts_lines.py docs/epXX_..._script.md assets/voice/epXX`
6. 영상: 앞 편 코드를 복사해 장면만 바꿈(ep04가 가장 짧은 예). `--preview 초 초`로 장면 확인 → 전체 렌더
7. 업로드 글(5개 플랫폼) 자동 작성 → 드라이브 에피소드 폴더에 구글 문서로
8. 콘텐츠 목록에 한 줄 추가, 드라이브 시트 교체, 커밋·푸시

## 4. 드라이브 구조

```
차를 읽는 시간/                            1EKsBRwyZf-EsKgm0J5q_4erkElSWGduQ
├─ 00_채널 기본/                           1e8g8kt8DiSM3ZM2ajLd0r2iQvcmCrH6e  채널 규칙, SNS 채널 소개 글, 콘텐츠 목록 시트
├─ 01_캐릭터_차형/                         1Lt_VzLT2_RQP29JV3QwhVhVG2Ajai38a  v3 기준 그림, IP(사용 가이드 v3 등), SNS_이미지
├─ 02_공통 소스/                           (비어 있음)
├─ 03_에피소드/그랜저/                     1SuXgYM51elN5xfqkIdAUshuQp1z6_HSQ
│   ├─ EP01_각그랜저/   1smKi0hb34NXQxXtzsuuR5qsOvjgX3OgJ
│   ├─ EP02_뉴그랜저/   1FN7YXC6_NVil_L78xdkwBgSKjZ0sPVWS
│   ├─ EP03_그랜저XG/   1TG6pmm8JQZNnvOcD_Y2KJezqPw0-6QYm
│   └─ EP04_그랜저TG/   1xsqgVCDiQMOpI-N2ChBYmV5ZjNbsEcZJ
├─ 04_완성 영상 모음/                      1-WnBnyno0Qghmup15fVEr_CIKbw0rNsA
├─ 05_롱폼/                                1oMvMp3UEL2yXMk1Czqahh0ukWRhefXo5  L01·S01 업로드 글, 대본, 썸네일, 자막
├─ 06_블로그_제네시스시리즈/               1NlebKOJhjX7p38oz3dUL-WfqgPu0qXTE  원고 4편 + 이미지 17장
└─ 99_자료 출처/
```
- 드라이브 커넥터는 한 번에 약 3.1MB까지만 올라감 → 영상(mp4)은 사용자가 직접 올림. 저장소에는 mp4도 커밋돼 있음(50MB 넘는 롱폼은 GitHub 경고만 뜸)
- 마크다운을 구글 문서로 올리면 이모지가 깨짐 → 문서에 이모지 쓰지 않음

## 5. 꼭 기억할 교훈

- **제네시스(현대차) 뉴스룸 사진:** 이용 약관이 서면 허락 없는 복제·게시와 상업적 이용을 금지 → 쓰지 않음. 사실 확인용 글만 읽음
- **Commons:** 요청이 잦으면 429. 정해진 크기 썸네일(1280px/1920px)로 받고, 실패하면 10초씩 늘려 재시도
- **사실 표현:** 숫자가 엇갈리면 쓰지 않음(예: TG 출시가 2,527만/2,587만). 사고 이야기는 원인(과속)과 공식 발언만, "이 차라서 살았다" 단정 금지. 횟수 불명은 "여러 번"
- **인스타그램 해시태그 최대 5개**, 유튜브 쇼츠 최대 3분(4분은 일반 영상), 인스타 릴스 최대 3분
- **TTS:** 짧은 말("셋!")은 따로 만들면 잘림 → "하나... 둘... 셋!"을 한 파일로 만들고 소리 구간으로 박자를 찾음
- **글꼴:** Pretendard에 ✔ ✕ ○ 같은 기호가 없음 → 글자로 씀
- **타입캐스트:** 무료 계정은 클라우드에서 API를 부르면 남용 감지로 막힘(키는 환경에 남아 있으나 안 씀)
- **환경 `kumhotire` 네트워크:** Commons 3곳, newsroom.genesis.com 허용. 비밀값: 구글 TTS(헤더 X-Goog-Api-Key, 접두사 없음), 타입캐스트

## 6. 남은 일 / 사용자 할 일

- 영상 mp4를 드라이브·각 SNS에 직접 업로드, 업로드 글의 '(링크 넣기)'와 '관련 동영상' 연결
- 게시 전 체크리스트(각 업로드 글 끝)의 기사 원문 확인
- EP01·EP02는 영상 안에 구독·댓글 요청이 남아 있음(사용자 녹음이라 바꾸려면 끝 두 문장 재녹음 또는 AI 음성)
- 캐릭터 IP: KIPRIS 검색, 변리사 상담, 벡터 최종본(디자이너)
- 새 채널 「추억을 읽는 시간」도 Claude(이 클라우드)에서 운영 예정 — 두 채널 분리 방식은 사용자 결정 대기
