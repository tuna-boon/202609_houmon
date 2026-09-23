import secrets
from datetime import date

import pandas as pd


def _clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def _new_facility_id(existing_ids):
    existing = {str(v).strip() for v in existing_ids}
    while True:
        facility_id = f"f_{secrets.token_hex(4)}"
        if facility_id not in existing:
            return facility_id


def run_facility_admin(st, conn, facility_setting, facility_worksheet):
    st.title("施設設定 管理")
    st.caption("施設の新規登録・設定変更・利用停止を行います。")

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        password = st.text_input(
            "管理者パスワード",
            type="password",
            key="admin_password",
        )

        if st.button("ログイン", type="primary"):
            expected = str(st.secrets["admin"]["password"])
            if password == expected:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います。")

        st.stop()

    if st.button("ログアウト"):
        st.session_state.admin_authenticated = False
        st.rerun()

    df = facility_setting.copy()
    df.columns = df.columns.str.strip()

    expected_columns = [
        "facility_id",
        "facility_name",
        "active",
        "home_care_support_type",
        "enhanced_type",
        "bed_status",
        "housecall_support_class",
        "zai_soukan_1",
        "zai_soukan_2",
        "zai_soukan_3",
        "home_dx_class",
        "home_info_link",
        "home_data_submission",
        "home_performance_add",
        "home_enhanced_add",
        "created_at",
        "updated_at",
        "memo",
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""

    df = df[expected_columns]

    st.divider()

    action = st.radio(
        "操作",
        ["新規施設を追加", "既存施設を編集"],
        horizontal=True,
        key="admin_action",
    )

    selected_index = None
    current = {col: "" for col in expected_columns}

    if action == "既存施設を編集":
        if df.empty:
            st.info("登録済みの施設がありません。")
            st.stop()

        options = []
        option_map = {}

        for idx, row in df.iterrows():
            facility_id = _clean(row["facility_id"])
            facility_name = _clean(row["facility_name"])
            active = _clean(row["active"])
            label = f"{facility_name or '名称未設定'}（{facility_id} / {active or '状態未設定'}）"
            options.append(label)
            option_map[label] = idx

        selected_label = st.selectbox(
            "編集する施設",
            options,
            key="admin_selected_facility",
        )

        selected_index = option_map[selected_label]
        current = {
            col: _clean(df.loc[selected_index, col])
            for col in expected_columns
        }

        facility_id = current["facility_id"]

    else:
        facility_id = _new_facility_id(df["facility_id"].tolist())
        current.update(
            {
                "facility_id": facility_id,
                "active": "はい",
                "home_care_support_type": "なし",
                "enhanced_type": "いいえ",
                "bed_status": "なし",
                "housecall_support_class": "OTHER",
                "zai_soukan_1": "いいえ",
                "zai_soukan_2": "いいえ",
                "zai_soukan_3": "いいえ",
                "home_dx_class": "なし",
                "home_info_link": "いいえ",
                "home_data_submission": "いいえ",
                "home_performance_add": "なし",
                "home_enhanced_add": "なし",
            }
        )

    st.info(f"施設ID：`{facility_id}`")

    with st.form("facility_admin_form"):
        facility_name = st.text_input(
            "施設名",
            value=current["facility_name"],
        )

        active = st.radio(
            "利用状態",
            ["はい", "いいえ"],
            index=0 if current["active"] != "いいえ" else 1,
            horizontal=True,
        )

        support_options = ["なし", "在支診", "在支病"]
        support_value = current["home_care_support_type"]
        home_care_support_type = st.selectbox(
            "在宅療養支援診療所・病院",
            support_options,
            index=support_options.index(support_value)
            if support_value in support_options
            else 0,
        )

        enhanced_type = st.radio(
            "機能強化型",
            ["はい", "いいえ"],
            index=0 if current["enhanced_type"] == "はい" else 1,
            horizontal=True,
        )

        bed_status = st.radio(
            "病床",
            ["あり", "なし"],
            index=0 if current["bed_status"] == "あり" else 1,
            horizontal=True,
        )

        housecall_options = [
            "SOLO_ENHANCED",
            "GROUP_ENHANCED",
            "CONVENTIONAL_SUPPORT",
            "OTHER",
        ]
        housecall_value = current["housecall_support_class"]
        housecall_support_class = st.selectbox(
            "往診支援区分",
            housecall_options,
            index=housecall_options.index(housecall_value)
            if housecall_value in housecall_options
            else 3,
            format_func=lambda x: {
                "SOLO_ENHANCED": "単独型機能強化型",
                "GROUP_ENHANCED": "連携型機能強化型",
                "CONVENTIONAL_SUPPORT": "従来型在支診・在支病",
                "OTHER": "その他",
            }.get(x, x),
        )

        st.markdown("##### 在医総管")
        c1, c2, c3 = st.columns(3)
        with c1:
            zai_soukan_1 = st.checkbox(
                "在医総管1",
                value=current["zai_soukan_1"] == "はい",
            )
        with c2:
            zai_soukan_2 = st.checkbox(
                "在医総管2",
                value=current["zai_soukan_2"] == "はい",
            )
        with c3:
            zai_soukan_3 = st.checkbox(
                "在医総管3",
                value=current["zai_soukan_3"] == "はい",
            )

        st.markdown("##### その他の届出")

        dx_options = ["なし", "1", "2"]
        dx_value = current["home_dx_class"]
        home_dx_class = st.selectbox(
            "在宅医療DX情報活用加算",
            dx_options,
            index=dx_options.index(dx_value)
            if dx_value in dx_options
            else 0,
        )

        home_info_link = st.radio(
            "在宅医療情報連携",
            ["はい", "いいえ"],
            index=0 if current["home_info_link"] == "はい" else 1,
            horizontal=True,
        )

        home_data_submission = st.radio(
            "在宅データ提出",
            ["はい", "いいえ"],
            index=0 if current["home_data_submission"] == "はい" else 1,
            horizontal=True,
        )

        performance_options = ["なし", "1", "2"]
        performance_value = current["home_performance_add"]
        home_performance_add = st.selectbox(
            "在宅療養実績加算",
            performance_options,
            index=performance_options.index(performance_value)
            if performance_value in performance_options
            else 0,
        )

        enhanced_add_options = ["なし", "あり"]
        enhanced_add_value = current["home_enhanced_add"]
        home_enhanced_add = st.selectbox(
            "在宅医療充実体制加算",
            enhanced_add_options,
            index=enhanced_add_options.index(enhanced_add_value)
            if enhanced_add_value in enhanced_add_options
            else 0,
        )

        memo = st.text_area(
            "備考",
            value=current["memo"],
        )

        save = st.form_submit_button(
            "施設設定を保存",
            type="primary",
            use_container_width=True,
        )

    if save:
        if not facility_name.strip():
            st.error("施設名を入力してください。")
            st.stop()

        today = date.today().isoformat()

        row_data = {
            "facility_id": facility_id,
            "facility_name": facility_name.strip(),
            "active": active,
            "home_care_support_type": home_care_support_type,
            "enhanced_type": enhanced_type,
            "bed_status": bed_status,
            "housecall_support_class": housecall_support_class,
            "zai_soukan_1": "はい" if zai_soukan_1 else "いいえ",
            "zai_soukan_2": "はい" if zai_soukan_2 else "いいえ",
            "zai_soukan_3": "はい" if zai_soukan_3 else "いいえ",
            "home_dx_class": home_dx_class,
            "home_info_link": home_info_link,
            "home_data_submission": home_data_submission,
            "home_performance_add": home_performance_add,
            "home_enhanced_add": home_enhanced_add,
            "created_at": current["created_at"] if current["created_at"] else today,
            "updated_at": today,
            "memo": memo.strip(),
        }

        if action == "新規施設を追加":
            df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        else:
            for col, value in row_data.items():
                df.loc[selected_index, col] = value

        conn.update(
            worksheet=facility_worksheet,
            data=df,
        )

        st.cache_data.clear()
        st.success("施設設定を保存しました。")
        st.code(f"?facility={facility_id}", language=None)
        st.caption(
            "公開URLの末尾に上記を付けて、その施設用URLとして配布できます。"
        )
