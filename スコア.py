import streamlit as st
import pandas as pd

st.set_page_config(page_title="草野球スコア管理", layout="wide")

st.title("⚾ 草野球メンバー・オーダー管理")

# --- 1. 選手マスタ管理 ---
st.header("1. 選手マスタ登録")
if 'member_df' not in st.session_state:
    # 初期データ
    st.session_state.member_df = pd.DataFrame([
        {"名前": "座波孝行", "背番号": "16", "ポジション": "サード"},
        {"名前": "伊計直哉", "背番号": "29", "ポジション": "ファースト"},
        {"名前": "新垣敦生", "背番号": "1", "ポジション": "ピッチャー"},
        {"名前": "多宇恭輔", "背番号": "66", "ポジション": ""},
        {"名前": "玉城大夢", "背番号": "21", "ポジション": "サード"},
        {"名前": "安次富堅斗", "背番号": "34", "ポジション": "ライト"},
        {"名前": "安富翔", "背番号": "6", "ポジション": "レフト"},
        {"名前": "屋宜宏弥", "背番号": "22", "ポジション": "キャッチャー"},
        {"名前": "仲田匠輝", "背番号": "7", "ポジション": "センター"},
        {"名前": "伊計直哉", "背番号": "29", "ポジション": "ファースト"},


    ])
# 画面上で編集可能なテーブル
edited_df = st.data_editor(st.session_state.member_df, num_rows="dynamic", key="member_editor")
st.session_state.member_df = edited_df

# --- 2. オーダー作成 ---
st.header("2. 本日のオーダー作成")
member_list = st.session_state.member_df["名前"].tolist()
positions = ["投手", "捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "左翼手", "中堅手", "右翼手", "DH"]

order_data = []
cols = st.columns(3) # 3列で表示

for i in range(1, 10):
    with cols[(i-1) % 3]:
        st.subheader(f"{i}番")
        player = st.selectbox(f"選手選択", ["未選択"] + member_list, key=f"p_{i}")
        pos = st.selectbox(f"守備位置", positions, key=f"pos_{i}")
        order_data.append({"打順": i, "名前": player, "守備": pos})

# --- 3. 確認用表示 ---
st.header("📋 今日のスタメン")
st.table(pd.DataFrame(order_data))

