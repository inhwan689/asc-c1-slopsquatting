import argparse
import csv
import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor

from c1_core import exists, extract_packages, load_cache, save_cache

GEN_COLS = ["model", "id", "rep", "group", "lang", "eco", "cat", "finish", "n_tok", "n_pkg"]
PKG_COLS = ["model", "id", "rep", "group", "lang", "cat", "pkg_eco", "name", "src", "exists"]


def load_prompts(path):
    with open(path, encoding="utf-8") as f:
        return {p["id"]: p for p in map(json.loads, f)}


def iter_generations(collect_dir):
    for model_dir in sorted(glob.glob(os.path.join(collect_dir, "*", ""))):
        model = os.path.basename(os.path.dirname(model_dir))
        for chunk in sorted(glob.glob(os.path.join(model_dir, "chunk_r*.jsonl"))):
            with open(chunk, encoding="utf-8") as f:
                for line in f:
                    yield model, json.loads(line)


def build_tables(collect_dir, prompts):
    gens, pkgs = [], []
    for model, row in iter_generations(collect_dir):
        p = prompts[row["id"]]
        found = extract_packages(row["text"])
        gens.append({"model": model, "id": row["id"], "rep": row["rep"], "group": p["group"],
                     "lang": p["lang"], "eco": p["eco"], "cat": p["cat"], "finish": row["finish"],
                     "n_tok": row["n_tok"], "n_pkg": len(found)})
        for f in found:
            pkgs.append({"model": model, "id": row["id"], "rep": row["rep"], "group": p["group"],
                         "lang": p["lang"], "cat": p["cat"], "pkg_eco": f["eco"],
                         "name": f["name"], "src": f["src"]})
    return gens, pkgs


def check_all(pkgs, cache, workers=16):
    uniq = sorted({(r["pkg_eco"], r["name"]) for r in pkgs})
    with ThreadPoolExecutor(workers) as ex:
        res = dict(zip(uniq, ex.map(lambda k: exists(k[0], k[1], cache), uniq)))
    for r in pkgs:
        r["exists"] = res[(r["pkg_eco"], r["name"])]
    return len(uniq)


def write_csv(path, rows, cols):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", default="results/02_collect")
    ap.add_argument("--prompts", default="corpus/prompts.jsonl")
    ap.add_argument("--out", default="results/03_extract")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cache_path = os.path.join(args.out, "registry_cache.json")
    cache = load_cache(cache_path)

    gens, pkgs = build_tables(args.collect, load_prompts(args.prompts))
    n_uniq = check_all(pkgs, cache)
    save_cache(cache, cache_path)

    write_csv(os.path.join(args.out, "generations.csv"), gens, GEN_COLS)
    write_csv(os.path.join(args.out, "packages.csv"), pkgs, PKG_COLS)
    failed = sum(r["exists"] is None for r in pkgs)
    print(f"생성 {len(gens)}, 패키지 행 {len(pkgs)}, 고유 이름 {n_uniq}, 판정 실패 행 {failed}")


if __name__ == "__main__":
    main()
