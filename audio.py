"""배경음악(BGM)과 효과음(SFX)을 numpy로 직접 합성하고 나레이션과 믹스한다.

저작권 문제 없는 100% 자체 합성 사운드:
- BGM: 124BPM 일렉트로 팝 (킥/클랩/하이햇/베이스/코드 플럭)
- SFX: whoosh, impact, pop, ding, stop(잠깐), riser, cash(합리적 가격), click
"""
import numpy as np
import wave
from scipy.signal import butter, sosfilt

SR = 44100
rng = np.random.default_rng(7)


def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _filt(x, kind, f):
    sos = butter(2, f, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(1)
    return a


def write_wav(path, stereo):
    s = np.clip(stereo, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((s * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- 악기
def kick():
    t = _t(0.35)
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * 1.0


def clap():
    t = _t(0.25)
    n = _filt(rng.standard_normal(len(t)), "bandpass", [900, 3500])
    env = np.exp(-t * 22) + 0.6 * np.exp(-((t - 0.012) % 0.011) * 300) * (t < 0.035)
    return n * env * 0.5


def hat(open_=False):
    t = _t(0.18 if open_ else 0.05)
    n = _filt(rng.standard_normal(len(t)), "highpass", 7000)
    return n * np.exp(-t * (18 if open_ else 80)) * 0.22


def saw(freq, sec, detune=(0,)):
    t = _t(sec)
    out = np.zeros_like(t)
    for d in detune:
        ff = freq * (1 + d)
        out += 2 * ((t * ff) % 1) - 1
    return out / len(detune)


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def bgm(total):
    bpm = 124
    beat = 60 / bpm
    n = int(total * SR) + SR
    L = np.zeros(n); R = np.zeros(n)

    def add(buf, x, t, g=1.0):
        i = int(t * SR)
        if i >= n:
            return
        x = x[: n - i]
        buf[i:i + len(x)] += x * g

    # Am - F - C - G  (각 1마디)
    prog = [(57, [69, 72, 76]), (53, [65, 69, 72]), (48, [64, 67, 72]), (55, [62, 67, 71])]
    k, c = kick(), clap()
    bars = int(total / (beat * 4)) + 2
    for b in range(bars):
        root, chord = prog[b % 4]
        for q in range(4):
            tb = (b * 4 + q) * beat
            add(L, k, tb, 0.9); add(R, k, tb, 0.9)
            if q in (1, 3):
                add(L, c, tb, 0.55); add(R, c, tb, 0.45)
            for e in range(2):
                th = tb + e * beat / 2
                hh = hat(open_=(e == 1 and q == 3))
                add(L, hh, th + 0.004, 0.8 if e else 0.4); add(R, hh, th, 0.8 if e else 0.4)
            # 베이스: 8분 오프비트 펌핑
            for e in range(2):
                tbass = tb + e * beat / 2
                bs = saw(note(root - 12), beat / 2 * 0.9, (0, 0.004))
                bs = _filt(bs, "lowpass", 420) * np.exp(-_t(len(bs) / SR) * 5)
                add(L, bs, tbass, 0.42); add(R, bs, tbass, 0.42)
        # 코드 플럭 (3+3+2 리듬)
        for off in (0, 1.5, 3.0):
            tp = (b * 4 + off) * beat
            ch = sum(saw(note(m), beat * 1.2, (-0.006, 0.006)) for m in chord) / 3
            ch = _filt(ch, "lowpass", 2200) * np.exp(-_t(len(ch) / SR) * 4.5)
            add(L, ch, tp, 0.20); add(R, ch, tp + 0.008, 0.20)
        # 리드 아르페지오 (하이 레이어)
        for s in range(8):
            ta = (b * 4 + s * 0.5) * beat
            m = chord[s % 3] + 12
            ar = np.sin(2 * np.pi * note(m) * _t(beat * 0.45)) * np.exp(-_t(beat * 0.45) * 10)
            add(L if s % 2 else R, ar, ta, 0.06)

    # 사이드체인 펌핑 (킥에 맞춰 코드/베이스가 숨쉬는 느낌)
    tt = np.arange(n) / SR
    pump = 0.55 + 0.45 * np.clip(((tt % beat) / beat) * 3.0, 0, 1)
    out = np.stack([L * pump, R * pump], 1)
    return out[: int(total * SR)]


# ---------------------------------------------------------------- 효과음
def sfx_whoosh(sec=0.45, up=True):
    t = _t(sec)
    nse = rng.standard_normal(len(t))
    out = np.zeros_like(t)
    seg = 256
    for i in range(0, len(t), seg):
        p = i / len(t)
        fc = (400 + 5000 * p) if up else (5400 - 5000 * p)
        chunk = nse[max(0, i - 512): i + seg]
        y = _filt(chunk, "bandpass", [fc * 0.6, min(fc * 1.6, 20000)])
        out[i:i + seg] = y[-len(out[i:i + seg]):]
    env = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 1.5
    return out * env * 0.9


def sfx_impact():
    t = _t(0.9)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-t * 12)) / SR) * np.exp(-t * 4.5)
    crack = _filt(rng.standard_normal(len(t)), "lowpass", 2500) * np.exp(-t * 25)
    return boom * 1.0 + crack * 0.5


def sfx_pop():
    t = _t(0.12)
    f = 600 + 900 * (t / 0.12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * 0.6


def sfx_ding():
    t = _t(1.2)
    out = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d)
              for f, a, d in [(1568, 1, 3.5), (3136, .45, 5), (4704, .2, 7), (2349, .3, 4)])
    return out * 0.35


def sfx_stop():
    """'잠깐!' 레코드 스크래치 + 브레이크 느낌"""
    t = _t(0.35)
    f = 900 * np.exp(-t * 7) + 120
    s = (2 * ((np.cumsum(f) / SR) % 1) - 1)
    s = _filt(s, "lowpass", 3000) * np.exp(-t * 6)
    n = _filt(rng.standard_normal(len(t)), "bandpass", [1500, 6000]) * np.exp(-t * 10) * 0.4
    return (s + n) * 0.55


def sfx_riser(sec=1.2):
    t = _t(sec)
    f = 200 * 2 ** (3 * t / sec)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    n = _filt(rng.standard_normal(len(t)), "highpass", 3000)
    return (s * 0.25 + n * 0.25) * (t / sec) ** 2


def sfx_cash():
    t = _t(0.9)
    bell = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 6) for f in (2637, 3951, 5274)) / 3
    clk = _filt(rng.standard_normal(len(t)), "highpass", 4000) * np.exp(-t * 60)
    out = bell * 0.4 + clk * 0.5
    out2 = np.zeros(len(out) + int(0.09 * SR))
    out2[:len(out)] += clk * 0.5
    out2[int(0.09 * SR):] += bell * 0.45
    return out2


def sfx_click():
    t = _t(0.05)
    return _filt(rng.standard_normal(len(t)), "bandpass", [2000, 6000]) * np.exp(-t * 120) * 0.6


SFX = {"whoosh": sfx_whoosh, "whoosh_down": lambda: sfx_whoosh(0.4, False),
       "impact": sfx_impact, "pop": sfx_pop, "ding": sfx_ding, "stop": sfx_stop,
       "riser": sfx_riser, "cash": sfx_cash, "click": sfx_click}


def bgm_cute(total):
    """귀여운 톤: 112BPM, 장조(C-G-Am-F), 마림바 + 글로켄슈필 + 우쿨렐레풍 플럭 + 손가락 스냅"""
    bpm = 112
    beat = 60 / bpm
    n = int(total * SR) + SR
    L = np.zeros(n); R = np.zeros(n)

    def add(buf, x, t, g=1.0):
        i = int(t * SR)
        if i >= n:
            return
        x = x[: n - i]
        buf[i:i + len(x)] += x * g

    def marimba(f, sec=0.45):
        t = _t(sec)
        return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)) * np.exp(-t * 9)

    def glock(f, sec=0.9):
        t = _t(sec)
        return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 5)

    def pluck(f, sec=0.5):  # Karplus-Strong 우쿨렐레 느낌
        N = int(SR / f)
        buf = rng.uniform(-1, 1, N)
        out = np.zeros(int(sec * SR))
        for i in range(len(out)):
            out[i] = buf[i % N]
            buf[i % N] = 0.5 * (buf[i % N] + buf[(i + 1) % N]) * 0.996
        return out

    def snap():
        t = _t(0.08)
        return _filt(rng.standard_normal(len(t)), "bandpass", [1800, 5000]) * np.exp(-t * 70) * 0.5

    def soft_kick():
        t = _t(0.25)
        return np.sin(2 * np.pi * np.cumsum(55 + 70 * np.exp(-t * 30)) / SR) * np.exp(-t * 14)

    prog_ = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [57, 60, 64]), (41, [57, 60, 65])]
    melody = [0, 2, 1, 2, 0, 2, 1, 3]  # 코드톤 인덱스 패턴 (3 = 옥타브 위 루트)
    k, sn = soft_kick(), snap()
    plucks = {}
    bars = int(total / (beat * 4)) + 2
    for b in range(bars):
        root, chord = prog_[b % 4]
        for q in range(4):
            tb = (b * 4 + q) * beat
            if q in (0, 2):
                add(L, k, tb, 0.55); add(R, k, tb, 0.55)
            if q in (1, 3):
                add(L, sn, tb, 0.6); add(R, sn, tb + 0.006, 0.45)
            sh = hat() * 0.6
            add(L, sh, tb + beat / 2, 0.5); add(R, sh, tb + beat / 2, 0.7)
            # 베이스 (부드러운 사인 플럭)
            bt = _t(beat * 0.8)
            bass = np.sin(2 * np.pi * note(root - 12) * bt) * np.exp(-bt * 4)
            add(L, bass, tb, 0.35); add(R, bass, tb, 0.35)
            # 우쿨렐레 스트럼 (업/다운)
            for e, delay in ((0, 0.0), (1, beat / 2)):
                for j, m in enumerate(chord):
                    if m not in plucks:
                        plucks[m] = pluck(note(m))
                    add(L if j % 2 else R, plucks[m], tb + delay + j * 0.012, 0.11)
        # 마림바 멜로디 (8분음표)
        for s_ in range(8):
            idx = melody[(s_ + b) % 8]
            m = (chord[idx] if idx < 3 else chord[0] + 12) + 12
            add(L if s_ % 2 else R, marimba(note(m)), (b * 4 + s_ * 0.5) * beat, 0.16)
        # 글로켄 반짝 (마디 끝)
        add(L, glock(note(chord[2] + 24)), (b * 4 + 3.5) * beat, 0.07)
        add(R, glock(note(chord[0] + 36)), (b * 4 + 3.75) * beat, 0.05)
    return np.stack([L, R], 1)[: int(total * SR)]


def sfx_boing():
    t = _t(0.5)
    f = 180 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4) + 90 * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * 0.7


def sfx_squeak():
    t = _t(0.18)
    f = 900 + 1600 * (t / 0.18) ** 0.7
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.18) * 0.45


def sfx_sparkle():
    out = np.zeros(int(0.9 * SR))
    for i, m in enumerate([88, 92, 95, 100, 104]):
        t = _t(0.5)
        x = np.sin(2 * np.pi * note(m) * t) * np.exp(-t * 9)
        j = int(i * 0.06 * SR)
        out[j:j + len(x)] += x[: len(out) - j]
    return out * 0.25


def sfx_shock():
    """'헉!' 만화 효과: 내려가는 슬라이드 휘슬 + 쿵"""
    t = _t(0.55)
    f = 1400 * np.exp(-t * 4) + 200
    w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3) * 0.35
    return w + sfx_impact()[: len(t)] * 0.5


SFX.update({"boing": sfx_boing, "squeak": sfx_squeak, "sparkle": sfx_sparkle, "shock": sfx_shock})


def build_mix(total, narr_paths, narr_starts, events, out_path, style="default"):
    n = int(total * SR)
    music = bgm_cute(total) if style == "cute" else bgm(total)
    # 인트로 0.25초 페이드인, 아웃트로 1.2초 페이드아웃
    fade = np.ones(n)
    fi = int(0.25 * SR); fo = int(1.2 * SR)
    fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)

    voice = np.zeros(n)
    for p, st in zip(narr_paths, narr_starts):
        v = read_wav(p)
        i = int(st * SR)
        v = v[: n - i]
        voice[i:i + len(v)] += v
    voice /= max(1e-6, np.abs(voice).max())
    voice *= 0.92

    # 덕킹: 나레이션이 있는 구간에서 BGM을 낮춘다 (부드러운 엔벨로프)
    act = (np.abs(voice) > 0.02).astype(float)
    win = int(0.25 * SR)
    act = np.convolve(act, np.ones(win) / win, mode="same")
    duck = 1.0 - 0.55 * np.clip(act * 4, 0, 1)
    music = music * (duck * fade)[:, None] * 0.55

    fx = np.zeros((n, 2))
    for t0, name, g, pan in events:
        s = SFX[name]()
        i = int(t0 * SR)
        if i >= n:
            continue
        s = s[: n - i]
        fx[i:i + len(s), 0] += s * g * (1 - max(0, pan))
        fx[i:i + len(s), 1] += s * g * (1 + min(0, pan))

    mix = music + fx * 0.75 + voice[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    write_wav(out_path, mix)
