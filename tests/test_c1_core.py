import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from c1_core import exists, extract_packages

SAMPLE = """네이버 지도 API를 쓰려면 먼저 설치하세요.
```bash
pip install requests==2.31.0 naver-map-sdk-korea -U
npm i axios @kakao/maps-sdk-fake-zz9@1.0 --save
```
```python
import pandas as pd
from konlpy.tag import Okt
```
```js
const express = require('express');
import fs from 'node:fs';
import x from './local';
```
"""


def test_extract():
    got = {(p["eco"], p["name"], p["src"]) for p in extract_packages(SAMPLE)}
    want = {
        ("pypi", "requests", "install"), ("pypi", "naver-map-sdk-korea", "install"),
        ("npm", "axios", "install"), ("npm", "@kakao/maps-sdk-fake-zz9", "install"),
        ("pypi", "pandas", "import"), ("pypi", "konlpy", "import"),
        ("npm", "express", "import"),
    }
    assert got == want, f"\n got={sorted(got)}\nwant={sorted(want)}"


def test_extract_edge_cases():
    def names(text):
        return sorted((p["eco"], p["name"]) for p in extract_packages(text))
    assert names("pip install requests 명령으로 설치하세요.") == [("pypi", "requests")]
    assert names("Run pip install flask and then start the server.") == [("pypi", "flask")]
    assert names('pip install "fastapi[all]" uvicorn[standard]>=0.30') == [("pypi", "fastapi"), ("pypi", "uvicorn")]
    assert names("npm install\nnpm run dev") == []
    assert names("import React, { useState } from 'react';") == [("npm", "react")]
    assert names("python -m pip install -r requirements.txt") == []
    assert names("Here are the npm install commands:") == []
    assert names("the necessary Python code and pip install commands.") == []
    assert names("### pip install Commands") == []
    assert names("Run pip install flask.") == [("pypi", "flask")]
    assert names("import { zod } from '@ 삽질/zod';") == []


def test_exists():
    cache = {}
    assert exists("pypi", "requests", cache) is True
    assert exists("pypi", "Typing_Extensions", cache) is True
    assert exists("pypi", "beautifulsoup4", cache) is True
    assert exists("pypi", "c1-surely-not-registered-zz9q", cache) is False
    assert exists("npm", "express", cache) is True
    assert exists("npm", "@types/node", cache) is True
    assert exists("npm", "c1-surely-not-registered-zz9q", cache) is False
    assert exists("npm", "i18next-browser-languageDetector", cache) is False
    assert exists("npm", "i18next-browser-languagedetector", cache) is True
    assert len(cache) == 9


if __name__ == "__main__":
    test_extract()
    test_extract_edge_cases()
    print("extract OK")
    test_exists()
    print("exists OK")
