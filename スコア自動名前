import streamlit as st
import pandas as pd
import sqlite3

# スマホ特化レイアウト
st.set_page_config(page_title="草野球スマホスコア", layout="centered")

st.title("⚾ スマホ専用スタメンボード")

# --- データベースの初期設定 ---
# データベースファイル（baseball_data.db）を自動で作成します
conn = sqlite3.connect('baseball_data.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS members (
        team_id TEXT,
        name TEXT,
        number TEXT,
        position TEXT
    )
''')
conn.commit()

# --- 1. チーム認証（合言葉エリア） ---
# スマホの一番上で合言葉を入力してもらう
st.markdown("### 🔑 チームの合言葉（チームID）")
team_id = st.text_input(
    "合言葉を入力してください", 
    placeholder="例: miratech または tigers", 
    label_visibility="collapsed"
).strip()

# 合言葉が入力されていない時は、ここで処理を止めて案内だけ出します
if not team_id:
    st.info("👆 チームで決めた「合言葉」を入力すると、メンバー表を自動で読み込みます！\n\n（初めての合言葉を入力すると、新規チームとして登録を開始できます）")
    st.stop()

# --- データベースからメンバーを読み込む関数 ---
def load_members(tid):
    df = pd.read_sql_query("SELECT name as 名前, number as 背番号, position as ポジション FROM members WHERE team_id = ?", conn, params=(tid,))
    if df.empty:
        # 新規チーム向けの初期枠（ダミーデータ）
        return pd.DataFrame([
            {"名前": "選手1", "背番号": "1", "ポジション": "ピッチャー"},
            {"名前": "選手2", "背番号": "2", "ポジション": "キャッチャー"},
        ])
    return df

# DBからデータをロードしてセッションに保持
if 'current_team_id' not in st.session_state or st.session_state.current_team_id != team_id:
    st.session_state.current_team_id = team_id
    st.session_state.member_df = load_members(team_id)

# --- 2. 選手マスタ管理（各自で追加・保存してもらう） ---
with st.expander(f"👥 「{team_id}」の選手マスタ編集（タップで開閉）", expanded=False):
    st.caption("※表を編集した後は、必ず下の「保存」ボタンを押してください")
    
    # データエディターで自由に編集してもらう
    edited_df = st.data_editor(
        st.session_state.member_df, 
        num_rows="dynamic", 
        key=f"editor_{team_id}",
        use_container_width=True
    )
    
    # 編集結果をDBに保存するボタン
    if st.button("💾 このメンバー表をデータベースに保存", use_container_width=True):
        # 古いデータを消して、新しいデータを書き込む
        c.execute("DELETE FROM members WHERE team_id = ?", (team_id,))
        for _, row in edited_df.iterrows():
            c.execute("INSERT INTO members (team_id, name, number, position) VALUES (?, ?, ?, ?)", 
                      (team_id, str(row["名前"]), str(row["背番号"]), str(row["ポジション"])))
        conn.commit()
        st.session_state.member_df = edited_df
        st.success("✨ メンバー表を記憶しました！次回からは合言葉を入れるだけで呼び出せます。")

# --- 3. オーダー作成（スマホ特化の縦スクロール仕様） ---
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
            player = st.selectbox(
                f"{i}番選手", 
                ["- 未選択 -"] + member_list, 
                label_visibility="collapsed",
                key=f"p_{i}"
            )
        
        if player != "- 未選択 -":
            p_info = st.session_state.member_df[st.session_state.member_df["名前"] == player]
            b_num = p_info["背番号"].values[0] if not p_info.empty else "-"
            default_pos = p_info["ポジション"].values[0] if not p_info.empty else "未設定"
            if default_pos not in positions:
                default_pos = "未設定"
            
            sub1, sub2 = st.columns([1.2, 3])
            with sub1:
                st.info(f"背番号 **#{b_num}**")
            with sub2:
                pos = st.selectbox(
                    f"{i}番守備", 
                    positions, 
                    index=positions.index(default_pos),
                    label_visibility="collapsed",
                    key=f"pos_{i}"
                )
            order_data.append({"打順": i, "名前": player, "背番号": b_num, "守備": pos})
        else:
            order_data.append({"打順": i, "名前": "未選択", "背番号": "-", "守備": "-"})
            
        st.divider()

# --- 4. 確認＆シェア用出力 ---
st.header("📱 オーダー確認・共有")
order_df = pd.DataFrame(order_data)
st.dataframe(order_df, use_container_width=True)

if st.button("💬 LINE共有用のテキストを作る", use_container_width=True):
    share_text = f"【本日のスタメン ({team_id})】\n"
    for item in order_data:
        if item['名前'] != "未選択":
            share_text += f"{item['打順']}番 {item['守備']} {item['名前']} (#{item['背番号']})\n"
    
    st.success("以下のテキストをコピーしてLINEに貼り付けられます！")
    st.code(share_text, language="text")

# 接続を閉じる
conn.close()
