import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg

st.set_page_config(page_title="SmartStat Pro | النسخة الأكاديمية", page_icon="🎓", layout="wide")

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
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات الديموغرافية (مثل الجنس):", df_encoded.columns, default=cat_cols_auto)
        base_numeric_cols = st.sidebar.multiselect("🔢 أسئلة الاستبيان المراد تحليلها:", df_encoded.columns, default=[c for c in num_cols_auto if c not in categorical_cols])

        # --- السحر الأكاديمي: حساب المتوسط العام (بدلاً من المجموع الضخم) ---
        main_var = "المتوسط العام للاستبيان (من 1 إلى 5)"
        analysis_numeric_cols = []
        if base_numeric_cols:
            # هنا التعديل: حساب المتوسط الحسابي لكل صف
            df_encoded[main_var] = df_encoded[base_numeric_cols].mean(axis=1)
            analysis_numeric_cols = [main_var] + base_numeric_cols
            for col in analysis_numeric_cols:
                df_encoded[col] = pd.to_numeric(df_encoded[col], errors='coerce')

        st.success(f"✅ تم حساب **{main_var}** بنجاح! القيم الآن محصورة بين 1 و 5 لسهولة المقارنة.")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "👥 الديموغرافيا", 
            "📊 وصف المقارنة", 
            "🧪 الثبات", 
            "⚖️ اختبار الفروق", 
            "🔗 الارتباط",
            "📈 الانحدار"
        ])

        # ==========================================
        # التبويب الأول: الديموغرافيا
        with tab1:
            st.subheader("👥 توزيع العينة")
            if categorical_cols:
                demo_col = st.selectbox("اختر المتغير:", categorical_cols, key="d1")
                counts = df_encoded[demo_col].value_counts()
                st.dataframe(pd.DataFrame({'العدد': counts, 'النسبة (%)': (counts/len(df)*100).round(2)}), use_container_width=True)
                st.plotly_chart(px.pie(values=counts, names=counts.index, hole=0.3), use_container_width=True)

        # ==========================================
        # التبويب الثاني: الإحصاء الوصفي (المقارنة المباشرة)
        with tab2:
            st.subheader("📊 مقارنة المتوسطات بين المجموعات")
            if analysis_numeric_cols and categorical_cols:
                comp_col = st.selectbox("قارن المتوسط العام حسب:", categorical_cols, key="c_comp")
                
                # جدول المقارنة الذي طلبه المستخدم
                summary_table = df_encoded.groupby(comp_col)[main_var].agg(['count', 'mean', 'std']).reset_index()
                summary_table.columns = [comp_col, 'عدد العينة', 'المتوسط العام (من 5)', 'الانحراف المعياري']
                
                st.markdown(f"### 📝 جدول مقارنة {main_var} حسب {comp_col}")
                st.dataframe(summary_table.style.highlight_max(subset=['المتوسط العام (من 5)'], color='#d4edda'), use_container_width=True)
                
                fig_comp = px.bar(summary_table, x=comp_col, y='المتوسط العام (من 5)', text_auto='.2f', title=f"مقارنة متوسط الإجابات بين فئات {comp_col}")
                st.plotly_chart(fig_comp, use_container_width=True)
                st.info("💡 **تفسير:** القيمة التي تظهر (مثلاً 3.50) تعني أن هذه المجموعة تقع في منطقة 'أحياناً' أو 'محايد' بشكل عام.")

        # ==========================================
        # التبويب الرابع: الفروق (T-test / ANOVA)
        with tab4:
            st.subheader("⚖️ هل الفرق بين المجموعات حقيقي (دلالة إحصائية)؟")
            if categorical_cols:
                g_col = st.selectbox("المتغير المستقل:", categorical_cols, key="g_f")
                # الافتراضي هو المتوسط العام
                res_data = df_encoded[[g_col, main_var]].dropna()
                grps = res_data[g_col].unique()
                
                try:
                    if len(grps) == 2:
                        st.markdown(f"**اختبار T-test للمقارنة بين ({grps[0]}) و ({grps[1]})**")
                        res = pg.ttest(res_data[res_data[g_col]==grps[0]][main_var], res_data[res_data[g_col]==grps[1]][main_var])
                        st.dataframe(res)
                        pval = res['p-val'].values[0]
                        if pval < 0.05: st.success("✅ يوجد فرق جوهري ذو دلالة إحصائية بين المجموعتين.")
                        else: st.warning("لا يوجد فرق جوهري، الإجابات متقاربة جداً.")
                    elif len(grps) > 2:
                        st.markdown(f"**اختبار ANOVA للمقارنة بين فئات {g_col}**")
                        res = pg.anova(data=res_data, dv=main_var, between=g_col)
                        st.dataframe(res)
                    
                    st.plotly_chart(px.box(res_data, x=g_col, y=main_var, color=g_col, title="توزيع المتوسط العام لكل فئة"), use_container_width=True)
                except: st.error("البيانات غير كافية للاختبار.")

        # التبويبات الأخرى (الثبات، الارتباط، الانحدار) تبقى كما هي برمجياً لخدمة البحث
        with tab3:
            if len(base_numeric_cols) > 1:
                st.metric("معامل ألفا كرونباخ (الثبات)", f"{pg.cronbach_alpha(data=df_encoded[base_numeric_cols].dropna())[0]:.3f}")
        with tab5:
            if len(analysis_numeric_cols) >= 2:
                st.plotly_chart(px.imshow(df_encoded[analysis_numeric_cols].corr(method='spearman'), text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1), use_container_width=True)
        with tab6:
            if len(analysis_numeric_cols) >= 2:
                st.markdown("تحليل تأثير المتغيرات على المتوسط العام:")
                y_reg = main_var
                x_reg = st.multiselect("المتغيرات المؤثرة:", [c for c in base_numeric_cols if c != y_reg])
                if x_reg:
                    st.dataframe(pg.linear_regression(df_encoded[x_reg], df_encoded[y_reg]))

    except Exception as e: st.error(f"حدث خطأ: {e}")
