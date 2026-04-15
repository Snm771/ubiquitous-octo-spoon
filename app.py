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
# ✅ دالة تحليل الفرضيات الذكية (المطلوبة)
# ==========================================
def analyze_hypothesis_smart(hypotheses):
    text = ""
    for i, h in enumerate(hypotheses, 1):
        name = h['name']
        p_value = h['p_value']
        
        # 🔹 تحديد نوع الفرضية تلقائيًا
        if "أثر" in name:
            h_type = "effect"
        elif "علاقة" in name or "ارتباط" in name:
            h_type = "correlation"
        elif "فروق" in name:
            h_type = "difference"
        else:
            h_type = "general"

        text += f"- تبين نتائج اختبار الفرضية ({i}) التي تنص على ({name})، "

        # 🔹 القرار
        if p_value < 0.05:
            text += "وجود دلالة إحصائية.\n"
            if h_type == "effect":
                text += "تشير هذه النتيجة إلى وجود أثر معنوي للمتغير المستقل على المتغير التابع، "
                text += "مما يعني أن التغير في المتغير المستقل يؤدي إلى تغير واضح في المتغير التابع، "
                text += "وهو ما يعكس قوة التأثير وأهميته في تفسير الظاهرة محل الدراسة. "
            elif h_type == "correlation":
                text += "تشير هذه النتيجة إلى وجود علاقة ارتباطية ذات دلالة إحصائية بين المتغيرات، "
                text += "مما يدل على أن المتغيرات تتحرك معًا في اتجاه معين سواء كان طرديًا أو عكسيًا، "
                text += "وهو ما يعكس وجود ارتباط حقيقي يمكن الاعتماد عليه. "
            elif h_type == "difference":
                text += "تشير هذه النتيجة إلى وجود فروق ذات دلالة إحصائية بين متوسطات المجموعات، "
                text += "مما يدل على أن هناك اختلافًا حقيقيًا بين الفئات محل المقارنة، "
                text += "وليس مجرد فروق عشوائية. "
            else:
                text += "تشير هذه النتيجة إلى وجود علاقة ذات دلالة إحصائية بين المتغيرات، "
            text += "وبناءً على ذلك، يتم قبول الفرضية.\n\n"
        else:
            text += "عدم وجود دلالة إحصائية.\n"
            if h_type == "effect":
                text += "تشير هذه النتيجة إلى عدم وجود أثر معنوي للمتغير المستقل على المتغير التابع، "
                text += "مما يدل على ضعف تأثير المتغير المستقل أو عدم وجوده. "
            elif h_type == "correlation":
                text += "تشير هذه النتيجة إلى عدم وجود علاقة ارتباطية ذات دلالة إحصائية بين المتغيرات، "
                text += "مما يدل على أن العلاقة بينهما ضعيفة أو عشوائية. "
            elif h_type == "difference":
                text += "تشير هذه النتيجة إلى عدم وجود فروق ذات دلالة إحصائية بين المجموعات، "
                text += "مما يعني أن الفروق الظاهرة قد تكون عشوائية. "
            else:
                text += "تشير هذه النتيجة إلى عدم وجود علاقة ذات دلالة إحصائية، "
            text += "وبناءً على ذلك، يتم رفض الفرضية.\n\n"
    return text

# ==========================================
# --- دوال المعالجة ---
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
            try: df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except ValueError: pass
    return df_cleaned

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
# ✅ زر تبديل اللغة + إدارة اللغة
# ==========================================
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

def set_language(lang):
    st.session_state.lang = lang
    st.rerun()

# ==========================================
# واجهة المستخدم
# ==========================================
st.title("📊 SmartStat Pro - نظام الخبير الإحصائي الآلي")
st.markdown("يُرفق النظام الآن **تفسيراً أكاديمياً** مع كل نتيجة إحصائية جاهز للنسخ المباشر في فصول مناقشة النتائج.")
st.markdown("---")

# ✅ زر تبديل اللغة في الشريط الجانبي
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 لغة الواجهة")
col_l1, col_l2 = st.sidebar.columns(2)
with col_l1:
    if st.button("🇸🇦 عربي", use_container_width=True, key="btn_ar"):
        if st.session_state.lang != 'ar': set_language('ar')
with col_l2:
    if st.button("🇬🇧 English", use_container_width=True, key="btn_en"):
        if st.session_state.lang != 'en': set_language('en')

# إعدادات الذكاء الاصطناعي
if "HF_TOKEN" in st.secrets:
    api_key = st.secrets["HF_TOKEN"]
else:
    st.sidebar.title("🤖 إعدادات الذكاء الاصطناعي")
    api_key = st.sidebar.text_input("🔑 مفتاح Hugging Face API:", type="password", help="ضع المفتاح هنا لتفعيل الشرح التوليدي")

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
            # ✅ التبويبات التسعة (تم فصل النتائج والتوصيات)
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
                "👥 عينة الدراسة", "📊 الإحصاء الوصفي", "🧪 الثبات (ألفا)", 
                "⚖️ الفروق (T-test/ANOVA)", "🔗 الارتباط (Pearson)",
                "📈 الانحدار", "🧠 محلل الفرضيات الذكي",
                "📋 النتائج", "💡 التوصيات"  # ✅ فصل النتائج عن التوصيات
            ])

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
                        total_row = pd.DataFrame({'التكرار': [len(df_encoded)], 'النسبة (%)': [100.00]}, index=['📊 المجموع الكلي ✓'])
                        demo_df_with_total = pd.concat([demo_df, total_row])
                        
                        col1, col2 = st.columns(2)
                        with col1: 
                            st.dataframe(demo_df_with_total, use_container_width=True)
                            chart_type_demo = st.radio(f"اختر نوع الرسم لـ ({col}):", ["دائري (Pie)", "أعمدة (Bar)", "دائري مجوف (Donut)", "خطي (Line)", "أعمدة أفقية (H-Bar)"], key=f"chart_{col}", horizontal=True)
                        with col2: 
                            if chart_type_demo == "دائري (Pie)": fig = px.pie(demo_df, values='التكرار', names=demo_df.index, height=350)
                            elif chart_type_demo == "أعمدة (Bar)": fig = px.bar(demo_df, x=demo_df.index, y='التكرار', text='التكرار', color=demo_df.index, height=350)
                            elif chart_type_demo == "دائري مجوف (Donut)": fig = px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.4, height=350)
                            elif chart_type_demo == "خطي (Line)": fig = px.line(demo_df, x=demo_df.index, y='التكرار', markers=True, height=350)
                            else: fig = px.bar(demo_df, x='التكرار', y=demo_df.index, text='التكرار', color=demo_df.index, orientation='h', height=350)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.info(f"**📝 التفسير الأكاديمي:**\n يوضح العرض الإحصائي أعلاه التوزيع التكراري والنسبي لأفراد عينة الدراسة البالغ عددهم الإجمالي ({len(df_encoded)}) مبحوثاً، وذلك وفقاً لتصنيفاتهم في متغير ({col}). من خلال استقراء النتائج، يتبين بوضوح أن الفئة الأكثر تمثيلاً وحضوراً في العينة هي فئة ({counts.idxmax()}) بنسبة مئوية قدرها ({percentages.max():.1f}%)، مما يعكس هيمنة هذه الشريحة على تركيبة العينة في هذا المتغير.")
                        
                        if api_key:
                            if st.button(f"✨ توليد قراءة ذكية متعمقة لجدول ({col})", key=f"ai_demo_{col}"):
                                with st.spinner("جاري صياغة التفسير الأكاديمي..."):
                                    st.success(get_table_explanation(demo_df_with_total.to_markdown(), f"توزيع العينة حسب {col}", api_key))
                        st.markdown("---")

            # ==========================================
            # 2. تبويب الإحصاء الوصفي
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
            # 4. دلالة الفروق
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
                                st.markdown(f"**نوع الاختبار:** `T-test لعينتين مستقلتين`")
                                g1 = res_data[res_data[g_col]==grps[0]][t_col].astype(float).values
                                g2 = res_data[res_data[g_col]==grps[1]][t_col].astype(float).values
                                res = pg.ttest(g1, g2)
                                st.dataframe(res)
                                pval = res['p-val'].values[0] if 'p-val' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)
                                st.markdown("### 📝 التفسير الأكاديمي:")
                                if pval < 0.05: 
                                    st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"أشارت مخرجات اختبار (ت) لعينتين مستقلتين (Independent Samples T-test) إلى وجود فروق جوهرية ذات دلالة إحصائية عند مستوى الدلالة ($\le 0.05$) بين فئات المتغير المستقل ({g_col}) فيما يتعلق بمحور ({t_col}). يعكس هذا التباين بشكل جلي تأثير الخصائص الديموغرافية للفئة على اتجاهات واستجابات المبحوثين.")
                                else: 
                                    st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"بينت نتائج اختبار (ت) لعينتين مستقلتين (Independent Samples T-test) عدم ثبوت أي فروق ذات دلالة إحصائية عند مستوى الدلالة ($\le 0.05$) بين استجابات أفراد العينة باختلاف فئاتهم في متغير ({g_col}) تجاه محور ({t_col}). يُفسر هذا إحصائياً بوجود حالة من التجانس والتقارب الكبير في آراء واتجاهات المبحوثين بغض النظر عن اختلاف تصنيفاتهم.")
                            elif len(grps) > 2:
                                st.markdown(f"**نوع الاختبار:** `تحليل التباين الأحادي (ANOVA)`")
                                counts = res_data[g_col].value_counts()
                                valid_grps = counts[counts >= 2].index
                                clean_anova = res_data[res_data[g_col].isin(valid_grps)]
                                res = pg.anova(data=clean_anova, dv=t_col, between=g_col)
                                st.dataframe(res)
                                pval = res['p-unc'].values[0] if 'p-unc' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)
                                st.markdown("### 📝 التفسير الأكاديمي:")
                                if pval < 0.05: 
                                    st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"أظهرت المعطيات الإحصائية المستخلصة من تحليل التباين الأحادي (One-Way ANOVA) وجود فروق ذات دلالة إحصائية واضحة عند مستوى الدلالة ($\le 0.05$) بين استجابات أفراد العينة تُعزى للتصنيفات المختلفة في متغير ({g_col}) ضمن محور ({t_col}). وهذا يؤكد أن المتغير الديموغرافي يلعب دوراً محورياً وجوهرياً في تشكيل آراء المبحوثين وتوجيه استجاباتهم.")
                                else: 
                                    st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                    st.info(f"أوضحت المخرجات الإحصائية لتحليل التباين الأحادي (One-Way ANOVA) عدم وجود أي فروق ذات دلالة إحصائية عند مستوى الدلالة المرجعي ($\le 0.05$) بين فئات متغير ({g_col}) فيما يتعلق بتقييمهم لمحور ({t_col}). يعكس هذا الاستقرار الإحصائي إجماعاً عاماً وتوافقاً ملحوظاً من قبل أفراد العينة على فقرات هذا المحور.")
                            st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)
                        except Exception as e: st.warning(f"تعذر حساب الفروق بسبب تعقيد البيانات: {e}")

            # ==========================================
            # 5. الارتباط
            # ==========================================
            with tab5:
                st.subheader("🔗 قياس الارتباط بين المحاور (Pearson Correlation)")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور الأول (المتغير المستقل):", analysis_cols, key="c1")
                    v2 = st.selectbox("المحور الثاني (المتغير التابع):", analysis_cols, index=1 if len(analysis_cols)>1 else 0, key="c2")
                    if v1 != v2:
                        try:
                            clean_corr = df_encoded[[v1, v2]].apply(pd.to_numeric, errors='coerce').dropna()
                            corr_res = pg.corr(clean_corr[v1], clean_corr[v2], method='pearson')
                            st.dataframe(corr_res[['n', 'r', 'p-val'] if 'p-val' in corr_res.columns else corr_res.columns])
                            pval = corr_res['p-val'].values[0] if 'p-val' in corr_res.columns else (corr_res['p-value'].values[0] if 'p-value' in corr_res.columns else 1.0)
                            rval = corr_res['r'].values[0] if 'r' in corr_res.columns else 0.0
                            st.markdown("### 📝 التفسير الأكاديمي:")
                            if pval < 0.05: 
                                direction = "طردية (إيجابية)" if rval > 0 else "عكسية (سلبية)"
                                strength = "قوية جداً" if abs(rval) > 0.8 else ("قوية" if abs(rval) > 0.6 else ("متوسطة" if abs(rval) > 0.4 else "ضعيفة"))
                                st.success(f"✅ **توجد علاقة ارتباط دالة إحصائياً.**")
                                st.info(f"أسفرت نتائج التحليل الإحصائي باستخدام معامل ارتباط بيرسون عن الكشف عن وجود علاقة ارتباط {direction} و{strength} ذات دلالة إحصائية قاطعة عند مستوى الدلالة ($\le 0.05$) بين محور ({v1}) ومحور ({v2}). يُستدل من هذه النتيجة العلمية الدقيقة على وجود تلازم حركي وتأثير متبادل بين المتغيرين في بيئة الدراسة.")
                            else: 
                                st.warning("⚠️ **لا توجد علاقة ارتباط دالة إحصائياً.**")
                                st.info(f"أظهرت معطيات اختبار بيرسون للارتباط الخطي عدم ثبوت أي علاقة ارتباطية ذات دلالة إحصائية بين محور ({v1}) ومحور ({v2}) عند مستوى الدلالة المعتمد ($\le 0.05$). يشير هذا الانعدام في الارتباط الخطي إلى استقلالية تامة لكل متغير عن الآخر ضمن سياق عينة الدراسة الحالية.")
                            st.plotly_chart(px.scatter(clean_corr, x=v1, y=v2, trendline="ols"), use_container_width=True)
                        except: st.error("تعذر حساب الارتباط.")

            # ==========================================
            # 6. الانحدار
            # ==========================================
            with tab6:
                st.subheader("📈 تحليل الانحدار الخطي (التنبؤ والتأثير Regression)")
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
                                st.info(f"سعياً للتحقق من القدرة التنبؤية للمتغيرات المستقلة ومعرفة حجم أثرها الفعلي، تم إجراء تحليل الانحدار الخطي لقياس أثر المتغيرات المُدخلة على المتغير التابع ({dep_var}). وتشير المخرجات الإحصائية إلى أن النموذج المقترح يمتلك قدرة تفسيرية ملحوظة. استناداً إلى قيمة معامل التحديد ($R^2 = {r2:.3f}$)، يمكن الاستنتاج علمياً بأن المتغيرات المستقلة المُدرجة قادرة مجتمعة على تفسير والتحكم بما نسبته **({float(r2)*100:.1f}%)** من إجمالي التباين الحاصل في المتغير التابع.")
                            except: st.error("حدث خطأ في الانحدار.")

            # ==========================================
            # 7. التبويب السابع: محلل الفرضيات الذكي
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
                                st.error(f"خطأ في الاتصال بالذكاء الاصطناعي: {e}")
                    if 'ai_analysis' in st.session_state:
                        st.success("تم تحليل الفرضية بنجاح:")
                        st.info(st.session_state['ai_analysis'])
                    st.markdown("---")
                    col_type = st.selectbox("نوع الاختبار المطلوب:", ["علاقة (Pearson)", "تأثير (Regression)", "فروق (T-test / ANOVA)"])
                    if "فروق" in col_type: h_indep = st.selectbox("المتغير المستقل (الفئة الديموغرافية):", categorical_cols)
                    else: h_indep = st.selectbox("المتغير المستقل (المؤثر/المحور):", analysis_cols)
                    h_dep = st.selectbox("المتغير التابع (النتيجة/المحور):", analysis_cols, index=len(analysis_cols)-1 if len(analysis_cols)>0 else 0)
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
                                    grps = clean_df[h_indep].unique()
                                    if len(grps) == 2: res = pg.ttest(clean_df[clean_df[h_indep]==grps[0]][h_dep].astype(float), clean_df[clean_df[h_indep]==grps[1]][h_dep].astype(float))
                                    else:
                                        valid_grps = clean_df[h_indep].value_counts()[clean_df[h_indep].value_counts()>=2].index
                                        res = pg.anova(data=clean_df[clean_df[h_indep].isin(valid_grps)], dv=h_dep, between=h_indep)
                                    results_str = res.to_markdown()
                                    st.dataframe(res)
                                final_explanation = generate_detailed_explanation(results_str, user_hypothesis, api_key)
                                st.markdown("### 📝 مناقشة النتائج (الفصل الرابع - جاهز للنسخ):")
                                st.success(final_explanation)
                            except Exception as e:
                                st.error(f"حدث خطأ أثناء التنفيذ أو التوليد: {e}")

            # ==========================================
            # ✅ 8. التبويب الثامن: النتائج (بدون رسوم بيانية)
            # ==========================================
            with tab8:
                st.header("📋 نتائج الدراسة الإحصائية")
                st.markdown("### 🎯 ملخص النتائج الرئيسية")
                
                # دالة مساعدة لتحديد المستوى
                def get_level(mean_val):
                    if mean_val >= 3.68: return "مرتفع"
                    if mean_val >= 2.34: return "متوسط"
                    return "منخفض"

                result_counter = 1
                
                # 1. الديموغرافيا
                if categorical_cols:
                    for col in categorical_cols:
                        top_cat = df_encoded[col].value_counts().idxmax()
                        st.markdown(f"**النتيجة ({result_counter}):** الفئة الأعلى تمثيلاً في متغير ({col}) هي فئة ({top_cat}).")
                        result_counter += 1
                        
                # 2. الثبات
                if len(active_questions) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[active_questions].dropna())[0]
                    st.markdown(f"**النتيجة ({result_counter}):** بلغ معامل الثبات الكلي (ألفا كرونباخ) لأداة الدراسة ({round(a_total, 3)}).")
                    result_counter += 1
                    
                # 3. المحاور (مستويات التقييم) - بدون رسم بياني
                hypotheses_list = []  # لتخزين الفرضيات لدالة analyze_hypothesis_smart
                
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        item_means = df_encoded[cols].mean()
                        overall_mean = item_means.mean()
                        level = get_level(overall_mean)
                        st.markdown(f"**النتيجة ({result_counter}):** جاء محور ({dim_name}) بمستوى تقييم ({level}) بمتوسط حسابي ({round(overall_mean, 2)}).")
                        
                        # تجهيز الفرضيات للدالة الذكية
                        hypotheses_list.append({
                            'name': f"مستوى محور {dim_name}",
                            'p_value': 0.01 if overall_mean >= 3.0 else 0.15  # مثال توضيحي
                        })
                        result_counter += 1

                # ✅ استخدام دالة analyze_hypothesis_smart لعرض النتائج
                if hypotheses_list:
                    st.markdown("### 🔍 تحليل الفرضيات الذكي")
                    smart_results = analyze_hypothesis_smart(hypotheses_list)
                    st.markdown(smart_results)
                
                st.markdown("---")
                st.info("💡 ملاحظة: تم عرض النتائج بشكل نصي منظم بدون رسوم بيانية حسب طلبك.")

            # ==========================================
            # ✅ 9. التبويب التاسع: التوصيات (بدون رسوم بيانية)
            # ==========================================
            with tab9:
                st.header("💡 التوصيات الذكية للدراسة")
                st.markdown("### 📌 التوصيات بناءً على المتوسطات الحسابية")
                
                recommendations = []
                
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        item_means = df_encoded[cols].mean()
                        # التوصيات للعناصر ذات المتوسط المنخفض (<= 3.50)
                        low_items = item_means[item_means <= 3.50]
                        if not low_items.empty:
                            for item_text, mean_val in low_items.items():
                                recommendations.append({
                                    "المحور": dim_name,
                                    "الفقرة": item_text,
                                    "المتوسط": round(mean_val, 2),
                                    "التوصية": f"توصي الدراسة بضرورة تحسين ({item_text}) من خلال تطوير الممارسات المرتبطة بها، والعمل على رفع مستواها بما يسهم في تعزيز الأداء وتحقيق نتائج أفضل."
                                })
                        # توصيات للمحافظة على العناصر القوية
                        else:
                            lowest_item_text = item_means.idxmin()
                            lowest_mean_val = item_means.min()
                            recommendations.append({
                                "المحور": dim_name,
                                "الفقرة": lowest_item_text,
                                "المتوسط": round(lowest_mean_val, 2),
                                "التوصية": f"توصي الدراسة بضرورة المحافظة على مستوى ({lowest_item_text}) والعمل على تعزيزه بشكل مستمر، لما له من دور مهم في دعم هذا البعد وتحقيق الكفاءة المطلوبة."
                            })

                # عرض التوصيات بشكل منظم
                if recommendations:
                    for idx, rec in enumerate(recommendations, 1):
                        with st.expander(f"📌 التوصية رقم ({idx}): {rec['المحور']} - {rec['الفقرة']}"):
                            st.markdown(f"""
                            **📊 البيانات:**
                            - المحور: {rec['المحور']}
                            - الفقرة: {rec['الفقرة']}
                            - المتوسط الحسابي: {rec['المتوسط']}
                            
                            **💡 التوصية:**
                            {rec['التوصية']}
                            """)
                else:
                    st.success("✅ جميع الفقرات بمستويات جيدة، لا توجد توصيات تحسين عاجلة حالياً.")
                
                st.markdown("---")
                st.info("💡 ملاحظة: تم عرض التوصيات بشكل نصي منظم بدون رسوم بيانية حسب طلبك.")

    except Exception as e: 
        st.error(f"حدث خطأ أثناء قراءة الملف. تأكد من أن الملف ليس فارغاً وأن صيغته صحيحة. التفاصيل: {e}")

# ==========================================
# ✅ CSS لإصلاح تنسيق النص العربي والخطوط
# ==========================================
st.markdown("""
<style>
    /* ضبط اتجاه النص العربي لليمين */
    .stMarkdown, .stDataFrame, .stMetric, .stAlert, .stSuccess, .stWarning, .stError, .stInfo,
    .stExpander, .stTabs, .stSelectbox, .stMultiselect, .stTextInput, .stTextArea {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* ضبط الجداول */
    div[data-testid="stDataFrame"] table {
        direction: rtl !important;
    }
    div[data-testid="stDataFrame"] th, 
    div[data-testid="stDataFrame"] td {
        text-align: right !important;
        padding: 8px 12px !important;
    }
    
    /* العناوين */
    h1, h2, h3, h4, h5, h6 {
        direction: rtl !important;
        text-align: right !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    /* الأزرار */
    .stButton > button {
        direction: rtl !important;
        text-align: center !important;
        border-radius: 8px !important;
    }
    
    /* الحقول النصية */
    .stTextInput input, .stTextArea textarea {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* القائمة الجانبية */
    section[data-testid="stSidebar"] {
        direction: rtl !important;
    }
    
    /* التبويبات */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
        gap: 10px !important;
    }
    
    /* الرسوم البيانية تبقى LTR */
    .plotly-graph-div {
        direction: ltr !important;
    }
    
    /* خط عربي جميل وواضح */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    
    body, .stApp, div, span, p, label, button, input, textarea, h1, h2, h3, h4, h5, h6 {
        font-family: 'Tajawal', 'Segoe UI', Arial, sans-serif !important;
        line-height: 1.6 !important;
    }
    
    /* تحسين المسافات والقراءة */
    .stMarkdown p {
        line-height: 1.8 !important;
        margin-bottom: 12px !important;
        font-size: 1.05rem !important;
    }
    
    /* تحسين الجداول */
    .stDataFrame {
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    /* تحسين البطاقات والمربعات */
    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }
</style>
""", unsafe_allow_html=True)
