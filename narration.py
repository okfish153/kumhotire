"""AI 나레이션 생성.

0순위: Typecast 등에서 받은 음성 파일 (assets/voice/)
   - 대본 6단락을 각각 파일로: 01.wav ~ 06.wav (mp3/m4a도 가능, 이름순 정렬)
   - 또는 전체 1개 파일: 단락 사이 무음(약 0.8초 이상)을 찾아 자동으로 6조각으로 자름
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


VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "voice")
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac")


def voice_files():
    if not os.path.isdir(VOICE_DIR):
        return []
    return sorted(os.path.join(VOICE_DIR, f) for f in os.listdir(VOICE_DIR)
                  if f.lower().endswith(AUDIO_EXT))


def _split_single(path, n, build_dir):
    """전체 음성 1개를 가장 긴 무음 n-1곳에서 잘라 n개 파일로"""
    import re
    log = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-40dB:d=0.25",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    total = probe_duration(path)
    gaps = [(e - s, (s + e) / 2) for s, e in zip(st, en) if s > 0.3 and e < total - 0.3]
    if len(gaps) < n - 1:
        raise SystemExit(f"[narration] 무음 구간이 {len(gaps)}곳뿐이라 {n}단락으로 못 나눕니다. "
                         "Typecast에서 단락 사이 쉼을 1초 정도로 늘리거나, 단락별 파일 6개로 넣어주세요.")
    cuts = sorted(m for _, m in sorted(gaps, reverse=True)[: n - 1])
    bounds = [0.0] + cuts + [total]
    outs = []
    for i in range(n):
        o = os.path.join(build_dir, f"voice_split_{i:02d}.wav")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ss", f"{bounds[i]:.3f}",
                               "-to", f"{bounds[i + 1]:.3f}", o])
        outs.append(o)
    print("[narration] 자동 분할 지점(초):", [round(c, 2) for c in cuts])
    return outs


def generate(build_dir, engine="auto"):
    os.makedirs(build_dir, exist_ok=True)
    use = engine
    files = voice_files()
    if engine == "auto" and files:
        use = "files"
    if use == "files":
        if len(files) == 1:
            files = _split_single(files[0], len(LINES), build_dir)
        if len(files) != len(LINES):
            raise SystemExit(f"[narration] assets/voice 에 파일이 {len(files)}개입니다. "
                             f"단락별 {len(LINES)}개 또는 전체 1개를 넣어주세요.")
    elif engine == "auto":
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
        if use == "files":
            raw = files[i]
        else:
            (_openai_tts if use == "openai" else _espeak_tts)(line, raw)
        # 앞뒤 무음 제거 + 보이스 EQ/컴프레션 (방송 톤)
        af = ("silenceremove=start_periods=1:start_threshold=-45dB,"
              "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              "highpass=f=90,equalizer=f=3000:t=q:w=1.2:g=3,"
              "acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=3")
        if use == "files":  # 이미 다듬어진 성우 음성: EQ는 약하게
            af = af.replace("g=3,", "g=1.5,")
        if use == "espeak":
            # 로봇 톤을 조금 완화: 저역 보강 + 아주 약한 공간감
            af += ",equalizer=f=180:t=q:w=1:g=3,aecho=0.8:0.5:28:0.12"
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                               "-af", af, "-ar", "44100", "-ac", "1", out])
        durs.append(probe_duration(out))
    return use, durs
