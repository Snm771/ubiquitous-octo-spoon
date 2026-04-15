import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

try:
    from openai import OpenAI
except ImportError:
    st.warning("جاري إعداد المكتبات...")

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
            '👥 عينة الدراسة',
            '📊 الإحصاء الوصفي',
            '🧪 الثبات (ألفا)',
            '⚖️ الفروق',
            '🔗 الارتباط',
            '📈 الانحدار',
            '🧠 محلل الفرضيات الذكي',
            '📌 النتائج',
            '💡 التوصيات',
        ],
        'warning_select': 'يرجى تحديد أسئلة المحاور من القائمة الجانبية للبدء.',
        'lang_toggle': '🌐 English',
        'results_title': '📌 أبرز نتائج الدراسة',
        'recs_title': '💡 التوصيات الذكية (بناءً على المتوسطات الحسابية)',
        'result_label': 'النتيجة ({})',
        'no_recs': 'لا توجد بيانات كافية لاستخراج التوصيات حالياً.',
        'axis_label': 'المحور',
        'mean_label': 'المتوسط',
        'rec_label': 'التوصية',
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
            '👥 Study Sample',
            '📊 Descriptive Stats',
            '🧪 Reliability (Alpha)',
            '⚖️ Differences',
            '🔗 Correlation',
            '📈 Regression',
            '🧠 Smart Hypothesis Analyzer',
            '📌 Results',
            '💡 Recommendations',
        ],
        'warning_select': 'Please select dimension questions from the sidebar to begin.',
        'lang_toggle': '🌐 عربي',
        'results_title': '📌 Key Study Results',
        'recs_title': '💡 Smart Recommendations (Based on Means)',
        'result_label': 'Result ({})',
        'no_recs': 'Not enough data to generate recommendations. Please check sidebar settings.',
        'axis_label': 'Dimension',
        'mean_label': 'Mean',
        'rec_label': 'Recommendation',
    }
}

# ==========================================
# --- CSS المخصص (RTL + خطوط + تصميم) ---
# ==========================================
lang = st.session_state['lang']
direction = 'rtl' if lang == 'ar' else 'ltr'
font_family = "'Tajawal', 'IBM Plex Arabic', sans-serif" if lang == 'ar' else "'Outfit', 'DM Sans', sans-serif"
google_font = "https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&family=IBM+Plex+Arabic:wght@300;400;600&family=Outfit:wght@300;400;600;700&family=DM+Sans:wght@300;400;500&display=swap"

st.markdown(f"""
<link href="{google_font}" rel="stylesheet">
<style>
    /* ===== Base RTL/LTR Direction ===== */
    html, body, [class*="css"] {{
        direction: {direction} !important;
        font-family: {font_family} !important;
    }}
    
    /* ===== Main App Container ===== */
    .main .block-container {{
        direction: {direction} !important;
        font-family: {font_family} !important;
        padding-top: 1.5rem;
        max-width: 1200px;
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
    p, div, span, label, .stMarkdown {{
        font-family: {font_family} !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {{
        direction: {direction} !important;
        font-family: {font_family} !important;
        background: linear-gradient(180deg, #0f0c29, #302b63, #24243e) !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: #ffffff !important;
        font-family: {font_family} !important;
        direction: {direction} !important;
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
        right: -10%;
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

    /* ===== File Uploader ===== */
    .stFileUploader {{
        direction: {direction} !important;
    }}
    .stFileUploader label {{
        font-family: {font_family} !important;
        font-weight: 600 !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    
    /* ===== Radio Buttons ===== */
    .stRadio label {{
        font-family: {font_family} !important;
        direction: {direction} !important;
    }}
    
    /* ===== Spinner ===== */
    .stSpinner p {{
        font-family: {font_family} !important;
        direction: {direction} !important;
    }}
</style>
""", unsafe_allow_html=True)

L = LABELS[lang]

# ==========================================
# --- زر تبديل اللغة ---
# ==========================================
col_lang, col_space = st.columns([1, 5])
with col_lang:
    if st.button(L['lang_toggle'], key='lang_btn'):
        st.session_state['lang'] = 'en' if lang == 'ar' else 'ar'
        st.rerun()

# ==========================================
# --- Header Banner ---
# ==========================================
st.markdown(f"""
<div class="app-header">
    <h1>{L['title']}</h1>
    <p>{L['subtitle']}</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# --- دوال الذكاء الاصطناعي ---
# ==========================================
def run_ai(prompt, api_key):
    try:
        client = OpenAI(
            base_url="https://router.huggingface.co/v1/",
            api_key=api_key
        )
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ خطأ في الاتصال بالذكاء الاصطناعي: {e}"

def analyze_hypothesis_text(text, api_key):
    prompt = f"""
    حلل الفرضية الإحصائية التالية بدقة:
    "{text}"
    استخرج المعلومات التالية باختصار شديد:
    - نوع الفرضية: (اكتب فقط: علاقة، أو تأثير، أو فروق)
    - المتغير المستقل: (اسم المتغير)
    - المتغير التابع: (اسم المتغير)
    """
    return run_ai(prompt, api_key)

def generate_detailed_explanation(results, hypothesis, api_key):
    prompt = f"""
    بصفتك أستاذاً جامعياً ومشرفاً على رسائل الماجستير والدكتوراه، لديك نتائج تحليل إحصائي:
    {results}
    
    والفرضية التي تم اختبارها هي:
    "{hypothesis}"

    اكتب تفسيراً أكاديمياً تفصيلياً جداً (يصلح للنسخ المباشر في الفصل الرابع: مناقشة النتائج)، ويجب أن يشمل:
    1. قراءة وتفسير الأرقام في الجدول.
    2. تفسير كل قيمة علمياً (R Square, Beta, T/F value, P-value) حسب نوع الاختبار المجرى.
    3. تفسير اتجاه العلاقة أو حجم الأثر بشكل دقيق.
    4. قرار واضح بـ (قبول) أو (رفض) الفرضية.
    5. فقرة مناقشة النتائج وربطها بشكل افتراضي منطقي مع الدراسات السابقة والنظريات العلمية.
    
    اجعل اللغة أكاديمية، رصينة، واحترافية جداً باللغة العربية.
    """
    return run_ai(prompt, api_key)

def get_table_explanation(table_string, context, api_key):
    prompt = f"""
    بصفتك خبيراً إحصائياً، قم بقراءة هذا الجدول الخاص بـ ({context}):
    {table_string}
    
    اكتب فقرة أكاديمية تشرح أهم ما جاء في هذا الجدول، استخرج أعلى وأقل القيم، وفسر معناها في سياق البحث العلمي.
    """
    return run_ai(prompt, api_key)

# ==========================================
# --- 1. دالة التشفير الذكي ---
# ==========================================
def encode_likert(df):
    likert_map = {
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1, "لا أوافق": 2, "لا أوافق بشدة": 1,
        "راض جدا": 5, "راض جداً": 5, "راض": 4, "راضي": 4, "راضي جدا": 5, "غير راض": 2, "غير راضي": 2, "غير راض جدا": 1, "غير راض جداً": 1, "غير راضي جدا": 1,
        "دائما": 5, "دائماً": 5, "غالبا": 4, "غالباً": 4, "أحيانا": 3, "أحياناً": 3, "نادرا": 2, "نادراً": 2, "أبدا": 1, "أبداً": 1, "مطلقا": 1, "مطلقاً": 1,
        "بدرجة كبيرة جدا": 5, "بدرجة كبيرة جداً": 5, "بدرجة كبيرة": 4, "بدرجة متوسطة": 3, "بدرجة قليلة": 2, "بدرجة ضعيفة": 2, "بدرجة قليلة جدا": 1, "بدرجة ضعيفة جدا": 1,
        "نعم": 2, "لا": 1
    }
    df_cleaned = df.copy()
    for col in df_cleaned.select_dtypes(include=['object']).columns:
        df_cleaned[col] = df_cleaned[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
    df_cleaned = df_cleaned.replace(likert_map)
    for col in df_cleaned.columns:
        if col != 'Timestamp':
            try:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except ValueError:
                pass
    return df_cleaned

# --- 2. التصنيف الدلالي المطور ---
def smart_classify_columns(df):
    categorical_cols, numeric_cols = [], []
    demo_keywords = ['عمر', 'سن', 'جنس', 'نوع', 'مؤهل', 'مرحلة', 'صف', 'خبرة', 'حالة', 'دخل', 'تخصص', 'عمل', 'تعليم', 'مهنة', 'زيارة', 'مستوى']
    for col in df.columns:
        if col.lower() in ['timestamp', 'unnamed: 0']: continue
        words_count = len(str(col).split())
        is_demo = any(keyword in str(col).lower() for keyword in demo_keywords) and words_count <= 4
        if is_demo:
            categorical_cols.append(col)
        else:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > (len(df) * 0.3):
                numeric_cols.append(col)
            elif df[col].nunique() <= 15:
                categorical_cols.append(col)
    return categorical_cols, numeric_cols

# ==========================================
# مفتاح API
# ==========================================
if "HF_TOKEN" in st.secrets:
    api_key = st.secrets["HF_TOKEN"]
else:
    st.sidebar.title(L['ai_settings'])
    api_key = st.sidebar.text_input(L['api_key'], type="password", help="ضع المفتاح هنا لتفعيل الشرح التوليدي والتبويب السابع")

uploaded_file = st.file_uploader(L['upload'], type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)

        st.sidebar.title(L['dimensions'])
        st.sidebar.success(L['detected'].format(len(num_cols_auto)))

        categorical_cols = st.sidebar.multiselect(L['cat_vars'], df_encoded.columns, default=cat_cols_auto)
        all_questions = [c for c in num_cols_auto if c not in categorical_cols]

        num_dims = st.sidebar.number_input(L['num_dims'], min_value=1, max_value=15, value=6)

        dimensions_dict = {}
        analysis_cols = []
        active_questions = []

        chunk_size = max(1, len(all_questions) // int(num_dims)) if all_questions else 1

        for i in range(int(num_dims)):
            st.sidebar.markdown("---")
            dim_name = st.sidebar.text_input(L['dim_name'].format(i+1), L['dim_default'].format(i+1), key=f"name_{i}")
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < int(num_dims) - 1 else len(all_questions)
            default_cols = all_questions[start_idx:end_idx] if all_questions else []
            dim_cols = st.sidebar.multiselect(L['dim_cols'].format(dim_name), all_questions, default=default_cols, key=f"cols_{i}")

            if dim_cols:
                dimensions_dict[dim_name] = dim_cols
                df_encoded[dim_cols] = df_encoded[dim_cols].apply(pd.to_numeric, errors='coerce')
                df_encoded[dim_name] = df_encoded[dim_cols].mean(axis=1)
                analysis_cols.append(dim_name)
                active_questions.extend(dim_cols)

        active_questions = list(dict.fromkeys(active_questions))

        if len(active_questions) > 0:
            df_encoded['الاستبيان ككل (المتوسط العام)'] = df_encoded[active_questions].mean(axis=1)
            analysis_cols.append('الاستبيان ككل (المتوسط العام)')

        if not analysis_cols:
            st.warning(L['warning_select'])
        else:
            # ==========================================
            # التبويبات التسعة
            # ==========================================
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(L['tabs'])

            # ==========================================
            # 1. تبويب عينة الدراسة
            # ==========================================
            with tab1:
                st.subheader("👥 وصف عينة الدراسة (التكرارات والنسب)")
                if categorical_cols:
                    for col in categorical_cols:
                        st.markdown(f"### 📊 توزيع أفراد العينة حسب: ({col})")

                        counts = df_encoded[col].value_counts()
                        percentages = df_encoded[col].value_counts(normalize=True) * 100
                        demo_df = pd.DataFrame({'التكرار': counts, 'النسبة (%)': percentages.round(2)})

                        total_row = pd.DataFrame({
                            'التكرار': [len(df_encoded)],
                            'النسبة (%)': [100.00]
                        }, index=['📊 المجموع الكلي ✓'])
                        demo_df_with_total = pd.concat([demo_df, total_row])

                        col1, col2 = st.columns(2)
                        with col1:
                            st.dataframe(demo_df_with_total, use_container_width=True)
                            chart_type_demo = st.radio(f"اختر نوع الرسم لـ ({col}):", ["دائري (Pie)", "أعمدة (Bar)", "دائري مجوف (Donut)", "خطي (Line)", "أعمدة أفقية (H-Bar)"], key=f"chart_{col}", horizontal=True)

                        with col2:
                            if chart_type_demo == "دائري (Pie)":
                                fig = px.pie(demo_df, values='التكرار', names=demo_df.index, height=350)
                            elif chart_type_demo == "أعمدة (Bar)":
                                fig = px.bar(demo_df, x=demo_df.index, y='التكرار', text='التكرار', color=demo_df.index, height=350)
                            elif chart_type_demo == "دائري مجوف (Donut)":
                                fig = px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.4, height=350)
                            elif chart_type_demo == "خطي (Line)":
                                fig = px.line(demo_df, x=demo_df.index, y='التكرار', markers=True, height=350)
                            else:
                                fig = px.bar(demo_df, x='التكرار', y=demo_df.index, text='التكرار', color=demo_df.index, orientation='h', height=350)

                            st.plotly_chart(fig, use_container_width=True)

                        st.info(f"**📝 التفسير الأكاديمي:**\n يوضح العرض الإحصائي أعلاه التوزيع التكراري والنسبي لأفراد عينة الدراسة البالغ عددهم الإجمالي ({len(df_encoded)}) مبحوثاً، وذلك وفقاً لتصنيفاتهم في متغير ({col}). من خلال استقراء النتائج، يتبين بوضوح أن الفئة الأكثر تمثيلاً وحضوراً في العينة هي فئة ({counts.idxmax()}) بنسبة مئوية قدرها ({percentages.max():.1f}%)، مما يعكس هيمنة هذه الشريحة على تركيبة العينة في هذا المتغير.")

                        if api_key:
                            if st.button(f"✨ توليد قراءة ذكية متعمقة لجدول ({col})", key=f"ai_demo_{col}"):
                                with st.spinner("جاري صياغة التفسير الأكاديمي..."):
                                    st.success(get_table_explanation(demo_df_with_total.to_markdown(), f"توزيع العينة حسب {col}", api_key))
                        st.markdown("---")

            # ==========================================
            # 2. الإحصاء الوصفي
            # ==========================================
            with tab2:
                st.subheader("📊 الإحصاء الوصفي (المتوسطات والانحرافات المعيارية)")
                st.markdown("### 1️⃣ الإحصاء العام للمحاور والأبعاد")
                desc_df = df_encoded[analysis_cols].describe().T
                desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)

                if api_key:
                    if st.button("✨ توليد قراءة ذكية لجدول المحاور", key="ai_desc"):
                        with st.spinner("جاري التحليل..."):
                            st.success(get_table_explanation(desc_df.to_markdown(), "المتوسطات والانحرافات المعيارية للمحاور", api_key))

                st.markdown(f"### 2️⃣ الإحصاء التفصيلي لجميع فقرات الاستبيان (العدد: {len(active_questions)})")
                if active_questions:
                    items_desc = df_encoded[active_questions].describe().T
                    items_desc = items_desc.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                    st.dataframe(items_desc[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']].style.background_gradient(subset=['المتوسط'], cmap='Blues'), use_container_width=True)

                st.markdown("### 📝 التفسير الأكاديمي:")
                st.info("يهدف التحليل الوصفي المعروض في الجداول أعلاه إلى تشخيص مستوى الاستجابة لمتغيرات ومحاور الدراسة وفقاً لآراء أفراد العينة. بالاعتماد على مقياس النزعة المركزية المتمثل في **المتوسط الحسابي (Mean)**، يتم تحديد الاتجاه العام والميل الغالب لإجابات المبحوثين، حيث تشير القيم المرتفعة إلى تبلور رأي إيجابي، أو مستوى موافقة عالٍ. وبالتوازي مع ذلك، يبرز دور مقياس التشتت المتمثل في **الانحراف المعياري (Standard Deviation)** كمؤشر إحصائي دقيق لقياس مدى تشتت أو تقارب تلك الآراء حول متوسطها.")

            # ==========================================
            # 3. الثبات
            # ==========================================
            with tab3:
                st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
                alpha_results = []
                for dim_name, cols in dimensions_dict.items():
                    if len(cols) > 1:
                        a_val = pg.cronbach_alpha(data=df_encoded[cols].dropna())[0]
                        alpha_results.append({"المحور / البعد": dim_name, "عدد العبارات": len(cols), "معامل ألفا": round(a_val, 3)})

                if len(active_questions) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0]
                    alpha_results.append({"المحور / البعد": "الاستبيان ككل", "عدد العبارات": len(active_questions), "معامل ألفا": round(a_total, 3)})

                if alpha_results:
                    st.dataframe(pd.DataFrame(alpha_results), use_container_width=True)
                    st.markdown("### 📝 التفسير الأكاديمي:")
                    st.info("تشير نتائج التقييم الإحصائي باستخدام معامل ألفا كرونباخ (Cronbach's Alpha) إلى أن أداة الدراسة تتمتع بدرجة من الاتساق الداخلي. يُعد هذا المعامل مؤشراً علمياً دقيقاً على مدى تجانس فقرات الاستبيان وترابطها في قياس الأبعاد التي أُعدت لقياسها. وكلما اقتربت القيمة من الواحد الصحيح (1.00) دلّ ذلك على موثوقية ممتازة.")

            # ==========================================
            # 4. الفروق
            # ==========================================
            with tab4:
                st.subheader("⚖️ دلالة الفروق (T-test و ANOVA)")
                if categorical_cols and analysis_cols:
                    g_col = st.selectbox("المتغير المستقل (ديموغرافي):", categorical_cols, key="g_f")
                    t_col = st.selectbox("المتغير التابع (المحور المراد اختباره):", analysis_cols, index=len(analysis_cols)-1, key="t_f")

                    temp_df = df_encoded[[g_col, t_col]].copy()
                    temp_df[t_col] = pd.to_numeric(temp_df[t_col], errors='coerce')
                    res_data = temp_df.dropna()
                    grps = res_data[g_col].unique()

                    if len(grps) < 2:
                        st.warning("⚠️ لا توجد مجموعات كافية للمقارنة في هذا المتغير.")
                    else:
                        try:
                            if len(grps) == 2:
                                st.markdown("**نوع الاختبار:** `T-test لعينتين مستقلتين`")
                                g1 = res_data[res_data[g_col]==grps[0]][t_col].astype(float).values
                                g2 = res_data[res_data[g_col]==grps[1]][t_col].astype(float).values
                                res = pg.ttest(g1, g2)
                                st.dataframe(res)
                                pval = res['p-val'].values[0] if 'p-val' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)

                                st.markdown("### 📝 التفسير الأكاديمي:")
                                if pval < 0.05:
                                    st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"أشارت مخرجات اختبار (ت) لعينتين مستقلتين إلى وجود فروق جوهرية ذات دلالة إحصائية عند مستوى الدلالة (≤ 0.05) بين فئات المتغير المستقل ({g_col}) فيما يتعلق بمحور ({t_col}).")
                                else:
                                    st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"بينت نتائج اختبار (ت) لعينتين مستقلتين عدم ثبوت أي فروق ذات دلالة إحصائية عند مستوى الدلالة (≤ 0.05) بين استجابات أفراد العينة باختلاف فئاتهم في متغير ({g_col}) تجاه محور ({t_col}).")

                            elif len(grps) > 2:
                                st.markdown("**نوع الاختبار:** `تحليل التباين الأحادي (ANOVA)`")
                                counts_grp = res_data[g_col].value_counts()
                                valid_grps = counts_grp[counts_grp >= 2].index
                                clean_anova = res_data[res_data[g_col].isin(valid_grps)]
                                res = pg.anova(data=clean_anova, dv=t_col, between=g_col)
                                st.dataframe(res)
                                pval = res['p-unc'].values[0] if 'p-unc' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)

                                st.markdown("### 📝 التفسير الأكاديمي:")
                                if pval < 0.05:
                                    st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"أظهرت المعطيات الإحصائية من تحليل التباين الأحادي (ANOVA) وجود فروق ذات دلالة إحصائية عند مستوى الدلالة (≤ 0.05) بين فئات متغير ({g_col}) في محور ({t_col}).")
                                else:
                                    st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"أوضحت مخرجات تحليل التباين الأحادي (ANOVA) عدم وجود فروق ذات دلالة إحصائية عند مستوى الدلالة (≤ 0.05) بين فئات متغير ({g_col}) في محور ({t_col}).")

                            st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)
                        except Exception as e:
                            st.warning(f"تعذر حساب الفروق: {e}")

            # ==========================================
            # 5. الارتباط
            # ==========================================
            with tab5:
                st.subheader("🔗 قياس الارتباط بين المحاور (Pearson Correlation)")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور الأول (المتغير المستقل):", analysis_cols, key="c1")
                    v2 = st.selectbox("المحور الثاني (المتغير التابع):", analysis_cols, index=1 if len(analysis_cols) > 1 else 0, key="c2")
                    if v1 != v2:
                        try:
                            clean_corr = df_encoded[[v1, v2]].apply(pd.to_numeric, errors='coerce').dropna()
                            corr_res = pg.corr(clean_corr[v1], clean_corr[v2], method='pearson')
                            st.dataframe(corr_res[['n', 'r', 'p-val'] if 'p-val' in corr_res.columns else corr_res.columns])
                            pval = corr_res['p-val'].values[0] if 'p-val' in corr_res.columns else (corr_res['p-value'].values[0] if 'p-value' in corr_res.columns else 1.0)
                            rval = corr_res['r'].values[0] if 'r' in corr_res.columns else 0.0

                            st.markdown("### 📝 التفسير الأكاديمي:")
                            if pval < 0.05:
                                direction_r = "طردية (إيجابية)" if rval > 0 else "عكسية (سلبية)"
                                strength = "قوية جداً" if abs(rval) > 0.8 else ("قوية" if abs(rval) > 0.6 else ("متوسطة" if abs(rval) > 0.4 else "ضعيفة"))
                                st.success("✅ **توجد علاقة ارتباط دالة إحصائياً.**")
                                st.info(f"أسفرت نتائج معامل ارتباط بيرسون عن وجود علاقة ارتباط {direction_r} و{strength} ذات دلالة إحصائية عند مستوى الدلالة (≤ 0.05) بين محور ({v1}) ومحور ({v2}).")
                            else:
                                st.warning("⚠️ **لا توجد علاقة ارتباط دالة إحصائياً.**")
                                st.info(f"أظهرت معطيات اختبار بيرسون عدم ثبوت أي علاقة ارتباطية ذات دلالة إحصائية بين محور ({v1}) ومحور ({v2}) عند مستوى الدلالة (≤ 0.05).")

                            st.plotly_chart(px.scatter(clean_corr, x=v1, y=v2, trendline="ols"), use_container_width=True)
                        except:
                            st.error("تعذر حساب الارتباط.")

            # ==========================================
            # 6. الانحدار
            # ==========================================
            with tab6:
                st.subheader("📈 تحليل الانحدار الخطي (Regression)")
                if len(analysis_cols) >= 2:
                    dep_var = st.selectbox("المتغير التابع (Y / النتيجة):", analysis_cols, key='reg_y')
                    indep_vars = st.multiselect("المتغيرات المستقلة (X / المؤثرات):", [c for c in analysis_cols if c != dep_var], default=[c for c in analysis_cols if c != dep_var][:1], key='reg_x')
                    if indep_vars:
                        reg_data = df_encoded[[dep_var] + indep_vars].apply(pd.to_numeric, errors='coerce').dropna()
                        if len(reg_data) > 2:
                            try:
                                lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var])
                                st.dataframe(lm)
                                r2 = lm['r2'].values[0] if 'r2' in lm.columns else 0
                                st.markdown("### 📝 التفسير الأكاديمي:")
                                st.info(f"تم إجراء تحليل الانحدار الخطي لقياس أثر المتغيرات المُدخلة على المتغير التابع ({dep_var}). استناداً إلى قيمة معامل التحديد (R² = {r2:.3f})، فإن المتغيرات المستقلة قادرة مجتمعة على تفسير ما نسبته **({float(r2)*100:.1f}%)** من إجمالي التباين في المتغير التابع.")
                            except:
                                st.error("حدث خطأ في الانحدار.")

            # ==========================================
            # 7. المحلل الذكي للفرضيات
            # ==========================================
            with tab7:
                st.header("🧠 المحلل الذكي للفرضيات (AI Hypothesis Engine)")
                st.markdown("ضع فرضية بحثك هنا، وسيقوم الذكاء الاصطناعي بفهمها، واختيار الاختبار المناسب، وتنفيذه، وكتابة تقرير أكاديمي كامل لها!")

                if not api_key:
                    st.error("⚠️ يرجى إدخال مفتاح Hugging Face API في القائمة الجانبية أو إضافته في إعدادات التطبيق.")
                else:
                    user_hypothesis = st.text_area("✍️ أدخل نص الفرضية هنا:", "مثال: توجد علاقة ذات دلالة إحصائية بين جودة المعلومات والترويج للحدث.")
                    if st.button("🔍 تحليل الفرضية آلياً"):
                        with st.spinner("جاري فهم الفرضية عبر الذكاء الاصطناعي..."):
                            try:
                                st.session_state['ai_analysis'] = analyze_hypothesis_text(user_hypothesis, api_key)
                            except Exception as e:
                                st.error(f"خطأ: {e}")
                    if 'ai_analysis' in st.session_state:
                        st.success("تم تحليل الفرضية بنجاح:")
                        st.info(st.session_state['ai_analysis'])

                    st.markdown("---")
                    col_type = st.selectbox("نوع الاختبار المطلوب:", ["علاقة (Pearson)", "تأثير (Regression)", "فروق (T-test / ANOVA)"])
                    if "فروق" in col_type:
                        h_indep = st.selectbox("المتغير المستقل (الفئة الديموغرافية):", categorical_cols)
                    else:
                        h_indep = st.selectbox("المتغير المستقل (المؤثر/المحور):", analysis_cols)
                    h_dep = st.selectbox("المتغير التابع (النتيجة/المحور):", analysis_cols, index=len(analysis_cols)-1 if len(analysis_cols) > 0 else 0)

                    if st.button("🚀 تنفيذ وكتابة مناقشة النتائج (الفصل الرابع)"):
                        with st.spinner("جاري إجراء الاختبار وتأليف التفسير الأكاديمي..."):
                            clean_df = df_encoded[[h_indep, h_dep]].dropna()
                            results_str = ""
                            try:
                                if "علاقة" in col_type:
                                    res = pg.corr(clean_df[h_indep].astype(float), clean_df[h_dep].astype(float), method='pearson')
                                    results_str = res.to_markdown()
                                    st.dataframe(res)
                                elif "تأثير" in col_type:
                                    res = pg.linear_regression(clean_df[[h_indep]].astype(float), clean_df[h_dep].astype(float))
                                    results_str = res.to_markdown()
                                    st.dataframe(res)
                                elif "فروق" in col_type:
                                    grps_h = clean_df[h_indep].unique()
                                    if len(grps_h) == 2:
                                        res = pg.ttest(clean_df[clean_df[h_indep]==grps_h[0]][h_dep].astype(float), clean_df[clean_df[h_indep]==grps_h[1]][h_dep].astype(float))
                                    else:
                                        valid_grps_h = clean_df[h_indep].value_counts()[clean_df[h_indep].value_counts() >= 2].index
                                        res = pg.anova(data=clean_df[clean_df[h_indep].isin(valid_grps_h)], dv=h_dep, between=h_indep)
                                    results_str = res.to_markdown()
                                    st.dataframe(res)

                                final_explanation = generate_detailed_explanation(results_str, user_hypothesis, api_key)
                                st.markdown("### 📝 مناقشة النتائج (الفصل الرابع - جاهز للنسخ):")
                                st.success(final_explanation)
                            except Exception as e:
                                st.error(f"حدث خطأ: {e}")

            # ==========================================
            # 8. تبويب النتائج (بدون رسوم بيانية)
            # ==========================================
            with tab8:
                st.markdown(f'<div class="section-title">{L["results_title"]}</div>', unsafe_allow_html=True)

                def get_level(mean_val):
                    if mean_val >= 3.68: return "مرتفع" if lang == 'ar' else "High"
                    if mean_val >= 2.34: return "متوسط" if lang == 'ar' else "Medium"
                    return "منخفض" if lang == 'ar' else "Low"

                result_counter = 1
                dim_recs = []  # تُجمع هنا لتُعرض في تبويب التوصيات

                # الديموغرافيا
                if categorical_cols:
                    for col in categorical_cols:
                        top_cat = df_encoded[col].value_counts().idxmax()
                        top_pct = df_encoded[col].value_counts(normalize=True).max() * 100
                        st.markdown(f"""
                        <div class="result-card">
                            <span class="result-number">النتيجة ({result_counter}):</span>
                            الفئة الأعلى تمثيلاً في متغير <strong>({col})</strong> هي فئة <strong>({top_cat})</strong> بنسبة <strong>({top_pct:.1f}%)</strong> من إجمالي أفراد العينة البالغ عددهم ({len(df_encoded)}) مبحوثاً.
                        </div>
                        """, unsafe_allow_html=True)
                        result_counter += 1

                # الثبات
                if len(active_questions) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0]
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="result-number">النتيجة ({result_counter}):</span>
                        بلغ معامل الثبات الكلي <strong>(ألفا كرونباخ)</strong> لأداة الدراسة <strong>({round(a_total, 3)})</strong>، مما يدل على موثوقية {"ممتازة" if a_total >= 0.9 else "عالية" if a_total >= 0.8 else "مقبولة"} للأداة.
                    </div>
                    """, unsafe_allow_html=True)
                    result_counter += 1

                # المحاور
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        item_means = df_encoded[cols].mean()
                        overall_mean = item_means.mean()
                        level = get_level(overall_mean)

                        st.markdown(f"""
                        <div class="result-card">
                            <span class="result-number">النتيجة ({result_counter}):</span>
                            جاء محور <strong>({dim_name})</strong> بمستوى تقييم <strong>({level})</strong> بمتوسط حسابي <strong>({round(overall_mean, 2)})</strong>، {"مما يعكس موافقة مرتفعة من أفراد العينة على فقرات هذا المحور." if level == "مرتفع" else "مما يشير إلى مستوى متوسط من الموافقة لدى أفراد العينة." if level == "متوسط" else "مما يدل على مستوى منخفض من الموافقة ويستدعي الاهتمام والتحسين."}
                        </div>
                        """, unsafe_allow_html=True)
                        result_counter += 1

                        # جمع التوصيات لتبويب 9
                        low_items = item_means[item_means <= 3.50]
                        if not low_items.empty:
                            for item_text, mean_val in low_items.items():
                                dim_recs.append({
                                    "المحور": dim_name,
                                    "المتوسط": round(mean_val, 2),
                                    "التوصية": f"توصي الدراسة بضرورة تحسين ({item_text}) من خلال تطوير الممارسات المرتبطة بها، والعمل على رفع مستواها بما يسهم في تعزيز الأداء وتحقيق نتائج أفضل."
                                })
                        else:
                            lowest_item_text = item_means.idxmin()
                            lowest_mean_val = item_means.min()
                            dim_recs.append({
                                "المحور": dim_name,
                                "المتوسط": round(lowest_mean_val, 2),
                                "التوصية": f"توصي الدراسة بضرورة المحافظة على مستوى ({lowest_item_text}) والعمل على تعزيزه بشكل مستمر، لما له من دور مهم في دعم هذا البعد وتحقيق الكفاءة المطلوبة."
                            })

                # حفظ التوصيات في session_state لاستخدامها في التبويب 9
                st.session_state['dim_recs'] = dim_recs

            # ==========================================
            # 9. تبويب التوصيات (بدون رسوم بيانية)
            # ==========================================
            with tab9:
                st.markdown(f'<div class="section-title">{L["recs_title"]}</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                saved_recs = st.session_state.get('dim_recs', [])

                if saved_recs:
                    for idx, rec in enumerate(saved_recs, 1):
                        st.markdown(f"""
                        <div class="rec-card">
                            <div class="rec-header">
                                📌 التوصية ({idx}) &nbsp;|&nbsp; المحور: {rec['المحور']} &nbsp;|&nbsp; المتوسط: {rec['المتوسط']}
                            </div>
                            <div class="rec-body">
                                {rec['التوصية']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("⚠️ " + L['no_recs'] + " يرجى الانتقال إلى تبويب النتائج (📌) أولاً لتوليد التوصيات.")

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف. تأكد من أن الملف ليس فارغاً وأن صيغته صحيحة. التفاصيل: {e}")
