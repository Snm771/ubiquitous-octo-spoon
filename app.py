import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

# استيراد مكتبة OpenAI المستقرة جداً للربط مع سيرفرات Hugging Face
try:
    from openai import OpenAI
except ImportError:
    st.warning("جاري إعداد المكتبات...")

st.set_page_config(page_title="SmartStat Pro | الخبير الإحصائي", page_icon="📊", layout="wide")

# ==========================================
# 🌍 1. نظام اللغات والتنسيق المتقدم (RTL / LTR)
# ==========================================
if 'lang' not in st.session_state:
    st.session_state.lang = "العربية"

lang = st.sidebar.radio("🌍 اختر لغة الواجهة / Select Language:", ["العربية", "English"])

# قاموس الترجمة لجميع نصوص الواجهة
t = {
    "العربية": {
        "main_title": "📊 SmartStat Pro - نظام الخبير الإحصائي الآلي",
        "sub_title": "يُرفق النظام الآن **تفسيراً أكاديمياً** مع كل نتيجة إحصائية (وصفي، عينة، فروق، ارتباط، انحدار) جاهز للنسخ المباشر في فصول مناقشة النتائج.",
        "ai_settings": "🤖 إعدادات الذكاء الاصطناعي",
        "api_input": "🔑 مفتاح Hugging Face API:",
        "upload": "قم برفع ملف البيانات الخام (CSV أو Excel)",
        "build_dims": "⚙️ بناء المحاور (Dimensions)",
        "success_detect": "تم اكتشاف {} سؤال استبيان بنجاح!",
        "personal_vars": "👥 المتغيرات الشخصية (للمقارنة):",
        "num_dims": "🔢 كم عدد المحاور/الأبعاد في دراستك؟",
        "axis_name": "اسم المحور",
        "axis_q": "أسئلة المحور",
        "warn_dims": "يرجى تحديد أسئلة المحاور من القائمة الجانبية للبدء.",
        "tabs": [
            "👥 عينة الدراسة", "📊 الإحصاء الوصفي", "🧪 الثبات (ألفا)", 
            "⚖️ الفروق (T-test/ANOVA)", "🔗 الارتباط (Pearson)", "📈 الانحدار", 
            "🧠 محلل الفرضيات الذكي", "🎯 النتائج والتوصيات"
        ],
        "total_row": "📊 المجموع الكلي ✓",
        "chart_type": "اختر نوع الرسم لـ ({col}):",
        "charts": ["دائري (Pie)", "أعمدة (Bar)", "دائري مجوف (Donut)", "خطي (Line)", "أعمدة أفقية (H-Bar)"],
        "academic_exp": "📝 التفسير الأكاديمي:",
        "res_title": "🎯 النتائج والتوصيات الذكية",
        "level_high": "مرتفع", "level_mid": "متوسط", "level_low": "منخفض"
    },
    "English": {
        "main_title": "📊 SmartStat Pro - Automated Statistical Expert",
        "sub_title": "The system now provides an **academic explanation** with every statistical result, ready for direct copying.",
        "ai_settings": "🤖 AI Settings",
        "api_input": "🔑 Hugging Face API Key:",
        "upload": "Upload Raw Data File (CSV or Excel)",
        "build_dims": "⚙️ Build Dimensions",
        "success_detect": "Successfully detected {} survey questions!",
        "personal_vars": "👥 Personal Variables (for comparison):",
        "num_dims": "🔢 How many dimensions/axes in your study?",
        "axis_name": "Dimension Name",
        "axis_q": "Dimension Questions",
        "warn_dims": "Please select the dimension questions from the sidebar to start.",
        "tabs": [
            "👥 Study Sample", "📊 Descriptive Stats", "🧪 Reliability (Alpha)", 
            "⚖️ Differences (T-test/ANOVA)", "🔗 Correlation (Pearson)", "📈 Regression", 
            "🧠 AI Hypothesis Analyst", "🎯 Results & Recs"
        ],
        "total_row": "📊 Grand Total ✓",
        "chart_type": "Choose chart type for ({col}):",
        "charts": ["Pie", "Bar", "Donut", "Line", "H-Bar"],
        "academic_exp": "📝 Academic Explanation:",
        "res_title": "🎯 Smart Results & Recommendations",
        "level_high": "High", "level_mid": "Moderate", "level_low": "Low"
    }
}
c = t[lang]

# حقن كود CSS لإصلاح مشاكل اللغة العربية
if lang == "العربية":
    st.markdown("""
        <style>
        .stApp, [data-testid="stSidebar"], [data-testid="stMarkdownContainer"], .stText, .stDataFrame, .stTable {
            direction: rtl !important;
            text-align: right !important;
        }
        /* إصلاح علامات الترقيم في نهاية الجملة لتكون مضبوطة تماماً */
        p, div, span, label, h1, h2, h3, h4, h5, h6, li {
            unicode-bidi: plaintext !important;
            text-align: right !important;
        }
        .stRadio > div { direction: rtl !important; }
        .stTabs [data-baseweb="tab-list"] { direction: rtl !important; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""<style>.stApp { direction: ltr !important; text-align: left !important; }</style>""", unsafe_allow_html=True)

# تهيئة مخزن الجلسة للفرضيات المختبرة
if 'hypothesis_history' not in st.session_state:
    st.session_state['hypothesis_history'] = []

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
        return f"⚠️ Error: {e}"

def analyze_hypothesis_text(text, api_key):
    lang_instruction = "باللغة العربية" if lang == "العربية" else "in English"
    prompt = f"""حلل الفرضية الإحصائية التالية بدقة: "{text}"
    استخرج المعلومات التالية باختصار شديد {lang_instruction}:
    - نوع الفرضية: (علاقة، تأثير، أو فروق)
    - المتغير المستقل
    - المتغير التابع"""
    return run_ai(prompt, api_key)

def generate_detailed_explanation(results, hypothesis, api_key):
    lang_instruction = "اجعل اللغة أكاديمية، رصينة، واحترافية جداً باللغة العربية." if lang == "العربية" else "Make the language highly academic, formal, and professional in English."
    prompt = f"""بصفتك أستاذاً جامعياً، لديك نتائج تحليل إحصائي: {results}
    والفرضية: "{hypothesis}"
    اكتب تفسيراً أكاديمياً تفصيلياً (يصلح للنسخ المباشر في الفصل الرابع: مناقشة النتائج)، ويجب أن يشمل:
    1. قراءة وتفسير الأرقام في الجدول.
    2. تفسير كل قيمة علمياً.
    3. تفسير اتجاه العلاقة أو حجم الأثر.
    4. قرار واضح بقبول أو رفض الفرضية.
    5. فقرة مناقشة النتائج.
    {lang_instruction}"""
    return run_ai(prompt, api_key)

def get_table_explanation(table_string, context, api_key):
    lang_instruction = "باللغة العربية" if lang == "العربية" else "in English"
    prompt = f"بصفتك خبيراً إحصائياً، اكتب فقرة أكاديمية {lang_instruction} تشرح أهم ما جاء في هذا الجدول لـ ({context}): {table_string}"
    return run_ai(prompt, api_key)

# ==========================================
# --- 1. دالة التشفير الذكي ---
def encode_likert(df):
    likert_map = {
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1, "لا أوافق": 2, "لا أوافق بشدة": 1,
        "راض جدا": 5, "راض جداً": 5, "راض": 4, "راضي": 4, "راضي جدا": 5, "غير راض": 2, "غير راضي": 2, "غير راض جدا": 1, "غير راض جداً": 1, "غير راضي جدا": 1,
        "دائما": 5, "دائماً": 5, "غالبا": 4, "غالباً": 4, "أحيانا": 3, "أحياناً": 3, "نادرا": 2, "نادراً": 2, "أبدا": 1, "أبداً": 1, "مطلقا": 1, "مطلقاً": 1,
        "بدرجة كبيرة جدا": 5, "بدرجة كبيرة جداً": 5, "بدرجة كبيرة": 4, "بدرجة متوسطة": 3, "بدرجة قليلة": 2, "بدرجة ضعيفة": 2, "بدرجة قليلة جدا": 1, "بدرجة ضعيفة جدا": 1,
        "نعم": 2, "لا": 1,
        "Strongly Agree": 5, "Agree": 4, "Neutral": 3, "Disagree": 2, "Strongly Disagree": 1
    }
    df_cleaned = df.copy()
    for col in df_cleaned.select_dtypes(include=['object']).columns:
        df_cleaned[col] = df_cleaned[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
    df_cleaned = df_cleaned.replace(likert_map)
    for col in df_cleaned.columns:
        if col != 'Timestamp':
            try: df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except ValueError: pass 
    return df_cleaned

# --- 2. التصنيف الدلالي المطور ---
def smart_classify_columns(df):
    categorical_cols, numeric_cols = [], []
    demo_keywords = ['عمر', 'سن', 'جنس', 'نوع', 'مؤهل', 'مرحلة', 'صف', 'خبرة', 'حالة', 'دخل', 'تخصص', 'عمل', 'تعليم', 'مهنة', 'زيارة', 'مستوى', 'age', 'gender', 'edu', 'exp']
    for col in df.columns:
        if col.lower() in ['timestamp', 'unnamed: 0']: continue
        words_count = len(str(col).split())
        is_demo = any(keyword in str(col).lower() for keyword in demo_keywords) and words_count <= 4
        if is_demo: categorical_cols.append(col)
        else:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > (len(df) * 0.3): numeric_cols.append(col)
            elif df[col].nunique() <= 15: categorical_cols.append(col)
    return categorical_cols, numeric_cols

# ==========================================
# واجهة المستخدم الأساسية
# ==========================================
st.title(c["main_title"])
st.markdown(c["sub_title"])
st.markdown("---")

if "HF_TOKEN" in st.secrets:
    api_key = st.secrets["HF_TOKEN"]
else:
    st.sidebar.title(c["ai_settings"])
    api_key = st.sidebar.text_input(c["api_input"], type="password")

uploaded_file = st.file_uploader(c["upload"], type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)
        
        st.sidebar.title(c["build_dims"])
        st.sidebar.success(c["success_detect"].format(len(num_cols_auto)))
        
        categorical_cols = st.sidebar.multiselect(c["personal_vars"], df_encoded.columns, default=cat_cols_auto)
        all_questions = [c for c in num_cols_auto if c not in categorical_cols]
        
        num_dims = st.sidebar.number_input(c["num_dims"], min_value=1, max_value=15, value=6)
        
        dimensions_dict = {}
        analysis_cols = []
        active_questions = []
        chunk_size = max(1, len(all_questions) // int(num_dims)) if all_questions else 1
        
        for i in range(int(num_dims)):
            st.sidebar.markdown(f"---")
            dim_name = st.sidebar.text_input(f"{c['axis_name']} {i+1}:", f"المحور {i+1}" if lang=="العربية" else f"Axis {i+1}", key=f"name_{i}")
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < int(num_dims) - 1 else len(all_questions)
            default_cols = all_questions[start_idx:end_idx] if all_questions else []
            dim_cols = st.sidebar.multiselect(f"{c['axis_q']} {dim_name}:", all_questions, default=default_cols, key=f"cols_{i}")
            
            if dim_cols:
                dimensions_dict[dim_name] = dim_cols
                df_encoded[dim_cols] = df_encoded[dim_cols].apply(pd.to_numeric, errors='coerce')
                df_encoded[dim_name] = df_encoded[dim_cols].mean(axis=1)
                analysis_cols.append(dim_name)
                active_questions.extend(dim_cols)
                
        active_questions = list(dict.fromkeys(active_questions))

        if len(active_questions) > 0:
            gen_mean_label = 'الاستبيان ككل (المتوسط العام)' if lang=="العربية" else 'Overall Mean'
            df_encoded[gen_mean_label] = df_encoded[active_questions].mean(axis=1)
            analysis_cols.append(gen_mean_label)

        if not analysis_cols:
            st.warning(c["warn_dims"])
        else:
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(c["tabs"])

            # 1. تبويب عينة الدراسة
            with tab1:
                st.subheader(f"👥 {c['tabs'][0]}")
                if categorical_cols:
                    for col in categorical_cols:
                        st.markdown(f"### 📊 {col}")
                        
                        counts = df_encoded[col].value_counts()
                        percentages = df_encoded[col].value_counts(normalize=True) * 100
                        demo_df = pd.DataFrame({'التكرار' if lang=="العربية" else 'Frequency': counts, 'النسبة (%)' if lang=="العربية" else 'Percentage (%)': percentages.round(2)})
                        
                        total_row = pd.DataFrame({
                            'التكرار' if lang=="العربية" else 'Frequency': [len(df_encoded)],
                            'النسبة (%)' if lang=="العربية" else 'Percentage (%)': [100.00]
                        }, index=[c["total_row"]])
                        demo_df_with_total = pd.concat([demo_df, total_row])
                        
                        col1, col2 = st.columns(2)
                        with col1: 
                            st.dataframe(demo_df_with_total, use_container_width=True)
                            chart_type_demo = st.radio(c["chart_type"].format(col=col), c["charts"], key=f"chart_{col}", horizontal=True)
                            
                        with col2: 
                            freq_col = 'التكرار' if lang=="العربية" else 'Frequency'
                            if chart_type_demo == c["charts"][0]: # Pie
                                fig = px.pie(demo_df, values=freq_col, names=demo_df.index, height=350)
                            elif chart_type_demo == c["charts"][1]: # Bar
                                fig = px.bar(demo_df, x=demo_df.index, y=freq_col, text=freq_col, color=demo_df.index, height=350)
                            elif chart_type_demo == c["charts"][2]: # Donut
                                fig = px.pie(demo_df, values=freq_col, names=demo_df.index, hole=0.4, height=350)
                            elif chart_type_demo == c["charts"][3]: # Line
                                fig = px.line(demo_df, x=demo_df.index, y=freq_col, markers=True, height=350)
                            else: # H-Bar
                                fig = px.bar(demo_df, x=freq_col, y=demo_df.index, text=freq_col, color=demo_df.index, orientation='h', height=350)
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        exp_txt = f"يوضح العرض الإحصائي أعلاه التوزيع التكراري والنسبي لأفراد عينة الدراسة البالغ عددهم الإجمالي ({len(df_encoded)}) مبحوثاً، وذلك وفقاً لتصنيفاتهم في متغير ({col}). من خلال استقراء النتائج، يتبين بوضوح أن الفئة الأكثر تمثيلاً وحضوراً في العينة هي فئة ({counts.idxmax()}) بنسبة مئوية قدرها ({percentages.max():.1f}%)." if lang=="العربية" else f"The statistical display above shows the frequency and percentage distribution of the study sample, totaling ({len(df_encoded)}) respondents, according to ({col}). The most represented category is ({counts.idxmax()}) with a percentage of ({percentages.max():.1f}%)."
                        st.info(f"**{c['academic_exp']}**\n {exp_txt}")
                        
                        if api_key:
                            if st.button(f"✨ AI Insight ({col})", key=f"ai_demo_{col}"):
                                with st.spinner("Processing..."):
                                    st.success(get_table_explanation(demo_df_with_total.to_markdown(), f"{col}", api_key))
                        st.markdown("---")

            # 2. تبويب الإحصاء الوصفي
            with tab2:
                st.subheader(f"📊 {c['tabs'][1]}")
                desc_df = df_encoded[analysis_cols].describe().T
                if lang == "العربية": desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']] if lang=="العربية" else desc_df[['count', 'mean', 'std', 'min', 'max']], use_container_width=True)
                if api_key:
                    if st.button("✨ AI Insight", key="ai_desc"):
                        with st.spinner("Processing..."):
                            st.success(get_table_explanation(desc_df.to_markdown(), "Descriptive Stats", api_key))
                
                exp_desc = "يهدف التحليل الوصفي المعروض في الجداول أعلاه إلى تشخيص مستوى الاستجابة لمتغيرات ومحاور الدراسة. بالاعتماد على مقياس النزعة المركزية المتمثل في المتوسط الحسابي، يتم تحديد الاتجاه العام، بينما يبرز دور الانحراف المعياري كمؤشر إحصائي دقيق لقياس مدى تشتت تلك الآراء." if lang=="العربية" else "The descriptive analysis aims to diagnose the response level to the study variables. Relying on the mean to determine the general trend, while the standard deviation acts as a precise indicator to measure the dispersion of those opinions."
                st.info(f"**{c['academic_exp']}** {exp_desc}")

            # 3. الثبات
            with tab3:
                st.subheader(f"🧪 {c['tabs'][2]}")
                alpha_results = []
                for dim_name, cols in dimensions_dict.items():
                    if len(cols) > 1:
                        a_val = pg.cronbach_alpha(data=df_encoded[cols].dropna())[0]
                        alpha_results.append({"المحور / البعد" if lang=="العربية" else "Dimension": dim_name, "عدد العبارات" if lang=="العربية" else "Items": len(cols), "معامل ألفا" if lang=="العربية" else "Alpha": round(a_val, 3)})
                if len(active_questions) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0]
                    alpha_results.append({"المحور / البعد" if lang=="العربية" else "Dimension": "الاستبيان ككل" if lang=="العربية" else "Overall", "عدد العبارات" if lang=="العربية" else "Items": len(active_questions), "معامل ألفا" if lang=="العربية" else "Alpha": round(a_total, 3)})
                
                if alpha_results:
                    st.dataframe(pd.DataFrame(alpha_results), use_container_width=True)
                    exp_alpha = "تشير نتائج التقييم الإحصائي باستخدام معامل ألفا كرونباخ إلى أن أداة الدراسة تتمتع بدرجة من الاتساق الداخلي. وكلما اقتربت القيمة من الواحد الصحيح دلّ ذلك على موثوقية ممتازة." if lang=="العربية" else "The results using Cronbach's Alpha indicate internal consistency. The closer the value is to 1.00, the higher the excellent reliability."
                    st.info(f"**{c['academic_exp']}** {exp_alpha}")

            # 4. دلالة الفروق
            with tab4:
                st.subheader(f"⚖️ {c['tabs'][3]}")
                if categorical_cols and analysis_cols:
                    g_col = st.selectbox("المتغير المستقل (الفئة):" if lang=="العربية" else "Independent Var (Category):", categorical_cols, key="g_f")
                    t_col = st.selectbox("المتغير التابع (المحور):" if lang=="العربية" else "Dependent Var (Dimension):", analysis_cols, index=len(analysis_cols)-1, key="t_f")
                    temp_df = df_encoded[[g_col, t_col]].copy()
                    temp_df[t_col] = pd.to_numeric(temp_df[t_col], errors='coerce')
                    res_data = temp_df.dropna()
                    grps = res_data[g_col].unique()
                    
                    if len(grps) < 2:
                        st.warning("⚠️ مجموعات غير كافية." if lang=="العربية" else "⚠️ Insufficient groups.")
                    else:
                        try:
                            if len(grps) == 2:
                                st.markdown(f"**نوع الاختبار / Test Type:** `T-test`")
                                g1 = res_data[res_data[g_col]==grps[0]][t_col].astype(float).values
                                g2 = res_data[res_data[g_col]==grps[1]][t_col].astype(float).values
                                res = pg.ttest(g1, g2)
                                st.dataframe(res)
                                pval = res['p-val'].values[0] if 'p-val' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)
                            elif len(grps) > 2:
                                st.markdown(f"**نوع الاختبار / Test Type:** `ANOVA`")
                                counts = res_data[g_col].value_counts()
                                valid_grps = counts[counts >= 2].index
                                clean_anova = res_data[res_data[g_col].isin(valid_grps)]
                                res = pg.anova(data=clean_anova, dv=t_col, between=g_col)
                                st.dataframe(res)
                                pval = res['p-unc'].values[0] if 'p-unc' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)
                                
                            if pval < 0.05: 
                                st.success("✅ توجد فروق ذات دلالة إحصائية." if lang=="العربية" else "✅ Statistically significant differences exist.")
                            else: 
                                st.warning("⚠️ لا توجد فروق ذات دلالة إحصائية." if lang=="العربية" else "⚠️ No statistically significant differences.")
                            st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)
                        except Exception as e: st.warning(f"Error: {e}")

            # 5. الارتباط
            with tab5:
                st.subheader(f"🔗 {c['tabs'][4]}")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور 1:" if lang=="العربية" else "Dimension 1:", analysis_cols, key="c1")
                    v2 = st.selectbox("المحور 2:" if lang=="العربية" else "Dimension 2:", analysis_cols, index=1, key="c2")
                    if v1 != v2:
                        try:
                            clean_corr = df_encoded[[v1, v2]].apply(pd.to_numeric, errors='coerce').dropna()
                            corr_res = pg.corr(clean_corr[v1], clean_corr[v2], method='pearson')
                            st.dataframe(corr_res[['n', 'r', 'p-val'] if 'p-val' in corr_res.columns else corr_res.columns])
                            st.plotly_chart(px.scatter(clean_corr, x=v1, y=v2, trendline="ols"), use_container_width=True)
                        except: st.error("Error calculating correlation.")

            # 6. الانحدار
            with tab6:
                st.subheader(f"📈 {c['tabs'][5]}")
                if len(analysis_cols) >= 2:
                    dep_var = st.selectbox("التابع (Y):" if lang=="العربية" else "Dependent (Y):", analysis_cols, key='reg_y')
                    indep_vars = st.multiselect("المستقلات (X):" if lang=="العربية" else "Independents (X):", [col for col in analysis_cols if col != dep_var], default=[col for col in analysis_cols if col != dep_var][:1], key='reg_x')
                    if indep_vars:
                        reg_data = df_encoded[[dep_var] + indep_vars].apply(pd.to_numeric, errors='coerce').dropna()
                        if len(reg_data) > 2:
                            try:
                                lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var])
                                st.dataframe(lm)
                            except: pass

            # 7. محلل الفرضيات الذكي
            with tab7:
                st.subheader(f"🧠 {c['tabs'][6]}")
                u_hypo = st.text_area("✍️ نص الفرضية / Hypothesis text:", "مثال: توجد علاقة ذات دلالة إحصائية بين المتغيرين.")
                if st.button("🔍 AI Analysis"):
                    with st.spinner("Processing..."):
                        st.session_state['ai_analysis'] = analyze_hypothesis_text(u_hypo, api_key)
                if 'ai_analysis' in st.session_state:
                    st.info(st.session_state['ai_analysis'])
                
                st.markdown("---")
                col_type = st.selectbox("Test Type:", ["Pearson", "Regression", "T-test/ANOVA"])
                h_indep = st.selectbox("Independent:", categorical_cols if "T-test" in col_type else analysis_cols)
                h_dep = st.selectbox("Dependent:", analysis_cols)
                
                if st.button("🚀 تنفيذ وحفظ (Execute & Save)"):
                    with st.spinner("Processing..."):
                        clean_df = df_encoded[[h_indep, h_dep]].dropna()
                        try:
                            if "Pearson" in col_type: res = pg.corr(clean_df[h_indep].astype(float), clean_df[h_dep].astype(float))
                            elif "Regression" in col_type: res = pg.linear_regression(clean_df[[h_indep]].astype(float), clean_df[h_dep].astype(float))
                            else: res = pg.ttest(clean_df[clean_df[h_indep]==clean_df[h_indep].unique()[0]][h_dep].astype(float), clean_df[clean_df[h_indep]==clean_df[h_indep].unique()[1]][h_dep].astype(float)) if len(clean_df[h_indep].unique())==2 else pg.anova(data=clean_df, dv=h_dep, between=h_indep)
                            
                            st.dataframe(res)
                            final_exp = generate_detailed_explanation(res.to_markdown(), u_hypo, api_key)
                            st.success(final_exp)
                            st.session_state['hypothesis_history'].append({"text": u_hypo, "result": "tested", "exp": final_exp})
                        except Exception as e: st.error(e)

            # 8. النتائج والتوصيات (مفصولة)
            with tab8:
                st.header(c["res_title"])
                def get_level(mean_val):
                    if mean_val >= 3.68: return c["level_high"]
                    if mean_val >= 2.34: return c["level_mid"]
                    return c["level_low"]

                st.markdown("### 📌 أولاً: أبرز نتائج الدراسة" if lang=="العربية" else "### 📌 Firstly: Key Results")
                result_counter = 1
                
                if categorical_cols:
                    for col in categorical_cols:
                        top_cat = df_encoded[col].value_counts().idxmax()
                        txt = f"الفئة الأعلى تمثيلاً في متغير ({col}) هي فئة ({top_cat})." if lang=="العربية" else f"The highest category in ({col}) is ({top_cat})."
                        st.markdown(f"**{'النتيجة' if lang=='العربية' else 'Result'} ({result_counter}):** {txt}")
                        result_counter += 1
                        
                if len(active_questions) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0]
                    txt = f"بلغ معامل الثبات (ألفا كرونباخ) لأداة الدراسة ({round(a_total, 3)})." if lang=="العربية" else f"Cronbach's Alpha for the study is ({round(a_total, 3)})."
                    st.markdown(f"**{'النتيجة' if lang=='العربية' else 'Result'} ({result_counter}):** {txt}")
                    result_counter += 1
                    
                dim_recs, dim_means_data = [], []
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        item_means = df_encoded[cols].mean()
                        overall_mean = item_means.mean()
                        level = get_level(overall_mean)
                        dim_means_data.append({"المحور" if lang=="العربية" else "Dimension": dim_name, "المتوسط" if lang=="العربية" else "Mean": round(overall_mean, 2)})
                        
                        txt = f"جاء محور ({dim_name}) بمستوى تقييم ({level}) بمتوسط حسابي ({round(overall_mean, 2)})." if lang=="العربية" else f"({dim_name}) achieved a ({level}) level with a mean of ({round(overall_mean, 2)})."
                        st.markdown(f"**{'النتيجة' if lang=='العربية' else 'Result'} ({result_counter}):** {txt}")
                        result_counter += 1
                        
                        low_items = item_means[item_means <= 3.50]
                        if not low_items.empty:
                            for item_text, mean_val in low_items.items():
                                rec_txt = f"توصي الدراسة بضرورة تحسين ({item_text}) من خلال تطوير الممارسات المرتبطة بها." if lang=="العربية" else f"The study recommends improving ({item_text}) to enhance performance."
                                dim_recs.append({"dim": dim_name, "mean": round(mean_val, 2), "rec": rec_txt})
                        else:
                            lowest_item_text = item_means.idxmin()
                            rec_txt = f"توصي الدراسة بضرورة المحافظة على مستوى ({lowest_item_text}) والعمل على تعزيزه بشكل مستمر." if lang=="العربية" else f"The study recommends maintaining and enhancing the level of ({lowest_item_text})."
                            dim_recs.append({"dim": dim_name, "mean": round(item_means.min(), 2), "rec": rec_txt})

                if dim_means_data:
                    st.markdown("#### 📊 " + ("مستويات المحاور (رسم بياني)" if lang=="العربية" else "Dimension Levels (Chart)"))
                    dim_df = pd.DataFrame(dim_means_data)
                    x_col = "المحور" if lang=="العربية" else "Dimension"
                    y_col = "المتوسط" if lang=="العربية" else "Mean"
                    chart_type_res = st.radio("Chart Type:", c["charts"][:3], horizontal=True)
                    if chart_type_res == c["charts"][0]: fig_res = px.pie(dim_df, names=x_col, values=y_col, hole=0.3)
                    elif chart_type_res == c["charts"][1]: fig_res = px.bar(dim_df, x=x_col, y=y_col, text=y_col, color=x_col)
                    else: fig_res = px.line(dim_df, x=x_col, y=y_col, markers=True)
                    st.plotly_chart(fig_res, use_container_width=True)

                st.markdown("---")
                st.markdown("### 💡 ثانياً: التوصيات الذكية" if lang=="العربية" else "### 💡 Secondly: Smart Recommendations")
                if dim_recs:
                    for idx, rec in enumerate(dim_recs, 1):
                        d_lbl = "المحور" if lang=="العربية" else "Dim"
                        m_lbl = "المتوسط" if lang=="العربية" else "Mean"
                        st.info(f"**{idx}. {d_lbl}:** {rec['dim']} | **{m_lbl}:** {rec['mean']}\n\n📌 {rec['rec']}")

    except Exception as e: st.error(f"Error: {e}")
