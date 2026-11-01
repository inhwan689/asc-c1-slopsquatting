import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


_PIP_RE = re.compile(r"\bpip\d?[ \t]+install[ \t]+([^\n`;&|]+)", re.I)
_NPM_RE = re.compile(r"\b(?:npm[ \t]+(?:install|i|add)|yarn[ \t]+add|pnpm[ \t]+(?:add|install|i))[ \t]+([^\n`;&|]+)", re.I)
_PY_IMPORT_RE = re.compile(
    r"^(?![^\n]*['\"{};])\s*(?:from\s+([A-Za-z_]\w*)[\w.]*\s+import\b"
    r"|import\s+([A-Za-z_]\w*)[\w.]*(?:\s+as\s+\w+)?\s*(?:,|#|$))",
    re.M)
_JS_REQ_RE = re.compile(r"""(?:require\(\s*|from\s+|import\s+)['"]([^'"./][^'"]*)['"]""")

_PY_STDLIB = set(sys.stdlib_module_names)
_NODE_BUILTIN = {
    "assert", "buffer", "child_process", "cluster", "crypto", "dgram", "dns", "events", "fs",
    "http", "http2", "https", "net", "os", "path", "perf_hooks", "process", "querystring",
    "readline", "stream", "string_decoder", "timers", "tls", "tty", "url", "util", "v8", "vm",
    "worker_threads", "zlib",
}


_PYPI_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_NPM_NAME_RE = re.compile(r"^(?:@[a-z0-9~-][a-z0-9._~-]*/)?[a-z0-9~-][a-z0-9._~-]*$", re.I)
_PROSE_STOP = {"and", "or", "then", "to", "the", "with", "in", "on", "for", "if", "using", "via",
               "first", "before", "after", "also", "command", "commands", "package", "packages",
               "library", "would", "from"}


def _split_args(arg_str, strip_version, name_re):
    names = []
    for tok in arg_str.split():
        tok = tok.strip("'\"`,").rstrip(".:")
        if not tok or tok.startswith("-") or "://" in tok or tok.startswith((".", "/", "~")):
            continue
        if tok.endswith((".txt", ".whl", ".tar.gz")):
            continue
        name = strip_version(tok)
        if not name_re.match(name) or name.lower() in _PROSE_STOP:
            break
        names.append(name)
    return names


def _strip_py_version(tok):
    return re.split(r"[<>=!~\[;@ ]", tok, 1)[0]


def _strip_npm_version(tok):
    if tok.startswith("@"):
        head, _, rest = tok[1:].partition("@")
        return "@" + head
    return tok.split("@", 1)[0]


def extract_packages(text):
    found = {}

    def add(eco, name, src):
        if not name:
            return
        key = (eco, name.lower() if eco == "pypi" else name)
        if key not in found or src == "install":
            found[key] = {"eco": eco, "name": name, "src": src}

    for m in _PIP_RE.finditer(text):
        for name in _split_args(m.group(1), _strip_py_version, _PYPI_NAME_RE):
            add("pypi", name, "install")
    for m in _NPM_RE.finditer(text):
        for name in _split_args(m.group(1), _strip_npm_version, _NPM_NAME_RE):
            add("npm", name, "install")
    for m in _PY_IMPORT_RE.finditer(text):
        mod = m.group(1) or m.group(2)
        if mod not in _PY_STDLIB:
            add("pypi", mod, "import")
    for m in _JS_REQ_RE.finditer(text):
        spec = m.group(1)
        if spec.startswith("node:"):
            continue
        name = "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
        if name not in _NODE_BUILTIN and _NPM_NAME_RE.match(name):
            add("npm", name, "import")
    return list(found.values())


def pypi_normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _registry_url(eco, name):
    if eco == "pypi":
        return f"https://pypi.org/pypi/{urllib.parse.quote(pypi_normalize(name))}/json"
    if eco == "npm":
        return "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@").replace("/", "%2f")
    raise ValueError(eco)


def exists(eco, name, cache=None, retries=3):
    key = f"{eco}:{pypi_normalize(name) if eco == 'pypi' else name}"
    if cache is not None and key in cache:
        return cache[key]
    req = urllib.request.Request(_registry_url(eco, name), method="GET",
                                 headers={"User-Agent": "c1-slopsquat-research"})
    result = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                result = r.status == 200
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                result = False
                break
            time.sleep(2 ** i)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2 ** i)
    if cache is not None and result is not None:
        cache[key] = result
    return result


def load_cache(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_cache(cache, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=0)
