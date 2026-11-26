# 캐릭터 설정서 v1 (초안): 꼬망 — 「추억을 읽는 시간」

## 핵심
- **이름:** 꼬망 (2026-11-26 사용자 확정)
- **역할:** 그 시절 이야기를 들려주는 귀여운 해설자. 손녀·손자 같은 분위기의 귀여움이 핵심이지만 **특정 가족 역할로 고정하지 않는다** — 이야기에 따라 할아버지·할머니, 엄마·아빠, 삼촌·이모 역할을 **소품만 바꿔** 연기한다
- **목소리:** 구글 TTS Chirp3-HD-Leda → 4음 올림(떨림 없는 방식). `kkomang_voice.py` (견본 `assets/voice/samples/꼬망_인사.mp3`)
- **말투:** 존댓말, 밝고 호기심 많은 말투. "우와!", "그 시절엔 말이죠~", "하나, 둘, 셋!"
- **시그니처:** 낡은 사진첩을 펼치는 동작 / 사진첩 사이로 빼꼼 얼굴 내밀기

## 생김새 (기준 그림을 만들 때 그대로 지킴)
- 2.5등신, 아주 둥근 얼굴, 크고 반짝이는 동그란 눈(검은 눈동자에 흰 하이라이트 2개), 발그레한 볼, 작은 웃는 입
- 머리: 짧은 단발(밤색), 정수리에 작은 곱슬 한 가닥(꼬망의 표시)
- 옷: 머스터드 노랑 니트 가디건 + 크림색 셔츠 + 청 멜빵바지(1980~90년대 아이 옷 느낌), 갈색 운동화
- 소품: 갈색 가죽 표지의 낡은 사진첩(앞면에 작은 하트 스티커)
- 선: 진한 갈색 굵은 외곽선, 평면 채색(그림자 거의 없음), 차형과 같은 단순한 2D 스타일

## 색 (차를 읽는 시간의 빨강·검정·앰버와 겹치지 않게)
| 이름 | 색 | 쓰임 |
|---|---|---|
| 추억 크림 | #FFF4E0 | 얼굴 바탕·셔츠·자막 배경 |
| 머스터드 | #E8B23A | 가디건·강조 글자 |
| 사진첩 갈색 | #8B5E3C | 머리·사진첩·외곽선 |
| 데님 | #4A6FA5 | 멜빵바지 |
| 볼 분홍 | #F7A8B0 | 볼 |
| 바랜 청록 | #5FA8A0 | 포인트(도장·카운터) |

## 역할 소품 (기준 그림 위에 얹는 별도 그림)
| 역할 | 소품 |
|---|---|
| 할아버지 | 회색 중절모, 둥근 돋보기안경, 나무 지팡이 |
| 할머니 | 뜨개 숄, 동그란 안경, 머리 위 쪽진 머리 장식 |
| 아빠 | 넥타이, 서류 가방 |
| 엄마 | 앞치마, 국자 |
| 삼촌 | 야구 모자(뒤로), 카세트 플레이어 |
| 이모 | 큰 머리핀, 작은 핸드백 |

## 만드는 방법
1. 아래 프롬프트로 제미나이에서 **기준 그림 한 장**(초록 배경)을 만들어 올린다
2. 배경 제거 `tools/green_key.py` → `channels/chueok/assets/character/kkomang_base.png`
3. 차형처럼 한 장을 잘라 움직인다(머리 들썩, 점프, 놀람 등). 역할 소품은 따로 만들어 얹는다

## 제미나이 프롬프트 — 기준 그림 (복사해서 그대로)

```
A cute 2D mascot character named "Kkomang" for a Korean nostalgia YouTube channel.
Full body, standing, facing slightly to the right (3/4 view), smiling, holding an old brown leather photo album with both hands at chest height.
Proportions: 2.5 heads tall, very round soft face, big round sparkling black eyes with two white highlights, rosy pink cheeks, small happy mouth.
Hair: short chestnut-brown bob with one small curl sticking up on top of the head.
Outfit: mustard-yellow knitted cardigan over a cream shirt, denim overalls, brown sneakers — a 1980s–90s Korean child look.
Style: simple flat 2D illustration, thick dark-brown outlines, flat colors, almost no shading, clean shapes, friendly and warm.
Colors: cream #FFF4E0, mustard #E8B23A, brown #8B5E3C, denim #4A6FA5, cheek pink #F7A8B0.
Background: solid pure green #00FF00 only, no shadow on the ground, no text, no logo, no watermark, no other objects.
```

## 제미나이 프롬프트 — 역할 소품 예시 (기준 그림을 첨부하고)

```
Using the attached character exactly as-is (same face, proportions, colors and line style), draw the same character wearing a grey fedora hat and round reading glasses, holding a wooden cane — playing a grandpa role. Same pose. Solid pure green #00FF00 background, no text.
```

## 이름·권리 메모
- '꼬망'으로 확인된 비슷한 이름: 아동복 브랜드 '꼬망스'((주)꼬망스), 만화 '무술소년 꼬망'의 주인공, 유튜브 '꼬망 부부'(사용자 확인)
- 이름 자체는 저작권 보호 대상이 아니다. 문제는 **상표**(같거나 비슷한 이름이 같은 상품·서비스 분류에 먼저 등록돼 있는지)
- 굿즈·상표 출원 전 KIPRIS에서 '꼬망' 검색: 41류(방송·콘텐츠), 9류(영상 파일), 16류(문구), 25류(의류 — 꼬망스와 겹칠 수 있음), 28류(완구)
- 캐릭터 생김새는 '무술소년 꼬망'과 닮지 않게 독자적으로 만든다
