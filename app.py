import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

try:
    from openai import OpenAI
except ImportError:
    st.warning("⚠️ جاري تحميل المكتبات المطلوبة...")

st.set_page_config(page_title="SmartStat Pro | الخبير الإحصائي", page_icon="📊", layout="wide")

# ==========================================
# --- إعدادات اللغة ---
# ==========================================
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'ar'

LABELS = {
    'ar': {
        'title': '📊 SmartStat Pro - نظام الخبير الإحصائي الآلي',
        'subtitle': 'يُرفق النظام الآن **تفسيراً أكاديمياً** مع كل نتيجة إحصائية جاهز للنسخ المباشر في فصول مناقشة النتائج.',
        'upload': 'قم برفع ملف البيانات الخام (CSV أو Excel)',
        'ai_settings': '🤖 إعدادات الذكاء الاصطناعي',
        'api_key': '🔑 مفتاح Hugging Face API:',
        'dimensions': '⚙️ بناء المحاور (Dimensions)',
        'detected': 'تم اكتشاف {} سؤال استبيان بنجاح!',
        'cat_vars': '👥 المتغيرات الشخصية (للمقارنة):',
        'num_dims': '🔢 كم عدد المحاور/الأبعاد في دراستك؟',
        'dim_name': 'اسم المحور {}:',
        'dim_default': 'المحور {}',
        'dim_cols': 'أسئلة {}:',
        'tabs': [
            '👥 عينة الدراسة', '📊 الإحصاء الوصفي', '🧪 الثبات (ألفا)',
            '⚖️ الفروق', '🔗 الارتباط', '📈 الانحدار',
            '🧠 محلل الفرضيات الذكي', '📌 النتائج', '💡 التوصيات',
        ],
        'warning_select': 'يرجى تحديد أسئلة المحاور من القائمة الجانبية للبدء.',
        'lang_toggle': '🌐 English',
        'results_title': '📌 أبرز نتائج الدراسة',
        'recs_title': '💡 التوصيات الذكية (بناءً على المتوسطات الحسابية)',
        'result_label': 'النتيجة ({})',
        'no_recs': 'لا توجد بيانات كافية لاستخراج التوصيات حالياً.',
        'axis_label': 'المحور', 'mean_label': 'المتوسط', 'rec_label': 'التوصية',
    },
    'en': {
        'title': '📊 SmartStat Pro - Automated Statistical Expert System',
        'subtitle': 'The system now attaches an **academic interpretation** with every statistical result, ready to paste directly into research chapters.',
        'upload': 'Upload your raw data file (CSV or Excel)',
        'ai_settings': '🤖 AI Settings',
        'api_key': '🔑 Hugging Face API Key:',
        'dimensions': '⚙️ Build Dimensions',
        'detected': 'Detected {} survey questions successfully!',
        'cat_vars': '👥 Demographic Variables (for comparison):',
        'num_dims': '🔢 How many dimensions/axes does your study have?',
        'dim_name': 'Dimension {} name:',
        'dim_default': 'Dimension {}',
        'dim_cols': 'Questions for {}:',
        'tabs': [
            '👥 Study Sample', '📊 Descriptive Stats', '🧪 Reliability (Alpha)',
            '⚖️ Differences', '🔗 Correlation', '📈 Regression',
            '🧠 Smart Hypothesis Analyzer', '📌 Results', '💡 Recommendations',
        ],
        'warning_select': 'Please select dimension questions from the sidebar to begin.',
        'lang_toggle': '🌐 عربي',
        'results_title': '📌 Key Study Results',
        'recs_title': '💡 Smart Recommendations (Based on Means)',
        'result_label': 'Result ({})',
        'no_recs': 'Not enough data to generate recommendations. Please check sidebar settings.',
        'axis_label': 'Dimension', 'mean_label': 'Mean', 'rec_label': 'Recommendation',
    }
}

# ==========================================
# --- CSS المخصص (RTL + خطوط + تصميم محسن) ---
# ==========================================
lang = st.session_state['lang']
direction = 'rtl' if lang == 'ar' else 'ltr'
font_family = "'Tajawal', 'IBM Plex Arabic', sans-serif" if lang == 'ar' else "'Outfit', 'DM Sans', sans-serif"
google_font = "https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&family=IBM+Plex+Arabic:wght@300;400;600&family=Outfit:wght@300;400;600;700&family=DM+Sans:wght@300;400;500&display=swap"

st.markdown(f"""
<link href="{google_font}" rel="stylesheet">
<style>
    /* ===== Base RTL/LTR Direction ===== */
    html, body, [class*="css"], .stApp {{
        direction: {direction} !important;
        font-family: {font_family} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Main App Container ===== */
    .main .block-container {{
        direction: {direction} !important;
        font-family: {font_family} !important;
        padding-top: 1.5rem;
        max-width: 1200px;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Headers ===== */
    h1, h2, h3, h4, h5, h6 {{
        font-family: {font_family} !important;
        font-weight: 700 !important;
        color: #1a1a2e !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    h1 {{ font-size: 2rem !important; }}
    h2 {{ font-size: 1.6rem !important; }}
    h3 {{ font-size: 1.3rem !important; }}
    
    /* ===== Paragraphs & Text ===== */
    p, div, span, label, .stMarkdown, .stText, .stMarkdown p {{
        font-family: {font_family} !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {{
        direction: {direction} !important;
        font-family: {font_family} !important;
        background: linear-gradient(180deg, #0f0c29, #302b63, #24243e) !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: #ffffff !important;
        font-family: {font_family} !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] .stTextInput label {{
        color: #c9d1ff !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }}

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px !important;
        flex-wrap: wrap;
        background: #f0f2ff;
        padding: 8px;
        border-radius: 12px;
        direction: {direction} !important;
        justify-content: {"flex-end" if lang == "ar" else "flex-start"} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: white !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-family: {font_family} !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        color: #444 !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #302b63, #0f0c29) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(48,43,99,0.3) !important;
    }}
    
    /* ===== Buttons ===== */
    .stButton > button {{
        font-family: {font_family} !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        border: none !important;
        background: linear-gradient(135deg, #302b63, #0f0c29) !important;
        color: white !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(48,43,99,0.25) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(48,43,99,0.4) !important;
    }}
    
    /* ===== Info/Success/Warning boxes ===== */
    .stInfo, .stSuccess, .stWarning, .stError {{
        font-family: {font_family} !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        line-height: 1.8 !important;
    }}
    
    /* ===== DataFrames ===== */
    .stDataFrame {{
        direction: {"rtl" if lang == "ar" else "ltr"} !important;
        font-family: {font_family} !important;
    }}
    
    /* ===== Selectbox & Multiselect ===== */
    .stSelectbox > div, .stMultiSelect > div {{
        direction: {direction} !important;
        font-family: {font_family} !important;
    }}
    
    /* ===== Title Banner ===== */
    .app-header {{
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
        direction: {direction};
        text-align: {"right" if lang == "ar" else "left"};
        position: relative;
        overflow: hidden;
    }}
    .app-header::before {{
        content: '';
        position: absolute;
        top: -50%;
        {"right" if lang == "ar" else "left"}: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }}
    .app-header h1 {{
        color: white !important;
        margin: 0 !important;
        font-size: 1.9rem !important;
        font-weight: 900 !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    .app-header p {{
        color: #c9d1ff !important;
        margin-top: 0.5rem !important;
        font-size: 0.95rem !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Result Cards ===== */
    .result-card {{
        background: white;
        border: 1px solid #e8ecff;
        border-{"right" if lang == "ar" else "left"}: 4px solid #302b63;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        direction: {direction};
        text-align: {"right" if lang == "ar" else "left"};
        font-family: {font_family};
        font-size: 0.95rem;
        color: #1a1a2e;
        box-shadow: 0 2px 8px rgba(48,43,99,0.08);
    }}
    .result-card .result-number {{
        font-weight: 800;
        color: #302b63;
        font-size: 1rem;
    }}
    
    /* ===== Recommendation Cards ===== */
    .rec-card {{
        background: linear-gradient(135deg, #f8f9ff, #eef0ff);
        border: 1px solid #dde3ff;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        direction: {direction};
        text-align: {"right" if lang == "ar" else "left"};
        font-family: {font_family};
        color: #1a1a2e;
        box-shadow: 0 3px 10px rgba(48,43,99,0.08);
    }}
    .rec-card .rec-header {{
        font-weight: 700;
        color: #302b63;
        font-size: 0.9rem;
        margin-bottom: 6px;
    }}
    .rec-card .rec-body {{
        font-size: 0.93rem;
        line-height: 1.7;
        color: #333;
    }}
    
    /* ===== Section Dividers ===== */
    .section-title {{
        background: linear-gradient(135deg, #302b63, #0f0c29);
        color: white !important;
        padding: 12px 20px;
        border-radius: 10px;
        font-family: {font_family} !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        direction: {direction};
        text-align: {"right" if lang == "ar" else "left"};
        margin: 1rem 0 0.8rem 0;
    }}

    /* ===== File Uploader - FIXED: Remove duplicate styling ===== */
    .stFileUploader {{
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    .stFileUploader label {{
        font-family: {font_family} !important;
        font-weight: 600 !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Radio Buttons & Checkbox ===== */
    .stRadio label, .stCheckbox label {{
        font-family: {font_family} !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Spinner ===== */
    .stSpinner p {{
        font-family: {font_family} !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Fix Streamlit default elements for RTL ===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {{
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
        font-family: {font_family} !important;
    }}
</style>
""", unsafe_allow_html=True)

L = LABELS[lang]

# ==========================================
# --- زر تبديل اللغة ---
# ==========================================
col_lang, col_space = st.columns([1, 5])
with col_lang:
    if st.button(L['lang_toggle'], key='lang_btn_unique'):
        st.session_state['lang'] = 'en' if lang == 'ar' else 'ar'
        st.rerun()

# ==========================================
# --- Header Banner ---
# ==========================================
st.markdown(f"""
<div class="app-header" dir="{direction}">
    <h1>{L['title']}</h1>
    <p>{L['subtitle']}</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# --- دوال الذكاء الاصطناعي ---
# ==========================================
def run_ai(prompt, api_key):
    try:
        client = OpenAI(base_url="https://router.huggingface.co/v1/", api_key=api_key)
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500, temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ خطأ في الاتصال بالذكاء الاصطناعي: {e}"

def analyze_hypothesis_text(text, api_key):
    prompt = f"""
    حلل الفرضية الإحصائية التالية بدقة: "{text}"
    استخرج باختصار: نوع الفرضية (علاقة/تأثير/فروق)، المتغير المستقل، المتغير التابع.
    """
    return run_ai(prompt, api_key)

def generate_detailed_explanation(results, hypothesis, api_key):
    prompt = f"""
    بصفتك أستاذاً جامعياً، لديك نتائج: {results} والفرضية: "{hypothesis}"
    اكتب تفسيراً أكاديمياً للفصل الرابع يشمل: قراءة الأرقام، تفسير القيم الإحصائية، اتجاه العلاقة، قرار الفرضية، ومناقشة النتائج.
    """
    return run_ai(prompt, api_key)

def get_table_explanation(table_string, context, api_key):
    prompt = f"اشرح هذا الجدول ({context}) بشكل أكاديمي: {table_string}"
    return run_ai(prompt, api_key)

# ==========================================
# --- دوال المعالجة ---
# ==========================================
def encode_likert(df):
    likert_map = {
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1,
        "راض جداً": 5, "راض": 4, "غير راض": 2, "غير راض جداً": 1,
        "دائماً": 5, "غالبا": 4, "أحياناً": 3, "نادراً": 2, "أبدا": 1,
        "بدرجة كبيرة جداً": 5, "بدرجة كبيرة": 4, "بدرجة متوسطة": 3, "بدرجة قليلة": 2, "بدرجة ضعيفة جداً": 1,
        "نعم": 2, "لا": 1
    }
    df_cleaned = df.copy()
    for col in df_cleaned.select_dtypes(include=['object']).columns:
        df_cleaned[col] = df_cleaned[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
    df_cleaned = df_cleaned.replace(likert_map)
    for col in df_cleaned.columns:
        if col != 'Timestamp':
            try: df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except: pass
    return df_cleaned

def smart_classify_columns(df):
    categorical_cols, numeric_cols = [], []
    demo_keywords = ['عمر', 'جنس', 'مؤهل', 'خبرة', 'دخل', 'تخصص', 'عمل', 'مستوى']
    for col in df.columns:
        if col.lower() in ['timestamp', 'unnamed: 0']: continue
        is_demo = any(k in str(col).lower() for k in demo_keywords) and len(str(col).split()) <= 4
        if is_demo:
            categorical_cols.append(col)
        else:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > len(df)*0.3:
                numeric_cols.append(col)
            elif df[col].nunique() <= 15:
                categorical_cols.append(col)
    return categorical_cols, numeric_cols

# ==========================================
# --- مفتاح API ---
# ==========================================
if "HF_TOKEN" in st.secrets:
    api_key = st.secrets["HF_TOKEN"]
else:
    st.sidebar.title(L['ai_settings'])
    api_key = st.sidebar.text_input(L['api_key'], type="password", help="ضع المفتاح لتفعيل الميزات الذكية")

# ==========================================
# --- رفع الملف (مرة واحدة فقط - تم الإصلاح) ---
# ==========================================
uploaded_file = st.file_uploader(L['upload'], type=["csv", "xlsx"], key="uploader_unique_key_123")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)

        st.sidebar.title(L['dimensions'])
        st.sidebar.success(L['detected'].format(len(num_cols_auto)))

        categorical_cols = st.sidebar.multiselect(L['cat_vars'], df_encoded.columns, default=cat_cols_auto, key="cat_select_unique")
        all_questions = [c for c in num_cols_auto if c not in categorical_cols]
        num_dims = st.sidebar.number_input(L['num_dims'], min_value=1, max_value=15, value=6, key="num_dims_unique")

        dimensions_dict, analysis_cols, active_questions = {}, [], []
        chunk_size = max(1, len(all_questions) // int(num_dims)) if all_questions else 1

        for i in range(int(num_dims)):
            st.sidebar.markdown("---")
            dim_name = st.sidebar.text_input(L['dim_name'].format(i+1), L['dim_default'].format(i+1), key=f"name_{i}_unique")
            start_idx, end_idx = i*chunk_size, (i*chunk_size+chunk_size if i < int(num_dims)-1 else len(all_questions))
            default_cols = all_questions[start_idx:end_idx] if all_questions else []
            dim_cols = st.sidebar.multiselect(L['dim_cols'].format(dim_name), all_questions, default=default_cols, key=f"cols_{i}_unique")
            if dim_cols:
                dimensions_dict[dim_name] = dim_cols
                df_encoded[dim_cols] = df_encoded[dim_cols].apply(pd.to_numeric, errors='coerce')
                df_encoded[dim_name] = df_encoded[dim_cols].mean(axis=1)
                analysis_cols.append(dim_name)
                active_questions.extend(dim_cols)

        active_questions = list(dict.fromkeys(active_questions))
        if active_questions:
            df_encoded['الاستبيان ككل (المتوسط العام)'] = df_encoded[active_questions].mean(axis=1)
            analysis_cols.append('الاستبيان ككل (المتوسط العام)')

        if not analysis_cols:
            st.warning(L['warning_select'])
        else:
            # ==========================================
            # التبويبات التسعة
            # ==========================================
            tabs = st.tabs(L['tabs'])
            
            # 1. عينة الدراسة
            with tabs[0]:
                st.subheader("👥 وصف عينة الدراسة (التكرارات والنسب)")
                if categorical_cols:
                    for col in categorical_cols:
                        st.markdown(f"### 📊 توزيع أفراد العينة حسب: ({col})")
                        counts = df_encoded[col].value_counts()
                        percentages = df_encoded[col].value_counts(normalize=True) * 100
                        demo_df = pd.DataFrame({'التكرار': counts, 'النسبة (%)': percentages.round(2)})
                        total_row = pd.DataFrame({'التكرار': [len(df_encoded)], 'النسبة (%)': [100.00]}, index=['📊 المجموع الكلي ✓'])
                        demo_df_with_total = pd.concat([demo_df, total_row])
                        col1, col2 = st.columns(2)
                        with col1:
                            st.dataframe(demo_df_with_total, use_container_width=True)
                            chart_type = st.radio(f"نوع الرسم لـ ({col}):", ["دائري", "أعمدة", "دائري مجوف", "خطي", "أعمدة أفقية"], key=f"chart_{col}_unique", horizontal=True)
                        with col2:
                            if chart_type == "دائري": fig = px.pie(demo_df, values='التكرار', names=demo_df.index, height=350)
                            elif chart_type == "أعمدة": fig = px.bar(demo_df, x=demo_df.index, y='التكرار', text='التكرار', color=demo_df.index, height=350)
                            elif chart_type == "دائري مجوف": fig = px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.4, height=350)
                            elif chart_type == "خطي": fig = px.line(demo_df, x=demo_df.index, y='التكرار', markers=True, height=350)
                            else: fig = px.bar(demo_df, x='التكرار', y=demo_df.index, text='التكرار', orientation='h', height=350)
                            st.plotly_chart(fig, use_container_width=True)
                        st.info(f"**📝 التفسير الأكاديمي:**\n يوضح العرض التوزيع التكراري والنسبي لأفراد العينة ({len(df_encoded)}) حسب متغير ({col}). الفئة الأكثر تمثيلاً هي ({counts.idxmax()}) بنسبة ({percentages.max():.1f}%).")
                        if api_key and st.button(f"✨ قراءة ذكية لـ ({col})", key=f"ai_{col}_unique"):
                            with st.spinner("جاري التحليل..."):
                                st.success(get_table_explanation(demo_df_with_total.to_markdown(), f"توزيع {col}", api_key))
                        st.markdown("---")

            # 2. الإحصاء الوصفي
            with tabs[1]:
                st.subheader("📊 الإحصاء الوصفي (المتوسطات والانحرافات)")
                st.markdown("### 1️⃣ المحاور والأبعاد")
                desc_df = df_encoded[analysis_cols].describe().T.rename(columns={'count':'العدد','mean':'المتوسط','std':'الانحراف المعياري','min':'الأدنى','max':'الأقصى'})
                st.dataframe(desc_df[['العدد','المتوسط','الانحراف المعياري','الأدنى','الأقصى']], use_container_width=True)
                if api_key and st.button("✨ قراءة ذكية", key="ai_desc_unique"):
                    with st.spinner("جاري التحليل..."): st.success(get_table_explanation(desc_df.to_markdown(), "المحاور", api_key))
                st.markdown(f"### 2️⃣ فقرات الاستبيان ({len(active_questions)})")
                if active_questions:
                    items_desc = df_encoded[active_questions].describe().T.rename(columns={'count':'العدد','mean':'المتوسط','std':'الانحراف المعياري','min':'الأدنى','max':'الأقصى'})
                    st.dataframe(items_desc[['العدد','المتوسط','الانحراف المعياري','الأدنى','الأقصى']].style.background_gradient(subset=['المتوسط'], cmap='Blues'), use_container_width=True)
                st.info("📝 **التفسير:** المتوسط الحسابي يحدد الاتجاه العام للإجابات، والانحراف المعياري يقيس مدى تقارب الآراء حول المتوسط.")

            # 3. الثبات
            with tabs[2]:
                st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
                alpha_results = []
                for dim_name, cols in dimensions_dict.items():
                    if len(cols) > 1:
                        a_val = pg.cronbach_alpha(data=df_encoded[cols].dropna())[0]
                        alpha_results.append({"المحور": dim_name, "عدد العبارات": len(cols), "ألفا": round(a_val, 3)})
                if len(active_questions) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0]
                    alpha_results.append({"المحور": "الاستبيان ككل", "عدد العبارات": len(active_questions), "ألفا": round(a_total, 3)})
                if alpha_results:
                    st.dataframe(pd.DataFrame(alpha_results), use_container_width=True)
                    st.info("📝 **التفسير:** معامل ألفا يقيس اتساق أداة الدراسة. القيم القريبة من 1.00 تدل على موثوقية ممتازة.")

            # 4. الفروق
            with tabs[3]:
                st.subheader("⚖️ دلالة الفروق (T-test / ANOVA)")
                if categorical_cols and analysis_cols:
                    g_col = st.selectbox("المتغير الديموغرافي:", categorical_cols, key="g_f_unique")
                    t_col = st.selectbox("المحور المراد اختباره:", analysis_cols, index=len(analysis_cols)-1, key="t_f_unique")
                    temp_df = df_encoded[[g_col, t_col]].copy()
                    temp_df[t_col] = pd.to_numeric(temp_df[t_col], errors='coerce')
                    res_data = temp_df.dropna()
                    grps = res_data[g_col].unique()
                    if len(grps) < 2:
                        st.warning("⚠️ لا توجد مجموعات كافية للمقارنة.")
                    else:
                        try:
                            if len(grps) == 2:
                                st.markdown("**الاختبار:** `T-test لعينتين مستقلتين`")
                                g1, g2 = res_data[res_data[g_col]==grps[0]][t_col].astype(float).values, res_data[res_data[g_col]==grps[1]][t_col].astype(float).values
                                res = pg.ttest(g1, g2); st.dataframe(res)
                                pval = res['p-val'].values[0] if 'p-val' in res.columns else 1.0
                                st.markdown("### 📝 التفسير الأكاديمي:")
                                if pval < 0.05:
                                    st.success("✅ توجد فروق ذات دلالة إحصائية.")
                                    st.info(f"أشار اختبار (ت) إلى وجود فروق جوهرية عند مستوى (≤0.05) بين فئات ({g_col}) في محور ({t_col}).")
                                else:
                                    st.warning("⚠️ لا توجد فروق ذات دلالة إحصائية.")
                                    st.info(f"بين اختبار (ت) عدم وجود فروق دالة عند مستوى (≤0.05) بين فئات ({g_col}) في محور ({t_col}).")
                            else:
                                st.markdown("**الاختبار:** `تحليل التباين الأحادي (ANOVA)`")
                                valid_grps = res_data[g_col].value_counts()[lambda x: x>=2].index
                                clean_anova = res_data[res_data[g_col].isin(valid_grps)]
                                res = pg.anova(data=clean_anova, dv=t_col, between=g_col); st.dataframe(res)
                                pval = res['p-unc'].values[0] if 'p-unc' in res.columns else 1.0
                                st.markdown("### 📝 التفسير الأكاديمي:")
                                if pval < 0.05:
                                    st.success("✅ توجد فروق ذات دلالة إحصائية.")
                                    st.info(f"أظهر ANOVA وجود فروق دالة عند مستوى (≤0.05) بين فئات ({g_col}) في محور ({t_col}).")
                                else:
                                    st.warning("⚠️ لا توجد فروق ذات دلالة إحصائية.")
                                    st.info(f"أوضح ANOVA عدم وجود فروق دالة عند مستوى (≤0.05) بين فئات ({g_col}) في محور ({t_col}).")
                            st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)
                        except Exception as e: st.warning(f"تعذر الحساب: {e}")

            # 5. الارتباط
            with tabs[4]:
                st.subheader("🔗 ارتباط بيرسون بين المحاور")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور الأول:", analysis_cols, key="c1_unique")
                    v2 = st.selectbox("المحور الثاني:", [c for c in analysis_cols if c != v1], key="c2_unique")
                    try:
                        clean_corr = df_encoded[[v1, v2]].apply(pd.to_numeric, errors='coerce').dropna()
                        corr_res = pg.corr(clean_corr[v1], clean_corr[v2], method='pearson'); st.dataframe(corr_res[['n','r','p-val'] if 'p-val' in corr_res.columns else corr_res.columns])
                        pval = corr_res['p-val'].values[0] if 'p-val' in corr_res.columns else 1.0
                        rval = corr_res['r'].values[0] if 'r' in corr_res.columns else 0.0
                        st.markdown("### 📝 التفسير الأكاديمي:")
                        if pval < 0.05:
                            direction_r = "طردية" if rval > 0 else "عكسية"
                            strength = "قوية جداً" if abs(rval)>0.8 else ("قوية" if abs(rval)>0.6 else ("متوسطة" if abs(rval)>0.4 else "ضعيفة"))
                            st.success("✅ توجد علاقة ارتباط دالة إحصائياً.")
                            st.info(f"أسفر بيرسون عن علاقة {direction_r} {strength} (r={rval:.3f}, p={pval:.4f}) بين ({v1}) و ({v2}).")
                        else:
                            st.warning("⚠️ لا توجد علاقة ارتباط دالة إحصائياً.")
                            st.info(f"أظهر بيرسون عدم وجود علاقة دالة بين ({v1}) و ({v2}) عند مستوى (≤0.05).")
                        st.plotly_chart(px.scatter(clean_corr, x=v1, y=v2, trendline="ols"), use_container_width=True)
                    except: st.error("تعذر حساب الارتباط.")

            # 6. الانحدار
            with tabs[5]:
                st.subheader("📈 تحليل الانحدار الخطي")
                if len(analysis_cols) >= 2:
                    dep_var = st.selectbox("المتغير التابع (Y):", analysis_cols, key='reg_y_unique')
                    indep_vars = st.multiselect("المتغيرات المستقلة (X):", [c for c in analysis_cols if c != dep_var], default=[c for c in analysis_cols if c != dep_var][:1], key='reg_x_unique')
                    if indep_vars:
                        reg_data = df_encoded[[dep_var] + indep_vars].apply(pd.to_numeric, errors='coerce').dropna()
                        if len(reg_data) > 2:
                            try:
                                lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var]); st.dataframe(lm)
                                r2 = lm['r2'].values[0] if 'r2' in lm.columns else 0
                                st.markdown("### 📝 التفسير الأكاديمي:")
                                st.info(f"يُفسر نموذج الانحدار ما نسبته **({float(r2)*100:.1f}%)** من التباين في ({dep_var}) بناءً على المتغيرات المُدخلة (R²={r2:.3f}).")
                            except: st.error("حدث خطأ في الانحدار.")

            # 7. المحلل الذكي للفرضيات
            with tabs[6]:
                st.header("🧠 المحلل الذكي للفرضيات")
                st.markdown("أدخل فرضيتك وسيقوم الذكاء الاصطناعي بتحليلها وكتابة تقرير أكاديمي كامل!")
                if not api_key:
                    st.error("⚠️ يرجى إدخال مفتاح API في القائمة الجانبية.")
                else:
                    user_hypothesis = st.text_area("✍️ نص الفرضية:", "مثال: توجد علاقة بين جودة الخدمة ورضا العملاء.", key="hyp_text_unique")
                    if st.button("🔍 تحليل الفرضية", key="analyze_btn_unique"):
                        with st.spinner("جاري التحليل..."):
                            try: st.session_state['ai_analysis'] = analyze_hypothesis_text(user_hypothesis, api_key)
                            except Exception as e: st.error(f"خطأ: {e}")
                    if 'ai_analysis' in st.session_state:
                        st.success("✅ تم التحليل:"); st.info(st.session_state['ai_analysis'])
                    st.markdown("---")
                    col_type = st.selectbox("نوع الاختبار:", ["علاقة (Pearson)", "تأثير (Regression)", "فروق (T-test/ANOVA)"], key="col_type_unique")
                    if "فروق" in col_type:
                        h_indep = st.selectbox("المتغير الديموغرافي:", categorical_cols, key="h_indep_unique")
                    else:
                        h_indep = st.selectbox("المتغير المستقل:", analysis_cols, key="h_indep2_unique")
                    h_dep = st.selectbox("المتغير التابع:", analysis_cols, index=len(analysis_cols)-1 if analysis_cols else 0, key="h_dep_unique")
                    if st.button("🚀 تنفيذ وكتابة المناقشة", key="exec_btn_unique"):
                        with st.spinner("جاري التنفيذ..."):
                            clean_df = df_encoded[[h_indep, h_dep]].dropna()
                            try:
                                if "علاقة" in col_type:
                                    res = pg.corr(clean_df[h_indep].astype(float), clean_df[h_dep].astype(float), method='pearson')
                                elif "تأثير" in col_type:
                                    res = pg.linear_regression(clean_df[[h_indep]].astype(float), clean_df[h_dep].astype(float))
                                else:
                                    grps_h = clean_df[h_indep].unique()
                                    if len(grps_h) == 2:
                                        res = pg.ttest(clean_df[clean_df[h_indep]==grps_h[0]][h_dep].astype(float), clean_df[clean_df[h_indep]==grps_h[1]][h_dep].astype(float))
                                    else:
                                        valid_grps = clean_df[h_indep].value_counts()[lambda x: x>=2].index
                                        res = pg.anova(data=clean_df[clean_df[h_indep].isin(valid_grps)], dv=h_dep, between=h_indep)
                                st.dataframe(res)
                                final_explanation = generate_detailed_explanation(res.to_markdown(), user_hypothesis, api_key)
                                st.markdown("### 📝 مناقشة النتائج (جاهز للنسخ):"); st.success(final_explanation)
                            except Exception as e: st.error(f"حدث خطأ: {e}")

            # 8. النتائج
            with tabs[7]:
                st.markdown(f'<div class="section-title">{L["results_title"]}</div>', unsafe_allow_html=True)
                def get_level(m): return "مرتفع" if m>=3.68 else ("متوسط" if m>=2.34 else "منخفض") if lang=='ar' else ("High" if m>=3.68 else ("Medium" if m>=2.34 else "Low"))
                result_counter, dim_recs = 1, []
                if categorical_cols:
                    for col in categorical_cols:
                        top_cat, top_pct = df_encoded[col].value_counts().idxmax(), df_encoded[col].value_counts(normalize=True).max()*100
                        st.markdown(f"""<div class="result-card"><span class="result-number">النتيجة ({result_counter}):</span> الفئة الأعلى في <strong>({col})</strong> هي <strong>({top_cat})</strong> بنسبة <strong>({top_pct:.1f}%)</strong>.</div>""", unsafe_allow_html=True)
                        result_counter += 1
                if len(active_questions) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0]
                    reliability = "ممتازة" if a_total>=0.9 else ("عالية" if a_total>=0.8 else "مقبولة")
                    st.markdown(f"""<div class="result-card"><span class="result-number">النتيجة ({result_counter}):</span> معامل الثبات الكلي <strong>({round(a_total,3)})</strong> يدل على موثوقية <strong>{reliability}</strong>.</div>""", unsafe_allow_html=True)
                    result_counter += 1
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        item_means = df_encoded[cols].mean(); overall_mean = item_means.mean(); level = get_level(overall_mean)
                        interpretation = "موافقة مرتفعة" if level=="مرتفع" else ("مستوى متوسط" if level=="متوسط" else "مستوى منخفض يستدعي التحسين")
                        st.markdown(f"""<div class="result-card"><span class="result-number">النتيجة ({result_counter}):</span> محور <strong>({dim_name})</strong> جاء بمستوى <strong>({level})</strong> بمتوسط <strong>({round(overall_mean,2)})</strong>، مما يعكس {interpretation}.</div>""", unsafe_allow_html=True)
                        result_counter += 1
                        low_items = item_means[item_means <= 3.50]
                        if not low_items.empty:
                            for item_text, mean_val in low_items.items():
                                dim_recs.append({"المحور": dim_name, "المتوسط": round(mean_val,2), "التوصية": f"تحسين ({item_text}) من خلال تطوير الممارسات المرتبطة بها."})
                        else:
                            lowest_item_text, lowest_mean_val = item_means.idxmin(), item_means.min()
                            dim_recs.append({"المحور": dim_name, "المتوسط": round(lowest_mean_val,2), "التوصية": f"المحافظة على مستوى ({lowest_item_text}) وتعزيزه باستمرار."})
                st.session_state['dim_recs'] = dim_recs

            # 9. التوصيات
            with tabs[8]:
                st.markdown(f'<div class="section-title">{L["recs_title"]}</div>', unsafe_allow_html=True)
                saved_recs = st.session_state.get('dim_recs', [])
                if saved_recs:
                    for idx, rec in enumerate(saved_recs, 1):
                        st.markdown(f"""<div class="rec-card"><div class="rec-header">📌 التوصية ({idx}) | المحور: {rec['المحور']} | المتوسط: {rec['المتوسط']}</div><div class="rec-body">{rec['التوصية']}</div></div>""", unsafe_allow_html=True)
                else:
                    st.info("⚠️ " + L['no_recs'] + " يرجى زيارة تبويب النتائج أولاً.")

    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملف: {e}")
