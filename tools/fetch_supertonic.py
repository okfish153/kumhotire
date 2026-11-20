"""Supertonic 3 (Supertone Inc.) 다국어 TTS 모델을 npm 레지스트리에서 받아 복원한다.

HuggingFace가 막힌 환경용: @3sln/donki-lle-voice-multi(-2,-3) 패키지에
ONNX 모델이 base64 ES 모듈 조각으로 들어 있다. 이를 디코드해서
build/supertonic/ 에 원본 파일로 저장한다 (약 145MB, git 에는 올리지 않음).
"""
import base64, io, json, os, sys, tarfile, urllib.request

PKGS = ["donki-lle-voice-multi", "donki-lle-voice-multi-2", "donki-lle-voice-multi-3"]
VERSION = "0.1.1"


def fetch(dest):
    if os.path.exists(os.path.join(dest, "voice.bin")):
        return dest
    os.makedirs(dest, exist_ok=True)
    files = {}
    for p in PKGS:
        url = f"https://registry.npmjs.org/@3sln/{p}/-/{p}-{VERSION}.tgz"
        print("[supertonic] download", url)
        data = urllib.request.urlopen(url, timeout=300).read()
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            for m in t.getmembers():
                if m.isfile() and m.name.endswith(".js"):
                    files[f"@3sln/{p}@{VERSION}/" + m.name.split("package/", 1)[1]] = t.extractfile(m).read().decode()
    vj = files[f"@3sln/{PKGS[0]}@{VERSION}/voice.js"]
    cfg = json.loads(vj[vj.index("{"): vj.rindex("}") + 1])
    for fn, info in cfg["files"].items():
        blob = b"".join(base64.b64decode(files[part][files[part].index('"') + 1: files[part].rindex('"')])
                        for part in info["parts"])
        assert len(blob) == info["size"], fn
        with open(os.path.join(dest, fn), "wb") as f:
            f.write(blob)
    return dest


if __name__ == "__main__":
    print(fetch(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "build", "supertonic")))
