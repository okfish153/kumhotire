"""대본 표의 대사를 구글 클라우드 TTS로 문장마다 만든다 → assets/voice/epXX/line_XX.wav
키는 네트워크 프록시가 X-Goog-Api-Key 헤더로 넣는다(코드에는 키가 없다).
사용법: python3 tools/tts_lines.py docs/ep03_grandeur_xg_script.md assets/voice/ep03 [--voice ko-KR-Chirp3-HD-Algenib] [--rate 1.05]
"""
import argparse, base64, json, os, urllib.request

VOICE = "ko-KR-Chirp3-HD-Algenib"     # 채널 목소리 (2026-11-25 사용자 선택)


def synth(text, voice, out, rate=1.05):
    body = {"input": {"text": text}, "voice": {"languageCode": "ko-KR", "name": voice},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 44100, "speakingRate": rate}}
    req = urllib.request.Request("https://texttospeech.googleapis.com/v1/text:synthesize", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "X-Goog-Api-Key": "proxy-injected"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    with open(out, "wb") as f:
        f.write(base64.b64decode(d["audioContent"]))


def script_lines(path):
    """'## 녹음용 대본' 표의 첫 표만 읽는다"""
    out, inside = [], False
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("## "):
            if inside:
                break
            inside = "대본" in ln
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if inside and len(c) >= 3 and c[0].isdigit():
            out.append(c[2])
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("outdir")
    ap.add_argument("--voice", default=VOICE); ap.add_argument("--rate", type=float, default=1.05)
    ap.add_argument("--no-count", action="store_true", help="퀴즈 카운트다운(count.wav)을 만들지 않음")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for k, t in enumerate(script_lines(a.script), 1):
        p = os.path.join(a.outdir, f"line_{k:02d}.wav")
        synth(t, a.voice, p, a.rate)
        print(p, t)
    if not a.no_count:                     # 퀴즈 뒤 카운트다운: 한 파일로 만들어야 박자가 자연스럽다
        p = os.path.join(a.outdir, "count.wav")
        synth("하나... 둘... 셋!", a.voice, p, 0.9)
        print(p, "하나... 둘... 셋!")
