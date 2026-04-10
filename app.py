import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

st.set_page_config(page_title="SmartStat Pro | الخبير الإحصائي", page_icon="📊", layout="wide")

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
    df_cleaned = df_cleaned.map(lambda x: str(x).strip() if pd.notnull(x) and isinstance(x, str) else x)
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
# واجهة المستخدم
# ==========================================
st.title("📊 SmartStat Pro - نظام الخبير الإحصائي الآلي")
st.markdown("يرفق النظام الآن **تفسيراً أكاديمياً** مع كل نتيجة إحصائية جاهز للنسخ في الأبحاث العلمية.")
st.markdown("---")

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
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "👥 عينة الدراسة", 
                "📊 الإحصاء الوصفي", 
                "🧪 الثبات (ألفا)", 
                "⚖️ الفروق (T-test/ANOVA)", 
                "🔗 الارتباط (Pearson)",
                "📈 الانحدار"
            ])

            # ==========================================
            with tab1:
                st.subheader("👥 وصف عينة الدراسة (التكرارات والنسب)")
                if categorical_cols:
                    demo_col = st.selectbox("اختر المتغير:", categorical_cols, key="d1")
                    counts = df_encoded[demo_col].value_counts()
                    percentages = df_encoded[demo_col].value_counts(normalize=True) * 100
                    demo_df = pd.DataFrame({'التكرار': counts, 'النسبة (%)': percentages.round(2)})
                    col1, col2 = st.columns(2)
                    with col1: st.dataframe(demo_df, use_container_width=True)
                    with col2: st.plotly_chart(px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.3), use_container_width=True)

            # ==========================================
            with tab2:
                st.subheader("📊 الإحصاء الوصفي (المتوسطات والانحرافات المعيارية)")
                st.markdown("### 1️⃣ الإحصاء العام للمحاور والأبعاد")
                desc_df = df_encoded[analysis_cols].describe().T
                desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)
                
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
                    st.info("📝 **الصياغة الأكاديمية:** يشير معامل ألفا كرونباخ إلى مستوى الاتساق الداخلي لفقرات الاستبيان. تُعتبر القيمة التي تتجاوز (0.60) مقبولة لأغراض البحث العلمي، وكلما اقتربت القيمة من (1.0) دلّ ذلك على ثبات وموثوقية عالية جداً لأداة الدراسة.")

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
                                    st.warning("⚠️ إحدى المجموعات عدد أفرادها قليل جداً (أقل من شخصين) ولا يمكن إجراء الاختبار.")
                                else:
                                    res = pg.ttest(g1, g2)
                                    st.dataframe(res)
                                    pval = res['p-val'].values[0] if 'p-val' in res.columns else (res['p-value'].values[0] if 'p-value' in res.columns else 1.0)
                                    
                                    st.markdown("### 📝 التفسير العلمي للنتيجة:")
                                    if pval < 0.05: 
                                        st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"**الصياغة الأكاديمية:** تشير النتائج إلى وجود فروق ذات دلالة إحصائية عند مستوى الدلالة (0.05) بين فئات ({g_col}) في محور ({t_col})، حيث بلغت قيمة الدلالة ($p = {pval:.3f}$) وهي أصغر من (0.05). وهذا يعني أن الاختلاف الملاحظ في المتوسطات هو اختلاف حقيقي يعود لتأثير الفئة المستقلة وليس وليد الصدفة.")
                                    else: 
                                        st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"**الصياغة الأكاديمية:** أشارت نتائج اختبار (T-test) إلى عدم وجود فروق ذات دلالة إحصائية عند مستوى الدلالة (0.05) بين فئات ({g_col}) في محور ({t_col})، حيث بلغت قيمة الدلالة ($p = {pval:.3f}$) وهي أكبر من (0.05). هذا يعني أن الاختلافات الظاهرية في المتوسطات ترجع إلى الصدفة أو أخطاء المعاينة العشوائية، ولا يمكن تعميمها على مجتمع الدراسة، مما يشير إلى تقارب استجابات المجموعتين.")
                                    
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
                                    
                                    st.markdown("### 📝 التفسير العلمي للنتيجة:")
                                    if pval < 0.05: 
                                        st.success("✅ **توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"**الصياغة الأكاديمية:** أظهرت نتائج تحليل التباين (ANOVA) وجود فروق ذات دلالة إحصائية عند مستوى الدلالة (0.05) بين فئات ({g_col}) في محور ({t_col})، حيث بلغت الدلالة ($p = {pval:.3f}$). وهذا يعكس وجود تباين حقيقي في الاستجابات يختلف باختلاف الفئات المدروسة.")
                                    else: 
                                        st.warning("⚠️ **لا توجد فروق ذات دلالة إحصائية.**")
                                        st.info(f"**الصياغة الأكاديمية:** بينت نتائج تحليل التباين (ANOVA) عدم وجود فروق ذات دلالة إحصائية عند مستوى (0.05) بين فئات ({g_col}) في محور ({t_col})، حيث بلغت الدلالة ($p = {pval:.3f}$) وهي أكبر من (0.05). مما يشير إلى تجانس وتوافق في آراء العينة بغض النظر عن انتمائهم الفئوي.")
                                    
                            st.plotly_chart(px.box(res_data, x=g_col, y=t_col, color=g_col), use_container_width=True)
                        except Exception as e: 
                            st.warning(f"تعذر حساب الفروق بسبب تعقيد البيانات: {e}")

            # ==========================================
            with tab5:
                st.subheader("🔗 قياس الارتباط بين المحاور (Pearson)")
                if len(analysis_cols) >= 2:
                    v1 = st.selectbox("المحور الأول:", analysis_cols, key="c1")
                    v2 = st.selectbox("المحور الثاني:", analysis_cols, index=1 if len(analysis_cols)>1 else 0, key="c2")
                    if v1 != v2:
                        try:
                            clean_corr = df_encoded[[v1, v2]].apply(pd.to_numeric, errors='coerce').dropna()
                            if len(clean_corr) > 2:
                                corr_res = pg.corr(clean_corr[v1], clean_corr[v2], method='pearson')
                                st.dataframe(corr_res[['n', 'r', 'p-val'] if 'p-val' in corr_res.columns else corr_res.columns])
                                
                                pval = corr_res['p-val'].values[0] if 'p-val' in corr_res.columns else (corr_res['p-value'].values[0] if 'p-value' in corr_res.columns else 1.0)
                                rval = corr_res['r'].values[0] if 'r' in corr_res.columns else 0.0
                                
                                st.markdown("### 📝 التفسير العلمي للنتيجة:")
                                if pval < 0.05: 
                                    direction = "طردية (إيجابية)" if rval > 0 else "عكسية (سلبية)"
                                    strength = "قوية" if abs(rval) > 0.7 else ("متوسطة" if abs(rval) > 0.4 else "ضعيفة")
                                    st.success(f"✅ **توجد علاقة ارتباط دالة إحصائياً.**")
                                    st.info(f"**الصياغة الأكاديمية:** كشفت نتائج معامل ارتباط بيرسون عن وجود علاقة ارتباط {direction} و{strength} ذات دلالة إحصائية عند مستوى (0.05) بين ({v1}) و ({v2})، حيث بلغت قيمة معامل الارتباط ($r = {rval:.3f}$) بقيمة احتمالية ($p = {pval:.3f}$). مما يعني أنه كلما ارتفعت التقييمات في المتغير الأول، صاحَبَها [ارتفاع/انخفاض] ذو دلالة في المتغير الثاني.")
                                else: 
                                    st.warning("⚠️ **لا توجد علاقة ارتباط دالة إحصائياً.**")
                                    st.info(f"**الصياغة الأكاديمية:** أظهرت النتائج عدم وجود علاقة ارتباط ذات دلالة إحصائية بين ({v1}) و ({v2})، حيث بلغت الدلالة ($p = {pval:.3f}$) وهي أعلى من (0.05). مما يشير إلى أن التغير في أحد المتغيرين لا يرتبط بشكل خطي يعتد به إحصائياً مع التغير في المتغير الآخر.")
                                    
                                st.plotly_chart(px.scatter(clean_corr, x=v1, y=v2, trendline="ols"), use_container_width=True)
                            else:
                                st.warning("بيانات غير كافية للارتباط.")
                        except: st.error("تعذر حساب الارتباط.")

            # ==========================================
            with tab6:
                st.subheader("📈 تحليل الانحدار (التنبؤ والتأثير)")
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
                                
                                st.markdown("### 📝 التفسير العلمي للنتيجة:")
                                st.info(f"**الصياغة الأكاديمية:** يوضح نموذج الانحدار الخطي أن المتغيرات المستقلة المدروسة قادرة مجتمعة على تفسير ما مقداره **({float(r2)*100:.1f}%)** من التباين الحاصل في المتغير التابع ({dep_var})، وذلك استناداً إلى قيمة معامل التحديد ($R^2 = {r2:.3f}$). وتُعزى النسبة المتبقية إلى عوامل أخرى غير مشمولة في النموذج أو إلى الأخطاء العشوائية.")
                            except: st.error("حدث خطأ في الانحدار.")
                        else:
                            st.warning("عينة غير كافية للانحدار.")

    except Exception as e: st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
