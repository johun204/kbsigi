# 🍱 큽식이 (KBsigi)

<img src="./image/logo.png" width="100" alt="Project Logo">

구내식당의 식단 정보를 자동으로 수집(Crawling)하여 JSON 데이터로 제공하는 프로젝트입니다.
GitHub Actions를 통해 정해진 시간마다 최신 식단 정보를 업데이트합니다.

## 🚀 주요 기능

* **다양한 구내식당 지원**:
    * 현대그린푸드 (여의도 IT센터)
    * 아워홈 (본점/신관)
    * CJ 프레시밀 (전경련회관)
* **날씨 정보 제공**: 현재 여의도 날씨 및 기온 정보 포함.
* **오늘/내일 식단**: 당일 및 익일 식단 데이터 분리 저장.
* **자동 업데이트**: 스케줄링으로 데이터 최신화.

## 🔄 업데이트 스케줄 (KST 기준)

GitHub Actions를 통해 매시간 자동 갱신됩니다.


## 📂 데이터 구조 (`/data`)

수집된 데이터는 `/data` 폴더에 JSON 형식으로 저장되며, 카카오톡 챗봇에서 API처럼 호출하여 사용할 수 있습니다.

## 🛠 Tech Stack

* **Language**: Python 3.9
* **Libraries**: requests, json, datetime
* **CI/CD**: GitHub Actions
