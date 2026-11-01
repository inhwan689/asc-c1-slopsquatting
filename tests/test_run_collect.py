import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import json
import tempfile

from run_collect import chunk_path, collect, load_corpus, todo_reps

CORPUS = load_corpus(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "corpus", "prompts.jsonl"))


def fake_gen(calls):
    def generate(prompts, seeds):
        calls.append(seeds[0] // 1000)
        return [(f"{p}|{s}", "stop", 10) for p, s in zip(prompts, seeds)]
    return generate


def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


with tempfile.TemporaryDirectory() as d:
    quiet = lambda *_: None
    calls = []
    assert collect(fake_gen(calls), CORPUS, d, 3, 10, quiet)
    assert calls == [0, 1, 2]
    rows = read(chunk_path(d, 1))
    assert len(rows) == 200 and rows[5]["seed"] == 1005 and rows[5]["id"] == CORPUS[5]["id"]
    first = rows[5]["text"]

    calls = []
    assert collect(fake_gen(calls), CORPUS, d, 3, 10, quiet) and calls == []

    with open(chunk_path(d, 1), "w", encoding="utf-8") as f:
        f.write(json.dumps(rows[0]) + "\n")
    assert todo_reps(d, 3, 200) == [1]
    calls = []
    assert collect(fake_gen(calls), CORPUS, d, 3, 10, quiet) and calls == [1]
    assert read(chunk_path(d, 1))[5]["text"] == first

    calls = []
    collect(fake_gen(calls), CORPUS, d, 5, 10, quiet)
    assert calls == [3, 4]

    calls = []
    assert collect(fake_gen(calls), CORPUS, d, 6, 0, quiet) is False and calls == []

    assert not [f for f in os.listdir(d) if f.endswith(".tmp")]

print("test_run_collect OK")
