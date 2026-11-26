"""꼬망 목소리 만들기 (「추억을 읽는 시간」 전용)
구글 TTS ko-KR-Chirp3-HD-Leda(속도 1.05) → 높이 4음 올림(asetrate 방식, 떨림 없음, 길이 그대로)
사용법: python3 channels/chueok/kkomang_voice.py channels/chueok/docs/m001_<소재>_script.md channels/chueok/assets/voice/m001
"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tts_lines as T

VOICE, RATE, SEMI = "ko-KR-Chirp3-HD-Leda", 1.05, 4      # 2026-11-26 사용자 선택: 견본 '소니_3'
UP = 2 ** (SEMI / 12)


def kkomang(text, out, rate=RATE):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        T.synth(text, VOICE, tmp.name, rate)
        subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-af",
                               f"asetrate=44100*{UP:.4f},aresample=44100,atempo={1 / UP:.4f}", "-ac", "1", out])


if __name__ == "__main__":
    script, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for k, t in enumerate(T.script_lines(script), 1):
        p = os.path.join(outdir, f"line_{k:02d}.wav")
        kkomang(t, p)
        print(p, t)
    kkomang("하나... 둘... 셋!", os.path.join(outdir, "count.wav"), 0.9)
