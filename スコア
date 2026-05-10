import streamlit as st
import pandas as pd

st.set_page_config(page_title="草野球スコア管理", layout="wide")

st.title("⚾ 草野球メンバー・オーダー管理")

# --- 1. 選手マスタ管理 ---
st.header("1. 選手マスタ登録")
if 'member_df' not in st.session_state:
    # 初期データ
    st.session_state.member_df = pd.DataFrame([
        {"名前": "安富", "背番号": "1", "ポジション": "投手"},
        {"名前": "田中", "背番号": "10", "ポジション": "捕手"},
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

