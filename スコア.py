import streamlit as st
import pandas as pd

# スマホ画面にぴったり収まる "centered" モード
st.set_page_config(page_title="草野球スマホスコア", layout="centered")

st.title("⚾ スマホ専用スタメンボード")

# --- 1. 選手マスタ管理（普段は折りたたむ） ---
if 'member_df' not in st.session_state:
    # 重複を削除し、ポジション表記を統一した初期データ
    st.session_state.member_df = pd.DataFrame([
        {"名前": "新垣敦生", "背番号": "1", "ポジション": "ピッチャー"},
        {"名前": "安富翔", "背番号": "6", "ポジション": "レフト"},
        {"名前": "仲田匠輝", "背番号": "7", "ポジション": "センター"},
        {"名前": "座波孝行", "背番号": "16", "ポジション": "サード"},
        {"名前": "玉城大夢", "背番号": "21", "ポジション": "サード"},
        {"名前": "屋宜宏弥", "背番号": "22", "ポジション": "キャッチャー"},
        {"名前": "伊計直哉", "背番号": "29", "ポジション": "ファースト"},
        {"名前": "安次富堅斗", "背番号": "34", "ポジション": "ライト"},
        {"名前": "多宇恭輔", "背番号": "66", "ポジション": "キャッチャー"},
        {"名前": "棚原伸一", "背番号": "4", "ポジション": "セカンド"},
        {"名前": "佐次田祐輔", "背番号": "9", "ポジション": "ライト"},
        {"名前": "運天ジョン", "背番号": "10", "ポジション": "ピッチャー"},
        {"名前": "比嘉智哉", "背番号": "25", "ポジション": "ピッチャー"},
        {"名前": "相良大輔", "背番号": "33", "ポジション": "ファースト"},
        {"名前": "北村勇拓", "背番号": "38", "ポジション": "ピッチャー"},
        {"名前": "嶺井拓磨", "背番号": "42", "ポジション": "サード"},
        {"名前": "金城博也", "背番号": "55", "ポジション": "セカンド"},
        {"名前": "米田寛", "背番号": "88", "ポジション": "ピッチャー"},
        {"名前": "鎮目竜太", "背番号": "2", "ポジション": "セカンド"},
        {"名前": "比嘉吉人", "背番号": "26", "ポジション": "ショート"},
        {"名前": "宮城裕一", "背番号": "30", "ポジション": "ピッチャー"},
    ])

# スマホの画面領域を節約するため、expanderで折りたたみ式にする
with st.expander("👥 選手マスタの確認・追加（タップで開閉）", expanded=False):
    st.caption("※表をタップして直接編集・メンバー追加が可能です")
    edited_df = st.data_editor(
        st.session_state.member_df, 
        num_rows="dynamic", 
        key="member_editor",
        use_container_width=True
    )
    st.session_state.member_df = edited_df

# --- 2. オーダー作成（スマホ特化の縦スクロール仕様） ---
st.header("📋 本日のスタメン作成")

# 選択肢の準備
member_list = st.session_state.member_df["名前"].tolist()
positions = ["ピッチャー", "キャッチャー", "ファースト", "セカンド", "サード", "ショート", "レフト", "センター", "ライト", "DH", "未設定"]

order_data = []

# 1番から9番までを縦にスッキリ配置
for i in range(1, 10):
    with st.container():
        # 打順と選手選択を横に並べる（スマホでタップしやすい比率）
        c1, c2 = st.columns([1.2, 3])
        
        with c1:
            # 打順を少し大きめに表示
            st.markdown(f"### 🏏 {i}番")
        
        with c2:
            # 選手を選択
            player = st.selectbox(
                f"{i}番選手", 
                ["- 未選択 -"] + member_list, 
                label_visibility="collapsed",
                key=f"p_{i}"
            )
        
        # 選手が選ばれたら、背番号と守備位置入力欄をすぐ下に表示する連動機能
        if player != "- 未選択 -":
            # マスタから選ばれた選手の情報を取得
            p_info = st.session_state.member_df[st.session_state.member_df["名前"] == player]
            b_num = p_info["背番号"].values[0] if not p_info.empty else "-"
            default_pos = p_info["ポジション"].values[0] if not p_info.empty else "未設定"
            
            # デフォルトポジションが選択肢（positions）にない場合の安全対策
            if default_pos not in positions:
                default_pos = "未設定"
            
            # 背番号表示と守備位置選択をコンパクトに並べる
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
            # 未選択の時はプレースホルダーを入れておく
            order_data.append({"打順": i, "名前": "未選択", "背番号": "-", "守備": "-"})
            
        st.divider() # 各打順の間に区切り線を入れて視認性アップ

# --- 3. 確認＆シェア用出力 ---
st.header("📱 オーダー確認・共有")

# 決定したスタメンのデータフレーム化
order_df = pd.DataFrame(order_data)

# スマホ画面で確認しやすいシンプルなテーブル表示
st.dataframe(order_df, use_container_width=True)

# ベンチからLINE等へすぐに送れるテキスト生成機能
if st.button("💬 LINE共有用のテキストを作る", use_container_width=True):
    share_text = "【本日のスタメン】\n"
    for item in order_data:
        if item['名前'] != "未選択":
            share_text += f"{item['打順']}番 {item['守備']} {item['名前']} (#{item['背番号']})\n"
    
    st.success("以下のテキストをコピーしてLINEに貼り付けられます！")
    st.code(share_text, language="text")
