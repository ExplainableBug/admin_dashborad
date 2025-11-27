import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_loader import get_logs, get_log_by_id

st.set_page_config(page_title="Intrusion Detection Admin", page_icon="🚨", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ccc;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .metric-label { font-size: 0.85rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 1.1rem; font-weight: bold; color: #333; margin-top: 5px; }
    .metric-delta { font-size: 0.9rem; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 Network Anomaly Inspector")
st.markdown("XAI 기반 네트워크 침입 탐지 시스템 관리자 대시보드")

# --- 1. 사이드바: 로그 선택 ---
st.sidebar.header("Log Selection")

# 데이터 로드
df_summary, raw_logs = get_logs()

if df_summary.empty:
    st.error("표시할 로그 데이터가 없습니다. JSON 파일 경로를 확인해주세요.")
    st.info("예상 경로: /ExplainableBug/kafka/autoencoder/xai_results/*.json")
else:
    selected_log_id = st.sidebar.selectbox(
        "Select Suspicious Packet:",
        df_summary['ID'].tolist(),
        format_func=lambda x: f"{x} (Loss: {df_summary[df_summary['ID']==x]['Total Loss'].values[0]})"
    )

    if selected_log_id:
        log_data = get_log_by_id(selected_log_id)

        if log_data:
            # --- 상단: 핵심 요약 정보 ---
            col1, col2, col3 = st.columns(3)
            with col1:
                threshold = log_data.get('threshold', 100)
                loss = log_data.get('total_loss', 0)
                st.metric(
                    "Anomaly Score (Loss)",
                    f"{loss:.2f}",
                    delta=f"Threshold: {threshold}",
                    delta_color="inverse"
                )
            with col2:
                st.metric("Timestamp", log_data.get('timestamp', 'N/A'))
            with col3:
                filename = log_data.get('raw_data', {}).get('filename', 'Unknown')
                st.metric("Source File", filename)

            st.divider()

            # --- 메인 분석 영역 (2단 분리) ---
            col_shap, col_raw = st.columns([1, 1])

            # ---------------------------------------------------------
            # [Left Column] SHAP Analysis (Top 3 Focus)
            # ---------------------------------------------------------
            with col_shap:
                st.subheader("📊 Why Malicious? (Top 3 Factors)")
                st.caption("AI가 이 패킷을 비정상으로 판단하게 만든 가장 큰 원인 3가지입니다.")

                shap_data = log_data.get('shap_values', {})
                if shap_data:
                    # 숫자형 값만 필터링 후 절대값 기준으로 정렬하여 Top 3 추출
                    valid_shap = {k: v for k, v in shap_data.items() if isinstance(v, (int, float))}
                    sorted_shap = sorted(valid_shap.items(), key=lambda x: abs(x[1]), reverse=True)
                    top_3 = sorted_shap[:3]

                    if top_3:
                        # Top 3 카드 형태로 강조 표시
                        for idx, (feature, value) in enumerate(top_3):
                            # 양수(악성 기여)는 빨간색, 음수(정상 기여)는 파란색
                            impact_color = "#ef4444" if value > 0 else "#3b82f6"
                            impact_text = "Risk Increase ⬆" if value > 0 else "Risk Decrease ⬇"

                            st.markdown(f"""
                            <div class="metric-card" style="border-left-color: {impact_color};">
                                <div class="metric-label">Top {idx+1} Contributor</div>
                                <div class="metric-value">{feature}</div>
                                <div class="metric-delta" style="color:{impact_color};">
                                    Value: {value:.4f} ({impact_text})
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # 전체 맥락을 위한 차트 (Top 10)
                        with st.expander("View Detailed Chart (Top 10)", expanded=True):
                            top_10 = sorted_shap[:10]
                            features = [x[0] for x in top_10]
                            values = [x[1] for x in top_10]
                            colors = ['#ef4444' if v > 0 else '#3b82f6' for v in values]

                            fig = go.Figure(go.Bar(
                                x=values, y=features, orientation='h', marker_color=colors
                            ))
                            fig.update_layout(
                                margin=dict(l=0, r=0, t=0, b=0),
                                height=350,
                                yaxis=dict(autorange="reversed"),
                                xaxis_title="SHAP Value"
                            )
                            # use_container_width=True는 유지 (Plotly 차트에는 유효함)
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No numeric SHAP values found.")
                else:
                    st.warning("No SHAP values available.")

            # ---------------------------------------------------------
            # [Right Column] Raw Data (Fully Dynamic)
            # ---------------------------------------------------------
            with col_raw:
                st.subheader("📝 Packet Details (Dynamic)")
                st.caption("패킷의 원본 데이터를 테이블 형태로 표시합니다. (필드 자동 감지)")

                raw_data = log_data.get('raw_data', {})

                if raw_data:
                    df_raw = pd.DataFrame(
                        list(raw_data.items()),
                        columns=["Field Name", "Value"]
                    )

                    # 모든 값을 문자열로 변환하여 표시 오류 방지
                    df_raw['Value'] = df_raw['Value'].astype(str)

                    # 테이블 표시
                    st.dataframe(
                        df_raw,
                        width="stretch",
                        hide_index=True,
                        height=600,
                        column_config={
                            "Field Name": st.column_config.TextColumn("Field Name", width="medium"),
                            "Value": st.column_config.TextColumn("Captured Value", width="large")
                        }
                    )
                else:
                    st.warning("No raw data captured.")

            st.divider()

            # 하단: Kafka 메타데이터
            with st.expander("Broker Information (Kafka)", expanded=False):
                st.json(log_data.get('kafka_info', {}))
        else:
            st.error("로그 데이터를 불러오는 중 오류가 발생했습니다.")
