import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from classify_packages import is_stdlib, label_row

REG = {("pypi", "opencv-python"), ("pypi", "flask"), ("pypi", "fitz"), ("pypi", "asyncio"),
       ("pypi", "package_name"), ("pypi", "models")}


def check(eco, name):
    return (eco, name) in REG


def lab(name, src="install", eco="pypi"):
    return label_row({"pkg_eco": eco, "name": name, "src": src}, check)


def test_is_stdlib():
    for n in ["json", "concurrent.futures", "concurrent-futures", "unittest-mock", "unittest.mock",
              "xml.etree.ElementTree", "sqlite3", "asyncio"]:
        assert is_stdlib(n), n
    for n in ["sqlite-fake-zz9", "hwp-fake-zz9", "zzfake.security", "os-sys", "flask"]:
        assert not is_stdlib(n), n


def test_labels():
    assert lab("cv2", "import") == ("opencv-python", True, "ok")
    assert lab("fitz") == ("fitz", True, "alias")
    assert lab("fitz", "import")[2] == "hallucination"
    assert lab("dateutil") == ("dateutil", False, "alias")
    assert lab("concurrent.futures") == ("concurrent.futures", False, "stdlib")
    assert lab("asyncio")[2] == "stdlib"
    assert lab("package_name")[2] == "placeholder"
    assert lab("your-db-module", eco="npm")[2] == "placeholder"
    assert lab("models", "import")[2] == "placeholder"
    assert lab("models")[2] == "ok"
    assert lab("hwp-fake-zz9") == ("hwp-fake-zz9", False, "hallucination")
    assert lab("flask") == ("flask", True, "ok")
    assert label_row({"pkg_eco": "pypi", "name": "x", "src": "install"}, lambda e, n: None)[2] == "unknown"


if __name__ == "__main__":
    test_is_stdlib()
    test_labels()
    print("ok")
