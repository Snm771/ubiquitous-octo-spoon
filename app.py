import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg

st.set_page_config(page_title="SmartStat Pro | الأكاديمية", page_icon="🎓", layout="wide")

# --- 1. دالة التشفير الذكي ---
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

# --- 2. خوارزمية التصنيف الدلالي ---
def smart_classify_columns(df):
    categorical_cols, numeric_cols = [], []
    demo_keywords = ['عمر', 'سن', 'جنس', 'نوع', 'مؤهل', 'مرحلة', 'صف', 'خبرة', 'حالة', 'دخل', 'تخصص', 'عمل']
    
    for col in df.columns:
        if col.lower() == 'timestamp': continue
        is_demo = any(keyword in col for keyword in demo_keywords)
        
        if is_demo:
            categorical_cols.append(col)
        else:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > (len(df) * 0.5):
                numeric_cols.append(col)
            elif df[col].nunique() <= 15:
                categorical_cols.append(col)
                
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
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات الديموغرافية (التي تُستخدم للمقارنة):", df_encoded.columns, default=cat_cols_auto)
        
        # الأسئلة الأساسية للاستبيان
        base_numeric_cols = st.sidebar.multiselect("🔢 أسئلة الاستبيان الأساسية:", df_encoded.columns, default=[c for c in num_cols_auto if c not in categorical_cols])

        # --- السحر الأكاديمي: حساب المجموع الكلي تلقائياً ---
        analysis_numeric_cols = []
        if base_numeric_cols:
            df_encoded['المجموع الكلي للاستبيان'] = df_encoded[base_numeric_cols].sum(axis=1)
            # إضافة المجموع الكلي كأول خيار في القوائم ليصبح هو الافتراضي!
            analysis_numeric_cols = ['المجموع الكلي للاستبيان'] + base_numeric_cols
            
            for col in analysis_numeric_cols:
                df_encoded[col] = pd.to_numeric(df_encoded[col], errors='coerce')

        st.success("✅ تم قراءة البيانات وحساب **المجموع الكلي للاستبيان** بنجاح!")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "👥 الديموغرافيا المتقاطعة", 
            "📊 الإحصاء الوصفي", 
            "🧪 الثبات (ألفا)", 
            "⚖️ الفروق وحجم الأثر", 
            "🔗 الارتباط المزدوج",
            "📈 الانحدار"
        ])

        # ==========================================
        # التبويب الأول: الديموغرافيا المتقاطعة
        with tab1:
            st.subheader("👥 لوحة قيادة البيانات الشخصية (التوزيع والتقاطع)")
            if categorical_cols:
                st.markdown("### 1️⃣ التوزيع العام")
                demo_col = st.selectbox("اختر المتغير لعرض توزيعه:", categorical_cols)
                counts = df_encoded[demo_col].value_counts()
                percentages = df_encoded[demo_col].value_counts(normalize=True) * 100
                demo_df = pd.DataFrame({'العدد': counts, 'النسبة (%)': percentages.round(2)})
                
                col1, col2 = st.columns(2)
                with col1: st.dataframe(demo_df, use_container_width=True)
                with col2: st.plotly_chart(px.pie(demo_df, values='العدد', names=demo_df.index, hole=0.3), use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 2️⃣ التحليل المتقاطع (Cross-Tabulation)")
                if len(categorical_cols) >= 2:
                    c1, c2 = st.columns(2)
                    with c1: cat1 = st.selectbox("المتغير الأساسي:", categorical_cols, key="cross1")
                    with c2: cat2 = st.selectbox("مقسم حسب:", categorical_cols, index=1 if len(categorical_cols)>1 else 0, key="cross2")
                    
                    if cat1 != cat2:
                        cross_tab = pd.crosstab(df_encoded[cat1], df_encoded[cat2], margins=True, margins_name="المجموع")
                        st.dataframe(cross_tab, use_container_width=True)
                        fig_cross = px.histogram(df_encoded, x=cat1, color=cat2, barmode='group', text_auto=True)
                        st.plotly_chart(fig_cross, use_container_width=True)
            else:
                st.warning("لا توجد بيانات شخصية.")

        # ==========================================
        # التبويب الثاني: الإحصاء الوصفي
        with tab2:
            st.subheader("📊 الإحصاء الوصفي للمتغيرات والمجموع الكلي")
            if analysis_numeric_cols:
                desc_df = df_encoded[analysis_numeric_cols].describe().T
                desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)
            else:
                st.error("لم يتم العثور على أسئلة.")

        # ==========================================
        # التبويب الثالث: الثبات
        with tab3:
            st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
            st.markdown("يتم حساب الثبات للأسئلة الأساسية فقط (بدون المجموع الكلي لضمان دقة النتيجة).")
            if len(base_numeric_cols) > 1:
                try:
                    alpha_data = df_encoded[base_numeric_cols].dropna()
                    alpha_val = pg.cronbach_alpha(data=alpha_data)[0]
                    st.metric(label="قيمة ألفا كرونباخ", value=f"{alpha_val:.3f}")
                    if alpha_val >= 0.60: st.success("✅ الاستبيان يتمتع بثبات عالٍ.")
                    else: st.warning("⚠️ الثبات ضعيف.")
                except Exception:
                    st.error("تعذر حساب الثبات.")

        # ==========================================
        # التبويب الرابع: الفروق (مركز على المجموع الكلي)
        with tab4:
            st.subheader("⚖️ اختبار الفروق وحجم الأثر")
            st.markdown("تلقائياً يتم قياس الفروق بناءً على **المجموع الكلي للاستبيان**، ويمكنك اختيار سؤال محدد إذا أردت.")
            if categorical_cols and analysis_numeric_cols:
                group_col = st.selectbox("المتغير المستقل (فئات/ديموغرافي):", categorical_cols, key="dif_g")
                test_col = st.selectbox("المتغير التابع:", analysis_numeric_cols, key="dif_t")
                
                clean_data = df_encoded[[group_col, test_col]].dropna()
                groups = clean_data[group_col].unique()
                
                try:
                    if len(groups) == 2:
                        st.markdown("**تم تشغيل:** `اختبار (T-test) لعينتين مستقلتين`")
                        g1 = clean_data[clean_data[group_col] == groups[0]][test_col]
                        g2 = clean_data[clean_data[group_col] == groups[1]][test_col]
                        res = pg.ttest(g1, g2)
                        st.dataframe(res)
                        
                        pval = res['p-val'].values[0] if 'p-val' in res.columns else 1.0
                        eff = res['cohen-d'].values[0] if 'cohen-d' in res.columns else 0.0
                        
                        if pval < 0.05: st.success(f"توجد فروق ذات دلالة إحصائية. **حجم الأثر (Cohen's d): {eff:.2f}**")
                        else: st.warning("لا توجد فروق ذات دلالة إحصائية.")
                        
                    elif len(groups) > 2:
                        st.markdown("**تم تشغيل:** `تحليل التباين الأحادي (ANOVA)`")
                        res = pg.anova(data=clean_data, dv=test_col, between=group_col)
                        st.dataframe(res)
                        
                        pval = res['p-unc'].values[0] if 'p-unc' in res.columns else 1.0
                        eff2 = res['np2'].values[0] if 'np2' in res.columns else 0.0
                        
                        if pval < 0.05: st.success(f"توجد فروق ذات دلالة إحصائية. **حجم الأثر (مربع إيتا جزئي np2): {eff2:.2f}**")
                        else: st.warning("لا توجد فروق ذات دلالة إحصائية.")
                        
                    st.plotly_chart(px.box(clean_data, x=group_col, y=test_col, color=group_col), use_container_width=True)
                except Exception as e:
                    st.error("تعذر إجراء الاختبار (تأكد من تنوع الإجابات).")

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
                        st.markdown("#### 1️⃣ معامل بيرسون")
                        try:
                            rp = pg.corr(df_encoded[v1], df_encoded[v2], method='pearson')
                            st.dataframe(rp[['n', 'r', 'p-val']])
                        except: st.error("خطأ بالحساب")
                    with cs:
                        st.markdown("#### 2️⃣ معامل سبيرمان")
                        try:
                            rs = pg.corr(df_encoded[v1], df_encoded[v2], method='spearman')
                            st.dataframe(rs[['n', 'r', 'p-val']])
                        except: st.error("خطأ بالحساب")
                    st.plotly_chart(px.scatter(df_encoded, x=v1, y=v2, trendline="ols"), use_container_width=True)

        # ==========================================
        # التبويب السادس: الانحدار
        with tab6:
            st.subheader("📈 تحليل الانحدار والتنبؤ (Regression)")
            if len(analysis_numeric_cols) >= 2:
                dep_var = st.selectbox("المتغير التابع (النتيجة / Y):", analysis_numeric_cols, key='reg_y')
                indep_vars = st.multiselect("المتغيرات المستقلة (المؤثرات / X):", [c for c in analysis_numeric_cols if c != dep_var], key='reg_x')
                if indep_vars:
                    reg_data = df_encoded[[dep_var] + indep_vars].dropna()
                    if len(reg_data) > 2:
                        try:
                            lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var])
                            st.dataframe(lm)
                            r2 = lm['r2'].values[0] if 'r2' in lm.columns else 0
                            st.info(f"💡 قوة التفسير (R²): المتغيرات المستقلة تُفسر نسبة **({float(r2)*100:.1f}%)** من التغير في المتغير التابع.")
                        except Exception as e: st.error(f"خطأ: {e}")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
