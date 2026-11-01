import argparse
import json
import os
import time

MAX_TOKENS = 2048
MAX_MODEL_LEN = 4096
TEMPERATURE, TOP_P = 0.7, 0.95


def load_corpus(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def chunk_path(out_dir, rep):
    return os.path.join(out_dir, f"chunk_r{rep:02d}.jsonl")


def seed_of(rep, i):
    return rep * 1000 + i


def write_atomic(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def todo_reps(out_dir, reps, n_prompts):
    todo = []
    for rep in range(reps):
        p = chunk_path(out_dir, rep)
        try:
            with open(p, encoding="utf-8") as f:
                if sum(1 for line in f if line.strip()) == n_prompts:
                    continue
        except FileNotFoundError:
            pass
        todo.append(rep)
    return todo


def collect(generate, corpus, out_dir, reps, max_hours, log=print):
    os.makedirs(out_dir, exist_ok=True)
    t_start = time.time()
    last = 0.0
    for rep in todo_reps(out_dir, reps, len(corpus)):
        elapsed = time.time() - t_start
        if elapsed + last * 1.2 > max_hours * 3600:
            log(f"시간 예산 도달: rep {rep}부터 다음 세션에서 재개")
            return False
        t0 = time.time()
        outs = generate([r["prompt"] for r in corpus], [seed_of(rep, i) for i in range(len(corpus))])
        rows = [{"id": r["id"], "rep": rep, "seed": seed_of(rep, i), "text": text,
                 "finish": finish, "n_tok": n_tok}
                for i, (r, (text, finish, n_tok)) in enumerate(zip(corpus, outs))]
        write_atomic(chunk_path(out_dir, rep), rows)
        last = time.time() - t0
        n_tok = sum(x["n_tok"] for x in rows)
        n_len = sum(x["finish"] == "length" for x in rows)
        log(f"rep {rep}: {last/60:.1f}분, {n_tok/last:.0f} tok/s, 잘림 {n_len}/{len(rows)}")
    return True


def vllm_generator(model_id):
    from vllm import LLM, SamplingParams
    llm = LLM(model=model_id, quantization="awq", dtype="half", max_model_len=MAX_MODEL_LEN,
              gpu_memory_utilization=0.90, trust_remote_code=True, seed=0)

    def generate(prompts, seeds):
        sps = [SamplingParams(temperature=TEMPERATURE, top_p=TOP_P, max_tokens=MAX_TOKENS, seed=s)
               for s in seeds]
        outs = llm.chat([[{"role": "user", "content": p}] for p in prompts], sps, use_tqdm=True)
        return [(o.outputs[0].text, o.outputs[0].finish_reason, len(o.outputs[0].token_ids))
                for o in outs]
    return generate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_id")
    ap.add_argument("out_root")
    ap.add_argument("--corpus", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                     "corpus", "prompts.jsonl"))
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--max-hours", type=float, default=10.0)
    a = ap.parse_args()

    corpus = load_corpus(a.corpus)
    out_dir = os.path.join(a.out_root, a.model_id.replace("/", "__"))
    os.makedirs(out_dir, exist_ok=True)
    if not todo_reps(out_dir, a.reps, len(corpus)):
        print("이미 완료:", out_dir)
        return
    meta = {"model": a.model_id, "corpus": os.path.basename(a.corpus), "n_prompts": len(corpus),
            "reps": a.reps, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE, "top_p": TOP_P,
            "max_model_len": MAX_MODEL_LEN, "seed_rule": "rep*1000+prompt_index"}
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    t0 = time.time()
    gen = vllm_generator(a.model_id)
    print(f"적재 {time.time() - t0:.0f}초")
    done = collect(gen, corpus, out_dir, a.reps, a.max_hours - (time.time() - t0) / 3600)
    print("완료" if done else "미완료(재실행하면 이어서 돈다)")


if __name__ == "__main__":
    main()
