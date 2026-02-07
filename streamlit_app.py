import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1Mej0V4ql4P6hFDPstAJX-aD_Uea3ualUWgSJun6qHjs"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(page_title="道长训练计划", page_icon="💪", layout="wide")


@st.cache_resource
def _get_client() -> gspread.Client:
    conn_secrets = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(conn_secrets, scopes=SCOPES)
    return gspread.authorize(creds)


def load_sheet(gc, title):
    """加载指定 Sheet 页数据为 DataFrame"""
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(title)
    values = ws.get_all_values()
    if not values or len(values) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df


def render_table_with_rowspan(df: pd.DataFrame, merge_col: int = 0) -> str:
    """生成带 rowspan 合并的 HTML 表格"""
    if df.empty:
        return "<p>无数据</p>"

    html = ['<table class="fit-table">']

    # Header
    html.append('<thead><tr>')
    for col in df.columns:
        html.append(f'<th>{col}</th>')
    html.append('</tr></thead>')

    # Body
    html.append('<tbody>')
    first_col = df.iloc[:, merge_col].tolist()
    i = 0
    while i < len(df):
        curr_val = first_col[i]
        span = 1
        while i + span < len(df) and first_col[i + span] == curr_val:
            span += 1

        # First row
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

        # Remaining rows
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
    """生成普通 HTML 表格（不合并）"""
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
    """根据类别返回背景色"""
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
    """对特定内容添加样式"""
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


# === CSS ===
TABLE_CSS = """
<style>
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
.notes-table td:first-child {
    font-weight: bold;
    white-space: nowrap;
    min-width: 200px;
}
</style>
"""


# === 主应用 ===
st.markdown(TABLE_CSS, unsafe_allow_html=True)

st.title("💪 道长训练计划")
st.caption("数据来源：Google Sheet · 实时同步")

try:
    gc = _get_client()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 周训练计划",
        "📚 动作库",
        "🏥 身体状况与禁忌",
        "📝 备注与说明",
    ])

    # --- Tab 1: 周训练计划 ---
    with tab1:
        df_weekly = load_sheet(gc, "周训练计划")
        if not df_weekly.empty:
            df_weekly.iloc[:, 0] = df_weekly.iloc[:, 0].replace("", pd.NA).ffill().fillna("")

            # 筛选器
            days = df_weekly.iloc[:, 0].unique().tolist()
            selected = st.multiselect(
                "筛选训练日",
                options=days,
                default=days,
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
            # 按动作类型筛选
            if "动作类型" in df_lib.columns:
                types = df_lib["动作类型"].unique().tolist()
                selected_types = st.multiselect(
                    "按动作类型筛选",
                    options=types,
                    default=types,
                    key="type_filter",
                )
                df_lib_filtered = df_lib[df_lib["动作类型"].isin(selected_types)]
            else:
                df_lib_filtered = df_lib

            html = render_simple_table(df_lib_filtered)
            st.markdown(html, unsafe_allow_html=True)

            st.caption(f"共 {len(df_lib_filtered)} 个动作")
        else:
            st.info("无数据")

    # --- Tab 3: 身体状况与禁忌 ---
    with tab3:
        df_body = load_sheet(gc, "身体状况与禁忌")
        if not df_body.empty:
            df_body.iloc[:, 0] = df_body.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
            html = render_table_with_rowspan(df_body, merge_col=0)
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("无数据")

    # --- Tab 4: 备注与说明 ---
    with tab4:
        df_notes = load_sheet(gc, "备注与说明")
        if not df_notes.empty:
            # 渲染为更易读的格式
            for _, row in df_notes.iterrows():
                topic = str(row.iloc[0]).strip()
                content = str(row.iloc[1]).strip()
                if topic == "" and content == "":
                    st.markdown("---")
                elif content == "":
                    st.subheader(topic)
                else:
                    st.markdown(f"**{topic}**：{content}")
        else:
            st.info("无数据")

except Exception as e:
    st.error(f"连接失败：{e}")
    st.info("请检查 Streamlit Secrets 中的 Google Sheet 凭证配置。")
