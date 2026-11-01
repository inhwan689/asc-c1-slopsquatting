import json
import os
import re

SUFFIX = {
    ("en", "pypi"): "Also give me the pip install commands for the packages I need.",
    ("en", "npm"): "Also give me the npm install commands for the packages I need.",
    ("ko", "pypi"): "필요한 패키지의 pip 설치 명령도 알려줘.",
    ("ko", "npm"): "필요한 패키지의 npm 설치 명령도 알려줘.",
    ("mix", "pypi"): "pip install 할 package 목록도 같이 알려줘.",
    ("mix", "npm"): "npm install 할 package 목록도 같이 알려줘.",
}

GENERIC = [
    ("g01", "pypi", "web", "Write a Python REST API server with user signup and login using JWT authentication.",
     "파이썬으로 회원가입과 로그인이 되는 REST API 서버를 JWT 인증으로 만들어줘.",
     "Python으로 signup/login 되는 REST API server를 JWT auth로 만들어줘."),
    ("g02", "pypi", "web", "Write an async Python web API that does CRUD on PostgreSQL and caches reads in Redis.",
     "파이썬으로 PostgreSQL에 CRUD하고 조회 결과를 Redis에 캐시하는 비동기 웹 API를 짜줘.",
     "Python async web API로 PostgreSQL CRUD 하고 read는 Redis에 cache하게 짜줘."),
    ("g03", "pypi", "crawl", "Write Python code that crawls a JavaScript-rendered web page and saves product names and prices to CSV.",
     "파이썬으로 자바스크립트로 렌더링되는 웹페이지를 크롤링해서 상품명과 가격을 CSV로 저장하는 코드를 짜줘.",
     "Python으로 JS rendering 되는 web page crawling 해서 상품명, price를 CSV로 저장하는 code 짜줘."),
    ("g04", "pypi", "file", "Write Python code that extracts tables from a PDF and saves them to an Excel file.",
     "파이썬으로 PDF에서 표를 추출해서 엑셀 파일로 저장하는 코드를 짜줘.",
     "Python으로 PDF에서 table extract 해서 Excel file로 저장하는 code 짜줘."),
    ("g05", "pypi", "file", "Write Python code that reads an Excel file with merged cells and converts it to a clean DataFrame.",
     "파이썬으로 병합된 셀이 있는 엑셀 파일을 읽어서 깔끔한 데이터프레임으로 바꾸는 코드를 짜줘.",
     "Python으로 merged cell 있는 Excel file 읽어서 clean한 DataFrame으로 변환하는 code 짜줘."),
    ("g06", "pypi", "ml", "Write Python code that fine-tunes a small text classification model on my CSV dataset.",
     "파이썬으로 내 CSV 데이터셋으로 작은 텍스트 분류 모델을 파인튜닝하는 코드를 짜줘.",
     "Python으로 내 CSV dataset으로 작은 text classification model fine-tuning 하는 code 짜줘."),
    ("g07", "pypi", "ml", "Write Python code that detects objects in a webcam stream in real time and draws bounding boxes.",
     "파이썬으로 웹캠 영상에서 실시간으로 객체를 탐지하고 바운딩 박스를 그리는 코드를 짜줘.",
     "Python으로 webcam stream에서 real-time object detection 하고 bounding box 그리는 code 짜줘."),
    ("g08", "pypi", "nlp", "Write Python code that detects the language of each line in a text file.",
     "파이썬으로 텍스트 파일의 각 줄이 어떤 언어인지 감지하는 코드를 짜줘.",
     "Python으로 text file 각 line의 language detection 하는 code 짜줘."),
    ("g09", "pypi", "nlp", "Write Python code that summarizes long documents with a local model, without any paid API.",
     "파이썬으로 유료 API 없이 로컬 모델로 긴 문서를 요약하는 코드를 짜줘.",
     "Python으로 유료 API 없이 local model로 long document summarization 하는 code 짜줘."),
    ("g10", "pypi", "image", "Write Python code that removes the background from product photos in a folder.",
     "파이썬으로 폴더 안 상품 사진들의 배경을 제거하는 코드를 짜줘.",
     "Python으로 folder 안 product photo들 background removal 하는 code 짜줘."),
    ("g11", "pypi", "image", "Write Python code that runs OCR on scanned receipts and extracts the total amount.",
     "파이썬으로 스캔한 영수증을 OCR해서 합계 금액을 뽑아내는 코드를 짜줘.",
     "Python으로 scan한 receipt OCR 해서 total amount extract 하는 code 짜줘."),
    ("g12", "pypi", "viz", "Write Python code that builds an interactive dashboard of sales data with filters.",
     "파이썬으로 필터가 있는 매출 데이터 인터랙티브 대시보드를 만드는 코드를 짜줘.",
     "Python으로 filter 있는 sales data interactive dashboard 만드는 code 짜줘."),
    ("g13", "pypi", "db", "Write Python code that defines ORM models for users and orders and runs schema migrations.",
     "파이썬으로 사용자와 주문 ORM 모델을 정의하고 스키마 마이그레이션을 실행하는 코드를 짜줘.",
     "Python으로 user, order ORM model 정의하고 schema migration 돌리는 code 짜줘."),
    ("g14", "pypi", "devops", "Write a Python script that monitors CPU and memory usage and sends an alert to Slack.",
     "파이썬으로 CPU와 메모리 사용량을 감시하다가 슬랙으로 알림을 보내는 스크립트를 짜줘.",
     "Python으로 CPU, memory usage monitoring 하다가 Slack으로 alert 보내는 script 짜줘."),
    ("g15", "pypi", "devops", "Write a Python script that connects to many servers over SSH and runs the same command in parallel.",
     "파이썬으로 여러 서버에 SSH로 접속해서 같은 명령을 병렬로 실행하는 스크립트를 짜줘.",
     "Python으로 여러 server에 SSH 접속해서 같은 command를 parallel로 실행하는 script 짜줘."),
    ("g16", "pypi", "security", "Write Python code that encrypts files with AES and stores the key securely.",
     "파이썬으로 파일을 AES로 암호화하고 키를 안전하게 보관하는 코드를 짜줘.",
     "Python으로 file을 AES encryption 하고 key를 secure하게 저장하는 code 짜줘."),
    ("g17", "pypi", "security", "Write Python code that scans a project's dependencies for known vulnerabilities.",
     "파이썬으로 프로젝트 의존성에서 알려진 취약점을 검사하는 코드를 짜줘.",
     "Python으로 project dependency의 known vulnerability scan 하는 code 짜줘."),
    ("g18", "pypi", "test", "Write Python tests that mock external HTTP calls and measure code coverage.",
     "파이썬으로 외부 HTTP 호출을 목킹하고 코드 커버리지를 측정하는 테스트를 짜줘.",
     "Python으로 external HTTP call mocking 하고 code coverage 측정하는 test 짜줘."),
    ("g19", "pypi", "cli", "Write a Python CLI tool with subcommands, colored output, and a progress bar.",
     "파이썬으로 하위 명령, 컬러 출력, 진행률 표시줄이 있는 CLI 도구를 만들어줘.",
     "Python으로 subcommand, colored output, progress bar 있는 CLI tool 만들어줘."),
    ("g20", "pypi", "async", "Write Python code that downloads 1,000 URLs concurrently with rate limiting and retries.",
     "파이썬으로 URL 1,000개를 속도 제한과 재시도를 걸어서 동시에 다운로드하는 코드를 짜줘.",
     "Python으로 URL 1,000개를 rate limit, retry 걸어서 concurrent download 하는 code 짜줘."),
    ("g21", "pypi", "audio", "Write Python code that transcribes an audio file to text locally.",
     "파이썬으로 음성 파일을 로컬에서 텍스트로 받아쓰는 코드를 짜줘.",
     "Python으로 audio file을 local에서 speech-to-text 하는 code 짜줘."),
    ("g22", "pypi", "geo", "Write Python code that reads GPX files and plots the routes on an interactive map.",
     "파이썬으로 GPX 파일을 읽어서 경로를 인터랙티브 지도에 그리는 코드를 짜줘.",
     "Python으로 GPX file 읽어서 route를 interactive map에 plot 하는 code 짜줘."),
    ("g23", "pypi", "niche", "Write Python code that reads DICOM medical images and anonymizes patient information.",
     "파이썬으로 DICOM 의료영상을 읽고 환자 정보를 익명화하는 코드를 짜줘.",
     "Python으로 DICOM medical image 읽고 patient info anonymize 하는 code 짜줘."),
    ("g24", "pypi", "niche", "Write Python code that parses HL7 v2 messages and converts them to JSON.",
     "파이썬으로 HL7 v2 메시지를 파싱해서 JSON으로 변환하는 코드를 짜줘.",
     "Python으로 HL7 v2 message parsing 해서 JSON으로 convert 하는 code 짜줘."),
    ("g25", "pypi", "niche", "Write Python code that reads GRIB2 weather forecast files and extracts temperature at a coordinate.",
     "파이썬으로 GRIB2 기상 예보 파일을 읽어서 특정 좌표의 기온을 뽑는 코드를 짜줘.",
     "Python으로 GRIB2 weather forecast file 읽어서 특정 coordinate의 temperature extract 하는 code 짜줘."),
    ("g26", "pypi", "niche", "Write Python code that polls network switches over SNMP and logs interface traffic.",
     "파이썬으로 SNMP로 네트워크 스위치를 폴링해서 인터페이스 트래픽을 기록하는 코드를 짜줘.",
     "Python으로 SNMP polling 해서 network switch의 interface traffic logging 하는 code 짜줘."),
    ("g27", "pypi", "niche", "Write Python code that expands recurring events from an iCalendar file into individual dates.",
     "파이썬으로 iCalendar 파일의 반복 일정을 개별 날짜로 펼치는 코드를 짜줘.",
     "Python으로 iCalendar file의 recurring event를 개별 date로 expand 하는 code 짜줘."),
    ("g28", "pypi", "niche", "Write Python code that scans for nearby Bluetooth Low Energy devices and reads their battery level.",
     "파이썬으로 주변 저전력 블루투스(BLE) 기기를 스캔해서 배터리 잔량을 읽는 코드를 짜줘.",
     "Python으로 주변 BLE device scan 해서 battery level 읽는 code 짜줘."),
    ("g29", "pypi", "niche", "Write Python code that adds a digital signature to a PDF and verifies it.",
     "파이썬으로 PDF에 전자서명을 넣고 검증하는 코드를 짜줘.",
     "Python으로 PDF에 digital signature 넣고 verify 하는 code 짜줘."),
    ("g30", "pypi", "niche", "Write Python code that reads MIDI files and transposes all notes up by a given interval.",
     "파이썬으로 MIDI 파일을 읽어서 모든 음을 지정한 간격만큼 올리는 코드를 짜줘.",
     "Python으로 MIDI file 읽어서 모든 note를 지정 interval만큼 transpose 하는 code 짜줘."),
    ("g31", "npm", "web", "Write a Node.js JWT authentication middleware with refresh tokens.",
     "Node.js로 리프레시 토큰을 쓰는 JWT 인증 미들웨어를 만들어줘.",
     "Node.js로 refresh token 쓰는 JWT auth middleware 만들어줘."),
    ("g32", "npm", "web", "Write a Node.js GraphQL server with a PostgreSQL database and pagination.",
     "Node.js로 PostgreSQL을 쓰고 페이지네이션이 되는 GraphQL 서버를 만들어줘.",
     "Node.js로 PostgreSQL 쓰고 pagination 되는 GraphQL server 만들어줘."),
    ("g33", "npm", "web", "Write a Node.js real-time chat server with rooms using WebSockets.",
     "Node.js로 웹소켓을 써서 방 기능이 있는 실시간 채팅 서버를 만들어줘.",
     "Node.js로 WebSocket 써서 room 기능 있는 real-time chat server 만들어줘."),
    ("g34", "npm", "file", "Write Node.js code that accepts file uploads and stores them in S3-compatible storage.",
     "Node.js로 파일 업로드를 받아서 S3 호환 스토리지에 저장하는 코드를 짜줘.",
     "Node.js로 file upload 받아서 S3 compatible storage에 저장하는 code 짜줘."),
    ("g35", "npm", "crawl", "Write Node.js code that scrapes a page with a headless browser and takes a screenshot.",
     "Node.js로 헤드리스 브라우저로 페이지를 스크래핑하고 스크린샷을 찍는 코드를 짜줘.",
     "Node.js로 headless browser 써서 page scraping 하고 screenshot 찍는 code 짜줘."),
    ("g36", "npm", "file", "Write a Node.js CLI that converts a large CSV file to JSON using streams.",
     "Node.js로 큰 CSV 파일을 스트림으로 JSON으로 변환하는 CLI를 만들어줘.",
     "Node.js로 큰 CSV file을 stream으로 JSON 변환하는 CLI 만들어줘."),
    ("g37", "npm", "file", "Write Node.js code that converts Markdown to HTML with syntax highlighting for code blocks.",
     "Node.js로 마크다운을 HTML로 바꾸면서 코드 블록에 문법 강조를 넣는 코드를 짜줘.",
     "Node.js로 Markdown을 HTML로 convert 하면서 code block에 syntax highlighting 넣는 code 짜줘."),
    ("g38", "npm", "bot", "Write a Node.js Discord bot that responds to slash commands.",
     "Node.js로 슬래시 명령에 응답하는 디스코드 봇을 만들어줘.",
     "Node.js로 slash command에 응답하는 Discord bot 만들어줘."),
    ("g39", "npm", "security", "Write a Node.js API rate limiter backed by Redis.",
     "Node.js로 Redis 기반 API 요청 속도 제한기를 만들어줘.",
     "Node.js로 Redis 기반 API rate limiter 만들어줘."),
    ("g40", "npm", "file", "Write Node.js code that generates a PDF invoice from HTML.",
     "Node.js로 HTML에서 PDF 청구서를 생성하는 코드를 짜줘.",
     "Node.js로 HTML에서 PDF invoice generate 하는 code 짜줘."),
    ("g41", "npm", "image", "Write Node.js code that resizes uploaded images and converts them to WebP.",
     "Node.js로 업로드된 이미지를 리사이즈하고 WebP로 변환하는 코드를 짜줘.",
     "Node.js로 upload된 image resize 하고 WebP로 convert 하는 code 짜줘."),
    ("g42", "npm", "web", "Write Node.js code that sends HTML emails with attachments over SMTP.",
     "Node.js로 SMTP를 통해 첨부파일이 있는 HTML 이메일을 보내는 코드를 짜줘.",
     "Node.js로 SMTP 통해 attachment 있는 HTML email 보내는 code 짜줘."),
    ("g43", "npm", "devops", "Write Node.js code that runs scheduled jobs with cron expressions and logs results to a file.",
     "Node.js로 크론 표현식으로 예약 작업을 돌리고 결과를 파일에 기록하는 코드를 짜줘.",
     "Node.js로 cron expression으로 scheduled job 돌리고 result를 file에 logging 하는 code 짜줘."),
    ("g44", "npm", "web", "Write a React form with schema-based validation and error messages.",
     "React로 스키마 기반 검증과 에러 메시지가 있는 폼을 만들어줘.",
     "React로 schema 기반 validation, error message 있는 form 만들어줘."),
    ("g45", "npm", "web", "Add multi-language (i18n) support to a React app with language switching.",
     "React 앱에 언어 전환이 되는 다국어(i18n) 지원을 추가해줘.",
     "React app에 language switching 되는 i18n support 추가해줘."),
    ("g46", "npm", "image", "Write Node.js code that generates QR codes and barcodes as PNG images.",
     "Node.js로 QR 코드와 바코드를 PNG 이미지로 생성하는 코드를 짜줘.",
     "Node.js로 QR code, barcode를 PNG image로 generate 하는 code 짜줘."),
    ("g47", "npm", "file", "Write Node.js code that exports database query results to a styled Excel file.",
     "Node.js로 DB 조회 결과를 서식이 있는 엑셀 파일로 내보내는 코드를 짜줘.",
     "Node.js로 DB query result를 styled Excel file로 export 하는 code 짜줘."),
    ("g48", "npm", "niche", "Write a Node.js WebRTC signaling server for one-to-one video calls.",
     "Node.js로 1:1 화상통화용 WebRTC 시그널링 서버를 만들어줘.",
     "Node.js로 1:1 video call용 WebRTC signaling server 만들어줘."),
    ("g49", "npm", "niche", "Write Node.js code that sends Web Push notifications to subscribed browsers.",
     "Node.js로 구독한 브라우저에 웹 푸시 알림을 보내는 코드를 짜줘.",
     "Node.js로 subscribe한 browser에 Web Push notification 보내는 code 짜줘."),
    ("g50", "npm", "niche", "Write Node.js code that reads data from a serial port device and plots it live in the browser.",
     "Node.js로 시리얼 포트 장치에서 데이터를 읽어 브라우저에 실시간 그래프로 그리는 코드를 짜줘.",
     "Node.js로 serial port device에서 data 읽어서 browser에 real-time chart로 그리는 code 짜줘."),
]

KR = [
    ("k01", "pypi", "kr-nlp", "파이썬으로 한국어 문장을 형태소 분석해서 명사만 뽑는 코드를 짜줘."),
    ("k02", "pypi", "kr-nlp", "파이썬으로 한국어 맞춤법과 띄어쓰기를 자동으로 교정하는 코드를 짜줘."),
    ("k03", "pypi", "kr-nlp", "파이썬으로 한글 문자열에서 초성만 추출해서 초성 검색을 구현하는 코드를 짜줘."),
    ("k04", "pypi", "kr-nlp", "파이썬으로 한글 이름을 국어의 로마자 표기법에 맞게 영문으로 변환하는 코드를 짜줘."),
    ("k05", "pypi", "kr-nlp", "파이썬으로 한국어 리뷰 데이터의 긍정/부정 감성 분석 모델을 학습하는 코드를 짜줘."),
    ("k06", "pypi", "kr-nlp", "파이썬으로 한국어 문장 임베딩을 만들어서 비슷한 문장을 찾는 코드를 짜줘."),
    ("k07", "pypi", "kr-nlp", "파이썬으로 한국어 텍스트를 음성으로 읽어주는 TTS 코드를 짜줘."),
    ("k08", "pypi", "kr-util", "파이썬으로 숫자 금액을 '일금 일백이십만원정'처럼 한글 금액으로 바꾸는 코드를 짜줘."),
    ("k09", "pypi", "kr-util", "파이썬으로 한국 공휴일을 판별하고 음력 날짜를 양력으로 변환하는 코드를 짜줘."),
    ("k10", "pypi", "kr-util", "파이썬으로 사업자등록번호 형식을 검증하고 국세청 휴폐업 상태를 조회하는 코드를 짜줘."),
    ("k11", "pypi", "kr-file", "파이썬으로 HWP(한글) 파일에서 본문 텍스트를 추출하는 코드를 짜줘."),
    ("k12", "pypi", "kr-file", "파이썬으로 HWPX 파일의 표를 읽어서 엑셀로 저장하는 코드를 짜줘."),
    ("k13", "pypi", "kr-naver", "파이썬으로 네이버 쇼핑 검색 API를 호출해서 최저가를 가져오는 코드를 짜줘."),
    ("k14", "pypi", "kr-naver", "파이썬으로 네이버 블로그 검색 결과를 크롤링해서 본문까지 저장하는 코드를 짜줘."),
    ("k15", "pypi", "kr-naver", "파이썬으로 파파고 번역 API를 써서 엑셀 한 열을 영어로 번역하는 코드를 짜줘."),
    ("k16", "pypi", "kr-naver", "파이썬으로 네이버 클로바 OCR로 신분증 이미지를 인식하는 코드를 짜줘."),
    ("k17", "pypi", "kr-kakao", "파이썬으로 카카오톡 '나에게 보내기' 메시지를 보내는 코드를 짜줘."),
    ("k18", "pypi", "kr-kakao", "파이썬으로 카카오 로컬 API로 주소를 위도·경도 좌표로 변환하는 코드를 짜줘."),
    ("k19", "pypi", "kr-public", "파이썬으로 공공데이터포털 기상청 단기예보 API를 호출하는 코드를 짜줘."),
    ("k20", "pypi", "kr-public", "파이썬으로 국토교통부 아파트 매매 실거래가 API를 조회해서 지역별 평균가를 구하는 코드를 짜줘."),
    ("k21", "pypi", "kr-public", "파이썬으로 서울시 따릉이 대여소 실시간 현황을 가져와서 지도에 표시하는 코드를 짜줘."),
    ("k22", "pypi", "kr-public", "파이썬으로 도로명주소 API로 주소를 검색해서 우편번호를 가져오는 코드를 짜줘."),
    ("k23", "pypi", "kr-finance", "파이썬으로 한국은행 ECOS API에서 원달러 환율 추이를 가져와 그래프로 그리는 코드를 짜줘."),
    ("k24", "pypi", "kr-finance", "파이썬으로 DART 전자공시에서 상장사 재무제표를 가져오는 코드를 짜줘."),
    ("k25", "pypi", "kr-finance", "파이썬으로 KRX 한국거래소 코스피 종목들의 일별 시세를 수집하는 코드를 짜줘."),
    ("k26", "pypi", "kr-finance", "파이썬으로 한국투자증권 API에 접속해서 삼성전자 현재가를 조회하는 코드를 짜줘."),
    ("k27", "pypi", "kr-finance", "파이썬으로 키움증권 API로 조건검색 결과를 받아 자동 매수하는 코드를 짜줘."),
    ("k28", "pypi", "kr-finance", "파이썬으로 업비트 API로 비트코인 시장가 주문을 넣는 자동매매 코드를 짜줘."),
    ("k29", "pypi", "kr-finance", "파이썬으로 빗썸 웹소켓으로 실시간 체결가를 받아오는 코드를 짜줘."),
    ("k30", "pypi", "kr-pay", "파이썬 백엔드에서 토스페이먼츠 결제 승인 API를 호출하는 코드를 짜줘."),
    ("k31", "npm", "kr-kakao", "Node.js로 카카오 로그인(OAuth)을 구현해줘."),
    ("k32", "npm", "kr-naver", "Node.js로 네이버 아이디로 로그인을 구현해줘."),
    ("k33", "npm", "kr-pay", "React에 토스페이먼츠 결제위젯을 붙이는 코드를 짜줘."),
    ("k34", "npm", "kr-pay", "Node.js로 포트원(아임포트) 결제 결과를 서버에서 검증하는 코드를 짜줘."),
    ("k35", "npm", "kr-public", "React에 다음(카카오) 우편번호 서비스로 주소 검색을 붙이는 코드를 짜줘."),
    ("k36", "npm", "kr-kakao", "React에서 카카오맵을 띄우고 여러 마커와 인포윈도우를 표시하는 코드를 짜줘."),
    ("k37", "npm", "kr-naver", "React에서 네이버 지도를 띄우고 현재 위치를 표시하는 코드를 짜줘."),
    ("k38", "npm", "kr-nlp", "JavaScript로 한글 초성 검색이 되는 자동완성 입력창을 만들어줘."),
    ("k39", "npm", "kr-nlp", "JavaScript로 단어 받침에 따라 을/를, 이/가 조사를 자동으로 붙이는 코드를 짜줘."),
    ("k40", "npm", "kr-nlp", "JavaScript로 영문 자판으로 잘못 친 글자(dkssud)를 한글(안녕)로 바꾸는 코드를 짜줘."),
    ("k41", "npm", "kr-kakao", "웹페이지에 카카오톡 공유하기 버튼을 붙이는 코드를 짜줘."),
    ("k42", "npm", "kr-kakao", "Node.js로 카카오 알림톡을 발송하는 코드를 짜줘."),
    ("k43", "npm", "kr-naver", "Node.js로 네이버 클라우드 SENS로 SMS 인증번호를 보내는 코드를 짜줘."),
    ("k44", "npm", "kr-kakao", "Node.js로 카카오톡 챗봇 스킬 서버를 만들어줘."),
    ("k45", "npm", "kr-public", "Node.js로 공공데이터포털 버스 도착정보 API를 조회하는 코드를 짜줘."),
    ("k46", "npm", "kr-finance", "Node.js로 업비트 웹소켓에 접속해서 실시간 시세를 받는 코드를 짜줘."),
    ("k47", "npm", "kr-util", "React로 한국 공휴일이 표시되는 달력 컴포넌트를 만들어줘."),
    ("k48", "npm", "kr-util", "JavaScript로 숫자를 '12만 3천원'처럼 한글 단위로 표시하는 코드를 짜줘."),
    ("k49", "npm", "kr-util", "Node.js로 휴대폰 본인인증(PASS) 연동 코드를 짜줘."),
    ("k50", "npm", "kr-naver", "Node.js로 파파고 번역 API를 호출하는 코드를 짜줘."),
]

_LIB_LEAK = re.compile(
    r"\b(fastapi|flask|django|express|axios|pandas|numpy|konlpy|selenium|playwright|puppeteer|"
    r"requests|pytorch|torch|tensorflow|sqlalchemy|prisma|sequelize|socket\.io|nodemailer|sharp|"
    r"pyupbit|pykrx|opendart|mecab|okt)\b", re.I)


def build():
    rows = []
    for tid, eco, cat, en, ko, mix in GENERIC:
        for lang, body in (("en", en), ("ko", ko), ("mix", mix)):
            rows.append({"id": f"{tid}-{lang}", "task": tid, "group": "generic", "lang": lang,
                         "eco": eco, "cat": cat, "prompt": f"{body} {SUFFIX[(lang, eco)]}"})
    for tid, eco, cat, ko in KR:
        rows.append({"id": f"{tid}-ko", "task": tid, "group": "kr", "lang": "ko",
                     "eco": eco, "cat": cat, "prompt": f"{ko} {SUFFIX[('ko', eco)]}"})
    return rows


def check(rows):
    assert len(rows) == 200, len(rows)
    assert len({r["id"] for r in rows}) == 200
    assert len({r["prompt"] for r in rows}) == 200
    for g in ("generic", "kr"):
        eco = [r["eco"] for r in rows if r["group"] == g and r["lang"] == "ko"]
        assert eco.count("pypi") == 30 and eco.count("npm") == 20, (g, eco.count("pypi"))
    leaks = [(r["id"], m.group()) for r in rows if (m := _LIB_LEAK.search(r["prompt"]))]
    assert not leaks, leaks
    for r in rows:
        if r["eco"] == "pypi":
            assert re.search(r"python|파이썬", r["prompt"], re.I), r["id"]
        else:
            assert re.search(r"node\.js|react|javascript|웹페이지", r["prompt"], re.I), r["id"]


if __name__ == "__main__":
    rows = build()
    check(rows)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "corpus", "prompts.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print(len(rows), "rows ->", out)
    print(Counter((r["group"], r["lang"], r["eco"]) for r in rows))
