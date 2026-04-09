import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg

st.set_page_config(page_title="SmartStat Pro | النسخة الأكاديمية", page_icon="🎓", layout="wide")

# --- 1. دالة التشفير الذكي (القاموس الشامل) ---
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

# --- 2. خوارزمية التصنيف الدلالي للتمييز بين الديموغرافيا والأسئلة ---
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
# واجهة المستخدم
# ==========================================
st.title("🎓 SmartStat Pro - المحلل الإحصائي الأكاديمي الشامل")
st.markdown("---")

uploaded_file = st.file_uploader("قم برفع ملف البيانات (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)
        
        st.sidebar.title("⚙️ إعدادات المتغيرات")
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات الديموغرافية (للفصل والمقارنة):", df_encoded.columns, default=cat_cols_auto)
        base_numeric_cols = st.sidebar.multiselect("🔢 أسئلة الاستبيان الأساسية:", df_encoded.columns, default=[c for c in num_cols_auto if c not in categorical_cols])

        # --- حساب المجموع الكلي (التوتال النهائي) ---
        analysis_numeric_cols = []
        if base_numeric_cols:
            df_encoded['المجموع الكلي للاستبيان'] = df_encoded[base_numeric_cols].sum(axis=1)
            analysis_numeric_cols = ['المجموع الكلي للاستبيان'] + base_numeric_cols
            for col in analysis_numeric_cols:
                df_encoded[col] = pd.to_numeric(df_encoded[col], errors='coerce')

        st.success("✅ تم قراءة البيانات وتجهيز المجموع الكلي للفصل بين المتغيرات!")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "👥 الديموغرافيا المتقاطعة", 
            "📊 الإحصاء الوصفي (المقارن)", 
            "🧪 الثبات (ألفا)", 
            "⚖️ الفروق وحجم الأثر", 
            "🔗 الارتباط المزدوج",
            "📈 الانحدار"
        ])

        # ==========================================
        # التبويب الأول: الديموغرافيا
        with tab1:
            st.subheader("👥 تحليل التوزيع للفئات (مثل الجنس والعمر)")
            if categorical_cols:
                demo_col = st.selectbox("اختر المتغير لعرض توزيعه:", categorical_cols, key="demo_view")
                counts = df_encoded[demo_col].value_counts()
                percentages = df_encoded[demo_col].value_counts(normalize=True) * 100
                demo_df = pd.DataFrame({'العدد': counts, 'النسبة (%)': percentages.round(2)})
                col1, col2 = st.columns(2)
                with col1: st.dataframe(demo_df, use_container_width=True)
                with col2: st.plotly_chart(px.pie(demo_df, values='العدد', names=demo_df.index, hole=0.3), use_container_width=True)
            else: st.warning("لا توجد بيانات شخصية.")

        # ==========================================
        # التبويب الثاني: الإحصاء الوصفي (تم إضافة ميزة الفصل هنا)
        with tab2:
            st.subheader("📊 الإحصاء الوصفي والتحليل المقارن")
            st.markdown("يمكنك هنا رؤية المتوسطات للكل، أو فصلها حسب المتغير (مثل ذكر وأنثى).")
            
            if analysis_numeric_cols:
                # ميزة الفصل الذكي
                split_view = st.checkbox("🔄 فصل النتائج حسب متغير (مثلاً: مقارنة متوسطات الذكور ضد الإناث)")
                
                if split_view and categorical_cols:
                    split_col = st.selectbox("اختر المتغير الذي تريد الفصل بناءً عليه:", categorical_cols)
                    # حساب المتوسطات لكل مجموعة
                    grouped_desc = df_encoded.groupby(split_col)[analysis_numeric_cols].mean().T
                    st.markdown(f"**متوسطات الإجابات مقسمة حسب ({split_col}):**")
                    st.dataframe(grouped_desc.style.background_gradient(axis=1), use_container_width=True)
                    st.info("💡 الأرقام أعلاه تمثل المتوسط الحسابي لكل مجموعة. يمكنك ملاحظة أي فئة سجلت درجات أعلى في الاستبيان.")
                else:
                    # العرض العادي للكل
                    desc_df = df_encoded[analysis_numeric_cols].describe().T
                    desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                    st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)
            else: st.error("لم يتم العثور على أسئلة.")

        # ==========================================
        # التبويب الثالث: الثبات
        with tab3:
            st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
            if len(base_numeric_cols) > 1:
                try:
                    alpha_val = pg.cronbach_alpha(data=df_encoded[base_numeric_cols].dropna())[0]
                    st.metric(label="قيمة ألفا كرونباخ", value=f"{alpha_val:.3f}")
                    if alpha_val >= 0.60: st.success("✅ الاستبيان يتمتع بثبات عالٍ.")
                    else: st.warning("⚠️ الثبات ضعيف.")
                except Exception: st.error("تعذر حساب الثبات.")

        # ==========================================
        # التبويب الرابع: الفروق
        with tab4:
            st.subheader("⚖️ اختبار الفروق وحجم الأثر")
            if categorical_cols and analysis_numeric_cols:
                group_col = st.selectbox("المتغير المستقل (فئات):", categorical_cols, key="dif_g")
                test_col = st.selectbox("المتغير التابع (المجموع الكلي أو سؤال):", analysis_numeric_cols, key="dif_t")
                clean_data = df_encoded[[group_col, test_col]].dropna()
                groups = clean_data[group_col].unique()
                try:
                    if len(groups) == 2:
                        res = pg.ttest(clean_data[clean_data[group_col] == groups[0]][test_col], clean_data[clean_data[group_col] == groups[1]][test_col])
                        st.dataframe(res)
                        if res['p-val'].values[0] < 0.05: st.success(f"توجد فروق دالة. حجم الأثر: {res['cohen-d'].values[0]:.2f}")
                        else: st.warning("لا توجد فروق دالة.")
                    elif len(groups) > 2:
                        res = pg.anova(data=clean_data, dv=test_col, between=group_col)
                        st.dataframe(res)
                        if res['p-unc'].values[0] < 0.05: st.success(f"توجد فروق دالة. حجم الأثر: {res['np2'].values[0]:.2f}")
                        else: st.warning("لا توجد فروق دالة.")
                    st.plotly_chart(px.box(clean_data, x=group_col, y=test_col, color=group_col), use_container_width=True)
                except Exception: st.error("تعذر إجراء الاختبار.")

        # ==========================================
        # التبويب الخامس: الارتباط
        with tab5:
            st.subheader("🔗 قياس الارتباط (Pearson & Spearman)")
            if len(analysis_numeric_cols) >= 2:
                v1 = st.selectbox("المتغير الأول:", analysis_numeric_cols, key="c1")
                v2 = st.selectbox("المتغير الثاني:", analysis_numeric_cols, index=1, key="c2")
                if v1 != v2:
                    cp, cs = st.columns(2)
                    with cp:
                        try: st.markdown("#### بيرسون"); st.dataframe(pg.corr(df_encoded[v1], df_encoded[v2], method='pearson')[['n', 'r', 'p-val']])
                        except: st.error("خطأ بالحساب")
                    with cs:
                        try: st.markdown("#### سبيرمان"); st.dataframe(pg.corr(df_encoded[v1], df_encoded[v2], method='spearman')[['n', 'r', 'p-val']])
                        except: st.error("خطأ بالحساب")
                    st.plotly_chart(px.scatter(df_encoded, x=v1, y=v2, trendline="ols"), use_container_width=True)

        # ==========================================
        # التبويب السادس: الانحدار
        with tab6:
            st.subheader("📈 تحليل الانحدار والتأثير (Regression)")
            if len(analysis_numeric_cols) >= 2:
                dep_var = st.selectbox("المتغير التابع (Y):", analysis_numeric_cols, key='reg_y')
                indep_vars = st.multiselect("المتغيرات المستقلة (X):", [c for c in analysis_numeric_cols if c != dep_var], key='reg_x')
                if indep_vars:
                    reg_data = df_encoded[[dep_var] + indep_vars].dropna()
                    try:
                        lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var])
                        st.dataframe(lm)
                        st.info(f"💡 قوة التفسير (R²): {lm['r2'].values[0]:.3f}")
                    except Exception as e: st.error(f"خطأ: {e}")

    except Exception as e: st.error(f"حدث خطأ: {e}")
