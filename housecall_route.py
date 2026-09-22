def run_housecall_route(
    st,
    housecall_master,
    facility_class,
    housecall_support_class
):
    # -------------------------
    # 往診ルート
    # -------------------------

    st.divider()
    st.header("往診の算定判定")

    # 基本の往診料
    base_row = housecall_master[
        housecall_master["call_type"] == "BASE"
    ]

    housecall_base = int(base_row.iloc[0]["points"])

    st.metric(
        "往診料",
        f"{housecall_base:,} 点"
    )

    st.subheader("往診加算の患者区分「別に定める患者」")

    special_1 = st.radio(
            "過去60日以内に、当院で在宅患者訪問診療料（Ⅰ）・（Ⅱ）または在宅がん医療総合診療料を算定していますか？",
            ["いいえ", "はい"],
            key="special_1"
    )

    special_2 = st.radio(
            "過去60日以内に、当院と連携する他の医療機関で在宅患者訪問診療料（Ⅰ）・（Ⅱ）または在宅がん医療総合診療料を算定していますか？",
            ["いいえ", "はい"],
            key="special_2"
    )

    special_3 = st.radio(
            "当院の外来で継続的に診療を受けている患者ですか？",
            ["いいえ", "はい"],
            key="special_3"
    )

    special_4 = st.radio(
            "当院と平時から連携している老健・介護医療院・特別養護老人ホームの入所患者ですか？",
            ["いいえ", "はい"],
            key="special_4"
    )

    special_patient = (
            special_1 == "はい"
            or special_2 == "はい"
            or special_3 == "はい"
            or special_4 == "はい"
    )

    if special_patient:
        patient_class = "SPECIAL"
    else:
        patient_class = "NORMAL"

    if special_patient == "選択してください":
        st.stop()

    housecall_type = st.radio(
        "今回の往診区分を選択してください",
        [
            "通常の往診",
            "緊急往診",
            "夜間・休日往診",
            "深夜往診"
        ],
        index=None,
        key="housecall_type"
    )

    if housecall_type is None:
        st.stop()

    if housecall_type == "通常の往診":
        call_type = "NORMAL"

    elif housecall_type == "緊急往診":
        call_type = "EMERGENCY"

    elif housecall_type == "夜間・休日往診":
        call_type = "NIGHT_HOLIDAY"

    elif housecall_type == "深夜往診":
        call_type = "LATE_NIGHT"

    housecall_add = 0

    if call_type != "NORMAL":

        if patient_class == "SPECIAL":
            add_row = housecall_master[
                (housecall_master["patient_class"] == "SPECIAL")
                & (housecall_master["facility_class"] == facility_class)
                & (housecall_master["call_type"] == call_type)
            ]

        else:
            add_row = housecall_master[
                (housecall_master["patient_class"] == "NORMAL")
                & (housecall_master["facility_class"] == "ALL")
                & (housecall_master["call_type"] == call_type)
            ]

        if not add_row.empty:
            housecall_add = int(add_row.iloc[0]["points"])
        else:
            st.warning("該当する往診加算がマスターにありません。")

    # -------------------------
    # 患家診療時間加算
    # -------------------------

    visit_minutes = st.number_input(
        "患家での診療時間は何分ですか？",
        min_value=1,
        max_value=300,
        value=30,
        step=5,
        key="housecall_minutes"
    )

    long_time_point = 0

    if visit_minutes > 60:
        extra_minutes = visit_minutes - 60
        extra_units = (extra_minutes + 29) // 30
        long_time_point = extra_units * 100

    # -------------------------
    # 死亡診断加算
    # -------------------------

    death_cert = st.radio(
        "死亡診断加算の対象ですか？",
        ["いいえ", "はい"],
        key="death_cert"
    )

    death_cert_point = 200 if death_cert == "はい" else 0

    # -------------------------
    # 往診時医療情報連携加算
    # -------------------------

    st.subheader("往診時医療情報連携加算")

    regular_provider = st.radio(
        "この患者は、他の医療機関が主治医として計画的に定期訪問診療を行っていますか？",
        ["いいえ", "はい"],
        key="regular_provider"
    )

    info_link_point = 0

    if regular_provider == "はい":

        regular_provider_class = st.selectbox(
            "平時に訪問診療を行っている医療機関の区分は？",
            [
                "選択してください",
                "単独型機能強化型",
                "連携型機能強化型",
                "従来型在支診・在支病",
                "その他"
            ],
            key="regular_provider_class"
        )

        provider_class_map = {
            "単独型機能強化型": "SOLO_ENHANCED",
            "連携型機能強化型": "GROUP_ENHANCED",
            "従来型在支診・在支病": "CONVENTIONAL_SUPPORT",
            "その他": "OTHER"
        }

        if regular_provider_class != "選択してください":

            supported_class = provider_class_map[
                regular_provider_class
            ]

            support_side_ok = housecall_support_class in [
                "SOLO_ENHANCED",
                "GROUP_ENHANCED",
                "CONVENTIONAL_SUPPORT"
            ]

            supported_side_ok = supported_class in [
                "CONVENTIONAL_SUPPORT",
                "OTHER"
            ]

            if support_side_ok and supported_side_ok:
                info_link_point = 200
                st.success(
                    "往診時医療情報連携加算：算定候補 200点"
                )
                st.write(
                    "自院で訪問診療を行っている患者について、連携医療機関の医師が往診を行う際に、事前に診療情報を提供した場合に算定、連携先が機能強化型でない在宅療養支援診療所・在宅療養支援病院であっても算定可能（従来型の在支診・在支病同士の連携でも加算が取れる）\n\nこの場合、当該他の保険医療機関の名称、参考にした当該患者の診療情報及び当該患者の病状の急変時の対応方針等及び診療の要点を診療録に記録すること。"
                )
            else:
                st.info(
                    "この医療機関の組み合わせでは、"
                    "往診時医療情報連携加算の対象外候補です。"
                )

    #info_link_point = 200 if info_link == "はい" else 0

    # -------------------------
    # 介護保険施設等連携往診加算
    # -------------------------

    st.subheader("介護保険施設等連携往診加算")

    care_facility_patient = st.radio(
        "患者は介護保険施設等の入所者ですか？",
        ["いいえ", "はい"],
        key="care_facility_patient"
    )

    care_facility_add_point = 0

    if care_facility_patient == "はい":

        acute_change = st.radio(
            "今回は病状の急変等に伴う往診ですか？",
            ["いいえ", "はい"],
            key="care_facility_acute_change"
        )

        cooperation_provider = st.radio(
            "当院は当該施設の協力医療機関として定められていますか？",
            ["いいえ", "はい"],
            key="care_facility_cooperation"
        )

        contact_24h = st.radio(
            "当該施設から24時間連絡を受けることができる体制がありますか？",
            ["いいえ", "はい"],
            key="care_facility_contact_24h"
        )

        housecall_24h = st.radio(
            "当該施設の求めに応じて24時間往診できる体制がありますか？",
            ["いいえ", "はい"],
            key="care_facility_housecall_24h"
        )

        facility_request = st.radio(
            "今回は施設の従事者等からの求めに応じて往診しましたか？",
            ["いいえ", "はい"],
            key="care_facility_request"
        )

        info_used = st.radio(
            "患者の診療情報・病状急変時の対応方針等を踏まえて往診しましたか？",
            ["いいえ", "はい"],
            key="care_facility_info"
        )

        explanation_done = st.radio(
            "治療方針について患者または家族等へ十分に説明しましたか？",
            ["いいえ", "はい"],
            key="care_facility_explanation"
        )

        if all([
            acute_change == "はい",
            cooperation_provider == "はい",
            contact_24h == "はい",
            housecall_24h == "はい",
            facility_request == "はい",
            info_used == "はい",
            explanation_done == "はい"
        ]):
            care_facility_add_point = 200
            st.success("介護保険施設等連携往診加算：算定候補 200点")
            st.write(
                "介護老人保健施設、介護医療院及び特別養護老人ホーム（以下この注において「介護保険施設等」という。）の協力医療機関であって、当該介護保険施設等に入所している患者の病状の急変等に伴い、往診を行った場合に、介護保険施設等連携往診加算として、200点を所定点数に加算する。\n\n介護老人保健施設、介護医療院及び特別養護老人ホーム（当該保険医療機関と特別の関係にあるものを除く。以下この項において「介護保険施設等」という。）において療養を行っている患者の病状の急変等に伴い、当該介護保険施設等の従事者等の求めに応じて事前に共有されている当該患者に関する診療情報及び病状の急変時の対応方針等を踏まえて往診を行った際に、提供する医療の内容について患者又は当該介護保険施設等の従事者に十分に説明した場合に限り算定でき る。この場合、介護保険施設等の名称、活用した当該患者の診療情報、急変時の対応方針及び診療の要点を診療録に記録すること。なお、この項において「特別の関係」とは、当該保険医療機関と介護保険施設等の関係が以下のいずれかに該当する場合は特別の関係にあると認められる。\n\nア 当該保険医療機関の開設者が、当該介護保険施設等の開設者と同一の場合  イ 当該保険医療機関の代表者が、当該介護保険施設等の代表者と同一の場合  ウ 当該保険医療機関の代表者が、当該介護保険施設等の代表者の親族等の場合  エ 当該保険医療機関の理事・監事・評議員その他の役員等のうち、当該介護保険施設等の役員等の親族等の占める割合が 10 分の３を超える場合  オ アからエまでに掲げる場合に準ずる場合（人事、資金等の関係を通じて、当該保険医療機関が、当該介護保険施設等の経営方針に対して重要な影響を与えることができると認められる場合に限る。）"
            )
        else:
            st.info("介護保険施設等連携往診加算：要件を満たさない候補")

    # -------------------------
    # 合計
    # -------------------------

    housecall_total = (
        housecall_base
        + housecall_add
        + long_time_point
        + death_cert_point
        + info_link_point
        + care_facility_add_point
    )

#カード型
# =========================
# 往診 結果カード
# =========================

    st.divider()
    st.header("往診 算定結果")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="基本往診料",
            value=f"{housecall_base:,} 点"
        )

    with col2:
        st.metric(
            label="往診合計",
            value=f"{housecall_total:,} 点"
        )

    st.subheader("算定候補")

    result_items = []

    result_items.append(
        ("往診料", housecall_base)
    )

    if housecall_add > 0:
        result_items.append(
            (f"{housecall_type}加算", housecall_add)
        )

    if long_time_point > 0:
        result_items.append(
            ("患家診療時間加算", long_time_point)
        )

    if info_link_point > 0:
        result_items.append(
            ("往診時医療情報連携加算", info_link_point)
        )

    if care_facility_add_point > 0:
        result_items.append(
            ("介護保険施設等連携往診加算", care_facility_add_point)
        )

    if death_cert_point > 0:
        result_items.append(
            ("死亡診断加算", death_cert_point)
        )

    for item_name, item_point in result_items:
        st.markdown(
            f"""
            <div style="
                padding: 12px 16px;
                margin-bottom: 8px;
                border: 1px solid #dddddd;
                border-radius: 10px;
                background-color: #fafafa;
            ">
                <strong>{item_name}</strong>
                <span style="float:right;">
                    {item_point:,} 点
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

#追加
    # # =========================
    # # 往診 結果まとめ
    # # =========================

    # st.divider()
    # st.header("往診 算定結果")

    # # -------------------------
    # # 算定項目
    # # -------------------------

    # st.subheader("算定候補")

    # st.write(f"往診料：{housecall_base:,} 点")

    # if housecall_add > 0:
    #     st.write(
    #         f"{housecall_type}加算：{housecall_add:,} 点"
    #     )

    # if long_time_point > 0:
    #     st.write(
    #         f"患家診療時間加算：{long_time_point:,} 点"
    #     )

    # if info_link_point > 0:
    #     st.write(
    #         f"往診時医療情報連携加算：{info_link_point:,} 点"
    #     )

    # if care_facility_add_point > 0:
    #     st.write(
    #         f"介護保険施設等連携往診加算："
    #         f"{care_facility_add_point:,} 点"
    #     )

    # if death_cert_point > 0:
    #     st.write(
    #         f"死亡診断加算：{death_cert_point:,} 点"
    #     )

    # st.metric(
    #     "往診 合計",
    #     f"{housecall_total:,} 点"
    # )

    # -------------------------
    # 判定根拠
    # -------------------------
    with st.expander("判定根拠を見る"):

        if patient_class == "SPECIAL":
            st.write("✓ 往診加算上の「別に定める患者」に該当")

            if special_1 == "はい":
                st.write("・過去60日以内に当院で訪問診療等を算定")

            if special_2 == "はい":
                st.write("・過去60日以内に連携医療機関で訪問診療等を算定")

            if special_3 == "はい":
                st.write("・当院外来で継続的に診療")

            if special_4 == "はい":
                st.write("・平時から連携する介護保険施設等の入所患者")

        else:
            st.write("・「別に定める患者」には非該当")
        st.write(
        "往診加算上の「別に定める患者」\n\n一の三の二　往診料に規定する別に厚生労働大臣が定める患者\n\n次のいずれかに該当するものであること。\n\n(１)　往診を行う保険医療機関において過去六十日以内に在宅患者訪問診療料(Ⅰ)、在宅患者訪問診療料(Ⅱ)又は在宅がん医療総合診療料を算定しているもの\n\n(２)　往診を行う保険医療機関と連携体制を構築している他の保険医療機関において、過去六十日以内に在宅患者訪問診療料(Ⅰ)、在宅患者訪問診療料(Ⅱ)又は在宅がん医療総合診療料を算定しているもの\n\n(３)　往診を行う保険医療機関の外来において継続的に診療を受けている患者\n\n(４)　往診を行う保険医療機関と平時からの連携体制を構築している介護老人保健施設、介護医療院及び特別養護老人ホームに入所する患者"
        )
    
        st.write(f"・医療機関区分：{facility_class}")
        st.write(f"・往診区分：{housecall_type}")
        st.write(f"・患家での診療時間：{visit_minutes}分")

#ここからはもともと


    # st.subheader("判定根拠")

    # if patient_class == "SPECIAL":
    #     st.write(
    #         "往診加算上の「別に定める患者」に該当"
    #     )
        
    # else:
    #     st.write(
    #         "往診加算上の「別に定める患者」には非該当"
    #     )

    # st.write(
    #     "往診加算上の「別に定める患者」\n\n一の三の二　往診料に規定する別に厚生労働大臣が定める患者\n\n次のいずれかに該当するものであること。\n\n(１)　往診を行う保険医療機関において過去六十日以内に在宅患者訪問診療料(Ⅰ)、在宅患者訪問診療料(Ⅱ)又は在宅がん医療総合診療料を算定しているもの\n\n(２)　往診を行う保険医療機関と連携体制を構築している他の保険医療機関において、過去六十日以内に在宅患者訪問診療料(Ⅰ)、在宅患者訪問診療料(Ⅱ)又は在宅がん医療総合診療料を算定しているもの\n\n(３)　往診を行う保険医療機関の外来において継続的に診療を受けている患者\n\n(４)　往診を行う保険医療機関と平時からの連携体制を構築している介護老人保健施設、介護医療院及び特別養護老人ホームに入所する患者"
    # )

    # st.write(
    #     f"・医療機関区分：{facility_class}"
    # )

    # st.write(
    #     f"・往診区分：{housecall_type}"
    # )

    # st.write(
    #     f"・患家での診療時間：{visit_minutes}分"
    # )

    # if special_1 == "はい":
    #     st.write(
    #         "　→ 過去60日以内に当院で訪問診療等を算定"
    #     )

    # if special_2 == "はい":
    #     st.write(
    #         "　→ 過去60日以内に連携医療機関で訪問診療等を算定"
    #     )

    # if special_3 == "はい":
    #     st.write(
    #         "　→ 当院外来で継続的に診療"
    #     )

    # if special_4 == "はい":
    #     st.write(
    #         "　→ 平時から連携する介護保険施設等の入所患者"
    #     )
#ここまで

    # -------------------------
    # 確認事項・非該当理由
    # -------------------------

    notes = []

    with st.expander("確認事項"):

        st.write(
        "**往診時医療情報連携加算**\n\n自院で訪問診療を行っている患者について、連携医療機関の医師が往診を行う際に、事前に診療情報を提供した場合に算定、連携先が機能強化型でない在宅療養支援診療所・在宅療養支援病院であっても算定可能（従来型の在支診・在支病同士の連携でも加算OK、連携先が機能強化型の場合はNG）\n\nこの場合、当該他の保険医療機関の名称、参考にした当該患者の診療情報及び当該患者の病状の急変時の対応方針等及び診療の要点を診療録に記録すること。"
        )

        st.write(
            "**介護保険施設等連携往診加算**\n\n介護老人保健施設、介護医療院及び特別養護老人ホーム（以下この注において「介護保険施設等」という。）の協力医療機関であって、当該介護保険施設等に入所している患者の病状の急変等に伴い、往診を行った場合に、介護保険施設等連携往診加算として、200点を所定点数に加算する。 介護老人保健施設、介護医療院及び特別養護老人ホーム（当該保険医療機関と特別の関係にあるものを除く。以下この項において「介護保険施設等」という。）において療養を行っている患者の病状の急変等に伴い、当該介護保険施設等の従事者等の求めに応じて事前に共有されている当該患者に関する診療情報及び病状の急変時の対応方針等を踏まえて往診を行った際に、提供する医療の内容について患者又は当該介護保険施設等の従事者に十分に説明した場合に限り算定でき る。この場合、介護保険施設等の名称、活用した当該患者の診療情報、急変時の対応方針及び診療の要点を診療録に記録すること。なお、この項において「特別の関係」とは、当該保険医療機関と介護保険施設等の関係が以下のいずれかに該当する場合は特別の関係にあると認められる。\n\nア 当該保険医療機関の開設者が、当該介護保険施設等の開設者と同一の場合  イ 当該保険医療機関の代表者が、当該介護保険施設等の代表者と同一の場合  ウ 当該保険医療機関の代表者が、当該介護保険施設等の代表者の親族等の場合  エ 当該保険医療機関の理事・監事・評議員その他の役員等のうち、当該介護保険施設等の役員等の親族等の占める割合が 10 分の３を超える場合  オ アからエまでに掲げる場合に準ずる場合（人事、資金等の関係を通じて、当該保険医療機関が、当該介護保険施設等の経営方針に対して重要な影響を与えることができると認められる場合に限る。）"
        )    

        if notes:
            for note in notes:
                st.info(note)
        else:
            st.success("追加の確認事項はありません。")

    # st.subheader("確認事項")

    # notes = []

    # # 往診時医療情報連携加算
    # if regular_provider == "はい" and info_link_point == 0:
    #     notes.append(
    #         "往診時医療情報連携加算："
    #         "医療機関の組み合わせ等の要件を満たしていない可能性があります。"
    #     )

    # st.write(
    #     "**往診時医療情報連携加算**\n\n自院で訪問診療を行っている患者について、連携医療機関の医師が往診を行う際に、事前に診療情報を提供した場合に算定、連携先が機能強化型でない在宅療養支援診療所・在宅療養支援病院であっても算定可能（従来型の在支診・在支病同士の連携でも加算OK、連携先が機能強化型の場合はNG）\n\nこの場合、当該他の保険医療機関の名称、参考にした当該患者の診療情報及び当該患者の病状の急変時の対応方針等及び診療の要点を診療録に記録すること。"
    # )

    # # 介護保険施設等連携往診加算
    # if care_facility_patient == "はい" and care_facility_add_point == 0:
    #     notes.append(
    #         "介護保険施設等連携往診加算："
    #         "協力医療機関・24時間対応・施設からの求め等の"
    #         "いずれかの要件を満たしていません。"
    #     )
    # st.write(
    #     "**介護保険施設等連携往診加算**\n\n介護老人保健施設、介護医療院及び特別養護老人ホーム（以下この注において「介護保険施設等」という。）の協力医療機関であって、当該介護保険施設等に入所している患者の病状の急変等に伴い、往診を行った場合に、介護保険施設等連携往診加算として、200点を所定点数に加算する。 介護老人保健施設、介護医療院及び特別養護老人ホーム（当該保険医療機関と特別の関係にあるものを除く。以下この項において「介護保険施設等」という。）において療養を行っている患者の病状の急変等に伴い、当該介護保険施設等の従事者等の求めに応じて事前に共有されている当該患者に関する診療情報及び病状の急変時の対応方針等を踏まえて往診を行った際に、提供する医療の内容について患者又は当該介護保険施設等の従事者に十分に説明した場合に限り算定でき る。この場合、介護保険施設等の名称、活用した当該患者の診療情報、急変時の対応方針及び診療の要点を診療録に記録すること。なお、この項において「特別の関係」とは、当該保険医療機関と介護保険施設等の関係が以下のいずれかに該当する場合は特別の関係にあると認められる。\n\nア 当該保険医療機関の開設者が、当該介護保険施設等の開設者と同一の場合  イ 当該保険医療機関の代表者が、当該介護保険施設等の代表者と同一の場合  ウ 当該保険医療機関の代表者が、当該介護保険施設等の代表者の親族等の場合  エ 当該保険医療機関の理事・監事・評議員その他の役員等のうち、当該介護保険施設等の役員等の親族等の占める割合が 10 分の３を超える場合  オ アからエまでに掲げる場合に準ずる場合（人事、資金等の関係を通じて、当該保険医療機関が、当該介護保険施設等の経営方針に対して重要な影響を与えることができると認められる場合に限る。）"
    # )

    # # 患家診療時間加算
    # if visit_minutes <= 60:
    #     notes.append(
    #         "患家診療時間加算：診療時間が60分以内のため算定なし。"
    #     )

    # # 死亡診断
    # if death_cert == "いいえ":
    #     notes.append(
    #         "死亡診断加算：対象外。"
    #     )

    # if notes:
    #     for note in notes:
    #         st.info(note)
    # else:
    #     st.success(
    #         "入力された条件では、追加の確認事項はありません。"
    #     )

#もともとはここから


    # st.divider()

    # st.subheader("往診 算定結果")

    # st.write(f"往診料：{housecall_base:,} 点")

    # if patient_class == "SPECIAL":
    #     st.success("往診加算上の「別に定める患者」に該当します。")
    #     st.write("一の三の二　往診料に規定する別に厚生労働大臣が定める患者\n\n次のいずれかに該当するものであること。\n\n(１)　往診を行う保険医療機関において過去六十日以内に在宅患者訪問診療料(Ⅰ)、在宅患者訪問診療料(Ⅱ)又は在宅がん医療総合診療料を算定しているもの\n\n(２)　往診を行う保険医療機関と連携体制を構築している他の保険医療機関において、過去六十日以内に在宅患者訪問診療料(Ⅰ)、在宅患者訪問診療料(Ⅱ)又は在宅がん医療総合診療料を算定しているもの\n\n(３)　往診を行う保険医療機関の外来において継続的に診療を受けている患者\n\n(４)　往診を行う保険医療機関と平時からの連携体制を構築している介護老人保健施設、介護医療院及び特別養護老人ホームに入所する患者")
    # else:
    #     st.info("往診加算上の「別に定める患者」には該当しません。")

    # if housecall_add > 0:
    #     st.write(f"往診加算：{housecall_add:,} 点")

    # if long_time_point > 0:
    #     st.write(f"患家診療時間加算：{long_time_point:,} 点")

    # if death_cert_point > 0:
    #     st.write(f"死亡診断加算：{death_cert_point:,} 点")

#     if info_link_point > 0:
#         st.write(f"往診時医療情報連携加算：{info_link_point:,} 点")

#     if care_facility_add_point > 0:
#         st.write(
#             f"介護保険施設等連携往診加算："
#             f"{care_facility_add_point:,} 点"
#         )

#     st.metric(
#         "往診 合計",
#         f"{housecall_total:,} 点"
#     )