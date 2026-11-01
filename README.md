# 한국어 프롬프트 패키지 환각(슬롭스쿼팅) 측정

ASC 개인 프로젝트. 코드 생성 LLM한테 한국어로 물어봤을 때 없는 패키지를 얼마나 추천하는지 측정

## 구성
- corpus/prompts.jsonl: 프롬프트 200개. 일반 태스크 50개는 영어/한국어/한영혼용 세 벌, 국내 스택 50개는 한국어
- src/build_corpus.py: 프롬프트 생성
- src/measure_model.py, notebooks/01_colab_setup.ipynb: T4에 모델 올라가는지, 속도 확인
- src/run_collect.py, notebooks/02_collect.ipynb: 모델 3개 × 200개 × 10회 수집. 끊겨도 이어서 돎
- src/c1_core.py, src/extract_collect.py: 답변에서 pip/npm install, import 패키지 이름 추출
- src/classify_packages.py: PyPI, npm 조회해서 정상/환각/표준 라이브러리/자리표시자 분류
- tests/: 테스트. 루트에서 python tests/test_c1_core.py 처럼 하나씩 실행

## 실행
- 수집: notebooks/02_collect.ipynb (Colab T4)
- 추출: python src/extract_collect.py --collect results/02_collect --out results/03_extract
- 분류: python src/classify_packages.py --dir results/03_extract

## 모델
Qwen2.5-Coder-7B, DeepSeek-Coder-6.7B, EXAONE-3.5-7.8B (AWQ, vLLM 0.6.6.post1)

## 안 올린 것
수집 응답이랑 환각 패키지 이름 목록. 공격자가 그 이름을 먼저 등록할 수 있어서 뺌

## AI 활용
코드 작성에 Claude Code 사용. 설계, Colab 실행, 검증 기준은 직접 정함

## 참고
We Have a Package for You!, USENIX Security 2025
