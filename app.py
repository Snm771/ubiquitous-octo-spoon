import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

st.set_page_config(page_title="SmartStat Pro | الخبير الإحصائي", page_icon="📊", layout="wide")

# --- 1. دالة التشفير الذكي (تحويل الكلمات لأرقام كما فعل الخبير) ---
def encode_likert(df):
    likert_map = {
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1, "لا أوافق": 2, "لا أوافق بشدة": 1,
        "راض جدا": 5, "راض جداً": 5, "راض": 4, "غير راض": 2, "غير راض جدا": 1, "غير راض جداً": 1,
        "دائما": 5, "دائماً": 5, "غالبا": 4, "غالباً": 4, "أحيانا": 3, "أحياناً": 3, "نادرا": 2, "نادراً": 2, "أبدا": 1, "أبداً": 1, "مطلقا": 1, "مطلقاً": 1,
        "بدرجة كبيرة جدا": 5, "بدرجة كبيرة جداً": 5, "بدرجة كبيرة": 4, "بدرجة متوسطة": 3, "بدرجة قليلة": 2, "بدرجة ضعيفة": 2, "بدرجة قليلة جدا": 1, "بدرجة ضعيفة جدا": 1,
        "نعم": 2, "لا": 1
    }
    df_cleaned = df.copy()
    df_cleaned = df_cleaned.map(lambda x: x.strip() if isinstance(x, str) else x)
    df_cleaned = df_cleaned.replace(likert_map)
    for col in df_cleaned.columns:
        if col != 'Timestamp':
            try: df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except ValueError: pass 
    return df_cleaned

# --- 2. التصنيف الدلالي ---
def smart_classify_columns(df):
    categorical_cols, numeric_cols = [], []
    demo_keywords = ['عمر', 'سن', 'جنس', 'نوع', 'مؤهل', 'مرحلة', 'صف', 'خبرة', 'حالة', 'دخل', 'تخصص', 'عمل']
    for col in df.columns:
        if col.lower() == 'timestamp': continue
        is_demo = any(keyword in col for keyword in demo_keywords)
        if is_demo: categorical_cols.append(col)
        else:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > (len(df) * 0.5): numeric_cols.append(col)
            elif df[col].nunique() <= 15: categorical_cols.append(col)
    return categorical_cols, numeric_cols

# ==========================================
# واجهة المستخدم والتطبيق
# ==========================================
st.title("📊 SmartStat Pro - نظام الخبير الإحصائي الآلي")
st.markdown("يقوم هذا النظام بمحاكاة التحليل الأكاديمي المتقدم. ارفع الملف الخام، حدد محاور دراستك، ودع النظام يستخرج النتائج.")
st.markdown("---")

uploaded_file = st.file_uploader("قم برفع ملف البيانات الخام (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)
        
        st.sidebar.title("⚙️ بناء محاور الدراسة (Dimensions)")
        st.sidebar.info("السر في التحليل الأكاديمي هو تجميع الأسئلة في محاور للحصول على متوسطاتها.")
        
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات المستقلة (الديموغرافية):", df_encoded.columns, default=cat_cols_auto)
        all_questions = [c for c in num_cols_auto if c not in categorical_cols]
        
        # بناء المحور الأول
        axis1_name = st.sidebar.text_input("اسم المحور الأول:", "المحور الأول")
        axis1_cols = st.sidebar.multiselect(f"أسئلة {axis1_name}:", all_questions, default=all_questions[:len(all_questions)//2] if all_questions else [])
        
        # بناء المحور الثاني
        axis2_name = st.sidebar.text_input("اسم المحور الثاني:", "المحور الثاني")
        axis2_cols = st.sidebar.multiselect(f"أسئلة {axis2_name}:", all_questions, default=[c for c in all_questions if c not in axis1_cols])

        # --- حساب متوسطات المحاور ---
        analysis_cols = []
        if axis1_cols:
            df_encoded[axis1_name] = df_encoded[axis1_cols].mean(axis=1)
            analysis_cols.append(axis1_name)
        if axis2_cols:
            df_encoded[axis2_name] = df_encoded[axis2_cols].mean(axis=1)
            analysis_cols.append(axis2_name)
            
        # المجموع الكلي للاستبيان (تم التعديل ليأخذ كل الأسئلة بلا استثناء)
        if len(all_questions) > 0:
            df_encoded['متوسط الاستبيان الكلي'] = df_encoded[all_questions].mean(axis=1)
            analysis_cols.append('متوسط الاستبيان الكلي')

        if not analysis_cols:
            st.warning("يرجى تحديد أسئلة المحاور من القائمة الجانبية للبدء.")
        else:
            st.success("✅ تم قراءة البيانات وحساب متوسطات المحاور بنجاح! توجه للتبويبات لرؤية تحليل الخبير.")
            
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "👥 عينة الدراسة", 
                "📊 الإحصاء الوصفي", 
                "🧪 الثبات (ألفا)", 
                "⚖️ الفروق (T-test/ANOVA)", 
                "🔗 الارتباط (Pearson)",
                "📈 الانحدار (Regression)"
            ])

            # ==========================================
            # التبويب الأول: عينة الدراسة
            with tab1:
                st.subheader("👥 وصف عينة الدراسة (التكرارات والنسب)")
                if categorical_cols:
                    demo_col = st.selectbox("اختر المتغير (مثلاً النوع أو العمر):", categorical_cols, key="d1")
                    counts = df_encoded[demo_col].value_counts()
                    percentages = df_encoded[demo_col].value_counts(normalize=True) * 100
                    demo_df = pd.DataFrame({'التكرار': counts, 'النسبة المئوية (%)': percentages.round(2)})
                    col1, col2 = st.columns(2)
                    with col1: st.dataframe(demo_df, use_container_width=True)
                    with col2: st.plotly_chart(px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.3), use_container_width=True)

            # ==========================================
            # التبويب الثاني: الإحصاء الوصفي الشامل (المحاور + الفقرات)
            with tab2:
                st.subheader("📊 الإحصاء الوصفي (المتوسطات والانحرافات المعيارية)")
                
                # 1. إحصاء عام للمحاور
                st.markdown("### 1️⃣ الإحصاء العام للمحاور")
                desc_df = df_encoded[analysis_cols].describe().T
                desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط الحسابي', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط الحسابي', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)
                
                # 2. الإحصاء التفصيلي لكل فقرة
                st.markdown("### 2️⃣ الإحصاء التفصيلي لجميع فقرات (أسئلة) الاستبيان")
                st.markdown("يعرض هذا الجدول المتوسط والانحراف المعياري لكل سؤال لمعرفة الأسئلة الأعلى والأدنى استجابة.")
                # التعديل هنا ليعرض كل الأسئلة بلا استثناء
                if all_questions:
                    items_desc = df_encoded[all_questions].describe().T
                    items_desc = items_desc.rename(columns={'count': 'العدد', 'mean': 'المتوسط الحسابي', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                    st.dataframe(items_desc[['العدد', 'المتوسط الحسابي', 'الانحراف المعياري', 'الأدنى', 'الأقصى']].style.background_gradient(subset=['المتوسط الحسابي'], cmap='Blues'), use_container_width=True)

                # 3. إحصاء مقارن حسب الفئات
                st.markdown("### 3️⃣ الإحصاء المقارن (حسب الفئات)")
                if categorical_cols:
                    comp_cat = st.selectbox("قسم النتائج بناءً على:", categorical_cols)
                    comp_axis = st.selectbox("اختر المحور للمقارنة:", analysis_cols)
                    grouped_desc = df_encoded.groupby(comp_cat)[comp_axis].agg(['count', 'mean', 'std']).reset_index()
                    grouped_desc.columns = [comp_cat, 'العدد', 'المتوسط الحسابي', 'الانحراف المعياري']
                    st.dataframe(grouped_desc.style.highlight_max(subset=['المتوسط الحسابي'], color='#d4edda'), use_container_width=True)
                    st.plotly_chart(px.bar(grouped_desc, x=comp_cat, y='المتوسط الحسابي', color=comp_cat, text_auto='.2f'), use_container_width=True)

            # ==========================================
            # التبويب الثالث: الثبات (ألفا كرونباخ)
            with tab3:
                st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
                st.markdown("يتم حساب الثبات لكل محور على حدة، وللاستبيان ككل.")
                
                alpha_results = []
                if len(axis1_cols) > 1:
                    a1 = pg.cronbach_alpha(data=df_encoded[axis1_cols].dropna())[0]
                    alpha_results.append({"المحور": axis1_name, "عدد العبارات": len(axis1_cols), "معامل ألفا": round(a1, 3)})
                if len(axis2_cols) > 1:
                    a2 = pg.cronbach_alpha(data=df_encoded[axis2_cols].dropna())[0]
                    alpha_results.append({"المحور": axis2_name, "عدد العبارات": len(axis2_cols), "معامل ألفا": round(a2, 3)})
                
                # التعديل هنا لحساب جميع الأسئلة بلا استثناء
                all_q = all_questions 
                if len(all_q) > 1:
                    a_total = pg.cronbach_alpha(data=df_encoded[all_q].dropna())[0]
                    alpha_results.append({"المحور": "الاستبيان ككل", "عدد العبارات": len(all_q), "معامل ألفا": round(a_total, 3)})
                
                if alpha_results:
                    st.dataframe(pd.DataFrame(alpha_results), use_container_width=True)
                    if 'a_total' in locals() and a_total >= 0.60: st.success("✅ أداة الدراسة تتمتع بثبات ممتاز.")
                    else: st.warning("⚠️ الثبات يحتاج للمراجعة.")

            # ==========================================
            # التبويب الرابع: اختبار الفروق
            with tab4:
                st.subheader("⚖️ دلالة الفروق (T-test و ANOVA)")
                if categorical_cols and analysis_cols:
                    g_col = st.selectbox("المتغير المستقل (مثال: النوع، العمر):", categorical_cols, key="g_f")
                    t_col = st.selectbox("المتغير التابع (المحور المراد اختباره):", analysis_cols, key="t_f")
                    
                    res_data = df_encoded[[g_col, t_col]].dropna()
                    grps = res_data[g_col].unique()
                    
                    try:
                        if len(grps) == 2:
                            st.markdown(f"**نوع الاختبار:** `T-test` للمقارنة بين ({grps[0]}) و ({grps[1]})")
                            res = pg.ttest(res_data[res_data[g_col]==grps[0]][t_col], res_data[res_data[g_col]==grps[1]][t_col])
                            st.dataframe(res)
                            pval = res['p-val'].values[0]
                            if pval < 0.05: st.success(f"✅ توجد فروق ذات دلالة إحصائية في {t_col} تعزى لمتغير {g_col}.")
                            else: st.warning(f"لا توجد فروق ذات دلالة إحصائية في {t_col} تعزى لمتغير {g_col}.")
                        elif len(grps) > 2:
                            st.markdown(f"**نوع الاختبار:** `ANOVA` للمقارنة بين فئات ({g_col})")
                            res = pg.anova(data=res_data, dv=t_col, between=g_col)
                            st.dataframe(res)
                            pval = res['p-unc'].values[0]
                            if pval < 0.05: st.success(f"✅ توجد فروق ذات دلالة إحصائية.")
                            else: st.warning("لا توجد فروق ذات دلالة إحصائية.")
                        
                        st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)
                    except: st.error("البيانات غير كافية لإجراء الاختبار.")

            # ==========================================
            # التبويب الخامس: الارتباط
            with tab5:
                st.subheader("🔗 قياس الارتباط بين المحاور (Pearson Correlation)")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور الأول (المتغير المستقل):", analysis_cols, key="c1")
                    v2 = st.selectbox("المحور الثاني (المتغير التابع):", analysis_cols, index=1 if len(analysis_cols)>1 else 0, key="c2")
                    if v1 != v2:
                        try:
                            corr_res = pg.corr(df_encoded[v1], df_encoded[v2], method='pearson')
                            st.dataframe(corr_res[['n', 'r', 'p-val']])
                            r_val = corr_res['r'].values[0]
                            pval = corr_res['p-val'].values[0]
                            
                            if pval < 0.05:
                                direction = "طردية" if r_val > 0 else "عكسية"
                                st.success(f"✅ توجد علاقة ارتباط {direction} دالة إحصائياً بين ({v1}) و ({v2}). قوة الارتباط: {r_val:.3f}")
                            else:
                                st.warning("لا توجد علاقة ارتباط ذات دلالة إحصائية.")
                                
                            st.plotly_chart(px.scatter(df_encoded, x=v1, y=v2, trendline="ols"), use_container_width=True)
                        except: st.error("تعذر حساب الارتباط.")

            # ==========================================
            # التبويب السادس: الانحدار
            with tab6:
                st.subheader("📈 تحليل الانحدار (التنبؤ والتأثير)")
                if len(analysis_cols) >= 2:
                    dep_var = st.selectbox("المتغير التابع (النتيجة / Y):", analysis_cols, key='reg_y')
                    indep_vars = st.multiselect("المتغيرات المستقلة (المؤثرات / X):", [c for c in analysis_cols if c != dep_var], default=[c for c in analysis_cols if c != dep_var][:1], key='reg_x')
                    if indep_vars:
                        reg_data = df_encoded[[dep_var] + indep_vars].dropna()
                        try:
                            lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var])
                            st.dataframe(lm)
                            r2 = lm['r2'].values[0] if 'r2' in lm.columns else 0
                            st.info(f"💡 قوة النموذج (R²): المحاور المستقلة تُفسر نسبة **({float(r2)*100:.1f}%)** من التغير الذي يحدث في ({dep_var}).")
                        except Exception as e: st.error(f"حدث خطأ: {e}")

    except Exception as e: st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
