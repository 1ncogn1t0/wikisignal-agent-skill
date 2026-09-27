import os
import subprocess
import json
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_ANALYSIS_PATH = os.path.join(SCRIPTS_DIR, "run_analysis.py")


def run(topic, source_lang, langs, years=2, fmt="full"):
    cmd = [
        sys.executable,
        RUN_ANALYSIS_PATH,
        "--topic", topic,
        "--source_lang", source_lang,
        "--langs", langs,
        "--years", str(years),
        "--format", fmt,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[FAIL] {topic} ({langs}):\n{res.stderr}")
        return None
    return json.loads(res.stdout)


def test():
    print("Cristiano Ronaldo")
    data3 = run("Cristiano Ronaldo", "en", "pt,es,en", years=2, fmt="json")
    if data3:
        print(json.dumps(data3, indent=2, ensure_ascii=False))

    print("\nFC Barcelona")
    data4 = run("FC Barcelona", "en", "es,ca,en", years=2, fmt="json")
    if data4:
        print(json.dumps(data4, indent=2, ensure_ascii=False))

    print("\nгетьман")
    data5 = run("гетьман", "uk", "uk,pl,en", years=2, fmt="json")
    if data5:
        print(json.dumps(data5, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test()