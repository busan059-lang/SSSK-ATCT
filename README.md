# 삼성전자 vs SK하이닉스 종목토론방 여론 비교 대시보드

네이버 금융 종목토론방 게시글을 찬티(긍정) / 중립 / 안티(부정)로 라벨링한 데이터를 기반으로,
삼성전자(005930)와 SK하이닉스(000660)의 투자자 여론을 비교하는 Streamlit 대시보드입니다.

## 화면 구성 (탭 4개)

1. **📊 여론 비교** — 감성 비율 비교(대칭 막대 / 그룹 막대 / 파이차트)
2. **🔑 핵심 키워드** — 정규식 기반 키워드 빈도 막대 + Plotly 기반 키워드 클라우드
3. **⏰ 시간대 · 작성자** — 시간대별(시 단위) 게시글 추이(감성별 영역차트), 작성자 Top 10(도배 계정 파악용)
4. **📝 본문 길이 · 샘플** — 감성별 본문 길이 박스플롯, 종목/감성별 샘플 게시글 조회 및 CSV 다운로드

상단 KPI 카드에서 전체 게시글 수, 종목별 찬티/안티 비율, 최다 게시자를 한눈에 확인할 수 있습니다.

## 데이터

- `data/samsung_labeled.csv`, `data/hynix_labeled.csv` — 이미 감성 라벨이 붙은 데이터(대시보드가 실제로 읽는 파일)
- 각 행: `nid, title, author, date, content, company, content_clean, sentiment`

### 데이터가 만들어진 과정 (참고용, 이 앱에는 포함되지 않음)

원본 `Untitled.ipynb`에서는 아래 과정을 거쳐 위 CSV를 만들었습니다.

1. Selenium(undetected_chromedriver)으로 네이버 종목토론방 목록/상세 페이지를 순회하며 원문 수집
2. URL/특수문자 제거, 중복 제거 등 전처리
3. Groq LLM(`llama-3.3-70b-versatile`)으로 찬티/중립/안티 3분류 라벨링 (반어법·냉소 고려)

> **왜 이 앱에 "실시간 수집" 탭이 없나요?**
> 네이버 종목토론방 상세 페이지의 본문은 `iframe`으로 `m.stock.naver.com`의 Next.js
> 페이지를 불러오는데, 이 본문 콘텐츠는 브라우저에서 자바스크립트가 실행된 뒤
> 클라이언트 사이드에서 비공개 API를 호출해 채워집니다. `requests`만으로는 이
> API를 안정적으로 찾아낼 수 없었고(내부 호출 경로가 난독화된 JS 번들에 있음),
> Selenium 없이는 재현이 어려워 이번 대시보드는 **이미 라벨링된 데이터를
> 시각화하는 데 집중**했습니다. 데이터를 다시 수집하려면 `Untitled.ipynb`의
> Selenium 파이프라인을 그대로 사용하면 됩니다.

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 프로젝트 구조

```
.
├── app.py                  # Streamlit 대시보드 메인 (탭 4개)
├── requirements.txt
├── .gitignore
├── README.md
├── data/
│   ├── samsung_labeled.csv
│   └── hynix_labeled.csv
└── src/
    ├── data_loader.py       # CSV 로드 + 파생 컬럼(시각, 본문 길이) 생성
    ├── keywords.py           # 정규식 기반 키워드 추출 + 워드클라우드 레이아웃
    └── theme.py              # 색상/Plotly 테마 상수
```

GitHub에 올릴 때는 위 파일들만 커밋하면 됩니다(원본 노트북 `Untitled.ipynb`와
`*_board.csv`, 루트의 `samsung_labeled.csv`/`hynix_labeled.csv`는 데이터 생성
과정을 남기고 싶으면 함께 올려도 되지만, 대시보드 실행에는 `data/` 폴더만
있으면 충분합니다).

## Streamlit Community Cloud 배포 방법

1. 이 폴더를 GitHub 저장소로 push합니다 (`app.py`, `requirements.txt`, `src/`, `data/` 포함 필수).
2. [share.streamlit.io](https://share.streamlit.io) 접속 → **New app**
3. 저장소/브랜치 선택, **Main file path**에 `app.py` 입력
4. **Deploy** 클릭 — 별도 API 키나 secrets 설정 없이 바로 동작합니다.

이 앱은 외부 API 키를 사용하지 않으므로 `secrets.toml` 설정이 필요 없습니다.
(참고: `.gitignore`에 `secrets.toml`/`.env`를 미리 제외해 두었으니, 추후 API
연동 기능을 추가하더라도 키가 실수로 커밋되지 않습니다.)
