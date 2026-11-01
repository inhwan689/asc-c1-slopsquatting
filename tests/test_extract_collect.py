import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import json
import tempfile

from extract_collect import build_tables, check_all

PROMPTS = {
    "g01-ko": {"id": "g01-ko", "group": "generic", "lang": "ko", "eco": "pypi", "cat": "web"},
    "k01-ko": {"id": "k01-ko", "group": "kr", "lang": "ko", "eco": "npm", "cat": "naver"},
}


def test_build_and_check():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "m1"))
        rows = [
            {"id": "g01-ko", "rep": 0, "seed": 0, "text": "pip install flask fake-zz9", "finish": "stop", "n_tok": 5},
            {"id": "k01-ko", "rep": 0, "seed": 1, "text": "설명만 있음", "finish": "length", "n_tok": 9},
        ]
        with open(os.path.join(d, "m1", "chunk_r00.jsonl"), "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        gens, pkgs = build_tables(d, PROMPTS)

    assert [(g["model"], g["id"], g["n_pkg"], g["finish"]) for g in gens] == [
        ("m1", "g01-ko", 2, "stop"), ("m1", "k01-ko", 0, "length")]
    assert gens[1]["group"] == "kr" and gens[1]["cat"] == "naver"
    assert [(p["name"], p["lang"], p["src"]) for p in pkgs] == [
        ("flask", "ko", "install"), ("fake-zz9", "ko", "install")]

    cache = {"pypi:flask": True, "pypi:fake-zz9": False}
    assert check_all(pkgs, cache) == 2
    assert [p["exists"] for p in pkgs] == [True, False]


if __name__ == "__main__":
    test_build_and_check()
    print("extract_collect OK")
