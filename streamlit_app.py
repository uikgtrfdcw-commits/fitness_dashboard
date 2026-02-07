import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_js_eval import streamlit_js_eval

SPREADSHEET_ID = "1Mej0V4ql4P6hFDPstAJX-aD_Uea3ualUWgSJun6qHjs"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(page_title="道长训练计划", page_icon="💪", layout="wide")


# ============================================================
# 数据加载
# ============================================================
@st.cache_resource
def _get_client() -> gspread.Client:
    conn_secrets = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(conn_secrets, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_data(ttl=300)
def load_sheet(_gc, title):
    sh = _gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(title)
    values = ws.get_all_values()
    if not values or len(values) < 2:
        return pd.DataFrame()
    return pd.DataFrame(values[1:], columns=values[0])


def get_day_data(df):
    """将周训练计划按训练日分组"""
    df.iloc[:, 0] = df.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
    days = df.iloc[:, 0].unique().tolist()
    return {day: df[df.iloc[:, 0] == day].reset_index(drop=True) for day in days}


# ============================================================
# 颜色/样式映射
# ============================================================
DAY_COLORS = {
    "每日通用热身": ("#00695c", "#e0f7fa", "🔥"),
    "第1天：下肢+核心": ("#283593", "#e8eaf6", "🦵"),
    "第2天：上肢拉": ("#004d40", "#e0f2f1", "💪"),
    "第3天：轻量全身+恢复": ("#33691e", "#f1f8e9", "🌿"),
    "第4天：上肢推": ("#ff6f00", "#fff8e1", "🏋️"),
    "第5天：后链+下肢": ("#283593", "#e8eaf6", "🔗"),
    "周末：动态恢复": ("#880e4f", "#fce4ec", "🧘"),
}

TYPE_BADGES = {
    "💪": ("复合", "#1565c0", "#e3f2fd"),
    "🎯": ("孤立", "#e65100", "#fff3e0"),
    "🔧": ("激活", "#2e7d32", "#e8f5e9"),
    "🧘": ("拉伸", "#6a1b9a", "#f3e5f5"),
}

CATEGORY_COLORS = {
    "🔴 伤病状况": ("#c0392b", "#fff0f0"),
    "🚫 训练禁忌": ("#e65100", "#fff3e0"),
    "🟡 环境因素": ("#f57f17", "#fffde7"),
    "🟢 恢复策略": ("#2e7d32", "#e8f5e9"),
    "🔵 营养与作息": ("#1565c0", "#e3f2fd"),
    "📋 训练原则": ("#6a1b9a", "#f3e5f5"),
}


def _get_type_badge(action_type: str) -> str:
    for emoji, (label, color, bg) in TYPE_BADGES.items():
        if emoji in str(action_type):
            return f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;color:{color};background:{bg};">{emoji} {label}</span>'
    if action_type.strip():
        return f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;background:#f5f5f5;">{action_type}</span>'
    return ""


# ============================================================
# 手机端：卡片式渲染
# ============================================================
def render_mobile_exercise_card(row, header, index):
    name = row[header.index("动作名称")] if "动作名称" in header else ""
    action_type = row[header.index("动作类型")] if "动作类型" in header else ""
    sets = row[header.index("组数x次数")] if "组数x次数" in header else ""
    tempo = row[header.index("节奏/要点")] if "节奏/要点" in header else ""
    rpe = row[header.index("目标RPE")] if "目标RPE" in header else ""
    progression = row[header.index("渐进规则")] if "渐进规则" in header else ""
    note = row[header.index("注意事项")] if "注意事项" in header else ""
    phase = row[header.index("阶段")] if "阶段" in header else ""

    # 根据动作类型选择左边框颜色
    border_color = "#ddd"
    for emoji, (_, color, _) in TYPE_BADGES.items():
        if emoji in str(action_type):
            border_color = color
            break

    badge = _get_type_badge(action_type)

    # RPE 颜色
    rpe_html = ""
    if rpe.strip():
        rpe_color = "#c62828" if any(x in rpe for x in ("7", "8", "9")) else "#2e7d32"
        rpe_html = f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:13px;font-weight:bold;color:white;background:{rpe_color};">RPE {rpe}</span>'

    # 警告标记
    has_warning = "⚠️" in note
    warning_border = "border-left:4px solid #ff9800;" if has_warning else f"border-left:4px solid {border_color};"

    card_html = f'''
    <div style="{warning_border}background:white;border-radius:8px;padding:14px 16px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:17px;font-weight:700;color:#1a1a2e;">{index}. {name}</span>
            {badge}
        </div>'''

    if sets.strip():
        card_html += f'<div style="font-size:15px;color:#333;margin-bottom:4px;">📊 <b>{sets}</b></div>'

    if tempo.strip():
        card_html += f'<div style="font-size:13px;color:#555;margin-bottom:4px;">⏱ {tempo}</div>'

    if rpe_html:
        card_html += f'<div style="margin-bottom:4px;">{rpe_html}</div>'

    if progression.strip():
        card_html += f'<div style="font-size:12px;color:#666;margin-bottom:4px;">📈 {progression}</div>'

    if note.strip():
        note_bg = "#fff3e0" if has_warning else "#f8f9fa"
        note_color = "#e65100" if has_warning else "#444"
        card_html += f'<div style="font-size:13px;color:{note_color};background:{note_bg};padding:8px 10px;border-radius:6px;margin-top:6px;line-height:1.6;">{note}</div>'

    card_html += '</div>'
    return card_html


def render_mobile_day(day_name, day_df, header):
    color, bg, icon = DAY_COLORS.get(day_name, ("#333", "#f5f5f5", "📋"))

    html = f'''
    <div style="background:{bg};border-radius:12px;padding:16px;margin-bottom:20px;">
        <div style="font-size:20px;font-weight:800;color:{color};margin-bottom:12px;text-align:center;">
            {icon} {day_name}
        </div>
    </div>'''
    st.markdown(html, unsafe_allow_html=True)

    # 按阶段分组显示
    phase_col = header.index("阶段") if "阶段" in header else -1
    current_phase = ""
    exercise_num = 1

    for _, row_series in day_df.iterrows():
        row = row_series.tolist()
        if phase_col >= 0:
            phase = row[phase_col]
            if phase and phase != current_phase:
                current_phase = phase
                phase_color = "#6a1b9a" if "拉伸" in phase else "#00695c" if "热身" in phase or "激活" in phase else "#1565c0"
                st.markdown(
                    f'<div style="font-size:14px;font-weight:700;color:{phase_color};padding:8px 0 4px 0;border-bottom:2px solid {phase_color};margin:12px 0 8px 0;">{phase}</div>',
                    unsafe_allow_html=True,
                )

        name = row[header.index("动作名称")] if "动作名称" in header else ""
        if name.strip() and "严禁" not in name:
            card = render_mobile_exercise_card(row, header, exercise_num)
            st.markdown(card, unsafe_allow_html=True)
            exercise_num += 1
        elif "严禁" in name:
            note = row[header.index("注意事项")] if "注意事项" in header else ""
            st.markdown(
                f'<div style="background:#fff0f0;border-left:4px solid #c62828;padding:10px 14px;border-radius:6px;margin-bottom:10px;font-size:14px;color:#c62828;font-weight:600;">🚫 {name}：{note}</div>',
                unsafe_allow_html=True,
            )


def render_mobile_body(df):
    df.iloc[:, 0] = df.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
    current_cat = ""
    for _, row in df.iterrows():
        cat = str(row.iloc[0])
        item = str(row.iloc[1])
        detail = str(row.iloc[2]) if len(row) > 2 else ""

        if cat != current_cat:
            current_cat = cat
            color, bg = CATEGORY_COLORS.get(cat, ("#333", "#f5f5f5"))
            st.markdown(
                f'<div style="background:{bg};padding:10px 14px;border-radius:8px;margin:16px 0 8px 0;font-size:16px;font-weight:700;color:{color};">{cat}</div>',
                unsafe_allow_html=True,
            )

        if item.strip():
            st.markdown(
                f'''<div style="background:white;border-left:3px solid #ddd;padding:10px 14px;margin-bottom:8px;border-radius:6px;box-shadow:0 1px 2px rgba(0,0,0,0.05);">
                    <div style="font-size:15px;font-weight:600;color:#1a1a2e;margin-bottom:4px;">{item}</div>
                    <div style="font-size:13px;color:#555;line-height:1.6;">{detail}</div>
                </div>''',
                unsafe_allow_html=True,
            )


def render_mobile_lib(df):
    for _, row in df.iterrows():
        name = str(row.get("动作名称", ""))
        atype = str(row.get("动作类型", ""))
        muscle = str(row.get("目标肌群", ""))
        note = str(row.get("道长专属注意事项", ""))
        badge = _get_type_badge(atype)

        st.markdown(
            f'''<div style="background:white;border-radius:8px;padding:12px 14px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="font-size:15px;font-weight:700;color:#1a1a2e;">{name}</span>
                    {badge}
                </div>
                <div style="font-size:13px;color:#666;margin-bottom:4px;">🎯 {muscle}</div>
                <div style="font-size:12px;color:#555;line-height:1.5;">{note}</div>
            </div>''',
            unsafe_allow_html=True,
        )


# ============================================================
# 电脑端：表格渲染（保留原有逻辑）
# ============================================================
def render_table_with_rowspan(df: pd.DataFrame, merge_col: int = 0) -> str:
    if df.empty:
        return "<p>无数据</p>"

    html = ['<table class="fit-table">']
    html.append('<thead><tr>')
    for col in df.columns:
        html.append(f'<th>{col}</th>')
    html.append('</tr></thead>')

    html.append('<tbody>')
    first_col = df.iloc[:, merge_col].tolist()
    i = 0
    while i < len(df):
        curr_val = first_col[i]
        span = 1
        while i + span < len(df) and first_col[i + span] == curr_val:
            span += 1

        html.append('<tr>')
        for j in range(len(df.columns)):
            if j == merge_col:
                css = _get_category_css(curr_val)
                html.append(f'<td rowspan="{span}" class="merged-cell" {css}>{curr_val}</td>')
            else:
                cell = str(df.iloc[i, j])
                cell = _style_cell(cell, df.columns[j])
                html.append(f'<td>{cell}</td>')
        html.append('</tr>')

        for k in range(1, span):
            html.append('<tr>')
            for j in range(len(df.columns)):
                if j == merge_col:
                    continue
                cell = str(df.iloc[i + k, j])
                cell = _style_cell(cell, df.columns[j])
                html.append(f'<td>{cell}</td>')
            html.append('</tr>')

        i += span

    html.append('</tbody></table>')
    return ''.join(html)


def render_simple_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p>无数据</p>"

    html = ['<table class="fit-table">']
    html.append('<thead><tr>')
    for col in df.columns:
        html.append(f'<th>{col}</th>')
    html.append('</tr></thead><tbody>')

    for i in range(len(df)):
        html.append('<tr>')
        for j in range(len(df.columns)):
            cell = str(df.iloc[i, j])
            cell = _style_cell(cell, df.columns[j])
            html.append(f'<td>{cell}</td>')
        html.append('</tr>')

    html.append('</tbody></table>')
    return ''.join(html)


def _get_category_css(val: str) -> str:
    val = str(val)
    if "伤病" in val or "🔴" in val:
        return 'style="background-color:#fff0f0; color:#c0392b;"'
    elif "禁忌" in val or "🚫" in val or "⚠️" in val:
        return 'style="background-color:#fff3e0; color:#e65100;"'
    elif "恢复" in val or "🟢" in val:
        return 'style="background-color:#e8f5e9; color:#2e7d32;"'
    elif "环境" in val or "🟡" in val:
        return 'style="background-color:#fffde7; color:#f57f17;"'
    elif "营养" in val or "🔵" in val:
        return 'style="background-color:#e3f2fd; color:#1565c0;"'
    elif "原则" in val or "📋" in val:
        return 'style="background-color:#f3e5f5; color:#6a1b9a;"'
    elif "热身" in val:
        return 'style="background-color:#e0f7fa; color:#00695c;"'
    elif "恢复" in val or "周末" in val:
        return 'style="background-color:#fce4ec; color:#880e4f;"'
    elif "第1天" in val or "第5天" in val:
        return 'style="background-color:#e8eaf6; color:#283593;"'
    elif "第2天" in val:
        return 'style="background-color:#e0f2f1; color:#004d40;"'
    elif "第3天" in val:
        return 'style="background-color:#f1f8e9; color:#33691e;"'
    elif "第4天" in val:
        return 'style="background-color:#fff8e1; color:#ff6f00;"'
    return 'style="background-color:#fafafa;"'


def _style_cell(cell: str, col_name: str) -> str:
    if "💪" in cell:
        return f'<span style="color:#1565c0; font-weight:600;">{cell}</span>'
    elif "🎯" in cell:
        return f'<span style="color:#e65100; font-weight:600;">{cell}</span>'
    elif "🔧" in cell:
        return f'<span style="color:#2e7d32; font-weight:600;">{cell}</span>'
    elif "🧘" in cell:
        return f'<span style="color:#6a1b9a; font-weight:600;">{cell}</span>'
    if col_name == "目标RPE":
        cell = cell.strip()
        if cell in ("7-8", "8-9", "8"):
            return f'<span style="color:#c62828; font-weight:bold;">{cell}</span>'
        elif cell in ("4-5", "4", "5", "5-6"):
            return f'<span style="color:#2e7d32;">{cell}</span>'
    return cell


# ============================================================
# CSS
# ============================================================
GLOBAL_CSS = """
<style>
/* 电脑端表格 */
.fit-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    line-height: 1.5;
}
.fit-table th {
    background-color: #1a1a2e;
    color: #ffffff;
    padding: 10px 12px;
    text-align: center;
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #333;
    position: sticky;
    top: 0;
    z-index: 1;
}
.fit-table td {
    padding: 8px 10px;
    border: 1px solid #e0e0e0;
    vertical-align: middle;
}
.fit-table .merged-cell {
    font-weight: 700;
    font-size: 13px;
    vertical-align: middle;
    text-align: center;
    border-right: 2px solid #ccc;
}
.fit-table tr:hover td {
    background-color: #f0f4ff;
}
.fit-table tr:nth-child(even) td {
    background-color: #fafbfc;
}

/* 手机端全局 */
@media (max-width: 768px) {
    .block-container { padding: 0.5rem 0.8rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { font-size: 13px; padding: 6px 8px; }
}
</style>
"""


# ============================================================
# 主应用
# ============================================================
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# 检测屏幕宽度
screen_width = streamlit_js_eval(js_expressions="window.innerWidth", key="screen_width")
is_mobile = screen_width is not None and screen_width < 768

if is_mobile:
    st.markdown(
        '<div style="text-align:center;padding:8px 0;"><span style="font-size:22px;font-weight:800;">💪 道长训练计划</span></div>',
        unsafe_allow_html=True,
    )
else:
    st.title("💪 道长训练计划")
    st.caption("数据来源：Google Sheet · 实时同步")

try:
    gc = _get_client()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 训练计划",
        "📚 动作库",
        "🏥 身体状况",
        "📝 备注",
    ])

    # --- Tab 1: 周训练计划 ---
    with tab1:
        df_weekly = load_sheet(gc, "周训练计划")
        if not df_weekly.empty:
            header = df_weekly.columns.tolist()
            day_data = get_day_data(df_weekly)
            day_names = list(day_data.keys())

            if is_mobile:
                # 手机端：单日选择 + 卡片式展示
                st.markdown(
                    '<div style="font-size:14px;color:#666;text-align:center;margin-bottom:8px;">选择今天的训练日 👇</div>',
                    unsafe_allow_html=True,
                )

                # 排除"每日通用热身"，单独显示
                training_days = [d for d in day_names if "热身" not in d]
                selected_day = st.selectbox(
                    "训练日",
                    options=training_days,
                    index=0,
                    key="mobile_day",
                    label_visibility="collapsed",
                )

                # 先显示热身
                warmup_key = [d for d in day_names if "热身" in d]
                if warmup_key:
                    with st.expander("🔥 每日通用热身（点击展开）", expanded=False):
                        render_mobile_day(warmup_key[0], day_data[warmup_key[0]], header)

                # 显示选中的训练日
                if selected_day in day_data:
                    render_mobile_day(selected_day, day_data[selected_day], header)

            else:
                # 电脑端：表格视图 + 筛选器
                df_weekly.iloc[:, 0] = df_weekly.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
                selected = st.multiselect(
                    "筛选训练日",
                    options=day_names,
                    default=day_names,
                    key="day_filter",
                )
                df_filtered = df_weekly[df_weekly.iloc[:, 0].isin(selected)]
                html = render_table_with_rowspan(df_filtered, merge_col=0)
                st.markdown(html, unsafe_allow_html=True)
                st.caption(f"共 {len(df_filtered)} 行 · {len(selected)} 个训练日")
        else:
            st.info("无数据")

    # --- Tab 2: 动作库 ---
    with tab2:
        df_lib = load_sheet(gc, "动作库")
        if not df_lib.empty:
            if is_mobile:
                if "动作类型" in df_lib.columns:
                    types = df_lib["动作类型"].unique().tolist()
                    selected_type = st.selectbox("筛选类型", ["全部"] + types, key="mobile_type")
                    if selected_type != "全部":
                        df_lib = df_lib[df_lib["动作类型"] == selected_type]
                render_mobile_lib(df_lib)
            else:
                if "动作类型" in df_lib.columns:
                    types = df_lib["动作类型"].unique().tolist()
                    selected_types = st.multiselect(
                        "按动作类型筛选", options=types, default=types, key="type_filter",
                    )
                    df_lib = df_lib[df_lib["动作类型"].isin(selected_types)]
                html = render_simple_table(df_lib)
                st.markdown(html, unsafe_allow_html=True)
                st.caption(f"共 {len(df_lib)} 个动作")
        else:
            st.info("无数据")

    # --- Tab 3: 身体状况与禁忌 ---
    with tab3:
        df_body = load_sheet(gc, "身体状况与禁忌")
        if not df_body.empty:
            if is_mobile:
                render_mobile_body(df_body)
            else:
                df_body.iloc[:, 0] = df_body.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
                html = render_table_with_rowspan(df_body, merge_col=0)
                st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("无数据")

    # --- Tab 4: 备注与说明 ---
    with tab4:
        df_notes = load_sheet(gc, "备注与说明")
        if not df_notes.empty:
            for _, row in df_notes.iterrows():
                topic = str(row.iloc[0]).strip()
                content = str(row.iloc[1]).strip()
                if topic == "" and content == "":
                    st.markdown("---")
                elif content == "":
                    st.subheader(topic)
                else:
                    if is_mobile:
                        st.markdown(
                            f'<div style="margin-bottom:8px;"><span style="font-weight:700;font-size:14px;">{topic}</span><br><span style="font-size:13px;color:#444;">{content}</span></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**{topic}**：{content}")
        else:
            st.info("无数据")

except Exception as e:
    st.error(f"连接失败：{e}")
    st.info("请检查 Streamlit Secrets 中的 Google Sheet 凭证配置。")
