# 금호타이어 송월점 – 유튜브 숏츠 / 인스타 릴스

대본(`assets/script.pdf`)과 포스터·매장 사진(`assets/images/`)으로 만든 30초 세로 홍보 영상(1080x1920, 30fps).

- 결과물: `output/kumho_songwol_shorts.mp4` (+ 업로드용 자막 `output/kumho_songwol_shorts.srt`)
- 다시 렌더링: `python3 make_video.py` (필요: ffmpeg, Python 패키지 numpy·Pillow·scipy·sherpa-onnx)

## 구성 (대본 6단락 = 6장면)
| 시간 | 대본 | 화면 |
|---|---|---|
| 0~3초 | 타이어 바꾸실 때, 가격만 보세요? | 매장 거리 사진, '가격만' 슬램 타이포, 흔들리는 ₩ 가격표, 카메라 쉐이크 |
| 3~9초 | 잠깐! … 내 차에 맞는 선택이 더 중요 | '잠깐!' 스탬프, 가격 vs 내 차에 맞는 선택 비교 카드, '더 중요!' 배지 |
| 9~14초 | 상태·마모·휠얼라인먼트까지 꼼꼼하게 | 매장 사진 카드와 스캔 레이저·HUD, 01/02/03 체크리스트 |
| 14~18초 | 금호타이어 전문점! 합리적으로! | '전문점' 리본, 매장 포스터에서 렌탈 포스터로 넘어가는 장면, 빛 반사 |
| 18~21초 | 교환부터 휠얼라인먼트까지 한곳에서 | 포스터 서비스 아이콘 4종 타일, ONE STOP 배지 |
| 21~30초 | 나주 금호타이어 송월점! 지금 상담 | 매장명, 전화 버튼(061-335-6114), 주소, 네이버 리뷰 QR |

## 오디오
- BGM·효과음: `audio.py`에서 직접 합성(124BPM 일렉트로 팝, whoosh/impact/pop/ding/cash 등). 저작권 걱정 없음.
- 나레이션: `narration.py`. 기본값은 **Supertonic 3**(Supertone, 오프라인 신경망 한국어 TTS, 남성 음성 sid 5, 속도 1.0).
  - 모델(약 145MB)은 첫 실행 때 npm 레지스트리에서 `tools/fetch_supertonic.py`로 받아 `build/supertonic/`에 저장(git 제외). `pip install sherpa-onnx` 필요.
  - 음성 바꾸기: `SUPERTONIC_SID=0~4`(여성) / `5~9`(남성), 속도는 `SUPERTONIC_SPEED=1.1`처럼 지정.
  - `assets/voice/`에 음성 파일(Typecast·Google TTS 등)을 넣으면 그 파일을 우선 사용. `--engine google|openai|espeak`로 직접 선택도 가능.
- 나레이션이 나올 때 BGM 볼륨을 자동으로 낮추고, 전체 음량은 -14 LUFS(숏츠/릴스 권장)로 맞춤.
- 자막 타이밍과 장면 연출은 실제 나레이션 길이에 맞춰 자동으로 조정.
