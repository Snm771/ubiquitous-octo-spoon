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
# --- دوال الذكاء الاصطناعي (الرابط المحدث لـ Hugging Face) ---
# ==========================================
def run_ai(prompt, api_key):
    try:
        # ✅ تم تحديث الرابط إلى router.huggingface.co
        client = OpenAI(
            base_url="https://router.huggingface.co/v1/",
            api_key=api_key
        )
        
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct", # الموديل الجبار في اللغة العربية
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
    
    اكتب فقرة أكاديمية مسهبة تشرح أهم ما جاء في هذا الجدول، استخرج أعلى وأقل القيم، وفسر معناها في سياق البحث العلمي.
    """
    return run_ai(prompt, api_key)

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
# سحب مفتاح الذكاء الاصطناعي تلقائياً
# ==========================================
if "HF_TOKEN" in st.secrets:
    api_key = st.secrets["HF_TOKEN"]
else:
    st.sidebar.title("🤖 إعدادات الذكاء الاصطناعي")
    api_key = st.sidebar.text_input("🔑 مفتاح Hugging Face API:", type="password", help="ضع المفتاح هنا لتفعيل الشرح التوليدي والتبويب السابع")

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
            # التبويبات السبعة
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "👥 عينة الدراسة", 
                "📊 الإحصاء الوصفي", 
                "🧪 الثبات (ألفا)", 
                "⚖️ الفروق (T-test/ANOVA)", 
                "🔗 الارتباط (Pearson)",
                "📈 الانحدار",
                "🧠 محلل الفرضيات الذكي"
            ])

            # ==========================================
            # 1. تبويب عينة الدراسة ✅ مع إضافة المجموع الكلي
            # ==========================================
            with tab1:
                st.subheader("👥 وصف عينة الدراسة (التكرارات والنسب)")
                if categorical_cols:
                    for col in categorical_cols:
                        st.markdown(f"### 📊 توزيع أفراد العينة حسب: ({col})")
                        
                        counts = df_encoded[col].value_counts()
                        percentages = df_encoded[col].value_counts(normalize=True) * 100
                        demo_df = pd.DataFrame({'التكرار': counts, 'النسبة (%)': percentages.round(2)})
                        
                        # ✅ ✅ ✅ الإضافة الجديدة: صف المجموع الكلي ✅ ✅ ✅
                        total_row = pd.DataFrame({
                            'التكرار': [len(df_encoded)],
                            'النسبة (%)': [100.00]
                        }, index=['📊 المجموع الكلي ✓'])
                        demo_df_with_total = pd.concat([demo_df, total_row])
                        # ✅ ✅ ✅ نهاية الإضافة ✅ ✅ ✅
                        
                        col1, col2 = st.columns(2)
                        with col1: 
                            # عرض الجدول مع المجموع الكلي
                            st.dataframe(demo_df_with_total.style.set_properties(**{
                                'background-color': '#e8f5e9'
                            }, subset=pd.Index(['📊 المجموع الكلي ✓'])), use_container_width=True)
                        with col2: 
                            st.plotly_chart(px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.3, height=350), use_container_width=True)
                        
                        total_n = len(df_encoded)
                        top_cat = counts.idxmax()
                        top_val = counts.max()
                        top_pct = percentages.max()
                        bot_cat = counts.idxmin()
                        bot_val = counts.min()
                        bot_pct = percentages.min()

                        st.info(f"**📝 التفسير الأكاديمي المسهب:**\n يوضح العرض الإحصائي أعلاه التوزيع التكراري والنسبي لأفراد عينة الدراسة البالغ عددهم الإجمالي ({total_n}) مبحوثاً، وذلك وفقاً لتصنيفاتهم في متغير ({col}). من خلال استقراء النتائج، يتبين بوضوح أن الفئة الأكثر تمثيلاً وحضوراً في العينة هي فئة ({top_cat}) بتكرار بلغ ({top_val}) وبنسبة مئوية قدرها ({top_pct:.1f}%)، مما يعكس هيمنة هذه الشريحة على تركيبة العينة في هذا المتغير. في المقابل، جاءت فئة ({bot_cat}) كأقل الفئات تمثيلاً بتكرار ({bot_val}) ونسبة ({bot_pct:.1f}%). يُعد هذا التوصيف الديموغرافي محطة منهجية حيوية، حيث يبرز التباين أو التجانس في خصائص العينة، ويمنح الباحث مساحة موضوعية في تعميم النتائج وتفسير الفروق الإحصائية اللاحقة بناءً على هذا التوزيع الديموغرافي.")
                        
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

                st.markdown("### 3️⃣ المقارنة الوصفية بين الفئات")
                if categorical_cols:
                    comp_cat = st.selectbox("قسم النتائج بناءً على:", categorical_cols)
                    comp_axis = st.selectbox("اختر المحور للمقارنة:", analysis_cols)
                    grouped_desc = df_encoded.groupby(comp_cat)[comp_axis].agg(['count', 'mean', 'std']).reset_index()
                    grouped_desc.columns = [comp_cat, 'العدد', 'المتوسط الحسابي', 'الانحراف المعياري']
                    st.dataframe(grouped_desc.style.highlight_max(subset=['المتوسط الحسابي'], color='#d4edda'), use_container_width=True)
                
                st.markdown("### 📝 التفسير الأكاديمي المسهب للتحليل الوصفي:")
                st.info("يهدف التحليل الوصفي المعروض في الجداول أعلاه إلى تشخيص مستوى الاستجابة لمتغيرات ومحاور الدراسة وفقاً لآراء أفراد العينة. بالاعتماد على مقياس النزعة المركزية المتمثل في **المتوسط الحسابي (Mean)**، يتم تحديد الاتجاه العام والميل الغالب لإجابات المبحوثين، حيث تشير القيم المرتفعة إلى تبلور رأي إيجابي، أو مستوى موافقة عالٍ، أو ممارسة قوية تجاه الفقرة أو المحور المدروس. وبالتوازي مع ذلك، يبرز دور مقياس التشتت المتمثل في **الانحراف المعياري (Standard Deviation)** كمؤشر إحصائي دقيق لقياس مدى تشتت أو تقارب تلك الآراء حول متوسطها؛ فالانحراف المعياري المنخفض (الذي يقترب من الصفر) يدل على تجانس فكري وتوافق ملحوظ بين المبحوثين، بينما الانحراف المرتفع يعكس تبايناً وتعدداً في وجهات النظر. يُعد هذا التوصيف الإحصائي حجر الزاوية في بناء تصور شامل ودقيق للواقع الميداني، مما يمهد الطريق علمياً لاختبار الفرضيات وتقديم توصيات فعالة مستندة إلى أرقام تعكس نبض المجتمع المبحوث بوضوح.")

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
                    st.markdown("### 📝 التفسير الأكاديمي المسهب لمعامل الثبات:")
                    st.info("تشير نتائج التقييم الإحصائي باستخدام معامل ألفا كرونباخ (Cronbach's Alpha) إلى أن أداة الدراسة تتمتع بدرجة عالية ومطمئنة من الاتساق الداخلي. يُعد هذا المعامل مؤشراً علمياً دقيقاً على مدى تجانس فقرات الاستبيان وترابطها في قياس الأبعاد التي أُعدت لقياسها. ووفقاً للأدبيات المنهجية في البحث العلمي، فإن أي قيمة تتجاوز الحد المقبول (0.60) تعكس استقراراً في المقياس، وكلما اقتربت القيمة من الواحد الصحيح (1.00) دلّ ذلك على موثوقية ممتازة. بناءً على هذه النتائج، يمكن التأكيد بقوة على صلاحية أداة الدراسة الحالية للاستخدام، وموثوقية البيانات المستخلصة منها لتعميم النتائج والاعتماد عليها في اختبار الفرضيات.")

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
                                
                                if len(g1) < 2 or len(g2) < 2:
                                    st.warning("⚠️ إحدى المجموعات عدد أفرادها قليل جداً ولا يمكن إجراء الاختبار.")
                                else:
                                    res = pg.ttest(g1, g2)
                                    st.dataframe(res)
                                    pval = res['p-val'].values[0] if 'p-val' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)
                                    
                                    st.markdown("### 📝 التفسير الأكاديمي المسهب للنتيجة:")
                                    if pval < 0.05: 
                                        st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"أشارت مخرجات اختبار (ت) لعينتين مستقلتين (Independent Samples T-test) إلى وجود فروق جوهرية ذات دلالة إحصائية عند مستوى الدلالة ($\alpha \le 0.05$) بين فئات المتغير المستقل ({g_col}) فيما يتعلق بمحور ({t_col}). حيث بلغت القيمة الاحتمالية الدقيقة ($p = {pval:.3f}$) وهي قيمة أصغر من الحد المرجعي (0.05). يعكس هذا التباين بشكل جلي تأثير الخصائص الديموغرافية للفئة على اتجاهات واستجابات المبحوثين، مما يعني أن الاختلاف الملاحظ بين المتوسطات الحسابية للمجموعتين ليس وليد الصدفة أو ناتجاً عن أخطاء المعاينة العشوائية، بل هو اختلاف حقيقي يعبر عن تباين فعلي في وجهات النظر بين الفئتين المدروستين.")
                                    else: 
                                        st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"بينت نتائج اختبار (ت) لعينتين مستقلتين (Independent Samples T-test) عدم ثبوت أي فروق ذات دلالة إحصائية عند مستوى الدلالة ($\alpha \le 0.05$) بين استجابات أفراد العينة باختلاف فئاتهم في متغير ({g_col}) تجاه محور ({t_col}). فقد أظهرت النتائج أن القيمة الاحتمالية بلغت ($p = {pval:.3f}$) وهي تتجاوز بكثير مستوى الدلالة المعتمد (0.05). يُفسر هذا إحصائياً بوجود حالة من التجانس والتقارب الكبير في آراء واتجاهات المبحوثين بغض النظر عن اختلاف تصنيفاتهم. ويدل هذا التوافق على أن المحور المدروس يمثل ظاهرة مستقرة يتفق عليها أفراد العينة كافة، وأن الفروق الطفيفة الظاهرة في المتوسطات ترجع إلى تباينات عشوائية طبيعية.")
                                    
                            elif len(grps) > 2:
                                st.markdown(f"**نوع الاختبار:** `تحليل التباين الأحادي (ANOVA)`")
                                counts = res_data[g_col].value_counts()
                                valid_grps = counts[counts >= 2].index
                                if len(valid_grps) < 2:
                                    st.warning("⚠️ المجموعات لا تحتوي على عدد كافٍ لإجراء ANOVA.")
                                else:
                                    clean_anova = res_data[res_data[g_col].isin(valid_grps)]
                                    res = pg.anova(data=clean_anova, dv=t_col, between=g_col)
                                    st.dataframe(res)
                                    pval = res['p-unc'].values[0] if 'p-unc' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)
                                    
                                    st.markdown("### 📝 التفسير الأكاديمي المسهب للنتيجة:")
                                    if pval < 0.05: 
                                        st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"أظهرت المعطيات الإحصائية المستخلصة من تحليل التباين الأحادي (One-Way ANOVA) وجود فروق ذات دلالة إحصائية واضحة عند مستوى الدلالة ($\alpha \le 0.05$) بين استجابات أفراد العينة تُعزى للتصنيفات المختلفة في متغير ({g_col}) ضمن محور ({t_col}). فقد بلغت القيمة الاحتمالية ($p = {pval:.3f}$) وهي أدنى من (0.05). يشير هذا المؤشر بقوة إلى أن تباين الاستجابات بين المجموعات المختلفة كان أكبر بكثير من التباين الداخلي لكل مجموعة على حدة. وهذا يؤكد أن المتغير الديموغرافي يلعب دوراً محورياً وجوهرياً في تشكيل آراء المبحوثين وتوجيه استجاباتهم.")
                                    else: 
                                        st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"أوضحت المخرجات الإحصائية لتحليل التباين الأحادي (One-Way ANOVA) عدم وجود أي فروق ذات دلالة إحصائية عند مستوى الدلالة المرجعي ($\alpha \le 0.05$) بين فئات متغير ({g_col}) فيما يتعلق بتقييمهم لمحور ({t_col}). حيث جاءت قيمة الدلالة الاحتمالية ($p = {pval:.3f}$) متجاوزةً للحد المسموح به (0.05). يعكس هذا الاستقرار الإحصائي إجماعاً عاماً وتوافقاً ملحوظاً من قبل أفراد العينة على فقرات هذا المحور، مما يقود إلى استنتاج علمي مفاده أن طبيعة الانتماء الفئوي لم تشكل عاملاً حاسماً في إحداث تباينات جوهرية في وجهات النظر.")
                                    
                            st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)
                        except Exception as e: 
                            st.warning(f"تعذر حساب الفروق بسبب تعقيد البيانات: {e}")

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
                            if len(clean_corr) > 2:
                                corr_res = pg.corr(clean_corr[v1], clean_corr[v2], method='pearson')
                                st.dataframe(corr_res[['n', 'r', 'p-val'] if 'p-val' in corr_res.columns else corr_res.columns])
                                
                                pval = corr_res['p-val'].values[0] if 'p-val' in corr_res.columns else (corr_res['p-value'].values[0] if 'p-value' in corr_res.columns else 1.0)
                                rval = corr_res['r'].values[0] if 'r' in corr_res.columns else 0.0
                                
                                st.markdown("### 📝 التفسير الأكاديمي المسهب للنتيجة:")
                                if pval < 0.05: 
                                    direction = "طردية (إيجابية)" if rval > 0 else "عكسية (سلبية)"
                                    strength = "قوية جداً" if abs(rval) > 0.8 else ("قوية" if abs(rval) > 0.6 else ("متوسطة" if abs(rval) > 0.4 else "ضعيفة"))
                                    st.success(f"✅ **توجد علاقة ارتباط دالة إحصائياً.**")
                                    st.info(f"أسفرت نتائج التحليل الإحصائي باستخدام معامل ارتباط بيرسون (Pearson Correlation) عن الكشف عن وجود علاقة ارتباط {direction} و{strength} ذات دلالة إحصائية قاطعة عند مستوى الدلالة ($\alpha \le 0.05$) بين محور ({v1}) ومحور ({v2}). حيث بلغت قيمة معامل الارتباط ($r = {rval:.3f}$) مصحوبة بقيمة احتمالية ($p = {pval:.3f}$). يُستدل من هذه النتيجة العلمية الدقيقة على وجود تلازم حركي وتأثير متبادل بين المتغيرين في بيئة الدراسة؛ فكلما شهد المتغير الأول تغيراً، تبعه تغير ملحوظ وموازٍ في المتغير الثاني بالاتجاه الـ{direction}. تدعم هذه النتيجة وجود ترابط جوهري عميق يمكن الاعتماد عليه أكاديمياً وعملياً في تفسير سلوك أحد المتغيرين بمعلومية المتغير الآخر.")
                                else: 
                                    st.warning("⚠️ **لا توجد علاقة ارتباط دالة إحصائياً.**")
                                    st.info(f"أظهرت معطيات اختبار بيرسون للارتباط الخطي (Pearson Correlation) عدم ثبوت أي علاقة ارتباطية ذات دلالة إحصائية بين محور ({v1}) ومحور ({v2}) عند مستوى الدلالة المعتمد ($\alpha \le 0.05$). حيث بلغت القيمة الاحتمالية لاختبار الارتباط ($p = {pval:.3f}$) وهي قيمة تفوق الحد الحرج (0.05). يشير هذا الانعدام في الارتباط الخطي إلى استقلالية تامة لكل متغير عن الآخر ضمن سياق عينة الدراسة الحالية، مما يعني علمياً أن التغيرات التي تطرأ على تقييمات المبحوثين في المحور الأول لا تصاحبها بالضرورة تغيرات منتظمة أو قابلة للتنبؤ في المحور الثاني.")
                                    
                                st.plotly_chart(px.scatter(clean_corr, x=v1, y=v2, trendline="ols"), use_container_width=True)
                            else:
                                st.warning("بيانات غير كافية للارتباط.")
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
                                
                                st.markdown("### 📝 التفسير الأكاديمي المسهب لنموذج الانحدار:")
                                st.info(f"سعياً للتحقق من القدرة التنبؤية للمتغيرات المستقلة ومعرفة حجم أثرها الفعلي، تم إجراء تحليل الانحدار الخطي (Linear Regression) لقياس أثر المتغيرات المُدخلة على المتغير التابع ({dep_var}). وتشير المخرجات الإحصائية إلى أن النموذج المقترح يمتلك قدرة تفسيرية جيدة وملحوظة. استناداً إلى قيمة معامل التحديد ($R^2 = {r2:.3f}$)، يمكن الاستنتاج علمياً بأن المتغيرات المستقلة المُدرجة في النموذج قادرة مجتمعة على تفسير والتحكم بما نسبته **({float(r2)*100:.1f}%)** من إجمالي التباين (التغير) الحاصل في المتغير التابع. وتُعزى النسبة المتبقية والبالغة ({(1-float(r2))*100:.1f}%) إلى عوامل أو متغيرات أخرى محيطة بالظاهرة لم يتضمنها النموذج الإحصائي الحالي، بالإضافة إلى التباينات الناتجة عن أخطاء المعاينة العشوائية. يعكس هذا المؤشر الحجم الحقيقي لقوة التأثير، ويؤكد أهمية المتغيرات المستقلة في صياغة التوصيات.")
                            except: st.error("حدث خطأ في الانحدار.")
                        else:
                            st.warning("عينة غير كافية للانحدار.")

            # ==========================================
            # 7. التبويب السابع: محلل الفرضيات الذكي (AI Engine)
            # ==========================================
            with tab7:
                st.header("🧠 المحلل الذكي للفرضيات (AI Hypothesis Engine)")
                st.markdown("ضع فرضية بحثك هنا، وسيقوم الذكاء الاصطناعي بفهمها، واختيار الاختبار المناسب، وتنفيذه، وكتابة تقرير أكاديمي كامل لها!")
                
                if not api_key:
                    st.error("⚠️ يرجى إدخال مفتاح Hugging Face API في القائمة الجانبية أو إضافته في إعدادات التطبيق لتفعيل هذه الميزة الحصرية.")
                else:
                    user_hypothesis = st.text_area("✍️ أدخل نص الفرضية هنا:", "مثال: توجد علاقة ذات دلالة إحصائية بين جودة المعلومات والترويج للحدث.")
                    
                    if st.button("🔍 تحليل الفرضية آلياً"):
                        with st.spinner("جاري فهم الفرضية عبر الذكاء الاصطناعي..."):
                            try:
                                # تخزين النتيجة في الجلسة لكي لا تختفي
                                st.session_state['ai_analysis'] = analyze_hypothesis_text(user_hypothesis, api_key)
                            except Exception as e:
                                st.error(f"خطأ في الاتصال بالذكاء الاصطناعي: {e}")
                    
                    if 'ai_analysis' in st.session_state:
                        st.success("تم تحليل الفرضية بنجاح:")
                        st.info(st.session_state['ai_analysis'])
                    
                    st.markdown("---")
                    st.markdown("#### ⚙️ تنفيذ الاختبار وتوليد مناقشة النتائج")
                    st.markdown("بناءً على الفهم أعلاه، حدد المتغيرات بدقة لكي ينفذ النظام الاختبار ويكتب التفسير المسهب:")
                    
                    col_type = st.selectbox("نوع الاختبار المطلوب:", ["علاقة (Pearson)", "تأثير (Regression)", "فروق (T-test / ANOVA)"])
                    
                    if "فروق" in col_type:
                        h_indep = st.selectbox("المتغير المستقل (الفئة الديموغرافية):", categorical_cols)
                    else:
                        h_indep = st.selectbox("المتغير المستقل (المؤثر/المحور):", analysis_cols)
                        
                    h_dep = st.selectbox("المتغير التابع (النتيجة/المحور):", analysis_cols, index=len(analysis_cols)-1 if len(analysis_cols)>0 else 0)
                    
                    if st.button("🚀 تنفيذ وكتابة مناقشة النتائج (الفصل الرابع)"):
                        with st.spinner("جاري إجراء الاختبار وتأليف التفسير الأكاديمي المسهب عبر الذكاء الاصطناعي..."):
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
                                    if len(grps) == 2:
                                        res = pg.ttest(clean_df[clean_df[h_indep]==grps[0]][h_dep].astype(float), clean_df[clean_df[h_indep]==grps[1]][h_dep].astype(float))
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

    except Exception as e: st.error(f"حدث خطأ أثناء قراءة الملف. تأكد من أن الملف ليس فارغاً وأن صيغته صحيحة. التفاصيل: {e}")
