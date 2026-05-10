import streamlit as st
import pandas as pd
import sqlite3

# スマホ特化レイアウト
st.set_page_config(page_title="草野球スマホスコア", layout="centered")

st.title("⚾ スマホ専用スタメン＆成績管理")

# --- データベースの初期設定 ---
conn = sqlite3.connect('baseball_data.db')
c = conn.cursor()

# テーブル作成とカラム拡張
c.execute('''
    CREATE TABLE IF NOT EXISTS members (
        team_id TEXT, name TEXT, number TEXT, position TEXT,
        games INTEGER DEFAULT 0, at_bats INTEGER DEFAULT 0, 
        hits INTEGER DEFAULT 0, hr INTEGER DEFAULT 0, rbi INTEGER DEFAULT 0
    )
''')

# カラム不足チェック（安全対策）
existing_columns = [col[1] for col in c.execute("PRAGMA table_info(members)").fetchall()]
stats_cols = {"games": "INTEGER", "at_bats": "INTEGER", "hits": "INTEGER", "hr": "INTEGER", "rbi": "INTEGER"}
for col_name, col_type in stats_cols.items():
    if col_name not in existing_columns:
        c.execute(f"ALTER TABLE members ADD COLUMN {col_name} {col_type} DEFAULT 0")
conn.commit()

# --- 1. チーム認証 ---
st.markdown("### 🔑 チームの合言葉（チームID）")
team_id = st.text_input("合言葉を入力", placeholder="例: miratech", label_visibility="collapsed").strip()

if not team_id:
    st.info("👆 合言葉を入力してください。")
    conn.close()
    st.stop()

# --- データ読み込み関数 ---
def load_members(tid):
    query = "SELECT name as 名前, number as 背番号, position as ポジション, games as 試合, at_bats as 打数, hits as 安打, hr as 本塁打, rbi as 打点 FROM members WHERE team_id = ?"
    df = pd.read_sql_query(query, conn, params=(tid,))
    if df.empty:
        df = pd.DataFrame([{"名前": "選手1", "背番号": "1", "ポジション": "投手", "試合": 0, "打数": 0, "安打": 0, "本塁打": 0, "打点": 0}])
    return df

def calculate_avg(df):
    df["打率"] = df.apply(lambda row: f'{row["安打"] / row["打数"]:.3f}'.lstrip('0') if row["打数"] > 0 else '.000', axis=1)
    return df

# セッション状態の管理
st.session_state.member_df = calculate_avg(load_members(team_id))

# ==========================================
# 📱 タブ切り替え（3つに増やしました）
# ==========================================
tab1, tab2, tab3 = st.tabs(["📋 スタメン作成", "⚾ 本日の成績入力", "📊 通算成績・名簿"])

# ------------------------------------------
# タブ1: スタメン作成
# ------------------------------------------
with tab1:
    st.header("📋 本日のスタメン")
    member_list = st.session_state.member_df["名前"].tolist()
    positions = ["ピッチャー", "キャッチャー", "ファースト", "セカンド", "サード", "ショート", "レフト", "センター", "ライト", "DH", "未設定"]
    
    current_order = []
    for i in range(1, 10):
        col1, col2 = st.columns([1, 3])
        with col1: st.markdown(f"### {i}番")
        with col2:
            player = st.selectbox(f"p_{i}", ["- 未選択 -"] + member_list, label_visibility="collapsed", key=f"sel_{i}")
        
        if player != "- 未選択 -":
            p_info = st.session_state.member_df[st.session_state.member_df["名前"] == player].iloc[0]
            sub1, sub2 = st.columns([1.5, 2.5])
            with sub1: st.caption(f"#{p_info['背番号']} / **{p_info['打率']}**")
            with sub2:
                pos = st.selectbox(f"pos_{i}", positions, index=positions.index(p_info['ポジション']) if p_info['ポジション'] in positions else 10, label_visibility="collapsed", key=f"p_pos_{i}")
            current_order.append({"名前": player, "ポジション": pos})
        st.divider()
    
    st.session_state.current_order = current_order

# ------------------------------------------
# タブ2: 本日の成績入力（新機能！）
# ------------------------------------------
with tab2:
    st.header("⚾ 今日の結果を入力")
    if not st.session_state.get('current_order'):
        st.warning("先に「スタメン作成」で選手を選んでください。")
    else:
        st.write("今日の打席結果を入力してください。")
        
        # 入力用の枠組みを作成
        today_data = []
        for p in st.session_state.current_order:
            st.markdown(f"**{p['名前']}**")
            c1, c2, c3, c4 = st.columns(4)
            with c1: ab = st.number_input("打数", min_value=0, max_value=10, key=f"ab_{p['名前']}")
            with c2: h = st.number_input("安打", min_value=0, max_value=10, key=f"h_{p['名前']}")
            with c3: hr = st.number_input("本塁打", min_value=0, max_value=10, key=f"hr_{p['名前']}")
            with c4: rbi = st.number_input("打点", min_value=0, max_value=20, key=f"rbi_{p['名前']}")
            today_data.append({"名前": p['名前'], "打数": ab, "安打": h, "本塁打": hr, "打点": rbi})
            st.divider()
            
        if st.button("🚀 今日の成績を通算に加算する", use_container_width=True):
            for row in today_data:
                c.execute("""
                    UPDATE members 
                    SET games = games + 1, 
                        at_bats = at_bats + ?, 
                        hits = hits + ?, 
                        hr = hr + ?, 
                        rbi = rbi + ?
                    WHERE team_id = ? AND name = ?
                """, (row['打数'], row['安打'], row['本塁打'], row['打点'], team_id, row['名前']))
            conn.commit()
            st.success("✅ 通算成績に反映しました！「通算成績」タブを確認してください。")
            st.rerun()

# ------------------------------------------
# タブ3: 通算成績・メンバー管理
# ------------------------------------------
with tab2 if False else tab3: # タブの表示順序を整理
    st.header(f"📊 通算成績 ({team_id})")
    # 編集可能な状態で表示
    edited_df = st.data_editor(st.session_state.member_df, num_rows="dynamic", use_container_width=True, key="main_editor")
    
    if st.button("💾 手動で名簿・成績を保存", use_container_width=True):
        c.execute("DELETE FROM members WHERE team_id = ?", (team_id,))
        for _, r in edited_df.iterrows():
            c.execute("INSERT INTO members (team_id, name, number, position, games, at_bats, hits, hr, rbi) VALUES (?,?,?,?,?,?,?,?,?)",
                      (team_id, str(r["名前"]), str(r["背番号"]), str(r["ポジション"]), int(r["試合"]), int(r["打数"]), int(r["安打"]), int(r["本塁打"]), int(r["打点"])))
        conn.commit()
        st.success("保存しました。")
        st.rerun()

conn.close()
