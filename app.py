import streamlit as st

from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="在宅医療 算定支援",
    page_icon="🏠",
    layout="centered"
)


conn = st.connection("gsheets", type=GSheetsConnection)

point_master = conn.read(
#    worksheet="point_master",
#    ttl=0

)

st.subheader("Googleスプレッドシート接続テストOK")
#st.dataframe(point_master.head())

st.title("在宅医療 算定支援")
st.caption("患者・訪問条件を入力すると、算定候補を判定します。")

# -------------------------
# 1. 通院困難
# -------------------------
q001 = st.radio(
    "患者は通院困難ですか？",
    ["選択してください", "はい", "いいえ"],
    key="q001"
)

if q001 == "いいえ":
    st.warning("在宅患者訪問診療料の対象外となる可能性があります。")
    st.stop()

if q001 == "選択してください":
    st.stop()


# -------------------------
# 2. 計画的訪問
# -------------------------
q002 = st.radio(
    "今回は計画的な訪問診療ですか？",
    ["選択してください", "はい", "いいえ"],
    key="q002"
)

if q002 == "いいえ":
    st.info("定期訪問診療ではなく、往診ルートで判定します。")
    st.stop()

if q002 == "選択してください":
    st.stop()


# -------------------------
# 3. 療養場所
# -------------------------
q003 = st.radio(
    "療養場所はどこですか？",
    ["選択してください", "個人宅", "施設"],
    key="q003"
)

if q003 == "選択してください":
    st.stop()

if q003 == "施設":
    st.info("施設ルートは今後追加します。")
    st.stop()


# -------------------------
# 次の画面へ
# -------------------------
st.success("定期訪問診療・個人宅ルートです。")

st.subheader("ここまでの入力")

st.write({
    "通院困難": q001,
    "計画的訪問診療": q002,
    "療養場所": q003,
})

st.divider()

# -------------------------
# 4. 同一患家
# -------------------------
q010 = st.radio(
    "同じ患家で、同じ日に他の患者も診療しますか？",
    ["選択してください", "はい", "いいえ"],
    key="q010"
)

if q010 == "選択してください":
    st.stop()

q011 = None

if q010 == "はい":
    q011 = st.radio(
        "この患者は同一患家で何人目の診療ですか？",
        ["選択してください", "1人目", "2人目以降"],
        key="q011"
    )

    if q011 == "選択してください":
        st.stop()

    if q011 == "2人目以降":
        st.warning(
            "同一患家の2人目以降です。"
            "在宅患者訪問診療料ではなく、別の算定判定が必要です。"
        )


# -------------------------
# 5. 単一建物診療患者数
# -------------------------
q009 = st.selectbox(
    "単一建物診療患者数は何人ですか？",
    [
        "選択してください",
        "1",
        "2-9",
        "10-19",
        "20-49",
        "50以上"
    ],
    key="q009"
)

if q009 == "選択してください":
    st.stop()


# -------------------------
# 6. 今月の訪問診療回数
# -------------------------
visit_count = st.number_input(
    "今月の実際の訪問診療回数は何回ですか？",
    min_value=1,
    max_value=31,
    value=1,
    step=1
)

if visit_count == 1:
    frequency_group = "1回"
else:
    frequency_group = "2回以上"


# -------------------------
# 入力内容の確認
# -------------------------
st.subheader("入力内容")

st.write({
    "通院困難": q001,
    "計画的訪問診療": q002,
    "療養場所": q003,
    "同一患家で他患者を診療": q010,
    "同一患家での順番": q011,
    "単一建物診療患者数": q009,
    "今月の訪問診療回数": visit_count,
    "訪問回数区分": frequency_group,
})

# -------------------------
# 7. 在医総管の区分判定
# -------------------------

st.subheader("在医総管の判定")

q012 = "いいえ"
q013 = "いいえ"
q014 = "いいえ"

if visit_count >= 2:
    q012 = st.radio(
        "別表第8の2に該当しますか？",
        ["選択してください", "はい", "いいえ"],
        key="q012"
    )

    if q012 == "選択してください":
        st.stop()

    if q012 == "いいえ":
        q013 = st.radio(
            "月2回以上訪問区分の要件を満たしますか？",
            ["選択してください", "はい", "いいえ"],
            key="q013"
        )

        if q013 == "選択してください":
            st.stop()

        if q013 == "はい":
            q014 = st.radio(
                "今月、情報通信機器を用いた診療がありますか？",
                ["選択してください", "はい", "いいえ"],
                key="q014"
            )

            if q014 == "選択してください":
                st.stop()


# -------------------------
# frequency_class を決定
# -------------------------

if visit_count == 1:
    frequency_class = "M1"

elif q012 == "はい":
    frequency_class = "M2_SEVERE"

elif q013 == "いいえ":
    frequency_class = "M1"

elif q014 == "はい":
    frequency_class = "M2_ONLINE"

else:
    frequency_class = "M2"


st.success(f"在医総管の判定区分：{frequency_class}")
# -------------------------
# 8. 在医総管の点数計算
# -------------------------

zaisokan_points = {
    "OTHER": {
        "M1": {
            "1": 1745,
            "2-9": 980,
            "10-19": 545,
            "20-49": 455,
            "50以上": 395,
        },
        "M2": {
            "1": 2735,
            "2-9": 1460,
            "10-19": 735,
            "20-49": 655,
            "50以上": 555,
        },
        "M2_SEVERE": {
            "1": 3435,
            "2-9": 2820,
            "10-19": 1785,
            "20-49": 1500,
            "50以上": 1315,
        },
        "M2_ONLINE": {
            "1": 2014,
            "2-9": 1165,
            "10-19": 645,
            "20-49": 573,
            "50以上": 487,
        }
    }
}

facility_class = "OTHER"

try:
    zaisokan_point = zaisokan_points[facility_class][frequency_class][q009]

    st.subheader("在医総管 点数")
    st.metric(
        label="在医総管",
        value=f"{zaisokan_point:,} 点"
    )

except KeyError:
    st.warning("この条件の点数マスターがまだ登録されていません。")

# -------------------------
# 9. 訪問診療料
# -------------------------

same_building = st.radio(
    "同一建物居住者に該当しますか？",
    ["選択してください", "はい", "いいえ"],
    key="same_building"
)

if same_building == "選択してください":
    st.stop()

if same_building == "はい":
    visit_fee = 215
else:
    visit_fee = 890

st.subheader("訪問診療料")
st.metric(
    label="1回あたり",
    value=f"{visit_fee:,} 点"
)

# 今月の訪問診療料合計
visit_fee_month = visit_fee * visit_count

st.metric(
    label="今月の訪問診療料合計",
    value=f"{visit_fee_month:,} 点"
)


# -------------------------
# 10. 基本算定合計
# -------------------------

basic_total = zaisokan_point + visit_fee_month

st.subheader("基本算定合計")

st.metric(
    label="在医総管＋訪問診療料",
    value=f"{basic_total:,} 点"
)

st.write({
    "在医総管": f"{zaisokan_point:,}点",
    "訪問診療料1回": f"{visit_fee:,}点",
    "訪問回数": visit_count,
    "訪問診療料月合計": f"{visit_fee_month:,}点",
    "基本算定合計": f"{basic_total:,}点"
})

# -------------------------
# 11. 主要加算
# -------------------------

st.subheader("主要加算")

support_add = st.radio(
    "包括的支援加算の対象ですか？",
    ["選択してください", "はい", "いいえ"],
    key="support_add"
)

if support_add == "選択してください":
    st.stop()

support_add_point = 150 if support_add == "はい" else 0


dx_class = st.selectbox(
    "在宅医療DX情報活用加算の区分",
    ["なし", "1", "2"],
    key="dx_class"
)

if dx_class == "1":
    dx_point = 11
elif dx_class == "2":
    dx_point = 9
else:
    dx_point = 0


info_link_add = st.radio(
    "在宅医療情報連携加算の対象ですか？",
    ["選択してください", "はい", "いいえ"],
    key="info_link_add"
)

if info_link_add == "選択してください":
    st.stop()

info_link_point = 100 if info_link_add == "はい" else 0


data_submit_add = st.radio(
    "在宅データ提出加算の対象ですか？",
    ["選択してください", "はい", "いいえ"],
    key="data_submit_add"
)

if data_submit_add == "選択してください":
    st.stop()

data_submit_point = 50 if data_submit_add == "はい" else 0


# -------------------------
# 12. 最終合計
# -------------------------

add_total = (
    support_add_point
    + dx_point
    + info_link_point
    + data_submit_point
)

final_total = basic_total + add_total

st.subheader("算定結果")

st.write({
    "在医総管": f"{zaisokan_point:,}点",
    "訪問診療料": f"{visit_fee_month:,}点",
    "包括的支援加算": f"{support_add_point:,}点",
    "在宅医療DX情報活用加算": f"{dx_point:,}点",
    "在宅医療情報連携加算": f"{info_link_point:,}点",
    "在宅データ提出加算": f"{data_submit_point:,}点",
})

st.metric(
    label="医療保険 合計",
    value=f"{final_total:,} 点"
)

# -------------------------
# 13. 介護保険
# -------------------------

st.subheader("介護保険")

care_cert = st.radio(
    "要介護または要支援認定がありますか？",
    ["選択してください", "はい", "いいえ"],
    key="care_cert"
)

if care_cert == "選択してください":
    st.stop()

care_units = 0
care_item = None

if care_cert == "はい":

    care_info = st.radio(
        "ケアマネジャー等へ必要な情報提供を行いましたか？",
        ["選択してください", "はい", "いいえ"],
        key="care_info"
    )

    if care_info == "選択してください":
        st.stop()

    care_advice = st.radio(
        "本人または家族へ、介護上の指導・助言を行いましたか？",
        ["選択してください", "はい", "いいえ"],
        key="care_advice"
    )

    if care_advice == "選択してください":
        st.stop()

    if care_info == "はい" and care_advice == "はい":

        if q009 == "1":
            care_units = 299
        elif q009 == "2-9":
            care_units = 287
        else:
            care_units = 260

        care_item = "居宅療養管理指導費（Ⅱ）"

        st.success(
            f"{care_item}：{care_units} 単位"
        )

    else:
        st.warning(
            "居宅療養管理指導費の算定要件を満たしているか確認が必要です。"
        )

else:
    st.info("介護保険側の算定はありません。")

# -------------------------
# 14. 最終結果まとめ
# -------------------------

st.divider()
st.header("最終結果")

st.subheader("医療保険")

st.write(f"在医総管：{zaisokan_point:,} 点")
st.write(f"訪問診療料：{visit_fee_month:,} 点")

if support_add_point > 0:
    st.write(f"包括的支援加算：{support_add_point:,} 点")

if dx_point > 0:
    st.write(f"在宅医療DX情報活用加算：{dx_point:,} 点")

if info_link_point > 0:
    st.write(f"在宅医療情報連携加算：{info_link_point:,} 点")

if data_submit_point > 0:
    st.write(f"在宅データ提出加算：{data_submit_point:,} 点")

st.metric(
    "医療保険 合計",
    f"{final_total:,} 点"
)


# -------------------------
# 介護保険
# -------------------------

st.subheader("介護保険")

if care_item is not None:
    st.write(f"{care_item}：{care_units:,} 単位")
else:
    st.write("算定候補なし")


# -------------------------
# 判定根拠
# -------------------------

st.subheader("判定条件")

st.write(f"療養場所：{q003}")
st.write(f"単一建物診療患者数：{q009}")
st.write(f"今月の訪問診療回数：{visit_count} 回")
st.write(f"在医総管区分：{frequency_class}")
st.write(f"医療機関区分：{facility_class}")


# -------------------------
# 注意事項
# -------------------------

st.subheader("確認事項")

if q010 == "はい" and q011 == "2人目以降":
    st.warning(
        "同一患家の2人目以降です。"
        "訪問診療料の算定方法を別途確認してください。"
    )

if frequency_class == "M1" and visit_count >= 2:
    st.warning(
        "実際の訪問回数は2回以上ですが、"
        "在医総管は月1回区分として判定されています。"
    )

st.caption(
    "この結果は算定候補の確認用です。"
    "実際の請求時には診療報酬点数表・通知等を確認してください。"
)