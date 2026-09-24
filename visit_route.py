def run_visit_route(
    st,
    point_master,
    add_master,
    facility_class,
    setting
):

    def to_int(value):
        return int(str(value).replace(",", "").strip())

    def get_add_point(add_master, add_id):
        row = add_master[
        add_master["add_id"] == add_id
        ]
        if row.empty:
            return 0

        return to_int(
            row.iloc[0]["points"]
        )
    
    # =========================
    # 訪問診療ルート
    # =========================

    st.header("訪問診療の算定判定")

    # -------------------------
    # 療養場所
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
    # 同一患家
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

    # -------------------------
    # 単一建物診療患者数
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
    # 訪問回数
    # -------------------------

    visit_count = st.number_input(
        "今月の実際の訪問診療回数は何回ですか？",
        min_value=1,
        max_value=31,
        value=1,
        step=1,
        key="visit_count"
    )

    # -------------------------
    # 在医総管区分
    # -------------------------

    q012 = "いいえ"
    q013 = "いいえ"
    q014 = "いいえ"

    table8_2_reasons = []

    if visit_count >= 2:

        st.markdown("#### 別表第8の2")

        with st.expander("別表第8の2の対象となる疾患・状態を見る"):
            st.markdown(
                """
                **次のいずれかに該当する患者が対象です。**

                **疾患**
                - 末期の悪性腫瘍
                - スモン
                - 指定難病
                - 後天性免疫不全症候群
                - 脊髄損傷
                - 真皮を越える褥瘡

                **状態**
                - 在宅自己連続携行式腹膜灌流を行っている
                - 在宅血液透析を行っている
                - 在宅酸素療法を行っている
                - 在宅中心静脈栄養法を行っている
                - 在宅成分栄養経管栄養法を行っている
                - 在宅自己導尿を行っている
                - 在宅人工呼吸を行っている
                - 植込型脳・脊髄刺激装置による疼痛管理を行っている
                - 肺高血圧症でプロスタグランジンI2製剤を投与されている
                - その他、関係機関との調整等のために特別な医学管理を必要とする
                """
            )

        table8_2_reasons = st.multiselect(
            "該当する別表第8の2の疾患・状態を選択してください（複数選択可）",
            [
                "末期の悪性腫瘍",
                "スモン",
                "指定難病",
                "後天性免疫不全症候群",
                "脊髄損傷",
                "真皮を越える褥瘡",
                "在宅自己連続携行式腹膜灌流",
                "在宅血液透析",
                "在宅酸素療法",
                "在宅中心静脈栄養法",
                "在宅成分栄養経管栄養法",
                "在宅自己導尿",
                "在宅人工呼吸",
                "植込型脳・脊髄刺激装置による疼痛管理",
                "肺高血圧症＋プロスタグランジンI2製剤投与",
                "その他、関係機関との調整等のために特別な医学管理を必要とする状態",
            ],
            key="table8_2_reasons"
        )

        q012 = "はい" if table8_2_reasons else "いいえ"

        if q012 == "はい":
            st.success("別表第8の2：該当候補")
        else:
            st.info("別表第8の2：該当する疾患・状態が選択されていません。")

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
    # frequency_class
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

    st.success(
        f"在医総管の判定区分（M1 月1回,M2 月2回,SEVERE 難病,ONLINE オンライン）：{frequency_class}"
    )

    # -------------------------
    # 在医総管点数
    # -------------------------

    matched = point_master[
        (point_master["facility_class"] == facility_class)
        & (point_master["management_type"] == "在医総管")
        & (point_master["frequency_class"] == frequency_class)
        & (point_master["single_building_count"].astype(str)
            == str(q009)
        )
    ]

    if matched.empty:
        st.warning(
            "この条件の在医総管点数がマスターにありません。"
        )
        st.stop()

    zaisokan_point = to_int(
        matched.iloc[0]["points"]
    )

    # -------------------------
    # 訪問診療料
    # -------------------------

    same_building = st.radio(
        "同一建物居住者に該当しますか？",
        ["選択してください", "はい", "いいえ"],
        key="same_building"
    )

    if same_building == "選択してください":
        st.stop()

    building_type = (
        "同一建物居住者"
        if same_building == "はい"
        else "同一建物居住者以外"
    )

    visit_fee_row = point_master[
        (point_master["billing_item"] == "在宅患者訪問診療料（Ⅰ）1")
        & (point_master["building_count"] == building_type)
    ]

    if visit_fee_row.empty:
        st.warning(
            "訪問診療料の点数がマスターにありません。"
        )
        st.stop()

    visit_fee = to_int(
        visit_fee_row.iloc[0]["points"]
    )

    visit_fee_month = visit_fee * visit_count

    # -------------------------
    # 基本合計
    # -------------------------

    basic_total = (
        zaisokan_point
        + visit_fee_month
    )

    # =========================
    # 主要加算
    # =========================

    st.subheader("主要加算")

    # -------------------------
    # 包括的支援加算
    # -------------------------

    st.markdown("#### 包括的支援加算")

    with st.expander("対象となる状態を確認する"):
        st.markdown(
            """
            次のいずれかに該当する場合、包括的支援加算の対象候補です。

            - 要介護3・4・5、または障害支援区分2以上
            - 認知症高齢者の日常生活自立度ランクIIIa・IIIb・IV・M
            - 頻回の訪問看護を受けている状態
            - 訪問診療または訪問看護において処置を受けている状態
            - 特定施設等に入居し、医師の指示を受けた看護職員による処置を受けている状態
            - 麻薬投薬を受けている状態
            - その他、関係機関との調整等のために特別な医学管理を必要とする状態
            """
        )

    support_reasons = st.multiselect(
        "該当する状態を選択してください（複数選択可）",
        [
            "1-1 要介護3",
            "1-2 要介護4",
            "1-3 要介護5",
            "1-4 障害支援区分2以上",
            "2-1 認知症高齢者の日常生活自立度 ランクIIIa",
            "2-2 認知症高齢者の日常生活自立度 ランクIIIb",
            "2-3 認知症高齢者の日常生活自立度 ランクIV",
            "2-4 認知症高齢者の日常生活自立度 ランクM",
            "3 頻回の訪問看護を受けている状態",
            "4 訪問診療又は訪問看護において処置を受けている状態",
            "5 施設に入居し、看護職員による処置を受けている状態",
            "6 麻薬投薬を受けている状態",
            "7-1 脳性麻痺等・小児慢性特定疾病・障害児に該当する15歳未満の患者",
            "7-2 出生時体重1,500g未満であった1歳未満の患者",
            "7-3 超重症児（者）・準超重症児（者）の判定スコア10以上",
            "7-4 家族等が注射・喀痰吸引・経管栄養等の処置を行っている患者",
        ],
        key="support_reasons"
    )

    support_add = len(support_reasons) > 0

    support_add_point = (
        get_add_point(add_master, "ADD001")
        if support_add
        else 0
    )

    if support_add:
        st.success(
            f"包括的支援加算：算定候補 "
            f"{support_add_point:,} 点"
        )
    else:
        st.info(
            "包括的支援加算：該当する状態が選択されていません。"
        )

    # -------------------------
    # 頻回訪問加算
    # -------------------------

    st.markdown("#### 頻回訪問加算")

    with st.expander("頻回訪問加算の対象条件を見る"):
        st.markdown(
            """
            **算定候補となる基本条件**

            - 1か月に **往診＋訪問診療を合計4回以上** 行っている
            - かつ、次の①または②に該当する

            **① 末期の悪性腫瘍**

            **② 下記の状態のうち2つ以上に該当**

            - 在宅自己腹膜灌流指導管理
            - 在宅血液透析指導管理
            - 在宅酸素療法指導管理
            - 在宅中心静脈栄養法指導管理
            - 在宅成分栄養経管栄養法指導管理
            - 在宅自己導尿指導管理
            - 在宅人工呼吸指導管理
            - 在宅悪性腫瘍等患者指導管理
            - 在宅自己疼痛管理指導管理
            - 在宅肺高血圧症患者指導管理
            - 在宅気管切開患者指導管理
            - ドレーンチューブ又は留置カテーテルを使用
            - 人工肛門又は人工膀胱を設置

            ※「ドレーンチューブ又は留置カテーテル」と
            「人工肛門又は人工膀胱」の **2項目だけ** の組み合わせは対象外です。
            """
        )

    frequent_housecall_count = st.number_input(
        "今月、訪問診療とは別に往診した回数は何回ですか？",
        min_value=0,
        max_value=31,
        value=0,
        step=1,
        key="frequent_housecall_count"
    )

    frequent_total_count = visit_count + frequent_housecall_count

    frequent_terminal_cancer = st.checkbox(
        "末期の悪性腫瘍に該当する",
        key="frequent_terminal_cancer"
    )

    frequent_states = st.multiselect(
        "該当する管理・状態を選択してください（複数選択可）",
        [
            "在宅自己腹膜灌流指導管理",
            "在宅血液透析指導管理",
            "在宅酸素療法指導管理",
            "在宅中心静脈栄養法指導管理",
            "在宅成分栄養経管栄養法指導管理",
            "在宅自己導尿指導管理",
            "在宅人工呼吸指導管理",
            "在宅悪性腫瘍等患者指導管理",
            "在宅自己疼痛管理指導管理",
            "在宅肺高血圧症患者指導管理",
            "在宅気管切開患者指導管理",
            "ドレーンチューブ又は留置カテーテルを使用",
            "人工肛門又は人工膀胱を設置",
        ],
        key="frequent_states"
    )

    frequent_excluded_pair = (
        len(frequent_states) == 2
        and "ドレーンチューブ又は留置カテーテルを使用" in frequent_states
        and "人工肛門又は人工膀胱を設置" in frequent_states
    )

    frequent_patient_eligible = (
        frequent_terminal_cancer
        or (
            len(frequent_states) >= 2
            and not frequent_excluded_pair
        )
    )

    frequent_count_eligible = frequent_total_count >= 4

    frequent_add_point = 0
    frequent_add_variant = None

    if frequent_count_eligible and frequent_patient_eligible:
        frequent_variant = st.radio(
            "頻回訪問加算の算定区分を選択してください",
            ["選択してください", "初回", "2回目以降"],
            key="frequent_variant"
        )

        if frequent_variant == "選択してください":
            st.stop()

        if frequent_variant == "初回":
            frequent_add_point = get_add_point(
                add_master,
                "ADD007"
            )
            frequent_add_variant = "初回"

        else:
            frequent_add_point = get_add_point(
                add_master,
                "ADD008"
            )
            frequent_add_variant = "2回目以降"

        st.success(
            f"頻回訪問加算（{frequent_add_variant}）："
            f"算定候補 {frequent_add_point:,} 点"
        )

    else:
        reasons = []

        if not frequent_count_eligible:
            reasons.append(
                f"今月の往診＋訪問診療が{frequent_total_count}回で、4回未満"
            )

        if not frequent_patient_eligible:
            if frequent_excluded_pair:
                reasons.append(
                    "選択した2項目が除外される組み合わせ"
                )
            else:
                reasons.append(
                    "対象患者要件を満たしていない"
                )

        st.info(
            "頻回訪問加算：算定候補外（"
            + "／".join(reasons)
            + "）"
        )

    home_dx_class = str(
        setting["home_dx_class"]
    ).strip()

    home_info_link = str(
        setting["home_info_link"]
    ).strip()

    home_data_submission = str(
        setting["home_data_submission"]
    ).strip()

    dx_class = st.selectbox(
        "在宅医療DX情報活用加算の区分",
        ["なし", "1", "2"],
        key="dx_class"
    )

# -------------------------
# 在宅医療DX情報活用加算
# -------------------------

    if home_dx_class == "1":
        dx_point = get_add_point(
            add_master,
            "ADD004"
        )

    elif home_dx_class == "2":
        dx_point = get_add_point(
            add_master,
            "ADD005"
        )

    else:
        dx_point = 0

# -------------------------
# 在宅データ提出加算
# -------------------------

    if home_data_submission == "はい":
        data_submit_point = get_add_point(
            add_master,
            "ADD002"
        )
    else:
        data_submit_point = 0

# -------------------------
# 在宅医療情報連携加算
# -------------------------

    info_link_point = 0

    if home_info_link == "はい":

        info_link_patient = st.radio(
            "この患者について、在宅医療情報連携加算の患者・連携要件を満たしますか？",
            ["選択してください", "はい", "いいえ"],
            key="info_link_patient"
        )

        if info_link_patient == "選択してください":
            st.stop()

        if info_link_patient == "はい":
            info_link_point = get_add_point(
                add_master,
                "ADD003"
            )

    else:
        st.info(
            "在宅医療情報連携加算：施設設定上の届出なし"
        )

    add_total = (
        support_add_point
        + frequent_add_point
        + dx_point
        + info_link_point
        + data_submit_point
    )

    medical_total = basic_total + add_total

    # =========================
    # 介護保険
    # =========================

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

    # =========================
    # 最終結果
    # =========================

    st.divider()
    st.header("訪問診療 算定結果")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "在医総管",
            f"{zaisokan_point:,} 点"
        )

    with col2:
        st.metric(
            "医療保険 合計",
            f"{medical_total:,} 点"
        )


    st.subheader("算定候補")

    result_items = [
        ("在医総管", zaisokan_point),
        ("訪問診療料", visit_fee_month),
    ]

    if support_add_point > 0:
        result_items.append(
            ("包括的支援加算", support_add_point)
        )

    if frequent_add_point > 0:
        result_items.append(
            (
                f"頻回訪問加算（{frequent_add_variant}）",
                frequent_add_point
            )
        )

    if dx_point > 0:
        result_items.append(
            ("在宅医療DX情報活用加算", dx_point)
        )

    if info_link_point > 0:
        result_items.append(
            ("在宅医療情報連携加算", info_link_point)
        )

    if data_submit_point > 0:
        result_items.append(
            ("在宅データ提出加算", data_submit_point)
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


    st.subheader("介護保険")

    if care_item is not None:
        st.write(
            f"{care_item}：{care_units:,} 単位"
        )
    else:
        st.write("算定候補なし")


    # -------------------------
    # 判定根拠
    # -------------------------

    with st.expander("判定根拠を見る"):

        st.write(f"療養場所：{q003}")
        st.write(f"単一建物診療患者数：{q009}")
        st.write(f"今月の訪問診療回数：{visit_count}回")
        st.write(f"在医総管区分：{frequency_class}")
        st.write(f"医療機関区分：{facility_class}")

        if visit_count >= 2:
            if table8_2_reasons:
                st.write("別表第8の2：該当候補")
                for reason in table8_2_reasons:
                    st.write(f"・{reason}")
            else:
                st.write("別表第8の2：該当する疾患・状態の選択なし")

        st.write(
            f"在宅医療DX区分：{home_dx_class}"
        )

        st.write(
            f"在宅医療情報連携届出：{home_info_link}"
        )

        st.write(
            f"在宅データ提出届出：{home_data_submission}"
        )

        if support_add:
            st.write("包括的支援加算：対象候補")
            for reason in support_reasons:
                st.write(f"・{reason}")
        else:
            st.write("包括的支援加算：対象状態の選択なし")

        st.write(
            f"頻回訪問加算判定：今月の往診＋訪問診療 "
            f"{frequent_total_count}回"
        )

        if frequent_terminal_cancer:
            st.write("・対象患者要件：末期の悪性腫瘍")

        for state in frequent_states:
            st.write(f"・{state}")

        if frequent_add_point > 0:
            st.write(
                f"頻回訪問加算：{frequent_add_variant} "
                f"{frequent_add_point:,}点"
            )
        else:
            st.write("頻回訪問加算：算定候補外")

        if q010 == "はい":
            st.write(
                f"同一患家での診療順：{q011}"
            )


    # -------------------------
    # 確認事項
    # -------------------------

    notes = []

    if q010 == "はい" and q011 == "2人目以降":
        notes.append(
            "同一患家の2人目以降です。"
            "訪問診療料の算定方法を別途確認してください。"
        )

    if frequency_class == "M1" and visit_count >= 2:
        notes.append(
            "実際の訪問回数は2回以上ですが、"
            "在医総管は月1回区分として判定されています。"
        )

    if care_cert == "はい" and care_item is None:
        notes.append(
            "居宅療養管理指導費について、"
            "情報提供または指導・助言の要件を確認してください。"
        )

    if frequent_excluded_pair:
        notes.append(
            "頻回訪問加算："
            "「ドレーンチューブ又は留置カテーテル」と"
            "「人工肛門又は人工膀胱」の2項目だけの組み合わせは"
            "対象患者要件を満たしません。"
        )

    if frequent_patient_eligible and not frequent_count_eligible:
        notes.append(
            "頻回訪問加算：対象患者要件には該当しますが、"
            "今月の往診＋訪問診療が4回未満です。"
        )

    with st.expander("確認事項"):

        if notes:
            for note in notes:
                st.info(note)
        else:
            st.success(
                "入力された条件では、追加の確認事項はありません。"
            )
