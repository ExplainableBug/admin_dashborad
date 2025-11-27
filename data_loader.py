import pandas as pd
import os
import json
import glob
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_LOG_PATH = os.getenv("XAI_LOG_DIR")

if ENV_LOG_PATH:
    if os.path.isabs(ENV_LOG_PATH):
        LOG_DIR = ENV_LOG_PATH
    else:
        LOG_DIR = os.path.join(BASE_DIR, ENV_LOG_PATH)
else:
    LOG_DIR = os.path.join(BASE_DIR, 'kafka/autoencoder/xai_results')

def load_raw_logs():
    logs = []

    if not os.path.exists(LOG_DIR):
        print(f"Warning: Directory not found: {LOG_DIR}")
        return []

    json_files = glob.glob(os.path.join(LOG_DIR, "*.json"))

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

                filename = os.path.basename(filepath)
                file_id = os.path.splitext(filename)[0]

                if 'id' not in data:
                    data['id'] = file_id

                if 'raw_data' in data and 'filename' not in data['raw_data']:
                    data['raw_data']['filename'] = filename
                elif 'raw_data' not in data:
                    data['raw_data'] = {'filename': filename}

                logs.append(data)
        except Exception as e:
            print(f"Error loading file {filepath}: {e}")
            continue

    # 최신순 정렬 (timestamp 기준)
    try:
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except:
        pass

    return logs

def get_logs():
    logs = load_raw_logs()
    summary_list = []

    for log in logs:
        # SHAP 값 중 절대값이 가장 큰 Top 1 추출
        shap_dict = log.get('shap_values', {})
        top_risk = "N/A"
        if shap_dict:
            try:
                # 값이 숫자형인 경우에만 처리
                valid_items = {k: v for k, v in shap_dict.items() if isinstance(v, (int, float))}
                if valid_items:
                    top_risk = max(valid_items.items(), key=lambda x: abs(x[1]))[0]
            except ValueError:
                pass

        summary_list.append({
            "ID": log['id'],
            "Timestamp": log.get('timestamp', 'N/A'),
            "Total Loss": round(log.get('total_loss', 0.0), 2),
            "Top Risk Factor": top_risk,
            "Status": "Critical" if log.get('total_loss', 0) > log.get('threshold', 100) * 2 else "Anomaly"
        })

    # 데이터가 없을 경우 빈 프레임 반환
    if not summary_list:
        return pd.DataFrame(columns=["ID", "Timestamp", "Total Loss", "Top Risk Factor", "Status"]), []

    return pd.DataFrame(summary_list), logs

def get_log_by_id(log_id):
    logs = load_raw_logs()
    for log in logs:
        if log['id'] == log_id:
            return log
    return None
