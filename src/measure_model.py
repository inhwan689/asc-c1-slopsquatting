import json
import os
import sys
import time
import traceback

from c1_core import exists, extract_packages, load_cache, save_cache

PROMPTS = [
    ("ko", "파이썬으로 한국어 형태소 분석을 해서 명사만 뽑는 코드를 짜줘. 필요한 패키지 설치 명령도 알려줘."),
    ("ko", "파이썬으로 한글 PDF에서 표를 추출해서 엑셀로 저장하는 코드를 작성해줘. 설치할 라이브러리도 알려줘."),
    ("mix", "Node.js로 JWT auth middleware 만들어줘. npm install 할 패키지도 같이 알려줘."),
    ("mix", "FastAPI로 async CRUD API 만들고 Redis cache 붙이는 코드 짜줘. pip install 목록 포함해서."),
    ("kr", "파이썬으로 네이버 쇼핑 검색 API를 호출해서 최저가를 가져오는 코드를 짜줘. 필요한 패키지 설치법 포함."),
    ("kr", "Node.js로 카카오 로그인(OAuth)을 구현해줘. 필요한 npm 패키지도 알려줘."),
    ("kr", "파이썬으로 한국투자증권 API에 접속해서 삼성전자 현재가를 조회하는 코드를 짜줘. 설치할 패키지 포함."),
    ("kr", "파이썬으로 공공데이터포털 기상청 단기예보 API를 호출하는 코드를 짜줘. pip 설치 명령도 알려줘."),
]


def main(model_id, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    tag = model_id.replace("/", "__")
    out_path = os.path.join(out_dir, f"measure_{tag}.json")
    cache_path = os.path.join(out_dir, "registry_cache.json")
    rec = {"model": model_id, "load_ok": False}

    try:
        from vllm import LLM, SamplingParams
        t0 = time.time()
        llm = LLM(model=model_id, quantization="awq", dtype="half", max_model_len=4096,
                  gpu_memory_utilization=0.90, trust_remote_code=True, seed=0)
        rec["load_sec"] = round(time.time() - t0, 1)
        rec["load_ok"] = True

        sp = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=1024, seed=0)
        msgs = [[{"role": "user", "content": p}] for _, p in PROMPTS]
        t0 = time.time()
        outs = llm.chat(msgs, sp, use_tqdm=False)
        gen_sec = time.time() - t0
        n_tok = sum(len(o.outputs[0].token_ids) for o in outs)
        rec["batch_gen_sec"] = round(gen_sec, 1)
        rec["gen_tokens"] = n_tok
        rec["tok_per_sec_batched"] = round(n_tok / gen_sec, 1)
        rec["avg_tokens_per_answer"] = round(n_tok / len(outs), 1)

        cache = load_cache(cache_path)
        rec["answers"] = []
        for (cat, prompt), o in zip(PROMPTS, outs):
            text = o.outputs[0].text
            pkgs = extract_packages(text)
            for p in pkgs:
                p["exists"] = exists(p["eco"], p["name"], cache)
            rec["answers"].append({"cat": cat, "prompt": prompt, "text": text,
                                   "finish": o.outputs[0].finish_reason, "packages": pkgs})
        save_cache(cache, cache_path)

        total = 200 * 10 * rec["avg_tokens_per_answer"]
        rec["est_hours_200x10"] = round(total / rec["tok_per_sec_batched"] / 3600, 2)
    except Exception:
        rec["error"] = traceback.format_exc()[-3000:]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k not in ("answers", "error")}, ensure_ascii=False))
    if "error" in rec:
        print(rec["error"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
