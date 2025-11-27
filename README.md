# Network Anomaly Inspector Dashboard

> **Access Restricted:** 이 페이지는 관리자(Admin) 전용 대시보드입니다. 허가된 사용자만 접근할 수 있도록 보안 설정에 유의하십시오.

## 프로젝트 개요

이 프로젝트는 **네트워크 침입 탐지 시스템(NIDS)** 의 결과를 시각화하는 관리자용 웹 대시보드입니다.
Autoencoder 모델이 탐지한 이상 패킷 로그를 분석하여, XAI(설명 가능한 AI) 기법인 SHAP 값을 통해 "왜 이 패킷이 악성으로 판단되었는지" 직관적으로 설명합니다.

## 주요 기능

* **XAI 기반 원인 분석:** AI가 이상으로 판단한 핵심 요인(Top 3 Features)을 시각적으로 강조합니다.
* **동적 데이터 뷰어 (Dynamic Viewer):** 패킷의 `raw_data` 필드가 변경되거나 추가되어도 코드 수정 없이 자동으로 테이블에 반영됩니다.
* **대시보드 KPI:** 전체 탐지 건수, 평균 Loss Score, 시스템 상태 등을 한눈에 파악할 수 있습니다.
* **상세 분석 (Drill-Down):** 특정 로그를 선택하여 Kafka 오프셋 정보 및 상세 SHAP 기여도 차트를 확인할 수 있습니다.

## 디렉토리 구조

```text
admin_dashboard/
├── .env
├── app.py
├── data_loader.py
├── requirements.txt
└── README.md
```

## 설치 및 설정

```bash
# 필수 라이브러리 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env)
XAI_LOG_DIR=xai_analysis_json_directory
```

## 실행
```bash
streamlit run app.py
```
