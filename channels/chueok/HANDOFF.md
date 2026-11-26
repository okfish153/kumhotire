# 인수인계: 추억을 읽는 시간 (2026-11-26, 새 세션 시작용)

새 세션은 **루트 `CLAUDE.md`(공통 규칙·채널 구분) → `channels/chueok/CLAUDE.md`(이 채널 규칙) → 이 문서** 순서로 읽고 시작한다.
이 세션은 「추억을 읽는 시간」 전용이다. 「차를 읽는 시간」 파일(루트 `docs/`, `ep*.py`, `long*.py`, `output/` 등)과 그 드라이브는 **읽거나 고치지 않는다.** (참고 예시로 읽기만 하는 것은 아래 6번 목록만)

## 1. 한눈에 보기

| 구분 | 내용 |
|---|---|
| 채널 | 추억을 읽는 시간 — 매일 아침 주요 이슈를 그 시절 추억과 이어 1분 쇼츠로 읽어 주는 채널 (30대 후반~60대) |
| 캐릭터 | **꼬망** — 손녀·손자 같은 귀여운 분위기의 해설자. 역할은 고정하지 않고 소품만 바꿔 할아버지·할머니·엄마·아빠·삼촌·이모를 연기 |
| 목소리 | 꼬망 목소리 = 구글 TTS `ko-KR-Chirp3-HD-Leda` 속도 1.05 → 4음 올림(asetrate 방식, 떨림 없음). **반드시 `channels/chueok/kkomang_voice.py`로 만든다** |
| 화면 색 | 추억 크림 #FFF4E0 · 머스터드 #E8B23A · 사진첩 갈색 #8B5E3C · 데님 #4A6FA5 · 볼 분홍 #F7A8B0 · 바랜 청록 #5FA8A0 (차 채널의 빨강·검정·앰버와 겹치지 않게) |
| 번호 | M001부터 (차 채널 EP 번호와 겹치지 않게) |
| 해시태그 마지막 | `#추억을읽는시간` |
| 저장소 | okfish153/kumhotire — 기본 브랜치 `claude/youtube-shorts-reels-video-pbpz19`(= 작업 브랜치와 같은 상태). 이 채널 작업은 **`channels/chueok/` 안에서만**, 커밋 메시지는 `[추억] …` |
| 아침 브리핑 | 예약 작업 「[추억] 추억 아침 브리핑」 trig_01TLVx5X2vut4cUJANGsSctj — 매일 한국 시간 4:41 시작, 휴대폰 푸시. 오늘 주요 이슈 7개 + 추억 연결 아이디어 3개(중복 표시) + 오늘의 추천 1개 |

## 2. 지금까지 한 일 (2026-11-26)

1. 채널 구조 분리: 루트 `CLAUDE.md`(공통) / `channels/car/`(차) / `channels/chueok/`(추억). 드라이브 최상위 폴더도 따로
2. 목소리: 손녀·손자 후보 8개 → 사용자가 '손녀 A(Leda)' 선택 → 떨림 줄인 4개 중 **3번(asetrate 방식 4음)** 확정 → `kkomang_voice.py`
3. 캐릭터 이름: '소니'(Sony와 소리가 같아 상표 우려) → **꼬망** 확정
4. 이름 권리 확인: 비슷한 이름 = 아동복 「꼬망스」((주)꼬망스, 의류 25류와 겹칠 수 있음), 만화 「무술소년 꼬망」 주인공, 유튜브 「꼬망 부부」. 이름 자체는 저작권 대상이 아니고, 굿즈·상표 출원 전 KIPRIS 검색 필요(41·9·16·25·28류) — **사용자 할 일**
5. 캐릭터 설정서 v1 `docs/character_kkomang.md` (생김새·색·역할 소품·제미나이 프롬프트)
6. 기준 그림 확정(사용자가 제미나이로 만듦 → 배경 제거): `assets/character/kkomang_base.png`(기본, 사진첩), `assets/character/kkomang_role_grandpa.png`(할아버지 역할), 원본 `assets/character/raw/`
7. 콘텐츠 목록(빈 틀) `content_registry.csv` = 드라이브 시트, 템플릿 `docs/templates.md`, 교훈 `docs/lessons.md`

## 3. 파일 위치 (`channels/chueok/`)

| 파일 | 내용 |
|---|---|
| `CLAUDE.md` | 이 채널 규칙 (채널 정의, 꼬망, 목소리, 위치, 파일 이름 규칙, 만드는 순서) |
| `HANDOFF.md` | 이 문서 |
| `content_registry.csv` | 콘텐츠 목록 (중복 확인). 완성할 때마다 한 줄 추가 + 드라이브 시트 교체 |
| `kkomang_voice.py` | 꼬망 목소리: `python3 channels/chueok/kkomang_voice.py <대본.md> <음성 폴더>` (문장별 line_XX.wav + 카운트다운 count.wav) |
| `docs/character_kkomang.md` | 꼬망 설정서 v1 |
| `docs/templates.md` | 대본 표·근거 표·장면표·업로드 글 5종·블로그·목록 한 줄 틀 |
| `docs/lessons.md` | 교훈 13가지와 게시 전 체크리스트 |
| `assets/character/` | 꼬망 기준 그림, 역할 그림, 원본, 확인용 그림 |
| `assets/voice/samples/` | 목소리 견본 (확정본: `꼬망_인사.mp3`, `소니_3_다른방식_4음.mp3`) |
| `assets/`, `output/` | 에피소드 사진·음성, 완성 영상 |

공통 도구(가져다 쓰기만): `tools/tts_lines.py`(대본 읽기·TTS), `tools/green_key.py`(초록 배경 제거), `video.py`·`audio.py`(그리기·효과음), `tools/chahyung_motion.py`(차형용 움직임 — 꼬망용은 따로 만든다)

## 4. 드라이브 「추억을 읽는 시간」 1qXkcZSBmAca0fHF8-9Asc7sUE7jhY7hb

```
추억을 읽는 시간/
├─ 00_채널 기본/       1OHuZc5ZjMqSN3UqW-C7xoK4MD1gEUT_Y  채널 규칙, 공통 규칙, 인수인계, 콘텐츠 목록 시트(1l56WMEtH94r4LfjgratNnHwdIFOxPnEr39Ixv8XaeRg)
├─ 01_캐릭터/          1NjLFIxYWCT702bAjemE60onnl8udd9ZG  꼬망 설정서 v1, 기준 그림·할아버지 역할·원본
├─ 03_에피소드/        1BoroJ3JqwTAmF-u7azdDCHCQ39SvKpwN  편마다 M001_<소재>/ 폴더
├─ 04_완성 영상 모음/  1w68zf3WvXNklY5FrYy-SHgTrI96RXZuL
├─ 05_롱폼·블로그/     1gZ12hJHTAMiu5NamySZhUhAV6EH3oJPa
└─ 99_자료 출처/       1bef7pbdGCTHsyWig5R-6ZKE7aWSvIm7g
```
- 드라이브 연결 도구는 한 번에 약 3MB까지 → 영상(mp4)은 사용자가 직접 올림
- 마크다운을 구글 문서로 올리면 이모지가 깨짐 → 이모지 없이

## 5. 다음 할 일 (순서대로)

1. **꼬망 움직임 만들기:** `kkomang_base.png` 한 장을 머리·몸·팔(사진첩)로 나눠 움직임(말할 때 들썩, 점프, 놀람, 갸웃, 사진첩 흔들기, 손 흔들기 등) → `channels/chueok/kkomang_motion.py` + 짧은 시험 영상. 할아버지 역할 그림에도 같은 방식이 되게
2. **역할 그림 더 만들기:** 할머니·엄마·아빠·삼촌·이모용 제미나이 프롬프트(기본 꼬망 그림 첨부, 초록 배경) → 사용자가 만들어 올리면 배경 제거
3. **화면 틀 만들기:** 쇼츠 공통 형식(위 2줄 고정 제목 / 가운데 영상 / 아래 큰 자막)을 이 채널 색(크림·머스터드·갈색, '옛날 사진첩' 느낌)으로
4. **첫 편 M001:** 아침 브리핑 추천 아이디어로 시작 → 중복 확인 → 근거 표 → 대본(사용자 확인) → 사진·그림 → 꼬망 목소리 → 영상 → 업로드 글 5종 → 목록 추가 → 드라이브
5. 사용자: KIPRIS '꼬망' 검색, 제미나이에서 큰 원본 그림 받아 두기(지금 그림은 캐릭터 높이 약 1,000px)

## 6. 참고로 읽어도 되는 「차를 읽는 시간」 완성 예시 (고치지 않음)

- 쇼츠 구조: `ep04_grandeur_tg.py`(+ `ep03_grandeur_xg.py`의 타임라인·카운트다운), 대본 `docs/ep04_grandeur_tg_script.md`, 업로드 글 `docs/ep04_grandeur_tg_upload.md`
- 롱폼·홍보 쇼츠: `long01_genesis.py`, `short01_genesis.py` / 블로그: `docs/blog/genesis_0*.md`, `tools/make_blog_genesis.py`
- 캐릭터 움직임: `tools/chahyung_motion.py` (꼬망용을 만들 때 방식만 참고)

## 7. 환경 메모

- 클라우드 환경 `kumhotire`: Wikimedia Commons 3곳·newsroom.genesis.com 접속 허용, 구글 TTS 키(헤더 X-Goog-Api-Key) 저장됨
- Commons는 요청이 잦으면 429 → 1280/1920px 썸네일로 받고 10초씩 늘려 재시도
- 기업 뉴스룸 사진은 약관상 쓰지 않음(제네시스 뉴스룸: 서면 허락 없는 게시·상업 이용 금지)
- 퀴즈 카운트다운은 "하나... 둘... 셋!"을 한 파일로 만들어 소리 구간으로 박자를 찾음(따로 만들면 "셋"이 잘림)
