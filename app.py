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
# إعدادات اللغة
# ==========================================
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'ar'

LABELS = {
    'ar': {
        'title': '📊 SmartStat Pro - نظام الخبير الإحصائي الآلي',
        'subtitle': 'يُرفق النظام الآن **تفسيراً أكاديمياً** مع كل نتيجة إحصائية جاهز للنسخ المباشر',
        'upload': 'قم برفع ملف البيانات الخام (CSV أو Excel)',
        'ai_settings': '🤖 إعدادات الذكاء الاصطناعي',
        'api_key': '🔑 مفتاح Hugging Face API:',
        'dimensions': '⚙️ بناء المحاور',
        'detected': 'تم اكتشاف {} سؤال استبيان بنجاح!',
        'cat_vars': '👥 المتغيرات الشخصية (للمقارنة):',
        'num_dims': '🔢 كم عدد المحاور في دراستك؟',
        'dim_name': 'اسم المحور {}:',
        'dim_default': 'المحور {}',
        'dim_cols': 'أسئلة {}:',
        'tabs': ['👥 عينة الدراسة', '📊 الإحصاء الوصفي', '🧪 الثبات', '⚖️ الفروق', '🔗 الارتباط', '📈 الانحدار', '🧠 المحلل الذكي', '📌 النتائج', '💡 التوصيات'],
        'warning_select': 'يرجى تحديد أسئلة المحاور للبدء',
        'lang_toggle': '🌐 English',
        'results_title': '📌 أبرز نتائج الدراسة',
        'recs_title': '💡 التوصيات الذكية',
        'no_recs': 'لا توجد بيانات كافية',
    },
    'en': {
        'title': '📊 SmartStat Pro - Automated Statistical Expert System',
        'subtitle': 'The system attaches an **academic interpretation** with every result',
        'upload': 'Upload your raw data file (CSV or Excel)',
        'ai_settings': '🤖 AI Settings',
        'api_key': '🔑 Hugging Face API Key:',
        'dimensions': '⚙️ Build Dimensions',
        'detected': 'Detected {} survey questions successfully!',
        'cat_vars': '👥 Demographic Variables:',
        'num_dims': '🔢 How many dimensions?',
        'dim_name': 'Dimension {} name:',
        'dim_default': 'Dimension {}',
        'dim_cols': 'Questions for {}:',
        'tabs': ['👥 Study Sample', '📊 Descriptive', '🧪 Reliability', '⚖️ Differences', '🔗 Correlation', '📈 Regression', '🧠 AI Analyzer', '📌 Results', '💡 Recommendations'],
        'warning_select': 'Please select dimension questions to begin',
        'lang_toggle': '🌐 عربي',
        'results_title': '📌 Key Results',
        'recs_title': '💡 Smart Recommendations',
        'no_recs': 'Not enough data',
    }
}

# ==========================================
# CSS - التنسيقات
# ==========================================
lang = st.session_state['lang']
direction = 'rtl' if lang == 'ar' else 'ltr'
font_family = "'Tajawal', sans-serif" if lang == 'ar' else "'Outfit', sans-serif"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"], .stApp {{
        direction: {direction} !important;
        font-family: {font_family} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    .main .block-container {{
        direction: {direction} !important;
        font-family: {font_family} !important;
        padding-top: 2rem;
        max-width: 1200px;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: {font_family} !important;
        font-weight: 700 !important;
        color: #1a1a2e !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
    p, div, span, label, .stMarkdown {{
        font-family: {font_family} !important;
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
    }}
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
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: #f0f2ff;
        padding: 10px;
        border-radius: 12px;
        direction: {direction} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: white !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-family: {font_family} !important;
        font-weight: 600 !important;
        color: #444 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #302b63, #0f0c29) !important;
        color: white !important;
    }}
    .stButton > button {{
        font-family: {font_family} !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #302b63, #0f0c29) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
    }}
    .app-header {{
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        direction: {direction};
        text-align: {"right" if lang == "ar" else "left"};
    }}
    .app-header h1 {{
        color: white !important;
        font-size: 2rem !important;
        font-weight: 900 !important;
        margin: 0 !important;
    }}
    .app-header p {{
        color: #c9d1ff !important;
        margin-top: 0.5rem !important;
        font-size: 1rem !important;
    }}
    .result-card {{
        background: white;
        border: 1px solid #e8ecff;
        border-{"right" if lang == "ar" else "left"}: 4px solid #302b63;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        direction: {direction};
        text-align: {"right" if lang == "ar" else "left"};
        font-family: {font_family};
        box-shadow: 0 2px 8px rgba(48,43,99,0.08);
    }}
    .rec-card {{
        background: linear-gradient(135deg, #f8f9ff, #eef0ff);
        border: 1px solid #dde3ff;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
        direction: {direction};
        text-align: {"right" if lang == "ar" else "left"};
        font-family: {font_family};
    }}
    .section-title {{
        background: linear-gradient(135deg, #302b63, #0f0c29);
        color: white !important;
        padding: 12px 20px;
        border-radius: 10px;
        font-family: {font_family} !important;
        font-weight: 700 !important;
        margin: 1.5rem 0 1rem 0;
    }}
    .stFileUploader {{
        direction: {direction} !important;
    }}
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {{
        direction: {direction} !important;
        text-align: {"right" if lang == "ar" else "left"} !important;
        font-family: {font_family} !important;
    }}
</style>
""", unsafe_allow_html=True)

L = LABELS[lang]

# ==========================================
# زر تبديل اللغة
# ==========================================
col_lang, col_space = st.columns([1, 6])
with col_lang:
    if st.button(L['lang_toggle'], key='lang_btn'):
        st.session_state['lang'] = 'en' if lang == 'ar' else 'ar'
        st.rerun()

# ==========================================
# Header
# ==========================================
st.markdown(f"""
<div class="app-header">
    <h1>{L['title']}</h1>
    <p>{L['subtitle']}</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# دوال الذكاء الاصطناعي
# ==========================================
def run_ai(prompt, api_key):
    try:
        client = OpenAI(base_url="https://router.huggingface.co/v1/", api_key=api_key)
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ خطأ: {e}"

# ==========================================
# دوال المعالجة
# ==========================================
def encode_likert(df):
    likert_map = {
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "غير موافق": 2, "غير موافق بشدة": 1,
        "راض جداً": 5, "راض": 4, "غير راض": 2, "غير راض جداً": 1,
        "دائماً": 5, "غالبا": 4, "أحياناً": 3, "نادراً": 2, "أبدا": 1,
        "نعم": 2, "لا": 1
    }
    df_cleaned = df.copy()
    for col in df_cleaned.select_dtypes(include=['object']).columns:
        df_cleaned[col] = df_cleaned[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
    df_cleaned = df_cleaned.replace(likert_map)
    for col in df_cleaned.columns:
        try:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col])
        except:
            pass
    return df_cleaned

def smart_classify_columns(df):
    categorical_cols, numeric_cols = [], []
    demo_keywords = ['عمر', 'جنس', 'مؤهل', 'خبرة', 'دخل', 'تخصص', 'عمل', 'مستوى']
    for col in df.columns:
        if col.lower() in ['timestamp', 'unnamed: 0']:
            continue
        is_demo = any(k in str(col).lower() for k in demo_keywords) and len(str(col).split()) <= 4
        if is_demo:
            categorical_cols.append(col)
        else:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > len(df) * 0.3:
                numeric_cols.append(col)
            elif df[col].nunique() <= 15:
                categorical_cols.append(col)
    return categorical_cols, numeric_cols

# ==========================================
# الشريط الجانبي
# ==========================================
if "HF_TOKEN" in st.secrets:
    api_key = st.secrets["HF_TOKEN"]
else:
    st.sidebar.title(L['ai_settings'])
    api_key = st.sidebar.text_input(L['api_key'], type="password")

uploaded_file = st.file_uploader(L['upload'], type=["csv", "xlsx"], key="uploader_main")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)

        st.sidebar.title(L['dimensions'])
        st.sidebar.success(L['detected'].format(len(num_cols_auto)))

        categorical_cols = st.sidebar.multiselect(L['cat_vars'], df_encoded.columns, default=cat_cols_auto, key="cat_vars_sel")
        all_questions = [c for c in num_cols_auto if c not in categorical_cols]
        num_dims = st.sidebar.number_input(L['num_dims'], min_value=1, max_value=15, value=6, key="num_dims_inp")

        dimensions_dict, analysis_cols, active_questions = {}, [], []
        chunk_size = max(1, len(all_questions) // int(num_dims)) if all_questions else 1

        for i in range(int(num_dims)):
            st.sidebar.markdown("---")
            dim_name = st.sidebar.text_input(L['dim_name'].format(i+1), L['dim_default'].format(i+1), key=f"dim_name_{i}")
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < int(num_dims) - 1 else len(all_questions)
            default_cols = all_questions[start_idx:end_idx] if all_questions else []
            dim_cols = st.sidebar.multiselect(L['dim_cols'].format(dim_name), all_questions, default=default_cols, key=f"dim_cols_{i}")
            
            if dim_cols:
                dimensions_dict[dim_name] = dim_cols
                df_encoded[dim_cols] = df_encoded[dim_cols].apply(pd.to_numeric, errors='coerce')
                df_encoded[dim_name] = df_encoded[dim_cols].mean(axis=1)
                analysis_cols.append(dim_name)
                active_questions.extend(dim_cols)

        active_questions = list(dict.fromkeys(active_questions))
        if active_questions:
            df_encoded['الاستبيان ككل'] = df_encoded[active_questions].mean(axis=1)
            analysis_cols.append('الاستبيان ككل')

        if not analysis_cols:
            st.warning(L['warning_select'])
        else:
            # ==========================================
            # التبويبات
            # ==========================================
            tabs = st.tabs(L['tabs'])
            
            # التبويب 1: عينة الدراسة
            with tabs[0]:
                st.subheader("👥 وصف عينة الدراسة")
                if categorical_cols:
                    for col in categorical_cols:
                        st.markdown(f"### 📊 {col}")
                        counts = df_encoded[col].value_counts()
                        percentages = df_encoded[col].value_counts(normalize=True) * 100
                        demo_df = pd.DataFrame({'التكرار': counts, 'النسبة (%)': percentages.round(2)})
                        col1, col2 = st.columns(2)
                        with col1:
                            st.dataframe(demo_df, use_container_width=True)
                        with col2:
                            fig = px.pie(demo_df, values='التكرار', names=demo_df.index, height=300)
                            st.plotly_chart(fig, use_container_width=True)
                        st.info(f"**التفسير:** الفئة الأعلى هي ({counts.idxmax()}) بنسبة ({percentages.max():.1f}%)")
                        st.markdown("---")

            # التبويب 2: الإحصاء الوصفي
            with tabs[1]:
                st.subheader("📊 الإحصاء الوصفي")
                desc_df = df_encoded[analysis_cols].describe().T
                desc_df = desc_df.rename(columns={'count':'العدد', 'mean':'المتوسط', 'std':'الانحراف', 'min':'الأدنى', 'max':'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف', 'الأدنى', 'الأقصى']], use_container_width=True)
                st.info("📝 **التفسير:** المتوسط يحدد الاتجاه العام، والانحراف يقيس تشتت الآراء")

            # التبويب 3: الثبات
            with tabs[2]:
                st.subheader("🧪 معامل الثبات (ألفا)")
                alpha_results = []
                for dim_name, cols in dimensions_dict.items():
                    if len(cols) > 1:
                        a_val = pg.cronbach_alpha(data=df_encoded[cols].dropna())[0]
                        alpha_results.append({"المحور": dim_name, "ألفا": round(a_val, 3)})
                if alpha_results:
                    st.dataframe(pd.DataFrame(alpha_results), use_container_width=True)
                    st.info("📝 **التفسير:** القيم القريبة من 1.00 تدل على موثوقية ممتازة")

            # التبويب 4: الفروق
            with tabs[3]:
                st.subheader("⚖️ الفروق (T-test / ANOVA)")
                if categorical_cols and analysis_cols:
                    g_col = st.selectbox("المتغير الديموغرافي:", categorical_cols, key="g_col_sel")
                    t_col = st.selectbox("المحور:", analysis_cols, key="t_col_sel")
                    temp_df = df_encoded[[g_col, t_col]].dropna()
                    grps = temp_df[g_col].unique()
                    if len(grps) >= 2:
                        if len(grps) == 2:
                            g1 = temp_df[temp_df[g_col]==grps[0]][t_col].astype(float)
                            g2 = temp_df[temp_df[g_col]==grps[1]][t_col].astype(float)
                            res = pg.ttest(g1, g2)
                        else:
                            res = pg.anova(data=temp_df, dv=t_col, between=g_col)
                        st.dataframe(res)
                        pval = res['p-val'].values[0] if 'p-val' in res.columns else res['p-unc'].values[0]
                        if pval < 0.05:
                            st.success("✅ توجد فروق ذات دلالة إحصائية")
                        else:
                            st.warning("⚠️ لا توجد فروق ذات دلالة إحصائية")

            # التبويب 5: الارتباط
            with tabs[4]:
                st.subheader("🔗 الارتباط (Pearson)")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور الأول:", analysis_cols, key="corr_v1")
                    v2 = st.selectbox("المحور الثاني:", [c for c in analysis_cols if c != v1], key="corr_v2")
                    clean_data = df_encoded[[v1, v2]].dropna()
                    corr_res = pg.corr(clean_data[v1], clean_data[v2], method='pearson')
                    st.dataframe(corr_res[['n', 'r', 'p-val']])
                    rval = corr_res['r'].values[0]
                    pval = corr_res['p-val'].values[0]
                    if pval < 0.05:
                        st.success(f"✅ علاقة {'طردية' if rval > 0 else 'عكسية'} (r={rval:.3f})")
                    else:
                        st.warning("⚠️ لا توجد علاقة دالة")

            # التبويب 6: الانحدار
            with tabs[5]:
                st.subheader("📈 الانحدار الخطي")
                if len(analysis_cols) >= 2:
                    dep_var = st.selectbox("المتغير التابع:", analysis_cols, key="reg_dep")
                    indep_vars = st.multiselect("المتغيرات المستقلة:", [c for c in analysis_cols if c != dep_var], key="reg_indep")
                    if indep_vars:
                        reg_data = df_encoded[[dep_var] + indep_vars].dropna()
                        lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var])
                        st.dataframe(lm)
                        r2 = lm['r2'].values[0] if 'r2' in lm.columns else 0
                        st.info(f"معامل التحديد R² = {r2:.3f} ({float(r2)*100:.1f}%)")

            # التبويب 7: المحلل الذكي
            with tabs[6]:
                st.header("🧠 المحلل الذكي للفرضيات")
                if not api_key:
                    st.error("⚠️ أدخل مفتاح API في الشريط الجانبي")
                else:
                    hypothesis = st.text_area("أدخل الفرضية:", key="hyp_input")
                    if st.button("🔍 تحليل"):
                        with st.spinner("جاري التحليل..."):
                            result = run_ai(f"حلل هذه الفرضية: {hypothesis}", api_key)
                            st.success(result)

            # التبويب 8: النتائج
            with tabs[7]:
                st.markdown(f'<div class="section-title">{L["results_title"]}</div>', unsafe_allow_html=True)
                result_num = 1
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        mean_val = df_encoded[cols].mean().mean()
                        level = "مرتفع" if mean_val >= 3.68 else ("متوسط" if mean_val >= 2.34 else "منخفض")
                        st.markdown(f"""
                        <div class="result-card">
                            <strong>النتيجة ({result_num}):</strong> محور ({dim_name}) - مستوى: {level} - متوسط: {mean_val:.2f}
                        </div>
                        """, unsafe_allow_html=True)
                        result_num += 1

            # التبويب 9: التوصيات
            with tabs[8]:
                st.markdown(f'<div class="section-title">{L["recs_title"]}</div>', unsafe_allow_html=True)
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        item_means = df_encoded[cols].mean()
                        lowest_item = item_means.idxmin()
                        lowest_mean = item_means.min()
                        st.markdown(f"""
                        <div class="rec-card">
                            <strong>📌 توصية:</strong> الاهتمام بـ ({lowest_item}) في محور ({dim_name}) - المتوسط: {lowest_mean:.2f}
                        </div>
                        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ خطأ: {e}")
else:
    st.info("📁 يرجى رفع ملف البيانات للبدء")
