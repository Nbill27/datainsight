import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# PAGE CONFIG
st.set_page_config(
    page_title="DataInsight",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)


#SESSION STATE
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

if "show_upload_notice" not in st.session_state:
    st.session_state.show_upload_notice = False

if "show_workspace" not in st.session_state:
    st.session_state.show_workspace = False

if "working_df" not in st.session_state:
    st.session_state.working_df = None

if "dtype_overrides" not in st.session_state:
    st.session_state.dtype_overrides = {}

if "theme" not in st.session_state:
    st.session_state.theme = "dark"


#THEME PALETTES
THEMES = {
    "dark": {
        "app_bg": "#0E1117",
        "card_bg": "#161B22",
        "border": "#30363D",
        "text": "#F0F6FC",
        "text_muted": "#8B949E",
    },
    "light": {
        "app_bg": "#FFFFFF",
        "card_bg": "#F6F8FA",
        "border": "#D0D7DE",
        "text": "#1F2328",
        "text_muted": "#57606A",
    }
}

palette = THEMES[st.session_state.theme]

#CUSTOM CSS
st.markdown(
    f"""
    <style>

    /*GLOBAL LAYOUT*/

    .stApp {{
        background-color: {palette["app_bg"]};
    }}

    .block-container {{
        max-width: 1180px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }}


    /*HEADER*/

    .app-header {{
        margin-bottom: 1.8rem;
    }}

    .app-header h1 {{
        font-size: 2rem;
        font-weight: 650;
        margin: 0;
        padding: 0;
        color: {palette["text"]};
    }}

    .app-header p {{
        font-size: 0.95rem;
        margin-top: 0.35rem;
        margin-bottom: 2rem;
        color: {palette["text"]};
        opacity: 0.65;
    }}


    /*SECTION TITLE*/

    h2 {{
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        color: {palette["text"]} !important;
        margin-top: 2rem !important;
        margin-bottom: 0.5rem !important;
    }}

    h3 {{
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: {palette["text"]} !important;
    }}

    .section-description {{
        font-size: 0.9rem;
        margin-top: -0.25rem;
        margin-bottom: 1rem;
        color: {palette["text"]};
        opacity: 0.65;
    }}


    /*METRIC CARD*/

    .metric-card {{
        background-color: {palette["card_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        padding: 1rem 1.1rem;
        min-height: 90px;
    }}

    .metric-label {{
        font-size: 0.8rem;
        margin-bottom: 0.35rem;
        color: {palette["text_muted"]};
    }}

    .metric-value {{
        font-size: 1.35rem;
        font-weight: 600;
        color: {palette["text"]};
    }}


    /*UPLOAD NOTICE*/

    .upload-notice {{
        background-color: {palette["card_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 0.9rem;
        margin-bottom: 1.5rem;
        color: {palette["text"]};
        font-size: 0.9rem;
    }}


    /*FILE UPLOADER*/

    div[data-testid="stFileUploader"] {{
        background-color: {palette["card_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        padding: 0.25rem;
    }}


    /*SELECTED ANALYSIS*/

    .selected-box {{
        background-color: {palette["card_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }}

    .selected-item {{
        font-size: 0.9rem;
        padding: 0.18rem 0;
        color: {palette["text"]};
    }}


    /*ANALYSIS TITLE INSIDE CONTAINER*/

    .workspace-title {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {palette["text"]};
        margin-bottom: 0.2rem;
    }}

    .workspace-description {{
        font-size: 0.85rem;
        color: {palette["text_muted"]};
        line-height: 1.4;
    }}


    /*DATAFRAME*/

    div[data-testid="stDataFrame"] {{
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        overflow: hidden;
    }}


    /*BUTTON*/

    div.stButton > button {{
        border-radius: 8px;
        font-weight: 500;
    }}


    /*CHECKBOX*/

    div[data-testid="stCheckbox"] {{
        margin-bottom: 0.1rem;
    }}


    /*TABS*/

    button[data-baseweb="tab"] {{
        font-weight: 500;
    }}


    /*EXPANDER */

    details {{
        border-radius: 8px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


#READ UPLOADED FILE (CSV / XLS / XLSX)
@st.cache_data(show_spinner="Reading file...")
def read_uploaded_file(file_bytes, file_name):
    """
    Membaca file CSV, XLS, atau XLSX.
    Menerima bytes + nama file (bukan UploadedFile) agar bisa di-cache.
    """

    file_name = file_name.lower()

    # ===== CSV =====
    if file_name.endswith(".csv"):

        encodings_to_try = ["utf-8", "utf-8-sig", "ISO-8859-1", "cp1252"]

        df = None
        last_error = None

        for enc in encodings_to_try:

            try:
                buf = io.BytesIO(file_bytes)
                df = pd.read_csv(buf, encoding=enc)
                break

            except UnicodeDecodeError as e:
                last_error = e
                continue

            except pd.errors.ParserError as e:
                try:
                    buf = io.BytesIO(file_bytes)
                    df = pd.read_csv(
                        buf,
                        encoding=enc,
                        sep=None,
                        engine="python"
                    )
                    break
                except Exception as e2:
                    last_error = e2
                    continue

        if df is None:
            raise ValueError(
                f"Gagal membaca CSV dengan semua encoding yang dicoba. "
                f"Error terakhir: {last_error}"
            )

        return df

    # ===== XLS (Excel lama, format biner) =====
    elif file_name.endswith(".xls"):

        buf = io.BytesIO(file_bytes)

        try:
            df = pd.read_excel(buf, engine="xlrd")
        except ImportError:
            raise ImportError(
                "Package 'xlrd' belum terinstall. Jalankan: pip install xlrd"
            )

        return df

    # ===== XLSX (Excel baru, format XML) =====
    elif file_name.endswith(".xlsx"):

        buf = io.BytesIO(file_bytes)

        try:
            df = pd.read_excel(buf, engine="openpyxl")
        except ImportError:
            raise ImportError(
                "Package 'openpyxl' belum terinstall. Jalankan: pip install openpyxl"
            )

        return df

    else:
        raise ValueError(
            "Format file tidak didukung. Gunakan CSV, XLS, atau XLSX."
        )


#DETECT DATETIME COLUMNS
@st.cache_data(show_spinner=False)
def detect_datetime_columns(df):

    datetime_columns = []
    converted_df = df.copy()

    date_keywords = [
        "date",
        "datetime",
        "timestamp",
        "time"
    ]

    for column in df.columns:

        column_name = str(column).lower().strip()

        keyword_match = any(
            keyword in column_name
            for keyword in date_keywords
        )

        if not keyword_match:
            continue

        parsed = pd.to_datetime(
            df[column],
            errors="coerce",
            dayfirst=True
        )

        valid_ratio = parsed.notna().mean()

        if valid_ratio >= 0.5:

            converted_df[column] = parsed
            datetime_columns.append(column)

    return datetime_columns, converted_df

#DETECT IDENTIFIER COLUMNS
@st.cache_data(show_spinner=False)
def detect_identifier_columns(df):

    identifier_columns = []

    for column in df.columns:

        column_name = str(column).lower().strip()

        unique_count = df[column].nunique(dropna=True)
        total_count = len(df)

        if total_count == 0:
            continue

        unique_ratio = unique_count / total_count

        name_is_identifier = (
            "id" in column_name
            or "code" in column_name
            or "identifier" in column_name
        )

        high_uniqueness = (
            unique_ratio >= 0.95
            and unique_count > 20
        )

        if name_is_identifier or high_uniqueness:
            identifier_columns.append(column)

    return identifier_columns


#APPLY MANUAL COLUMN TYPE OVERRIDES
def apply_dtype_overrides(
    datetime_columns,
    identifier_columns,
    numerical_columns_source,
    categorical_columns_source,
    dtype_overrides
):
    """
    Menggabungkan hasil auto-detect dengan override manual dari user.
    Override manual selalu menang dibanding auto-detect.
    """

    datetime_columns = list(datetime_columns)
    identifier_columns = list(identifier_columns)

    for column, override in dtype_overrides.items():

        if override == "Datetime":

            if column not in datetime_columns:
                datetime_columns.append(column)

            if column in identifier_columns:
                identifier_columns.remove(column)

        elif override == "Identifier":

            if column not in identifier_columns:
                identifier_columns.append(column)

            if column in datetime_columns:
                datetime_columns.remove(column)

        elif override in ("Numeric", "Categorical/Text"):

            if column in identifier_columns:
                identifier_columns.remove(column)

            if column in datetime_columns:
                datetime_columns.remove(column)

    return datetime_columns, identifier_columns


#CLASSIFY NUMERIC / CATEGORICAL COLUMNS (respecting overrides)
def classify_columns(df, datetime_columns, identifier_columns, dtype_overrides):

    numerical_columns = []
    categorical_columns = []

    for column in df.columns:

        if column in datetime_columns or column in identifier_columns:
            continue

        override = dtype_overrides.get(column)

        if override == "Numeric":
            numerical_columns.append(column)

        elif override == "Categorical/Text":
            categorical_columns.append(column)

        elif pd.api.types.is_numeric_dtype(df[column]):
            numerical_columns.append(column)

        else:
            categorical_columns.append(column)

    return numerical_columns, categorical_columns


#CHART STYLE HELPER
CHART_COLORS = {
    "primary": "#818CF8",
    "secondary": "#4F46E5",
    "positive": "#10B981",
    "negative": "#EF4444",
    "accent": "#F59E0B",
    "bg": "#0E1117",
    "card_bg": "#161B22",
    "grid": "#30363D",
    "text": "#E5E7EB",
    "text_muted": "#8B949E",
}


def apply_chart_style(fig, ax):
    """Apply dark-theme styling to matplotlib figure."""
    fig.patch.set_facecolor(CHART_COLORS["bg"])
    ax.set_facecolor(CHART_COLORS["card_bg"])
    ax.tick_params(colors=CHART_COLORS["text_muted"], labelsize=9)
    ax.xaxis.label.set_color(CHART_COLORS["text_muted"])
    ax.yaxis.label.set_color(CHART_COLORS["text_muted"])
    ax.title.set_color(CHART_COLORS["text"])
    ax.title.set_fontsize(12)
    ax.title.set_fontweight(600)
    ax.grid(True, alpha=0.15, color=CHART_COLORS["grid"])
    for spine in ax.spines.values():
        spine.set_color(CHART_COLORS["grid"])
    fig.tight_layout()
    return fig, ax


#EXPORT HELPERS
def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


#CACHED OVERVIEW METRICS
@st.cache_data(show_spinner=False)
def compute_overview_metrics(df):
    return {
        "missing": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
    }


def df_to_excel_bytes(df):
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Result")
        return buffer.getvalue()
    except ImportError:
        return None


def fig_to_png_bytes(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buffer.seek(0)
    return buffer.getvalue()


def render_export_buttons(result_df, fig_or_builder, filename_base, key_prefix):
    """
    fig_or_builder: matplotlib Figure OR callable that returns a Figure.
    If callable, figure is built lazily only when PNG export is needed.
    """

    has_fig = fig_or_builder is not None

    if has_fig:
        col1, col2, col3 = st.columns(3)
    else:
        col1, col2 = st.columns(2)
        col3 = None

    with col1:
        st.download_button(
            "CSV",
            df_to_csv_bytes(result_df),
            file_name=f"{filename_base}.csv",
            mime="text/csv",
            key=f"{key_prefix}_csv",
            use_container_width=True
        )

    with col2:
        excel_bytes = df_to_excel_bytes(result_df)

        if excel_bytes is not None:
            st.download_button(
                "Excel",
                excel_bytes,
                file_name=f"{filename_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key_prefix}_excel",
                use_container_width=True
            )
        else:
            st.button(
                "Excel unavailable",
                disabled=True,
                key=f"{key_prefix}_excel_disabled",
                use_container_width=True,
                help="Install 'openpyxl' to enable Excel export (pip install openpyxl)"
            )

    if has_fig and col3 is not None:
        with col3:
            # Lazy: build fig only when exporting
            fig = fig_or_builder() if callable(fig_or_builder) else fig_or_builder
            st.download_button(
                "Chart (PNG)",
                fig_to_png_bytes(fig),
                file_name=f"{filename_base}.png",
                mime="image/png",
                key=f"{key_prefix}_png",
                use_container_width=True
            )
            plt.close(fig)


#GENERATE SUGGESTED ANALYSIS
def generate_suggestions(
    df,
    numerical_columns,
    categorical_columns,
    datetime_columns
):

    suggestions = []

    sales_column = None
    profit_column = None
    quantity_column = None

    for column in numerical_columns:

        column_name = str(column).lower().strip()

        if "sales" in column_name:
            sales_column = column

        elif "profit" in column_name:
            profit_column = column

        elif "quantity" in column_name:
            quantity_column = column

    #TIME ANALYSIS
    if datetime_columns:

        if sales_column:

            suggestions.append({
                "name": "Sales Trend Over Time",
                "description": "Analyze how sales change over time.",
                "category": "Time Analysis",
                "type": "sales_trend"
            })

        if profit_column:

            suggestions.append({
                "name": "Profit Trend Over Time",
                "description": "Analyze how profit changes over time.",
                "category": "Time Analysis",
                "type": "profit_trend"
            })

        if sales_column or profit_column:

            suggestions.append({
                "name": "Growth Rate / Period Comparison",
                "description": (
                    "Compare month-over-month growth rate for the "
                    "selected metric."
                ),
                "category": "Time Analysis",
                "type": "growth_rate"
            })

    #CATEGORY ANALYSIS
    if categorical_columns:

        preferred_categories = [
            "category",
            "sub-category",
            "segment",
            "region",
            "ship mode"
        ]

        selected_categories = []

        for preferred in preferred_categories:

            for column in categorical_columns:

                if column.lower().strip() == preferred:

                    selected_categories.append(
                        column
                    )

        selected_categories = list(
            dict.fromkeys(selected_categories)
        )

        selected_categories = selected_categories[:4]

        for category_column in selected_categories:

            if sales_column:

                suggestions.append({
                    "name": f"Sales by {category_column}",
                    "description": (
                        f"Compare sales performance across "
                        f"{category_column}."
                    ),
                    "category": "Category Analysis",
                    "type": "sales_by_category",
                    "dimension": category_column
                })

            if profit_column:

                suggestions.append({
                    "name": f"Profit by {category_column}",
                    "description": (
                        f"Compare profit performance across "
                        f"{category_column}."
                    ),
                    "category": "Category Analysis",
                    "type": "profit_by_category",
                    "dimension": category_column
                })

        if sales_column or profit_column:

            suggestions.append({
                "name": "Top & Bottom Performers",
                "description": (
                    "Show the best and worst performing items for a "
                    "chosen dimension and metric."
                ),
                "category": "Category Analysis",
                "type": "top_bottom_performer"
            })

    #RELATIONSHIP ANALYSIS
    if sales_column and profit_column:

        suggestions.append({
            "name": "Sales vs Profit",
            "description": (
                "Analyze the relationship between sales and profit."
            ),
            "category": "Relationship Analysis",
            "type": "sales_vs_profit"
        })

    if sales_column and quantity_column:

        suggestions.append({
            "name": "Quantity vs Sales",
            "description": (
                "Analyze the relationship between quantity and sales."
            ),
            "category": "Relationship Analysis",
            "type": "quantity_vs_sales"
        })

    if len(numerical_columns) >= 2:

        suggestions.append({
            "name": "Correlation Heatmap",
            "description": (
                "See how numerical columns relate to one another."
            ),
            "category": "Relationship Analysis",
            "type": "correlation_heatmap"
        })

    #DATA QUALITY ANALYSIS
    if numerical_columns:

        suggestions.append({
            "name": "Outlier Detection (IQR)",
            "description": (
                "Detect extreme values in a numerical column using "
                "the IQR method."
            ),
            "category": "Data Quality Analysis",
            "type": "outlier_detection"
        })

    return suggestions


#HEADER
header_col1, header_col2 = st.columns([9, 1])

with header_col1:

    st.markdown(
        """
        <div class="app-header">
            <h1>DataInsight</h1>
            <p>Explore, analyze, and understand your business data.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_col2:

    theme_icon = "Light Mode" if st.session_state.theme == "dark" else "Dark Mode"

    if st.button(theme_icon, key="theme_toggle", use_container_width=True):

        st.session_state.theme = (
            "light" if st.session_state.theme == "dark" else "dark"
        )

        st.rerun()



#FILE UPLOAD
uploaded_file = st.file_uploader(
    "Upload dataset",
    type=["csv", "xlsx", "xls"],
    help="Supported formats: CSV and Excel"
)



#MAIN APP
if uploaded_file is not None:

    try:

        #READ DATASET
        raw_df = read_uploaded_file(uploaded_file.getvalue(), uploaded_file.name)

        #RESET STATE WHEN A NEW FILE IS UPLOADED
        if (
            uploaded_file.name
            != st.session_state.last_uploaded_file
        ):

            st.session_state.last_uploaded_file = (
                uploaded_file.name
            )

            st.session_state.show_upload_notice = True
            st.session_state.working_df = raw_df.copy()
            st.session_state.dtype_overrides = {}
            st.session_state.show_workspace = False

        #SUCCESS NOTIFICATION
        if st.session_state.show_upload_notice:

            notice_col1, notice_col2 = st.columns(
                [12, 1],
                vertical_alignment="center"
            )

            with notice_col1:

                st.markdown(
                    f"""
                    <div class="upload-notice">
                        {uploaded_file.name} loaded successfully.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with notice_col2:

                if st.button(
                    "x",
                    key="close_upload_notice",
                    help="Close notification"
                ):

                    st.session_state.show_upload_notice = False

                    st.rerun()

        # PROFILING (based on the cleaned working copy)
        base_df = st.session_state.working_df

        datetime_columns, base_df = detect_datetime_columns(base_df)

        identifier_columns = detect_identifier_columns(base_df)

        datetime_columns, identifier_columns = apply_dtype_overrides(
            datetime_columns,
            identifier_columns,
            None,
            None,
            st.session_state.dtype_overrides
        )

        numerical_columns, categorical_columns = classify_columns(
            base_df,
            datetime_columns,
            identifier_columns,
            st.session_state.dtype_overrides
        )

        #DATA QUALITY TOOLS
        st.header("Data Quality Tools")

        st.markdown(
            """
            <div class="section-description">
                Handle missing values, duplicate rows, and column type
                overrides before running your analysis.
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("Open Data Quality Tools"):

            dq_tab1, dq_tab2, dq_tab3 = st.tabs(
                ["Missing Values", "Duplicate Rows", "Column Types"]
            )

            #MISSING VALUES
            with dq_tab1:

                missing_summary = base_df.isna().sum()
                missing_summary = missing_summary[missing_summary > 0]

                if missing_summary.empty:

                    st.success("No missing values found in this dataset.")

                else:

                    st.caption(
                        "Choose how to handle missing values per column."
                    )

                    missing_actions = {}

                    for column in missing_summary.index:

                        pct = base_df[column].isna().mean() * 100
                        is_numeric = pd.api.types.is_numeric_dtype(
                            base_df[column]
                        )

                        options = ["Keep as is", "Drop rows"]

                        if is_numeric:
                            options += ["Fill with Mean", "Fill with Median"]

                        options += ["Fill with Mode", "Fill with custom value"]

                        col_a, col_b = st.columns([2, 3])

                        with col_a:
                            st.write(
                                f"**{column}** "
                                f"({int(missing_summary[column])} missing, "
                                f"{pct:.1f}%)"
                            )

                        with col_b:
                            action = st.selectbox(
                                "Action",
                                options,
                                key=f"missing_action_{column}",
                                label_visibility="collapsed"
                            )

                        custom_value = None

                        if action == "Fill with custom value":

                            custom_value = st.text_input(
                                f"Custom value for {column}",
                                key=f"missing_custom_{column}"
                            )

                        missing_actions[column] = (action, custom_value)

                    if st.button(
                        "Apply Missing Value Actions",
                        key="apply_missing"
                    ):

                        new_df = base_df.copy()

                        for column, (action, custom_value) in missing_actions.items():

                            if action == "Drop rows":
                                new_df = new_df[new_df[column].notna()]

                            elif action == "Fill with Mean":
                                new_df[column] = new_df[column].fillna(
                                    new_df[column].mean()
                                )

                            elif action == "Fill with Median":
                                new_df[column] = new_df[column].fillna(
                                    new_df[column].median()
                                )

                            elif action == "Fill with Mode":

                                mode_values = new_df[column].mode()

                                if not mode_values.empty:
                                    new_df[column] = new_df[column].fillna(
                                        mode_values.iloc[0]
                                    )

                            elif (
                                action == "Fill with custom value"
                                and custom_value not in (None, "")
                            ):
                                new_df[column] = new_df[column].fillna(
                                    custom_value
                                )

                        st.session_state.working_df = new_df.reset_index(
                            drop=True
                        )

                        st.success("Missing value actions applied.")
                        st.rerun()

            #DUPLICATE ROWS
            with dq_tab2:

                duplicate_count = base_df.duplicated().sum()

                st.write(
                    f"Found **{duplicate_count}** duplicate row(s)."
                )

                if duplicate_count > 0:

                    with st.expander("View duplicate rows"):

                        st.dataframe(
                            base_df[base_df.duplicated(keep=False)],
                            use_container_width=True,
                            hide_index=True
                        )

                    if st.button(
                        "Remove Duplicate Rows",
                        key="remove_duplicates"
                    ):

                        st.session_state.working_df = (
                            base_df.drop_duplicates().reset_index(drop=True)
                        )

                        st.success("Duplicate rows removed.")
                        st.rerun()

            #COLUMN TYPES
            with dq_tab3:

                st.caption(
                    "Override a column's type if auto-detection got it "
                    "wrong (e.g. a ZIP code detected as numeric)."
                )

                type_options = [
                    "Auto-detect",
                    "Numeric",
                    "Categorical/Text",
                    "Datetime",
                    "Identifier"
                ]

                pending_overrides = {}

                for column in base_df.columns:

                    if column in datetime_columns:
                        detected_label = "Datetime"
                    elif column in identifier_columns:
                        detected_label = "Identifier"
                    elif column in numerical_columns:
                        detected_label = "Numeric"
                    else:
                        detected_label = "Categorical/Text"

                    current_override = st.session_state.dtype_overrides.get(
                        column, "Auto-detect"
                    )

                    col_a, col_b = st.columns([2, 3])

                    with col_a:
                        st.write(
                            f"**{column}**  \n_detected: {detected_label}_"
                        )

                    with col_b:
                        selected = st.selectbox(
                            "Type",
                            type_options,
                            index=type_options.index(current_override),
                            key=f"dtype_override_{column}",
                            label_visibility="collapsed"
                        )

                    if selected != "Auto-detect":
                        pending_overrides[column] = selected

                if st.button(
                    "Apply Column Type Changes",
                    key="apply_dtype"
                ):

                    st.session_state.dtype_overrides = pending_overrides
                    st.success("Column types updated.")
                    st.rerun()

        #INTERACTIVE FILTERS
        st.header("Filters")

        st.markdown(
            """
            <div class="section-description">
                Narrow down the dataset before running the analyses below.
            </div>
            """,
            unsafe_allow_html=True
        )

        filtered_df = base_df  # filters below create new frames; no copy needed

        with st.expander("Open Filters", expanded=False):

            #DATE RANGE FILTER
            if datetime_columns:

                date_column = datetime_columns[0]

                valid_dates = base_df[date_column].dropna()

                if not valid_dates.empty:

                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()

                    date_range = st.date_input(
                        f"Date range ({date_column})",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key="filter_date_range"
                    )

                    if isinstance(date_range, tuple) and len(date_range) == 2:

                        start_date, end_date = date_range

                        filtered_df = filtered_df[
                            (filtered_df[date_column].dt.date >= start_date)
                            & (filtered_df[date_column].dt.date <= end_date)
                        ]

            #CATEGORICAL FILTERS
            filterable_columns = [
                column
                for column in categorical_columns
                if 1 < base_df[column].nunique(dropna=True) <= 50
            ]

            filterable_columns = filterable_columns[:4]

            filter_columns_layout = st.columns(
                len(filterable_columns)
            ) if filterable_columns else []

            for column, layout_col in zip(
                filterable_columns, filter_columns_layout
            ):

                with layout_col:

                    options = sorted(
                        base_df[column].dropna().unique().tolist(),
                        key=lambda value: str(value)
                    )

                    selected_values = st.multiselect(
                        column,
                        options=options,
                        default=[],
                        key=f"filter_{column}"
                    )

                    if selected_values:

                        filtered_df = filtered_df[
                            filtered_df[column].isin(selected_values)
                        ]

        st.caption(
            f"Showing {len(filtered_df):,} of {len(base_df):,} rows "
            f"after filters."
        )

        #DATASET OVERVIEW
        st.header("Dataset Overview")

        st.markdown(
            """
            <div class="section-description">
                Basic information about the filtered dataset.
            </div>
            """,
            unsafe_allow_html=True
        )

        overview_metrics = compute_overview_metrics(filtered_df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Rows</div>
                    <div class="metric-value">
                        {filtered_df.shape[0]:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Columns</div>
                    <div class="metric-value">
                        {filtered_df.shape[1]:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        Missing Values
                    </div>
                    <div class="metric-value">
                        {overview_metrics["missing"]:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col4:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">
                        Duplicate Rows
                    </div>
                    <div class="metric-value">
                        {overview_metrics["duplicates"]:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        #DATASET PREVIEW
        st.header("Dataset Preview")

        st.markdown(
            """
            <div class="section-description">
                Preview rows of the filtered dataset. Use the search box
                to find specific rows.
            </div>
            """,
            unsafe_allow_html=True
        )

        search_term = st.text_input(
            "Search in preview",
            placeholder="Type to search across all columns...",
            key="preview_search"
        )

        preview_df = filtered_df

        if search_term:

            # ponytail: search limited to 5000 rows for speed; upgrade to server-side search if needed
            search_subset = filtered_df.head(5000)
            mask = (
                search_subset
                .astype(str)
                .apply(
                    lambda row: row.str.contains(
                        search_term, case=False, na=False
                    )
                )
                .any(axis=1)
            )

            preview_df = search_subset[mask]

            note = ""
            if len(filtered_df) > 5000:
                note = f" (searched first 5,000 of {len(filtered_df):,} rows)"

            st.caption(
                f"Found {len(preview_df):,} matching row(s){note}."
            )

        st.dataframe(
            preview_df.head(10),
            use_container_width=True,
            hide_index=True
        )

        #DATASET PROFILE
        st.header("Dataset Profile")

        st.markdown(
            """
            <div class="section-description">
                Review the detected structure and data types.
            </div>
            """,
            unsafe_allow_html=True
        )

        profile_tab_1, profile_tab_2 = st.tabs([
            "Column Information",
            "Column Classification"
        ])

        #COLUMN INFORMATION
        with profile_tab_1:

            column_info = pd.DataFrame({
                "Column": filtered_df.columns,

                "Data Type": [
                    str(filtered_df[column].dtype)
                    for column in filtered_df.columns
                ],

                "Unique Values": [
                    filtered_df[column].nunique(dropna=True)
                    for column in filtered_df.columns
                ],

                "Missing Values": [
                    filtered_df[column].isna().sum()
                    for column in filtered_df.columns
                ],

                "Missing (%)": [
                    round(
                        filtered_df[column].isna().mean() * 100,
                        2
                    )
                    for column in filtered_df.columns
                ]
            })

            st.dataframe(
                column_info,
                use_container_width=True,
                hide_index=True
            )

        # COLUMN CLASSIFICATION
        with profile_tab_2:

            col1, col2 = st.columns(2)

            with col1:

                st.subheader("Numerical")

                if numerical_columns:

                    st.write(
                        "\n".join(
                            f"- {column}"
                            for column in numerical_columns
                        )
                    )

                else:

                    st.write("None")

                st.subheader("Categorical")

                if categorical_columns:

                    st.write(
                        "\n".join(
                            f"- {column}"
                            for column in categorical_columns
                        )
                    )

                else:

                    st.write("None")

            with col2:

                st.subheader("Datetime")

                if datetime_columns:

                    st.write(
                        "\n".join(
                            f"- {column}"
                            for column in datetime_columns
                        )
                    )

                else:

                    st.write("None")

                st.subheader("Identifier")

                if identifier_columns:

                    st.write(
                        "\n".join(
                            f"- {column}"
                            for column in identifier_columns
                        )
                    )

                else:

                    st.write("None")

        #NUMERICAL STATISTICS
        if numerical_columns:

            with st.expander("Numerical Statistics"):

                statistics = (
                    filtered_df[numerical_columns]
                    .describe()
                    .T
                )

                statistics["Unique"] = [
                    filtered_df[column].nunique(dropna=True)
                    for column in numerical_columns
                ]

                statistics["Missing"] = [
                    filtered_df[column].isna().sum()
                    for column in numerical_columns
                ]

                statistics = statistics[
                    [
                        "count",
                        "Unique",
                        "mean",
                        "std",
                        "min",
                        "25%",
                        "50%",
                        "75%",
                        "max",
                        "Missing"
                    ]
                ]

                st.dataframe(
                    statistics.round(2),
                    use_container_width=True,
                    hide_index=True
                )

        #SUGGESTED ANALYSIS
        st.header("Suggested Analysis")

        st.markdown(
            """
            <div class="section-description">
                Select one or more analyses based on the structure of the dataset.
            </div>
            """,
            unsafe_allow_html=True
        )

        suggestions = generate_suggestions(
            filtered_df,
            numerical_columns,
            categorical_columns,
            datetime_columns
        )

        selected_analysis = []

        if not suggestions:

            st.info(
                "No suitable analysis was found for this dataset."
            )

        else:

            current_category = None

            for index, suggestion in enumerate(suggestions):

                category = suggestion["category"]

                if category != current_category:

                    st.subheader(category)
                    current_category = category

                selected = st.checkbox(
                    suggestion["name"],
                    key=f"analysis_{index}"
                )

                st.caption(
                    suggestion["description"]
                )

                if selected:

                    selected_analysis.append(
                        suggestion
                    )

        #SELECTED ANALYSIS

        if suggestions:

            st.divider()

            st.subheader("Selected Analysis")

            if selected_analysis:

                selected_text = "".join(
                    f"""
                    <div class="selected-item">
                        {analysis["name"]}
                    </div>
                    """
                    for analysis in selected_analysis
                )

                st.markdown(
                    f"""
                    <div class="selected-box">
                        {selected_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                analyze_clicked = st.button(
                    f"Analyze Selected ({len(selected_analysis)})",
                    type="primary",
                    use_container_width=True
                )

                if analyze_clicked:
                    st.session_state.show_workspace = True

                #ANALYSIS WORKSPACE
                if st.session_state.show_workspace:

                    st.header("Analysis Workspace")

                    st.markdown(
                        """
                        <div class="section-description">
                            Results for the selected analyses.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    for analysis_index, analysis in enumerate(selected_analysis):

                        analysis_type = analysis["type"]
                        key_prefix = f"result_{analysis_index}_{analysis_type}"


                        #ANALYSIS CONTAINER

                        with st.container(border=True):

                          try:

                            # TITLE + DESCRIPTION

                            st.markdown(
                                f"""
                                <div class="workspace-title">
                                    {analysis["name"]}
                                </div>

                                <div class="workspace-description">
                                    {analysis["description"]}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            st.divider()

                            # SALES TREND
                            if analysis_type == "sales_trend":

                                date_column = datetime_columns[0]

                                sales_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "sales" in column.lower()
                                    ),
                                    None
                                )

                                if sales_column:

                                    sales_data = (
                                        filtered_df
                                        .groupby(
                                            date_column
                                        )[sales_column]
                                        .sum()
                                        .reset_index()
                                    )

                                    st.line_chart(
                                        sales_data.set_index(
                                            date_column
                                        )[sales_column]
                                    )

                                    def _build_sales_fig(sd=sales_data, dc=date_column, sc=sales_column, name=analysis["name"]):
                                        fig, ax = plt.subplots(figsize=(8, 4))
                                        ax.plot(sd[dc], sd[sc], color=CHART_COLORS["primary"], linewidth=2)
                                        ax.fill_between(sd[dc], sd[sc], alpha=0.1, color=CHART_COLORS["primary"])
                                        ax.set_title(name)
                                        ax.set_xlabel(dc)
                                        ax.set_ylabel(sc)
                                        fig.autofmt_xdate()
                                        apply_chart_style(fig, ax)
                                        return fig

                                    with st.expander(
                                        "View detailed data"
                                    ):

                                        st.dataframe(
                                            sales_data,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        sales_data, _build_sales_fig,
                                        "sales_trend", key_prefix
                                    )

                                else:

                                    st.warning(
                                        "Sales column could not be identified."
                                    )

                            # PROFIT TREND
                            elif analysis_type == "profit_trend":

                                date_column = datetime_columns[0]

                                profit_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "profit" in column.lower()
                                    ),
                                    None
                                )

                                if profit_column:

                                    profit_data = (
                                        filtered_df
                                        .groupby(
                                            date_column
                                        )[profit_column]
                                        .sum()
                                        .reset_index()
                                    )

                                    st.line_chart(
                                        profit_data.set_index(
                                            date_column
                                        )[profit_column]
                                    )

                                    def _build_profit_fig(pd_=profit_data, dc=date_column, pc=profit_column, name=analysis["name"]):
                                        fig, ax = plt.subplots(figsize=(8, 4))
                                        ax.plot(pd_[dc], pd_[pc], color=CHART_COLORS["positive"], linewidth=2)
                                        ax.fill_between(pd_[dc], pd_[pc], alpha=0.1, color=CHART_COLORS["positive"])
                                        ax.set_title(name)
                                        ax.set_xlabel(dc)
                                        ax.set_ylabel(pc)
                                        fig.autofmt_xdate()
                                        apply_chart_style(fig, ax)
                                        return fig

                                    with st.expander(
                                        "View detailed data"
                                    ):

                                        st.dataframe(
                                            profit_data,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        profit_data, _build_profit_fig,
                                        "profit_trend", key_prefix
                                    )

                                else:

                                    st.warning(
                                        "Profit column could not be identified."
                                    )

                            # GROWTH RATE / PERIOD COMPARISON
                            elif analysis_type == "growth_rate":

                                date_column = datetime_columns[0]

                                metric_candidates = [
                                    column
                                    for column in numerical_columns
                                    if "sales" in column.lower()
                                    or "profit" in column.lower()
                                ]

                                if metric_candidates:

                                    metric_column = st.selectbox(
                                        "Metric",
                                        metric_candidates,
                                        key=f"{key_prefix}_metric"
                                    )

                                    period_series = (
                                        filtered_df
                                        .dropna(subset=[date_column])
                                        .set_index(date_column)[metric_column]
                                        .resample("MS")
                                        .sum()
                                    )

                                    growth_data = period_series.pct_change().reset_index()
                                    growth_data.columns = [
                                        date_column, "Growth Rate (%)"
                                    ]
                                    growth_data["Growth Rate (%)"] = (
                                        growth_data["Growth Rate (%)"] * 100
                                    ).round(2)

                                    st.bar_chart(
                                        growth_data.set_index(date_column)[
                                            "Growth Rate (%)"
                                        ]
                                    )

                                    def _build_growth_fig(gd=growth_data, dc=date_column, name=analysis["name"]):
                                        fig, ax = plt.subplots(figsize=(8, 4))
                                        colors = [CHART_COLORS["positive"] if v >= 0 else CHART_COLORS["negative"] for v in gd["Growth Rate (%)"]]
                                        ax.bar(gd[dc].astype(str), gd["Growth Rate (%)"], color=colors)
                                        ax.axhline(0, linewidth=0.8, color=CHART_COLORS["text_muted"])
                                        ax.set_title(name)
                                        ax.set_ylabel("Growth Rate (%)")
                                        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
                                        apply_chart_style(fig, ax)
                                        return fig

                                    with st.expander(
                                        "View detailed data"
                                    ):

                                        st.dataframe(
                                            growth_data,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        growth_data, _build_growth_fig,
                                        "growth_rate", key_prefix
                                    )

                                else:

                                    st.warning(
                                        "No Sales/Profit column could be identified."
                                    )

                            # SALES BY CATEGORY
                            elif analysis_type == "sales_by_category":

                                dimension = analysis["dimension"]

                                sales_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "sales" in column.lower()
                                    ),
                                    None
                                )

                                if sales_column:

                                    result = (
                                        filtered_df
                                        .groupby(
                                            dimension
                                        )[sales_column]
                                        .sum()
                                        .sort_values(
                                            ascending=False
                                        )
                                        .reset_index()
                                    )

                                    st.bar_chart(
                                        result.set_index(
                                            dimension
                                        )[sales_column]
                                    )

                                    def _build_sbc_fig(r=result, dim=dimension, sc=sales_column, name=analysis["name"]):
                                        fig, ax = plt.subplots(figsize=(8, 4))
                                        ax.bar(r[dim].astype(str), r[sc], color=CHART_COLORS["primary"])
                                        ax.set_title(name)
                                        ax.set_ylabel(sc)
                                        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
                                        apply_chart_style(fig, ax)
                                        return fig

                                    with st.expander(
                                        "View detailed data"
                                    ):

                                        st.dataframe(
                                            result,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        result, _build_sbc_fig,
                                        f"sales_by_{dimension}", key_prefix
                                    )

                                else:

                                    st.warning(
                                        "Sales column could not be identified."
                                    )

                            # PROFIT BY CATEGORY
                            elif analysis_type == "profit_by_category":

                                dimension = analysis["dimension"]

                                profit_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "profit" in column.lower()
                                    ),
                                    None
                                )

                                if profit_column:

                                    result = (
                                        filtered_df
                                        .groupby(
                                            dimension
                                        )[profit_column]
                                        .sum()
                                        .sort_values(
                                            ascending=False
                                        )
                                        .reset_index()
                                    )

                                    st.bar_chart(
                                        result.set_index(
                                            dimension
                                        )[profit_column]
                                    )

                                    def _build_pbc_fig(r=result, dim=dimension, pc=profit_column, name=analysis["name"]):
                                        fig, ax = plt.subplots(figsize=(8, 4))
                                        ax.bar(r[dim].astype(str), r[pc], color=CHART_COLORS["positive"])
                                        ax.set_title(name)
                                        ax.set_ylabel(pc)
                                        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
                                        apply_chart_style(fig, ax)
                                        return fig

                                    with st.expander(
                                        "View detailed data"
                                    ):

                                        st.dataframe(
                                            result,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        result, _build_pbc_fig,
                                        f"profit_by_{dimension}", key_prefix
                                    )

                                else:

                                    st.warning(
                                        "Profit column could not be identified."
                                    )

                            # TOP & BOTTOM PERFORMERS
                            elif analysis_type == "top_bottom_performer":

                                metric_candidates = [
                                    column
                                    for column in numerical_columns
                                    if "sales" in column.lower()
                                    or "profit" in column.lower()
                                ]

                                if metric_candidates and categorical_columns:

                                    setting_col1, setting_col2, setting_col3 = st.columns(3)

                                    with setting_col1:
                                        metric_column = st.selectbox(
                                            "Metric",
                                            metric_candidates,
                                            key=f"{key_prefix}_metric"
                                        )

                                    with setting_col2:
                                        dimension_column = st.selectbox(
                                            "Dimension",
                                            categorical_columns,
                                            key=f"{key_prefix}_dimension"
                                        )

                                    with setting_col3:
                                        top_n = st.slider(
                                            "N",
                                            min_value=3,
                                            max_value=15,
                                            value=5,
                                            key=f"{key_prefix}_n"
                                        )

                                    grouped = (
                                        filtered_df
                                        .groupby(dimension_column)[metric_column]
                                        .sum()
                                        .sort_values(ascending=False)
                                        .reset_index()
                                    )

                                    top_performers = grouped.head(top_n)
                                    bottom_performers = grouped.tail(top_n).sort_values(
                                        by=metric_column
                                    )

                                    combined = pd.concat([
                                        top_performers.assign(Group="Top"),
                                        bottom_performers.assign(Group="Bottom")
                                    ])

                                    fig, ax = plt.subplots(figsize=(8, 5))
                                    colors = [
                                        CHART_COLORS["positive"] if group == "Top" else CHART_COLORS["negative"]
                                        for group in combined["Group"]
                                    ]
                                    ax.barh(
                                        combined[dimension_column].astype(str),
                                        combined[metric_column],
                                        color=colors
                                    )
                                    ax.set_title(analysis["name"])
                                    ax.set_xlabel(metric_column)
                                    ax.invert_yaxis()
                                    apply_chart_style(fig, ax)

                                    st.pyplot(fig, use_container_width=True)

                                    top_col, bottom_col = st.columns(2)

                                    with top_col:
                                        st.caption(f"Top {top_n}")
                                        st.dataframe(
                                            top_performers,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    with bottom_col:
                                        st.caption(f"Bottom {top_n}")
                                        st.dataframe(
                                            bottom_performers,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        combined, fig,
                                        "top_bottom_performers", key_prefix
                                    )
                                    plt.close(fig)

                                else:

                                    st.warning(
                                        "Not enough numerical/categorical "
                                        "columns for this analysis."
                                    )

                            # SALES VS PROFIT                        
                            elif analysis_type == "sales_vs_profit":

                                sales_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "sales" in column.lower()
                                    ),
                                    None
                                )

                                profit_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "profit" in column.lower()
                                    ),
                                    None
                                )

                                if sales_column and profit_column:

                                    scatter_data = filtered_df[
                                        [
                                            sales_column,
                                            profit_column
                                        ]
                                    ].dropna()

                                    st.scatter_chart(
                                        scatter_data,
                                        x=sales_column,
                                        y=profit_column
                                    )

                                    def _build_svp_fig(sd=scatter_data, sc=sales_column, pc=profit_column, name=analysis["name"]):
                                        fig, ax = plt.subplots(figsize=(8, 5))
                                        ax.scatter(sd[sc], sd[pc], alpha=0.5, s=15, color=CHART_COLORS["primary"])
                                        ax.set_title(name)
                                        ax.set_xlabel(sc)
                                        ax.set_ylabel(pc)
                                        apply_chart_style(fig, ax)
                                        return fig

                                    with st.expander(
                                        "View sample data"
                                    ):

                                        st.dataframe(
                                            scatter_data.head(100),
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        scatter_data, _build_svp_fig,
                                        "sales_vs_profit", key_prefix
                                    )

                                else:

                                    st.warning(
                                        "Sales or Profit column could not be identified."
                                    )

                           
                            # QUANTITY VS SALES
                            elif analysis_type == "quantity_vs_sales":

                                quantity_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "quantity" in column.lower()
                                    ),
                                    None
                                )

                                sales_column = next(
                                    (
                                        column
                                        for column in numerical_columns
                                        if "sales" in column.lower()
                                    ),
                                    None
                                )

                                if quantity_column and sales_column:

                                    scatter_data = filtered_df[
                                        [
                                            quantity_column,
                                            sales_column
                                        ]
                                    ].dropna()

                                    st.scatter_chart(
                                        scatter_data,
                                        x=quantity_column,
                                        y=sales_column
                                    )

                                    def _build_qvs_fig(sd=scatter_data, qc=quantity_column, sc=sales_column, name=analysis["name"]):
                                        fig, ax = plt.subplots(figsize=(8, 5))
                                        ax.scatter(sd[qc], sd[sc], alpha=0.5, s=15, color=CHART_COLORS["accent"])
                                        ax.set_title(name)
                                        ax.set_xlabel(qc)
                                        ax.set_ylabel(sc)
                                        apply_chart_style(fig, ax)
                                        return fig

                                    with st.expander(
                                        "View sample data"
                                    ):

                                        st.dataframe(
                                            scatter_data.head(100),
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                    render_export_buttons(
                                        scatter_data, _build_qvs_fig,
                                        "quantity_vs_sales", key_prefix
                                    )

                                else:

                                    st.warning(
                                        "Quantity or Sales column could not be identified."
                                    )

                            # CORRELATION HEATMAP
                            elif analysis_type == "correlation_heatmap":

                                corr_matrix = filtered_df[numerical_columns].corr()

                                fig, ax = plt.subplots(
                                    figsize=(
                                        max(6, len(numerical_columns) * 0.9),
                                        max(5, len(numerical_columns) * 0.8)
                                    )
                                )

                                im = ax.imshow(
                                    corr_matrix,
                                    cmap="RdBu_r",
                                    vmin=-1,
                                    vmax=1
                                )

                                ax.set_xticks(range(len(numerical_columns)))
                                ax.set_xticklabels(
                                    numerical_columns, rotation=45, ha="right"
                                )
                                ax.set_yticks(range(len(numerical_columns)))
                                ax.set_yticklabels(numerical_columns)

                                for i in range(len(numerical_columns)):
                                    for j in range(len(numerical_columns)):
                                        val = corr_matrix.iloc[i, j]
                                        ax.text(
                                            j, i,
                                            f"{val:.2f}",
                                            ha="center", va="center",
                                            fontsize=8,
                                            color="white" if abs(val) > 0.5 else CHART_COLORS["text_muted"]
                                        )

                                fig.colorbar(im, ax=ax, shrink=0.8)
                                ax.set_title(analysis["name"])
                                apply_chart_style(fig, ax)

                                st.pyplot(fig, use_container_width=True)

                                #STRONGEST CORRELATION INSIGHT
                                corr_pairs = (
                                    corr_matrix
                                    .where(
                                        np.triu(
                                            np.ones(corr_matrix.shape), k=1
                                        ).astype(bool)
                                    )
                                    .stack()
                                    .reset_index()
                                )
                                corr_pairs.columns = ["Column A", "Column B", "Correlation"]

                                if not corr_pairs.empty:

                                    strongest = corr_pairs.loc[
                                        corr_pairs["Correlation"].abs().idxmax()
                                    ]

                                    st.caption(
                                        f"Strongest relationship: "
                                        f"**{strongest['Column A']}** and "
                                        f"**{strongest['Column B']}** "
                                        f"(correlation = {strongest['Correlation']:.2f})"
                                    )

                                with st.expander("View correlation table"):

                                    st.dataframe(
                                        corr_matrix.round(2),
                                        use_container_width=True
                                    )

                                render_export_buttons(
                                    corr_matrix.reset_index(), fig,
                                    "correlation_heatmap", key_prefix
                                )
                                plt.close(fig)

                            # OUTLIER DETECTION (IQR)
                            elif analysis_type == "outlier_detection":

                                outlier_column = st.selectbox(
                                    "Column",
                                    numerical_columns,
                                    key=f"{key_prefix}_column"
                                )

                                series = filtered_df[outlier_column].dropna()

                                q1 = series.quantile(0.25)
                                q3 = series.quantile(0.75)
                                iqr = q3 - q1
                                lower_bound = q1 - 1.5 * iqr
                                upper_bound = q3 + 1.5 * iqr

                                outliers = filtered_df[
                                    (filtered_df[outlier_column] < lower_bound)
                                    | (filtered_df[outlier_column] > upper_bound)
                                ]

                                metric_col1, metric_col2, metric_col3 = st.columns(3)

                                with metric_col1:
                                    st.metric("Lower Bound", f"{lower_bound:.2f}")

                                with metric_col2:
                                    st.metric("Upper Bound", f"{upper_bound:.2f}")

                                with metric_col3:
                                    st.metric(
                                        "Outliers Found",
                                        f"{len(outliers):,} "
                                        f"({len(outliers) / len(filtered_df) * 100:.1f}%)"
                                    )

                                fig, ax = plt.subplots(figsize=(6, 4))
                                bp = ax.boxplot(series, vert=False, patch_artist=True,
                                    boxprops=dict(facecolor=CHART_COLORS["secondary"], alpha=0.7),
                                    medianprops=dict(color=CHART_COLORS["accent"]),
                                    whiskerprops=dict(color=CHART_COLORS["text_muted"]),
                                    capprops=dict(color=CHART_COLORS["text_muted"]),
                                    flierprops=dict(markeredgecolor=CHART_COLORS["negative"], markersize=4))
                                ax.set_title(f"{outlier_column} — Boxplot")
                                ax.set_xlabel(outlier_column)
                                apply_chart_style(fig, ax)

                                st.pyplot(fig, use_container_width=True)

                                with st.expander("View outlier rows"):

                                    st.dataframe(
                                        outliers.head(100),
                                        use_container_width=True,
                                        hide_index=True
                                    )

                                render_export_buttons(
                                    outliers, fig,
                                    f"outliers_{outlier_column}", key_prefix
                                )
                                plt.close(fig)

                          except Exception as analysis_error:
                            st.error(
                                f"⚠️ Error in **{analysis['name']}**: {analysis_error}"
                            )
            else:

                st.caption(
                    "Select at least one analysis to continue."
                )

    except Exception as e:

        st.error(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:0.5em"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg> Error while reading dataset: {e}'
        )
else:

    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 3rem 1rem;
            margin-top: 1rem;
            border: 1px dashed {palette['border']};
            border-radius: 12px;
            background: {palette['card_bg']};
        ">
            <svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="display:block;margin:0 auto 1rem auto;color:#4F46E5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
            <div style="font-size: 1.1rem; font-weight: 600; color: {palette['text']}; margin-bottom: 0.3rem;">
                No dataset loaded
            </div>
            <div style="font-size: 0.9rem; color: {palette['text_muted']};">
                Upload a CSV or Excel file above to start exploring your data.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
