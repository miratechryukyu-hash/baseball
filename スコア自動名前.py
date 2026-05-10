import streamlit as st
import pandas as pd
import sqlite3

# スマホ特化レイアウト
st.set_page_config(page_title="草野球スマホスコア", layout="centered")

st.title("⚾ スマホ専用スタメン＆成績ボード")

# --- データベースの初期設定と自動アップデート ---
conn = sqlite3.connect('baseball_data.db')
c = conn.cursor()

# 1. 基本テーブルの作成
c.execute('''
    CREATE TABLE IF NOT EXISTS members (
        team_id TEXT,
        name TEXT,
        number TEXT,
        position TEXT
    )
''')

# 2. 既存のテーブルに成績カラムがなければ自動で追加する
existing_columns = [col[1] for col in c.execute("PRAGMA table_info(members)").fetchall()]
stats_columns = {
    "games": "INTEGER DEFAULT 0",     # 試合数
    "at_bats": "INTEGER DEFAULT 0",   # 打数
    "hits": "INTEGER DEFAULT 0",      # 安打
    "hr": "INTEGER DEFAULT 0",        # 本塁打
    "rbi": "INTEGER DEFAULT 0"        # 打点
}

for col_name, col_type in stats_columns.items():
    if col_name not in existing_columns:
        c.execute(f"ALTER TABLE members ADD COLUMN {col_name} {col_type}")

conn.commit()

# --- 1. チーム認証（合言葉エリア） ---
st.markdown("### 🔑 チームの合言葉（チームID）")
team_id = st.text_input(
    "合言葉を入力してください", 
    placeholder="例: miratech または tigers", 
    label_visibility="collapsed"
).strip()

if not team_id:
    st.info("👆 チームの「合言葉」を入力すると、メンバー表と成績を自動で読み込みます！")
    conn.close()
    st.stop()

# --- データベースからメンバーと成績を確実に読み込む関数 ---
def load_members(tid):
    query = """
        SELECT 
            name as 名前, 
            number as 背番号, 
            position as ポジション,
            COALESCE(games, 0) as 試合,
            COALESCE(at_bats, 0) as 打数,
            COALESCE(hits, 0) as 安打,
            COALESCE(hr, 0) as 本塁打,
            COALESCE(rbi, 0) as 打点
        FROM members WHERE team_id = ?
    """
    df = pd.read_sql_query(query, conn, params=(tid,))
    
    # 新規チーム、またはデータが空の場合の初期枠
    if df.empty:
        df = pd.DataFrame([
            {"名前": "選手1", "背番号": "1", "ポジション": "ピッチャー", "試合": 0, "打数": 0, "安打": 0, "本塁打": 0, "打点": 0},
        ])
    
    # 万が一、古いキャッシュが残っていて列が足りない場合の安全対策（KeyError防止）
    required_cols = ["試合", "打数", "安打", "本塁打", "打点"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0
            
    return df

# 打率を自動計算して追加表示する関数
def calculate_avg(df):
    # 安全に数値型へ変換
    df["打数"] = pd.to_numeric(df["打数"], errors='coerce').fillna(0).astype(int)
    df["安打"] = pd.to_numeric(df["安打"], errors='coerce').fillna(0).astype(int)
    
    # 打数が0の場合は .000 にする
    df["打率"] = df.apply(lambda row: f'{row["安打"] / row["打数"]:.3f}'.lstrip('0') if row["打数"] > 0 else '.000', axis=1)
    return df

# データの読み込みと打率計算を常に最新の状態で実行
st.session_state.current_team_id = team_id
st.session_state.member_df = calculate_avg(load_members(team_id))


# ==========================================
# 📱 スマホで見やすい「タブ切り替え」UI
# ==========================================
tab1, tab2 = st.tabs(["📋 スタメン作成", "📊 成績入力・メンバー管理"])

# ------------------------------------------
# タブ1: スタメン作成（ベンチ用）
# ------------------------------------------
with tab1:
    st.header("📋 本日のスタメン作成")
    
    member_list = st.session_state.member_df["名前"].tolist()
    positions = ["ピッチャー", "キャッチャー", "ファースト", "セカンド", "サード", "ショート", "レフト", "センター", "ライト", "DH", "未設定"]
    
    order_data = []
    
    for i in range(1, 10):
        with st.container():
            c1, c2 = st.columns([1.2, 3])
            with c1:
                st.markdown(f"### 🏏 {i}番")
            with c2:
                player = st.selectbox(f"{i}番選手", ["- 未選択 -"] + member_list, label_visibility="collapsed", key=f"p_{i}")
            
            if player != "- 未選択 -":
                p_info = st.session_state.member_df[st.session_state.member_df["名前"] == player]
                b_num = p_info["背番号"].values[0] if not p_info.empty else "-"
                default_pos = p_info["ポジション"].values[0] if not p_info.empty else "未設定"
                avg = p_info["打率"].values[0] if not p_info.empty else ".000"
                hr = p_info["本塁打"].values[0] if not p_info.empty else "0"
                
                if default_pos not in positions:
                    default_pos = "未設定"
                
                sub1, sub2 = st.columns([1.5, 2.5])
                with sub1:
                    st.caption(f"#{b_num} / **{avg}** (HR:{hr})")
                with sub2:
                    pos = st.selectbox(f"{i}番守備", positions, index=positions.index(default_pos), label_visibility="collapsed", key=f"pos_{i}")
                
                order_data.append({"打順": i, "名前": player, "背番号": b_num, "守備": pos})
            else:
                order_data.append({"打順": i, "名前": "未選択", "背番号": "-", "守備": "-"})
                
            st.divider()
    
    # 確認＆シェア
    st.subheader("📱 オーダー確認・共有")
    st.dataframe(pd.DataFrame(order_data), use_container_width=True)
    
    if st.button("💬 LINE共有用のテキストを作る", use_container_width=True):
        share_text = f"【本日のスタメン ({team_id})】\n"
        for item in order_data:
            if item['名前'] != "未選択":
                share_text += f"{item['打順']}番 {item['守備']} {item['名前']} (#{item['背番号']})\n"
        st.success("以下のテキストをコピーしてLINEに貼り付けられます！")
        st.code(share_text, language="text")

# ------------------------------------------
# タブ2: 成績入力・メンバー管理
# ------------------------------------------
with tab2:
    st.header(f"📊 「{team_id}」の成績・名簿")
    st.write("数字を書き換えて下の「保存」を押すと通算成績が更新されます。打率は自動計算されます！")
    
    edit_target_df = st.session_state.member_df[["名前", "背番号", "ポジション", "試合", "打数", "安打", "本塁打", "打点"]]
    
    edited_df = st.data_editor(
        edit_target_df, 
        num_rows="dynamic", 
        key=f"stats_editor_{team_id}",
        use_container_width=True
    )
    
    if st.button("💾 成績・メンバー表をデータベースに保存", use_container_width=True):
        c.execute("DELETE FROM members WHERE team_id = ?", (team_id,))
        for _, row in edited_df.iterrows():
            g = int(row["試合"]) if pd.notna(row["試合"]) and str(row["試合"]).isdigit() else 0
            ab = int(row["打数"]) if pd.notna(row["打数"]) and str(row["打数"]).isdigit() else 0
            h = int(row["安打"]) if pd.notna(row["安打"]) and str(row["安打"]).isdigit() else 0
            hr = int(row["本塁打"]) if pd.notna(row["本塁打"]) and str(row["本塁打"]).isdigit() else 0
            rbi = int(row["打点"]) if pd.notna(row["打点"]) and str(row["打点"]).isdigit() else 0
            
            c.execute("""
                INSERT INTO members (team_id, name, number, position, games, at_bats, hits, hr, rbi) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (team_id, str(row["名前"]), str(row["背番号"]), str(row["ポジション"]), g, ab, h, hr, rbi))
        
        conn.commit()
        st.success("✨ 成績データを完全にアップデートしました！")
        st.rerun()

conn.close()
