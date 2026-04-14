import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

# محاولة استيراد مكتبة Google Gemini بأمان
try:
    import google.generativeai as genai
except ImportError:
    st.warning("جاري إعداد مكتبة Google Gemini...")

st.set_page_config(page_title="SmartStat Pro | الخبير الإحصائي", page_icon="📊", layout="wide")

# ==========================================
# --- دوال الذكاء الاصطناعي (Gemini AI Functions) ---
# ==========================================
def run_gemini(prompt, api_key):
    try:
        # إعداد المفتاح واختيار الموديل المستقر (gemini-pro)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ خطأ في الاتصال بالذكاء الاصطناعي (Gemini): {e}"

def analyze_hypothesis_text(text, api_key):
    prompt = f"""
    حلل الفرضية الإحصائية التالية بدقة:
    "{text}"
    استخرج المعلومات التالية باختصار شديد:
    - نوع الفرضية: (اكتب فقط: علاقة، أو تأثير، أو فروق)
    - المتغير المستقل: (اسم المتغير)
    - المتغير التابع: (اسم المتغير)
    """
    return run_gemini(prompt, api_key)

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
    return run_gemini(prompt, api_key)

def get_table_explanation(table_string, context, api_key):
    prompt = f"""
    بصفتك خبيراً إحصائياً، قم بقراءة هذا الجدول الخاص بـ ({context}):
    {table_string}
    
    اكتب فقرة أكاديمية مسهبة تشرح أهم ما جاء في هذا الجدول، استخرج أعلى وأقل القيم، وفسر معناها في سياق البحث العلمي باللغة العربية.
    """
    return run_gemini(prompt, api_key)

# ==========================================
# --- 1. دالة التشفير الذكي ---
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
            try: df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except ValueError: pass 
    return df_cleaned

# --- 2. التصنيف الدلالي المطور ---
def smart_classify_columns(df):
    categorical_cols, numeric_cols = [], []
    demo_keywords = ['عمر', 'سن', 'جنس', 'نوع', 'مؤهل', 'مرحلة', 'صف', 'خبرة', 'حالة', 'دخل', 'تخصص', 'عمل', 'تعليم', 'مهنة', 'زيارة', 'مستوى']
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
st.title("📊 SmartStat Pro - نظام الخبير الإحصائي الآلي")
st.markdown("يُرفق النظام الآن **تفسيراً أكاديمياً مسهباً** مع كل نتيجة إحصائية (وصفي، عينة، فروق، ارتباط، انحدار) جاهز للنسخ المباشر في فصول مناقشة النتائج.")
st.markdown("---")

# ==========================================
# سحب مفتاح الذكاء الاصطناعي (Gemini) تلقائياً
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.sidebar.title("🤖 إعدادات الذكاء الاصطناعي")
    api_key = st.sidebar.text_input("🔑 مفتاح Gemini API:", type="password", help="ضع المفتاح هنا لتفعيل الشرح التوليدي والتبويب السابع")

uploaded_file = st.file_uploader("قم برفع ملف البيانات الخام (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)
        
        st.sidebar.title("⚙️ بناء المحاور (Dimensions)")
        st.sidebar.success(f"تم اكتشاف {len(num_cols_auto)} سؤال استبيان بنجاح!")
        
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات الشخصية (للمقارنة):", df_encoded.columns, default=cat_cols_auto)
        all_questions = [c for c in num_cols_auto if c not in categorical_cols]
        num_dims = st.sidebar.number_input("🔢 كم عدد المحاور/الأبعاد في دراستك؟", min_value=1, max_value=15, value=6)
        
        dimensions_dict = {}
        analysis_cols = []
        active_questions = []
        chunk_size = max(1, len(all_questions) // int(num_dims)) if all_questions else 1
        
        for i in range(int(num_dims)):
            st.sidebar.markdown(f"---")
            dim_name = st.sidebar.text_input(f"اسم المحور {i+1}:", f"المحور {i+1}", key=f"name_{i}")
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < int(num_dims) - 1 else len(all_questions)
            default_cols = all_questions[start_idx:end_idx] if all_questions else []
            dim_cols = st.sidebar.multiselect(f"أسئلة {dim_name}:", all_questions, default=default_cols, key=f"cols_{i}")
            
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
            st.warning("يرجى تحديد أسئلة المحاور من القائمة الجانبية للبدء.")
        else:
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "👥 عينة الدراسة", "📊 الإحصاء الوصفي", "🧪 الثبات (ألفا)", 
                "⚖️ الفروق (T-test/ANOVA)", "🔗 الارتباط (Pearson)", "📈 الانحدار", "🧠 محلل الفرضيات الذكي"
            ])

            # 1. تبويب عينة الدراسة
            with tab1:
                st.subheader("👥 وصف عينة الدراسة (التكرارات والنسب)")
                if categorical_cols:
                    for col in categorical_cols:
                        st.markdown(f"### 📊 توزيع أفراد العينة حسب: ({col})")
                        counts = df_encoded[col].value_counts()
                        percentages = df_encoded[col].value_counts(normalize=True) * 100
                        demo_df = pd.DataFrame({'التكرار': counts, 'النسبة (%)': percentages.round(2)})
                        col1, col2 = st.columns(2)
                        with col1: st.dataframe(demo_df, use_container_width=True)
                        with col2: st.plotly_chart(px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.3, height=350), use_container_width=True)
                        if api_key:
                            if st.button(f"✨ توليد قراءة ذكية متعمقة لجدول ({col})", key=f"ai_demo_{col}"):
                                with st.spinner("جاري صياغة التفسير الأكاديمي عبر Gemini..."):
                                    st.success(get_table_explanation(demo_df.to_markdown(), f"توزيع العينة حسب {col}", api_key))
                        st.markdown("---")

            # 2. تبويب الإحصاء الوصفي
            with tab2:
                st.subheader("📊 الإحصاء الوصفي (المتوسطات والانحرافات المعيارية)")
                desc_df = df_encoded[analysis_cols].describe().T.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)
                if api_key:
                    if st.button("✨ توليد قراءة ذكية لجدول المحاور", key="ai_desc"):
                        with st.spinner("جاري التحليل عبر Gemini..."):
                            st.success(get_table_explanation(desc_df.to_markdown(), "المتوسطات والانحرافات المعيارية للمحاور", api_key))
                st.info("التحليل الوصفي المعروض أعلاه يشخص مستوى الاستجابة لمتغيرات ومحاور الدراسة وفقاً لآراء أفراد العينة.")

            # 3. الثبات
            with tab3:
                st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
                alpha_results = [{"المحور / البعد": d, "عدد العبارات": len(c), "معامل ألفا": round(pg.cronbach_alpha(data=df_encoded[c].dropna())[0], 3)} for d, c in dimensions_dict.items() if len(c) > 1]
                if len(active_questions) > 1:
                    alpha_results.append({"المحور / البعد": "الاستبيان ككل", "عدد العبارات": len(active_questions), "معامل ألفا": round(pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0], 3)})
                st.dataframe(pd.DataFrame(alpha_results), use_container_width=True)

            # 4. الفروق
            with tab4:
                st.subheader("⚖️ دلالة الفروق (T-test و ANOVA)")
                if categorical_cols and analysis_cols:
                    g_col = st.selectbox("المتغير المستقل:", categorical_cols, key="g_f")
                    t_col = st.selectbox("المتغير التابع:", analysis_cols, index=len(analysis_cols)-1, key="t_f")
                    res_data = df_encoded[[g_col, t_col]].dropna()
                    grps = res_data[g_col].unique()
                    if len(grps) == 2:
                        res = pg.ttest(res_data[res_data[g_col]==grps[0]][t_col].astype(float), res_data[res_data[g_col]==grps[1]][t_col].astype(float))
                        st.dataframe(res)
                    elif len(grps) > 2:
                        res = pg.anova(data=res_data, dv=t_col, between=g_col)
                        st.dataframe(res)
                    st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)

            # 5. الارتباط
            with tab5:
                st.subheader("🔗 قياس الارتباط بين المحاور (Pearson Correlation)")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور 1:", analysis_cols, key="c1")
                    v2 = st.selectbox("المحور 2:", analysis_cols, index=1, key="c2")
                    if v1 != v2:
                        st.dataframe(pg.corr(df_encoded[v1].dropna(), df_encoded[v2].dropna(), method='pearson'))
                        st.plotly_chart(px.scatter(df_encoded, x=v1, y=v2, trendline="ols"), use_container_width=True)

            # 6. الانحدار
            with tab6:
                st.subheader("📈 تحليل الانحدار الخطي (Regression)")
                if len(analysis_cols) >= 2:
                    dep_var = st.selectbox("التابع (Y):", analysis_cols, key='reg_y')
                    indep_vars = st.multiselect("المستقل (X):", [c for c in analysis_cols if c != dep_var], key='reg_x')
                    if indep_vars:
                        st.dataframe(pg.linear_regression(df_encoded[indep_vars], df_encoded[dep_var]))

            # 7. محلل الفرضيات الذكي (AI Engine)
            with tab7:
                st.header("🧠 المحلل الذكي للفرضيات (Gemini AI)")
                if not api_key:
                    st.error("⚠️ يرجى إدخال مفتاح Gemini API في القائمة الجانبية.")
                else:
                    user_hypothesis = st.text_area("✍️ نص الفرضية:", "مثال: توجد علاقة بين جودة المعلومات والترويج.")
                    if st.button("🔍 تحليل الفرضية آلياً"):
                        with st.spinner("Gemini يحلل الفرضية..."):
                            st.session_state['ai_analysis'] = analyze_hypothesis_text(user_hypothesis, api_key)
                    if 'ai_analysis' in st.session_state:
                        st.info(st.session_state['ai_analysis'])
                    
                    st.markdown("---")
                    col_type = st.selectbox("نوع الاختبار:", ["علاقة (Pearson)", "تأثير (Regression)", "فروق"])
                    h_indep = st.selectbox("المستقل:", categorical_cols if "فروق" in col_type else analysis_cols)
                    h_dep = st.selectbox("التابع:", analysis_cols)
                    
                    if st.button("🚀 تنفيذ وتوليد مناقشة النتائج"):
                        with st.spinner("جاري التوليد عبر Gemini..."):
                            clean_df = df_encoded[[h_indep, h_dep]].dropna()
                            if "علاقة" in col_type: res = pg.corr(clean_df[h_indep].astype(float), clean_df[h_dep].astype(float))
                            elif "تأثير" in col_type: res = pg.linear_regression(clean_df[[h_indep]].astype(float), clean_df[h_dep].astype(float))
                            elif "فروق" in col_type:
                                grps = clean_df[h_indep].unique()
                                if len(grps) == 2: res = pg.ttest(clean_df[clean_df[h_indep]==grps[0]][h_dep], clean_df[clean_df[h_indep]==grps[1]][h_dep])
                                else: res = pg.anova(data=clean_df, dv=h_dep, between=h_indep)
                            
                            st.dataframe(res)
                            st.success(generate_detailed_explanation(res.to_markdown(), user_hypothesis, api_key))

    except Exception as e: st.error(f"خطأ في معالجة الملف: {e}")
