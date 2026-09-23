import streamlit as st
#from streamlit_gsheets import GSheetsConnection

from housecall_route import run_housecall_route
from visit_route import run_visit_route


def yes_no_icon(value):
    return "✅ あり" if str(value).strip() == "はい" else "— なし"


# =========================
# ページ設定
# =========================

st.set_page_config(
    page_title="在宅医療 算定支援",
    page_icon="🏠",
    layout="centered",
)


# =========================
# Googleスプレッドシート読込
# =========================

conn = st.connection("gsheets", type=GSheetsConnection)

# 管理画面判定を先に行う
# mode = str(
#     st.query_params.get("mode", "")
# ).strip().lower()

# 施設設定は管理画面でも必要なので先に読む
facility_setting = conn.read(
    worksheet=st.secrets["sheets"]["facility_setting"],
    ttl=0,
)
facility_setting.columns = facility_setting.columns.str.strip()

# =========================
# 管理画面
# =========================

# if mode == "admin":
#     run_facility_admin(
#         st,
#         conn,
#         facility_setting,
#         st.secrets["sheets"]["facility_setting"],
#     )
#     st.stop()

# 通常画面で使う残りのマスターを読む
point_master = conn.read(
    worksheet=st.secrets["sheets"]["point_master"],
    ttl=0,
)

housecall_master = conn.read(
    worksheet=st.secrets["sheets"]["housecall_master"],
    ttl=0,
)

add_master = conn.read(
    worksheet=st.secrets["sheets"]["add_master"],
    ttl=0,
)

for df in [
    point_master,
    housecall_master,
    add_master,
]:
    df.columns = df.columns.str.strip()


# =========================
# 施設設定
# =========================

# URL例:
# https://xxxx.streamlit.app/?facility=f_7a9c2e81

facility_id = st.query_params.get("facility")

if not facility_id:
    st.error(
        "施設IDが指定されていません。"
        "配布された専用URLからアクセスしてください。"
    )
    st.stop()

facility_rows = facility_setting[
    (
        facility_setting["facility_id"]
        .astype(str)
        .str.strip()
        == str(facility_id).strip()
    )
    & (
        facility_setting["active"]
        .astype(str)
        .str.strip()
        == "はい"
    )
]

if facility_rows.empty:
    st.error(
        "施設設定が見つからないか、"
        "現在利用停止になっています。"
    )
    st.stop()

setting = facility_rows.iloc[0]

facility_name = str(
    setting["facility_name"]
).strip()

support_type = str(
    setting["home_care_support_type"]
).strip()

enhanced_type = str(
    setting["enhanced_type"]
).strip()

bed_status = str(
    setting["bed_status"]
).strip()

housecall_support_class = str(
    setting["housecall_support_class"]
).strip()


# 医療機関区分
if (
    support_type != "なし"
    and enhanced_type == "はい"
    and bed_status == "あり"
):
    facility_class = "FUNC_BED"

elif (
    support_type != "なし"
    and enhanced_type == "はい"
    and bed_status == "なし"
):
    facility_class = "FUNC_NOBED"

elif (
    support_type != "なし"
    and enhanced_type == "いいえ"
):
    facility_class = "SUPPORT"

elif support_type == "なし":
    facility_class = "OTHER"

else:
    facility_class = "判定不能"


# =========================
# タイトル
# =========================

st.title("在宅医療 算定支援")
st.caption(
    "患者・訪問条件を入力すると、算定候補を判定します。"
)


# =========================
# 施設情報表示
# =========================

st.subheader("施設情報")

st.caption(
    f"施設：{facility_name}"
)

facility_class_label = {
    "FUNC_BED": "機能強化型在支診・在支病（病床あり）",
    "FUNC_NOBED": "機能強化型在支診・在支病（病床なし）",
    "SUPPORT": "在支診・在支病",
    "OTHER": "その他",
    "判定不能": "判定不能",
}.get(
    facility_class,
    facility_class,
)

housecall_support_label = {
    "SOLO_ENHANCED": "単独型機能強化型",
    "GROUP_ENHANCED": "連携型機能強化型",
    "CONVENTIONAL_SUPPORT": "従来型在支診・在支病",
    "OTHER": "その他",
}.get(
    housecall_support_class,
    housecall_support_class,
)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div style="
            padding: 14px 16px;
            border: 1px solid #dddddd;
            border-radius: 10px;
            min-height: 90px;
        ">
            <div style="font-size:14px; color:#666666;">
                医療機関区分
            </div>
            <div style="
                font-size:20px;
                font-weight:600;
                margin-top:8px;
                line-height:1.4;
            ">
                {facility_class_label}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div style="
            padding: 14px 16px;
            border: 1px solid #dddddd;
            border-radius: 10px;
            min-height: 90px;
        ">
            <div style="font-size:14px; color:#666666;">
                往診支援区分
            </div>
            <div style="
                font-size:20px;
                font-weight:600;
                margin-top:8px;
                line-height:1.4;
            ">
                {housecall_support_label}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with st.expander(
    "届出・施設設定を見る",
    expanded=False,
):
    home_dx_class = str(
        setting["home_dx_class"]
    ).strip()

    st.write(
        f"**在宅医療DX情報活用加算：** "
        f"区分 {home_dx_class}"
        if home_dx_class not in ["", "なし", "nan"]
        else "**在宅医療DX情報活用加算：** — なし"
    )

    st.write(
        "**在宅医療情報連携：**",
        yes_no_icon(
            setting["home_info_link"]
        ),
    )

    st.write(
        "**在宅データ提出：**",
        yes_no_icon(
            setting["home_data_submission"]
        ),
    )

    st.write(
        f"**機能強化型：** "
        f"{str(setting['enhanced_type']).strip()}"
    )

    st.write(
        f"**病床：** "
        f"{str(setting['bed_status']).strip()}"
    )


if facility_class == "判定不能":
    st.warning(
        "施設設定から医療機関区分を判定できません。"
        "施設設定シートを確認してください。"
    )
    st.stop()

st.caption(
    "※ 上記の施設設定を前提に算定候補を判定します。"
)


# =========================
# Q001 通院困難
# =========================

st.divider()

q001 = st.radio(
    "患者は通院困難ですか？",
    ["選択してください", "はい", "いいえ"],
    key="q001",
)

if q001 == "選択してください":
    st.stop()

if q001 == "いいえ":
    st.warning(
        "在宅患者訪問診療料の対象外となる可能性があります。"
    )
    st.stop()


# =========================
# Q002 訪問種別
# =========================

q002 = st.radio(
    "今回は計画的な訪問診療ですか？",
    ["選択してください", "はい", "いいえ"],
    key="q002",
)

if q002 == "選択してください":
    st.stop()

visit_route = (
    "訪問診療"
    if q002 == "はい"
    else "往診"
)


# =========================
# ルート分岐
# =========================

if visit_route == "往診":
    run_housecall_route(
        st,
        housecall_master,
        facility_class,
        housecall_support_class,
    )
    st.stop()


run_visit_route(
    st,
    point_master,
    add_master,
    facility_class,
    setting,
)
