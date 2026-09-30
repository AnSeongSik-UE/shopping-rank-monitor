# shopping-rank-monitor

기간: 2022.12 ~ 2023.02

등록한 상품과 검색어의 쇼핑 순위를 조회해 SQLite에 기록하고, 순위 변경과 예약 공지를 Telegram으로 전달하는 PyQt 응용 프로그램입니다.

## 처리 흐름

`상품·검색어 입력 → 쇼핑 순위 조회 → SQLite 이력 저장·비교 → 화면 갱신 및 Telegram 알림`

## 기술

- Python, PyQt5
- SQLite, Requests, Selenium
- python-telegram-bot, APScheduler
- pandas, Qt Designer

## 개인 기여

- 상품 등록 입력값을 확장하고 등록·삭제 과정의 예외 처리를 보완했습니다.
- 상품 정보를 SQLite에 추가·수정·삭제하는 흐름을 구현했습니다.
- Telegram 명령으로 상품을 등록·삭제하는 기능을 추가했습니다.
- 순위 조회 주기를 조정하고 예약 공지 저장·전송 흐름을 개발했습니다.
- 등록 상품을 불러오는 Excel 데이터 입력 기능과 작성 양식을 보완했습니다.

## 협업 범위

순위 조회의 기본 로직, Telegram 수신 목록과 UI 정리 등은 KAKIS 팀이 함께 개발했습니다.

## 코드 위치

| 파일 | 내용 |
| --- | --- |
| [`main.py`](./main.py) | 상품 관리, 순위 확인, SQLite 기록과 Telegram 명령·알림 흐름 |
| [`rank.py`](./rank.py) | 상품별 순위 이력 조회 화면 |
| [`notice.py`](./notice.py) | 예약 공지 등록·삭제와 전송 스레드 |
| [`list.py`](./list.py) | 업체별 Telegram 수신 대상 관리 |
| [`ui/`](./ui/) | Qt Designer UI 원본 |
| [`setup.py`](./setup.py) | Windows 응용 프로그램 빌드 설정 |

## 공개본 안내

Telegram Bot 토큰은 `TELEGRAM_BOT_TOKEN` 환경변수로 대체했으며, SQLite 데이터베이스, 운영 자료, 이미지·폰트, 로컬 설정과 실행 파일을 제외했습니다.

이 저장소는 별도의 오픈소스 라이선스를 제공하지 않습니다.
