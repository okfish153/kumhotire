"""AI 나레이션 생성.

1순위: OpenAI TTS (gpt-4o-mini-tts) — 네트워크 프록시가 키를 주입하므로 코드에는 키가 없다.
2순위(폴백): espeak-ng 한국어 음성 (오프라인).

각 대사를 build/narr_XX.wav (44.1kHz mono) 로 저장하고, 실제 길이(ffprobe)를 반환한다.
"""
import json
import os
import subprocess
import urllib.request

LINES = [
    "타이어 바꾸실 때, 가격만 보세요?",
    "잠깐! 타이어는 가격도 중요하지만, 내 차에 맞는 선택이 더 중요합니다!",
    "타이어 상태부터 마모, 휠얼라인먼트까지 꼼꼼하게!",
    "금호타이어 전문점! 내 차에 맞는 타이어를 합리적으로!",
    "교환부터 휠얼라인먼트까지 한곳에서!",
    "타이어 교환 고민 중이세요? 나주 금호타이어 송월점! 지금 상담해 보세요!",
]

VOICE_INSTRUCTIONS = (
    "한국 지역 자동차 정비점 광고 성우. 밝고 힘있고 신뢰감 있는 톤, "
    "빠른 템포로 또박또박. 질문은 호기심을 끌게, 마지막 문장은 친근하게 권유하듯."
)


def probe_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", path])
    return float(out.strip())


def _openai_tts(text, raw_path):
    body = json.dumps({
        "model": "gpt-4o-mini-tts", "voice": "onyx", "input": text,
        "instructions": VOICE_INSTRUCTIONS, "response_format": "wav",
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech", data=body,
        headers={"Content-Type": "application/json",
                 # 실제 키는 프록시가 주입한다 (placeholder).
                 "Authorization": "Bearer " + os.environ.get("OPENAI_API_KEY", "proxy-injected")})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    with open(raw_path, "wb") as f:
        f.write(data)


def _espeak_tts(text, raw_path):
    subprocess.check_call(["espeak-ng", "-v", "ko", "-s", "180", "-p", "45",
                           "-w", raw_path, text])


def generate(build_dir, engine="auto"):
    os.makedirs(build_dir, exist_ok=True)
    use = engine
    if engine == "auto":
        try:
            _openai_tts(LINES[0], os.path.join(build_dir, "probe.wav"))
            use = "openai"
        except Exception as e:  # 401, 네트워크 차단 등
            print(f"[narration] OpenAI TTS 사용 불가 ({e}) -> espeak-ng 폴백")
            use = "espeak"
    print(f"[narration] engine = {use}")
    durs = []
    for i, line in enumerate(LINES):
        raw = os.path.join(build_dir, f"narr_raw_{i:02d}.wav")
        out = os.path.join(build_dir, f"narr_{i:02d}.wav")
        (_openai_tts if use == "openai" else _espeak_tts)(line, raw)
        # 앞뒤 무음 제거 + 보이스 EQ/컴프레션 (방송 톤)
        af = ("silenceremove=start_periods=1:start_threshold=-45dB,"
              "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              "highpass=f=90,equalizer=f=3000:t=q:w=1.2:g=3,"
              "acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=3")
        if use == "espeak":
            # 로봇 톤을 조금 완화: 저역 보강 + 아주 약한 공간감
            af += ",equalizer=f=180:t=q:w=1:g=3,aecho=0.8:0.5:28:0.12"
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                               "-af", af, "-ar", "44100", "-ac", "1", out])
        durs.append(probe_duration(out))
    return use, durs
