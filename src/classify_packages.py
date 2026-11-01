import argparse
import csv
import importlib.util
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from c1_core import exists, load_cache, pypi_normalize, save_cache

IMPORT_ALIAS = {
    "cv2": "opencv-python", "PIL": "Pillow", "bs4": "beautifulsoup4", "sklearn": "scikit-learn",
    "skimage": "scikit-image", "fitz": "PyMuPDF", "tabula": "tabula-py", "camelot": "camelot-py",
    "speech_recognition": "SpeechRecognition", "dateutil": "python-dateutil", "Crypto": "pycryptodome",
    "OpenSSL": "pyOpenSSL", "yaml": "PyYAML", "dotenv": "python-dotenv", "docx": "python-docx",
    "jwt": "PyJWT", "magic": "python-magic", "telegram": "python-telegram-bot", "bluetooth": "PyBluez",
    "win32com": "pywin32", "pythoncom": "pywin32", "stdnum": "python-stdnum", "rtmidi": "python-rtmidi",
    "hwp5": "pyhwp", "websocket": "websocket-client", "pdfminer": "pdfminer.six", "faiss": "faiss-cpu",
    "mysql": "mysql-connector-python", "finnhub": "finnhub-python",
}
_ALIAS = {pypi_normalize(k): v for k, v in IMPORT_ALIAS.items()}

_PLACEHOLDER_RE = re.compile(
    r"^(?:your|my|some|example|sample|hypothetical|dummy|fake)(?:[-_.]|$)|^package[-_]?(?:\d+|name|list)?$", re.I)
_LOCAL_MODULES = {pypi_normalize(n) for n in [
    "main", "app", "src", "config", "models", "schemas", "routes", "migrations", "database", "cache",
    "api_client", "http_client", "fetch_data", "external_api", "cli_tool", "test_module", "test_my_module"]}

REVIEW_COLS = ["name", "label", "intended", "rows", "version", "n_releases", "first_upload", "summary"]


def is_stdlib(name):
    for cand in {name.replace("-", "_"), re.sub(r"[-_]", ".", name), name.replace("-", ".")}:
        if cand.split(".")[0] not in sys.stdlib_module_names:
            continue
        if "." not in cand:
            return True
        try:
            if importlib.util.find_spec(cand) is not None:
                return True
        except (ImportError, ValueError):
            pass
    return False


def label_row(r, check):
    eco, name, src = r["pkg_eco"], r["name"], r["src"]
    norm = pypi_normalize(name)
    target = _ALIAS.get(norm, name) if (eco == "pypi" and src == "import") else name
    ok = check(eco, target)
    if _PLACEHOLDER_RE.match(name) or (src == "import" and norm in _LOCAL_MODULES):
        label = "placeholder"
    elif eco == "pypi" and src == "install" and is_stdlib(name):
        label = "stdlib"
    elif eco == "pypi" and src == "install" and norm in _ALIAS:
        label = "alias"
    elif ok is None:
        label = "unknown"
    else:
        label = "ok" if ok else "hallucination"
    return target, ok, label


def pypi_meta(name):
    url = f"https://pypi.org/pypi/{pypi_normalize(name)}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "c1-slopsquat-research"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)
    uploads = [f["upload_time"] for fs in d["releases"].values() for f in fs]
    return {"version": d["info"]["version"], "n_releases": len(d["releases"]),
            "first_upload": min(uploads)[:10] if uploads else "",
            "summary": (d["info"]["summary"] or "").strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="results/03_extract")
    args = ap.parse_args()

    with open(os.path.join(args.dir, "packages.csv"), encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    cache_path = os.path.join(args.dir, "registry_cache.json")
    cache = load_cache(cache_path)
    for r in rows:
        r["target"], r["target_exists"], r["label"] = label_row(r, lambda e, n: exists(e, n, cache))
    save_cache(cache, cache_path)

    with open(os.path.join(args.dir, "packages_labeled.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    review = {}
    for r in rows:
        if (r["pkg_eco"] == "pypi" and r["src"] == "install" and r["target_exists"] is True
                and r["label"] in ("alias", "stdlib", "placeholder")):
            key = pypi_normalize(r["name"])
            review.setdefault(key, {"name": r["name"], "label": r["label"],
                                    "intended": _ALIAS.get(key, ""), "rows": 0})["rows"] += 1
    with ThreadPoolExecutor(8) as ex:
        for v, m in zip(review.values(), ex.map(lambda v: pypi_meta(v["name"]), review.values())):
            v.update(m)
    with open(os.path.join(args.dir, "review_registered.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, REVIEW_COLS)
        w.writeheader()
        w.writerows(sorted(review.values(), key=lambda v: (v["label"], -v["rows"])))

    print(Counter((r["src"], r["label"]) for r in rows))
    print(f"review {len(review)}개")


if __name__ == "__main__":
    main()
