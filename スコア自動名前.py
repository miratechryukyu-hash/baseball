import streamlit as st
import pandas as pd
import sqlite3

# スマホ特化レイアウト
st.set_page_config(page_title="草野球スマホスコア", layout="centered")

st.title("⚾ スマホ専用スコアブック")

# --- データベースの設定 ---
conn = sqlite3.connect('baseball_data.db')
c = conn.cursor()

# メンバーテーブル作成
c.execute('''
    CREATE TABLE IF NOT EXISTS members (
        team_id TEXT, name TEXT, number TEXT, position TEXT,
        games INTEGER DEFAULT 0, at_bats INTEGER DEFAULT 0, 
        hits INTEGER DEFAULT 0, hr INTEGER DEFAULT 0, rbi INTEGER DEFAULT 0
    )
''')

# 試合スコア用テーブル作成（新設）
c.execute('''
    CREATE TABLE IF NOT EXISTS line_scores (
        team_id TEXT, team_name TEXT, 
        i1 INT, i2 INT, i3 INT, i4 INT, i5 INT, i6 INT, i7 INT, i8 INT, i9 INT
    )
''')

# カラムチェックと拡張
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
    st.info("👆 合言葉を入力してスタートしてください。")
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
    df["打数"] = pd.to_numeric(df["打数"], errors='coerce').fillna(0).astype(int)
    df["安打"] = pd.to_numeric(df["安打"], errors='coerce').fillna(0).astype(int)
    df["打率"] = df.apply(lambda row: f'{row["安打"] / row["打数"]:.3f}'.lstrip('0') if row["打数"] > 0 else '.000', axis=1)
    return df

st.session_state.member_df = calculate_avg(load_members(team_id))

# 今日の打席ログを保持するセッション
if 'pa_log' not in st.session_state:
    st.session_state.pa_log = []

# ==========================================
# 📱 タブ構成（試合中の操作性を最優先）
# ==========================================
tab1, tab2, tab3 = st.tabs(["📋 スタメン", "⚾ スコア＆打席記録", "📊 名簿・成績"])

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
            current_order.append({"打順": i, "名前": player, "背番号": p_info['背番号']})
        st.divider()
    
    st.session_state.current_order = current_order

# ------------------------------------------
# タブ2: スコアボード＆打席記録（✨今回のメイン）
# ------------------------------------------
with tab2:
    st.header("🔢 ランニングスコア")
    st.caption("タップして1回〜9回の得点を直接入力できます")
    
    # スコアボードの初期化または読み込み
    if 'line_score_df' not in st.session_state:
        st.session_state.line_score_df = pd.DataFrame([
            {"チーム": "相手チーム", "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0},
            {"チーム": "自チーム", "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0},
        ])
    
    # データエディターで得点板を表示（スマホで横スクロール可能）
    edited_score = st.data_editor(
        st.session_state.line_score_df, 
        hide_index=True, 
        key="score_board",
        use_container_width=True
    )
    st.session_state.line_score_df = edited_score
    
    # 合計点の自動計算と表示
    opp_sum = sum([int(edited_score.iloc[0][str(i)]) for i in range(1, 10) if pd.notna(edited_score.iloc[0][str(i)])])
    my_sum  = sum([int(edited_score.iloc[1][str(i)]) for i in range(1, 10) if pd.notna(edited_score.iloc[1][str(i)])])
    
    st.markdown(f"### 計: 相手 **{opp_sum}** - **{my_sum}** 自チーム")
    st.divider()

    # --- 打者ごとの結果記録エリア ---
    st.header("🏏 打席結果のリアルタイム記録")
    
    if not st.session_state.current_order:
        st.warning("※先に「スタメン」タブで選手を選択してください。")
    else:
        # 入力しやすいようにスタメン選手をプルダウン化
        order_options = [f"{p['打順']}番: {p['名前']}" for p in st.session_state.current_order]
        
        c_batter, c_result = st.columns([1.5, 1.5])
        with c_batter:
            st.write("**打者選択**")
            selected_batter_str = st.selectbox("打者", order_options, label_visibility="collapsed")
            selected_batter_name = selected_batter_str.split(": ")[1]
            
        with c_result:
            st.write("**結果**")
            result_type = st.selectbox(
                "結果選択", 
                ["凡退・三振", "単打（ヒット）", "二塁打", "三塁打", "本塁打（HR）", "四死球（フォアボール）", "犠打・犠飛"],
                label_visibility="collapsed"
            )
            
        # 打点オプション
        add_rbi = st.checkbox("💡 この打席で打点あり（+1打点）")

        if st.button("📝 この打席を記録して通算成績へ反映", use_container_width=True):
            # 結果に応じた加算データの振り分け
            ab_add, h_add, hr_add, rbi_add = 0, 0, 0, 0
            
            if result_type in ["凡退・三振"]:
                ab_add = 1
            elif result_type in ["単打（ヒット）", "二塁打", "三塁打"]:
                ab_add = 1; h_add = 1
            elif result_type == "本塁打（HR）":
                ab_add = 1; h_add = 1; hr_add = 1
            # 四死球と犠打は「打数」にはカウントされない（野球ルール自動化）
            elif result_type in ["四死球（フォアボール）", "犠打・犠飛"]:
                ab_add = 0
                
            if add_rbi:
                rbi_add = 1
                
            # データベースを即座に更新
            c.execute("""
                UPDATE members 
                SET at_bats = at_bats + ?, hits = hits + ?, hr = hr + ?, rbi = rbi + ?
                WHERE team_id = ? AND name = ?
            """, (ab_add, h_add, hr_add, rbi_add, team_id, selected_batter_name))
            conn.commit()
            
            # ログに追加（画面表示用）
            st.session_state.pa_log.insert(0, f"・{selected_batter_str} ➔ **{result_type}**" + (" (打点1)" if add_rbi else ""))
            
            # 打席に立った＝試合に出た とみなして試合数を安全に+1（1試合につき1回だけ加算するロジックの実装も可能）
            c.execute("UPDATE members SET games = games + 1 WHERE team_id = ? AND name = ? AND games = 0", (team_id, selected_batter_name))
            conn.commit()
            
            st.success(f"{selected_batter_name}選手の成績を更新しました！")
            st.rerun()

        # 今日の打席履歴（簡易スコアブック機能）
        if st.session_state.pa_log:
            st.subheader("📖 本日の打席ログ")
            for log in st.session_state.pa_log:
                st.markdown(log)
            if st.button("🗑️ ログをリセット（成績は消えません）"):
                st.session_state.pa_log = []
                st.rerun()

# ------------------------------------------
# タブ3: 通算成績・名簿
# ------------------------------------------
with tab3:
    st.header(f"📊 通算成績 ({team_id})")
    st.write("※手動で修正したい場合のみ、表を書き換えて保存を押してください。")
    
    edit_target_df = st.session_state.member_df[["名前", "背番号", "ポジション", "試合", "打数", "安打", "本塁打", "打点"]]
    edited_df = st.data_editor(edit_target_df, num_rows="dynamic", use_container_width=True, key="main_editor")
    
    if st.button("💾 手動で名簿・成績を保存", use_container_width=True):
        c.execute("DELETE FROM members WHERE team_id = ?", (team_id,))
        for _, r in edited_df.iterrows():
            c.execute("INSERT INTO members (team_id, name, number, position, games, at_bats, hits, hr, rbi) VALUES (?,?,?,?,?,?,?,?,?)",
                      (team_id, str(r["名前"]), str(r["背番号"]), str(r["ポジション"]), int(r["試合"]), int(r["打数"]), int(r["安打"]), int(r["本塁打"]), int(r["打点"])))
        conn.commit()
        st.success("名簿を保存しました。")
        st.rerun()

conn.close()
