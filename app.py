import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

st.set_page_config(page_title="SmartStat Pro | AI", page_icon="🤖", layout="wide")

# --- 1. خوارزمية التنظيف والتشفير الذكي ---
def encode_likert(df):
    df_cleaned = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    likert_map = {
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1, "لا أوافق": 2, "لا أوافق بشدة": 1,
        "دائما": 5, "دائماً": 5, "غالبا": 4, "غالباً": 4, "أحيانا": 3, "أحياناً": 3, "نادرا": 2, "نادراً": 2, "أبدا": 1, "أبداً": 1, "مطلقا": 1, "مطلقاً": 1,
        "بدرجة كبيرة جدا": 5, "بدرجة كبيرة جداً": 5, "بدرجة كبيرة": 4, "بدرجة متوسطة": 3, "بدرجة قليلة": 2, "بدرجة ضعيفة": 2, "بدرجة قليلة جدا": 1, "بدرجة ضعيفة جدا": 1,
        "مهم جدا": 5, "مهم جداً": 5, "مهم": 4, "متوسط الأهمية": 3, "قليل الأهمية": 2, "غير مهم": 1,
        "ممتاز": 5, "جيد جدا": 4, "جيد جداً": 4, "جيد": 3, "مقبول": 2, "ضعيف": 1,
        "نعم": 2, "لا": 1
    }
    df_cleaned = df_cleaned.replace(likert_map)
    return df_cleaned

# --- 2. خوارزمية التصنيف الآلي لأنواع البيانات ---
def smart_classify_columns(df):
    categorical_cols, numeric_cols, text_cols = [], [], []
    for col in df.columns:
        if col.lower() == 'timestamp': continue
        converted = pd.to_numeric(df[col], errors='coerce')
        if converted.notnull().sum() > (len(df) * 0.5):
            numeric_cols.append(col)
        else:
            if df[col].nunique() <= 15: categorical_cols.append(col)
            else: text_cols.append(col)
    return categorical_cols, numeric_cols, text_cols

# ==========================================
# واجهة المستخدم والتطبيق
# ==========================================
st.title("🤖 SmartStat Pro - المحلل الإحصائي المدعوم بالذكاء الاصطناعي")
st.markdown("يقرأ البيانات بذكاء، يحلل الشخصيات بعمق، ولا يترك شاردة ولا واردة.")
st.markdown("---")

uploaded_file = st.file_uploader("قم برفع ملف البيانات (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto, text_cols_auto = smart_classify_columns(df_encoded)
        
        st.sidebar.title("⚙️ محرك الذكاء الاصطناعي")
        st.sidebar.success(f"تم قراءة {len(df)} استجابة.")
        st.sidebar.markdown("### 🤖 تصنيف المتغيرات الآلي")
        
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات الديموغرافية (الفئوية):", df_encoded.columns, default=cat_cols_auto)
        numeric_cols = st.sidebar.multiselect("🔢 متغيرات الاستبيان (الرقمية):", df_encoded.columns, default=[c for c in num_cols_auto if c not in categorical_cols])
        
        for col in numeric_cols:
            df_encoded[col] = pd.to_numeric(df_encoded[col], errors='coerce')

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🗂️ جودة البيانات",
            "👥 التحليل الديموغرافي العميق", 
            "📊 الإحصاء الوصفي", 
            "🧪 الثبات (ألفا)", 
            "⚖️ الفروق (إجمالي الاستبيان)", 
            "🔗 الارتباط"
        ])

        # ==========================================
        # التبويب الأول: جودة البيانات
        with tab1:
            st.subheader("🗂️ تقرير جودة وسلامة البيانات")
            missing_data = df_encoded.isnull().sum()
            missing_df = missing_data[missing_data > 0].reset_index()
            missing_df.columns = ['المتغير', 'عدد الإجابات المفقودة']
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("إجمالي العينة", len(df))
                st.metric("إجمالي المتغيرات", len(df.columns))
            with col2:
                if not missing_df.empty:
                    st.warning("⚠️ تم العثور على بيانات مفقودة في هذه الأعمدة:")
                    st.dataframe(missing_df, use_container_width=True)
                else:
                    st.success("✅ ممتازة! لا توجد أي بيانات مفقودة.")

        # ==========================================
        # التبويب الثاني: التحليل الديموغرافي العميق
        with tab2:
            st.subheader("👥 لوحة قيادة البيانات الشخصية (Demographic Dashboard)")
            
            if categorical_cols:
                st.markdown("### 1️⃣ التوزيع الشامل لجميع الفئات (نظرة عامة)")
                cols_per_row = 3
                cols = st.columns(cols_per_row)
                for i, col_name in enumerate(categorical_cols):
                    counts = df_encoded[col_name].value_counts().reset_index()
                    counts.columns = [col_name, 'العدد']
                    fig = px.pie(counts, values='العدد', names=col_name, title=f"توزيع: {col_name}", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(showlegend=False)
                    cols[i % cols_per_row].plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 2️⃣ التحليل المتقاطع العميق (Cross-Tabulation)")
                if len(categorical_cols) >= 2:
                    c1, c2 = st.columns(2)
                    with c1: cat1 = st.selectbox("المتغير الأول (المحور الأفقي):", categorical_cols, key="cross1")
                    with c2: cat2 = st.selectbox("المتغير الثاني (التقسيم الداخلي):", categorical_cols, index=1, key="cross2")
                    
                    if cat1 != cat2:
                        fig_cross = px.histogram(df_encoded, x=cat1, color=cat2, barmode='group', text_auto=True, 
                                                 title=f"مقارنة أعداد ({cat1}) مقسمة حسب ({cat2})",
                                                 color_discrete_sequence=px.colors.qualitative.Set2)
                        st.plotly_chart(fig_cross, use_container_width=True)
                        st.markdown(f"**جدول التقاطع الرقمي:**")
                        cross_tab = pd.crosstab(df_encoded[cat1], df_encoded[cat2], margins=True, margins_name="المجموع الكلي")
                        st.dataframe(cross_tab, use_container_width=True)
                    else:
                        st.warning("يرجى اختيار متغيرين مختلفين للتحليل المتقاطع.")
            else:
                st.info("لم يتم تحديد متغيرات شخصية/فئوية في لوحة التحكم الجانبية.")

        # ==========================================
        # التبويب الثالث: الإحصاء الرقمي
        with tab3:
            st.subheader("📊 الإحصاء الوصفي العميق (لأسئلة الاستبيان)")
            if numeric_cols:
                desc_df = df_encoded[numeric_cols].describe().T
                desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)
                
                mean_df = desc_df[['المتوسط']].reset_index()
                fig_bar = px.bar(mean_df, x='index', y='المتوسط', color='المتوسط', color_continuous_scale='viridis')
                fig_bar.update_layout(xaxis_title="السؤال/المتغير", yaxis_title="المتوسط الحسابي")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("لم يتم تحديد متغيرات رقمية.")

        # ==========================================
        # التبويب الرابع: الثبات
        with tab4:
            st.subheader("🧪 قياس الثبات الشامل (ألفا كرونباخ)")
            if len(numeric_cols) > 1:
                try:
                    alpha_data = df_encoded[numeric_cols].dropna()
                    if not alpha_data.empty and len(alpha_data) > 2:
                        alpha_tuple = pg.cronbach_alpha(data=alpha_data)
                        st.metric(label="قيمة معامل ألفا كرونباخ", value=f"{alpha_tuple[0]:.3f}")
                        if alpha_tuple[0] >= 0.60: st.success("✅ الاستبيان موثوق ويتمتع بثبات عالٍ.")
                        else: st.warning("⚠️ الثبات ضعيف.")
                except Exception:
                    st.error("⚠️ تعذر حساب الثبات، تأكد أن الإجابات ليست متطابقة تماماً.")

        # ==========================================
        # التبويب الخامس: الفروق (التعديل الجديد - التوتال والخلاصة)
        with tab5:
            st.subheader("⚖️ تقرير الفروق الإحصائية (لإجمالي الاستبيان)")
            st.markdown("يقوم هذا القسم بجمع إجابات الاستبيان بالكامل (التوتال) وقياس الفروق بناءً على المتغير الذي تختاره.")
            
            if categorical_cols and numeric_cols:
                g_col = st.selectbox("اختر المتغير الديموغرافي (للمقارنة بناءً عليه):", categorical_cols, key="g_main")
                
                # إنشاء عمود "الدرجة الكلية / التوتال" بجمع متوسط إجابات الشخص
                c_data = df_encoded.copy()
                c_data['⭐ التوتال (المتوسط العام)'] = c_data[numeric_cols].mean(axis=1)
                
                clean_data = c_data[[g_col, '⭐ التوتال (المتوسط العام)']].dropna()
                grps = clean_data[g_col].unique()
                
                if len(grps) < 2:
                    st.warning("هذا المتغير لا يحتوي على مجموعات كافية لإجراء المقارنة.")
                else:
                    test_name = "T-test" if len(grps) == 2 else "ANOVA"
                    test_stat_name = "T" if test_name == "T-test" else "F"
                    
                    try:
                        st.markdown("---")
                        st.markdown(f"### 1️⃣ الإحصاء الوصفي (من الأعلى إجابة؟)")
                        # حساب المتوسطات لكل فئة للتوتال
                        means_df = clean_data.groupby(g_col)['⭐ التوتال (المتوسط العام)'].agg(['count', 'mean', 'std']).reset_index()
                        means_df.columns = ['الفئة', 'العدد', 'المتوسط الحسابي الكلي', 'الانحراف المعياري']
                        st.dataframe(means_df.style.format({"المتوسط الحسابي الكلي": "{:.3f}", "الانحراف المعياري": "{:.3f}"}), use_container_width=True)

                        st.markdown(f"### 2️⃣ الخلاصة النهائية لاختبار ({test_name})")
                        # إجراء الاختبار للتوتال فقط
                        if test_name == "T-test":
                            g1 = clean_data[clean_data[g_col] == grps[0]]['⭐ التوتال (المتوسط العام)']
                            g2 = clean_data[clean_data[g_col] == grps[1]]['⭐ التوتال (المتوسط العام)']
                            res = pg.ttest(g1, g2)
                            stat_val = res['T'].values[0]
                            pval = res['p-val'].values[0]
                        else: # ANOVA
                            res = pg.anova(data=clean_data, dv='⭐ التوتال (المتوسط العام)', between=g_col)
                            stat_val = res['F'].values[0]
                            pval = res['p-unc'].values[0]
                            
                        sig = "توجد فروق دالة" if pval < 0.05 else "لا توجد فروق دالة"
                        
                        # جدول النتيجة النهائي
                        final_res = pd.DataFrame([{
                            "المتغير للقياس": g_col,
                            "الاختبار المستخدم": test_name,
                            f"قيمة ({test_stat_name})": round(stat_val, 3),
                            "مستوى الدلالة (Sig)": round(pval, 3),
                            "النتيجة": sig
                        }])
                        
                        def color_sig(val):
                            if val == 'توجد فروق دالة': return 'color: #2e7d32; font-weight: bold'
                            elif val == 'لا توجد فروق دالة': return 'color: #c62828; font-weight: bold'
                            return ''
                            
                        st.dataframe(final_res.style.map(color_sig, subset=['النتيجة']), use_container_width=True)
                        
                        if pval < 0.05:
                            st.success(f"💡 الخلاصة: يوجد اختلاف حقيقي إحصائياً في إجمالي إجابات الاستبيان بين فئات ({g_col}). راجع جدول المتوسطات أعلاه لمعرفة الفئة صاحبة الدرجة الأعلى.")
                        else:
                            st.warning(f"💡 الخلاصة: إجابات الاستبيان متقاربة جداً، ولا يوجد فرق حقيقي يُذكر بين فئات ({g_col}).")
                            
                        # رسم بياني للصندوق يوضح توزيع التوتال
                        fig = px.box(clean_data, x=g_col, y='⭐ التوتال (المتوسط العام)', color=g_col, title=f"مقارنة إجمالي الاستبيان حسب ({g_col})")
                        st.plotly_chart(fig, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"تعذر حساب الفروق. (السبب: {e})")

        # ==========================================
        # التبويب السادس: الارتباط
        with tab6:
            st.subheader("🔗 مصفوفة الارتباط الذكية (الخريطة الحرارية)")
            if len(numeric_cols) >= 2:
                sel_vars = st.multiselect("اختر المتغيرات لتحليل العلاقة بينها:", numeric_cols, default=numeric_cols[:3])
                if len(sel_vars) >= 2:
                    try:
                        c_mat = df_encoded[sel_vars].corr(method='spearman')
                        st.dataframe(c_mat.style.background_gradient(cmap='coolwarm', axis=None, vmin=-1, vmax=1).format("{:.2f}"))
                        st.plotly_chart(px.imshow(c_mat, text_auto=".2f", aspect="auto", color_continuous_scale="coolwarm", zmin=-1, zmax=1), use_container_width=True)
                    except Exception:
                        st.error("تعذر قياس الارتباط.")
                    
        st.markdown("---")
        st.download_button("⬇️ تحميل البيانات كأرقام (CSV)", data=df_encoded.to_csv(index=False).encode('utf-8-sig'), file_name="SmartStat_Data.csv", mime="text/csv")

    except Exception as e:
        st.error(f"حدث خطأ في قراءة الملف: {e}")
