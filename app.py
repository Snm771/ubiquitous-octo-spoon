import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg

st.set_page_config(page_title="SmartStat Pro", page_icon="🧠", layout="wide")

# --- دالة التشفير الذكي (القاموس الشامل المحدث) ---
def encode_likert(df):
    likert_map = {
        # مقياس الموافقة
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1, "لا أوافق": 2, "لا أوافق بشدة": 1,
        # مقياس التكرار (للمشكلات السلوكية وغيرها)
        "دائما": 5, "دائماً": 5, "غالبا": 4, "غالباً": 4, "أحيانا": 3, "أحياناً": 3, "نادرا": 2, "نادراً": 2, "أبدا": 1, "أبداً": 1, "مطلقا": 1, "مطلقاً": 1,
        # مقياس الدرجة
        "بدرجة كبيرة جدا": 5, "بدرجة كبيرة جداً": 5, "بدرجة كبيرة": 4, "بدرجة متوسطة": 3, "بدرجة قليلة": 2, "بدرجة ضعيفة": 2, "بدرجة قليلة جدا": 1, "بدرجة ضعيفة جدا": 1,
        # مقياس ثنائي
        "نعم": 2, "لا": 1
    }
    
    df_cleaned = df.copy()
    df_cleaned = df_cleaned.replace(likert_map)
    for col in df_cleaned.columns:
        try:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col])
        except Exception:
            pass 
    return df_cleaned

st.title("🧠 SmartStat Pro - نظام التحليل الإحصائي الشامل")
st.markdown("---")

# ----------------- القائمة الجانبية (لوحة التحكم) -----------------
st.sidebar.title("⚙️ لوحة التحكم وإعداد المتغيرات")
st.sidebar.info("بعد رفع الملف، استخدم هذه اللوحة لتقسيم المتغيرات بشكل صحيح.")
# -----------------------------------------------------------------

uploaded_file = st.file_uploader("قم برفع ملف البيانات (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # قراءة ومعالجة البيانات
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        
        st.success("✅ تم قراءة البيانات بنجاح! راجع لوحة التحكم الجانبية لضبط المتغيرات.")
        
        # --- الذكاء الاصطناعي لاختيار المتغيرات (مع إعطاء المستخدم حق التعديل) ---
        all_cols = [c for c in df_encoded.columns if c != 'Timestamp']
        
        # تخمين مبدئي للبيانات النصية لتكون هي الديموغرافية افتراضياً
        guessed_categorical = [c for c in all_cols if df_encoded[c].dtype == 'object']
        
        # لوحة التحكم في الـ Sidebar
        st.sidebar.markdown("### 1️⃣ تحديد البيانات الديموغرافية")
        categorical_cols = st.sidebar.multiselect(
            "اختر المتغيرات الشخصية (مثل: الجنس، العمر، المستوى):", 
            all_cols, 
            default=guessed_categorical
        )
        
        # باقي الأعمدة التي لم تُختر كديموغرافية، ستصبح هي أسئلة الاستبيان
        numeric_cols = [c for c in all_cols if c not in categorical_cols]
        
        st.sidebar.markdown("### 2️⃣ مراجعة أسئلة الاستبيان")
        st.sidebar.success(f"تم تصنيف ({len(numeric_cols)}) عمود كأسئلة استبيان/متغيرات رقمية للتحليل.")

        # --- إنشاء التبويبات ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "👥 البيانات الديموغرافية", 
            "📊 الإحصاء الوصفي", 
            "🧪 الثبات (ألفا كرونباخ)", 
            "⚖️ الفروق (T-test/ANOVA)", 
            "🔗 الارتباط (Spearman)"
        ])

        # ==========================================
        # التبويب الأول: البيانات الديموغرافية
        with tab1:
            st.subheader("👥 تحليل البيانات الشخصية (التكرارات والنسب)")
            if categorical_cols:
                demo_col = st.selectbox("اختر المتغير الديموغرافي:", categorical_cols)
                counts = df_encoded[demo_col].value_counts()
                percentages = df_encoded[demo_col].value_counts(normalize=True) * 100
                demo_df = pd.DataFrame({'التكرار': counts, 'النسبة المئوية (%)': percentages.round(2)})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(demo_df, use_container_width=True)
                with col2:
                    fig = px.pie(demo_df, values='التكرار', names=demo_df.index, title=f"توزيع {demo_col}")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("لم تقم بتحديد أي بيانات ديموغرافية من القائمة الجانبية.")

        # ==========================================
        # التبويب الثاني: الإحصاء الوصفي
        with tab2:
            st.subheader("📊 الإحصاء الوصفي للمتغيرات الرقمية")
            if numeric_cols:
                # التأكد من تحويل أسئلة الاستبيان إلى أرقام قسرياً حتى لو كان فيها نصوص شاذة
                df_numeric_only = df_encoded[numeric_cols].apply(pd.to_numeric, errors='coerce')
                
                desc_df = df_numeric_only.describe().T
                desc_df = desc_df.rename(columns={
                    'count': 'العدد (التكرار)', 'mean': 'المتوسط الحسابي', 
                    'std': 'الانحراف المعياري', 'min': 'الحد الأدنى', 
                    '25%': 'الربع الأول', '50%': 'الوسيط', 
                    '75%': 'الربع الثالث', 'max': 'الحد الأقصى'
                })
                st.dataframe(desc_df[['العدد (التكرار)', 'المتوسط الحسابي', 'الانحراف المعياري', 'الحد الأدنى', 'الحد الأقصى']], use_container_width=True)
            else:
                st.warning("لم يتم العثور على أسئلة استبيان صالحة.")

        # ==========================================
        # التبويب الثالث: الثبات (ألفا كرونباخ)
        with tab3:
            st.subheader("🧪 قياس ثبات الاستبيان (Cronbach's Alpha)")
            if len(numeric_cols) > 1:
                try:
                    df_numeric_only = df_encoded[numeric_cols].apply(pd.to_numeric, errors='coerce')
                    alpha_tuple = pg.cronbach_alpha(data=df_numeric_only)
                    alpha_value = alpha_tuple[0]
                    st.metric(label="قيمة معامل ألفا كرونباخ", value=f"{alpha_value:.3f}")
                    
                    if alpha_value >= 0.60:
                        st.success("✅ القيمة ممتازة ومقبولة إحصائياً.")
                    else:
                        st.error("⚠️ القيمة ضعيفة.")
                except Exception:
                    st.warning("⚠️ لا يمكن حساب معامل الثبات لهذه البيانات.")

        # ==========================================
        # التبويب الرابع: اختبار الفروق (T-test و ANOVA) مع الحماية
        with tab4:
            st.subheader("⚖️ اختبار الفروق الإحصائية وحجم الأثر")
            if categorical_cols and numeric_cols:
                group_col = st.selectbox("اختر المتغير المستقل (مثال: الجنس، المؤهل):", categorical_cols, key="diff_group")
                test_col = st.selectbox("اختر المتغير التابع (السؤال المراد قياسه):", numeric_cols, key="diff_test")
                
                # تحويل المتغير التابع إلى رقمي للتأكد
                clean_data = df_encoded[[group_col, test_col]].dropna()
                clean_data[test_col] = pd.to_numeric(clean_data[test_col], errors='coerce')
                clean_data = clean_data.dropna()
                
                groups = clean_data[group_col].unique()
                
                try:
                    if len(groups) == 2:
                        st.markdown(f"**نوع الاختبار الذكي:** `T-test`")
                        group1 = clean_data[clean_data[group_col] == groups[0]][test_col]
                        group2 = clean_data[clean_data[group_col] == groups[1]][test_col]
                        
                        if len(group1) < 2 or len(group2) < 2:
                            st.warning("⚠️ عدد الأفراد غير كافٍ في إحدى المجموعات.")
                        else:
                            res = pg.ttest(group1, group2)
                            st.dataframe(res)
                            p_val = res['p-val'].values[0] if 'p-val' in res.columns else 1.0
                            eff_size = res['cohen-d'].values[0] if 'cohen-d' in res.columns else 0.0
                            
                            if p_val < 0.05:
                                st.success(f"توجد فروق ذات دلالة إحصائية. حجم الأثر هو **{eff_size:.2f}**.")
                            else:
                                st.warning(f"لا توجد فروق ذات دلالة إحصائية.")
                                
                            fig2 = px.box(clean_data, x=group_col, y=test_col, color=group_col)
                            st.plotly_chart(fig2)

                    elif len(groups) > 2:
                        st.markdown(f"**نوع الاختبار الذكي:** `ANOVA`")
                        res = pg.anova(data=clean_data, dv=test_col, between=group_col)
                        st.dataframe(res)
                        p_val = res['p-unc'].values[0] if 'p-unc' in res.columns else 1.0
                        
                        if p_val < 0.05:
                            st.success("توجد فروق ذات دلالة إحصائية بين المجموعات.")
                        else:
                            st.warning("لا توجد فروق ذات دلالة إحصائية.")
                            
                        fig3 = px.box(clean_data, x=group_col, y=test_col, color=group_col)
                        st.plotly_chart(fig3)
                except Exception:
                    st.error("⚠️ تعذر إجراء الاختبار الإحصائي.")

        # ==========================================
        # التبويب الخامس: الارتباط المتعدد (Spearman)
        with tab5:
            st.subheader("🔗 قياس الارتباط (مصفوفة الارتباط والخريطة الحرارية)")
            if len(numeric_cols) >= 2:
                selected_vars = st.multiselect("اختر المتغيرات:", numeric_cols, default=numeric_cols[:2])
                
                if len(selected_vars) >= 2:
                    try:
                        df_corr_data = df_encoded[selected_vars].apply(pd.to_numeric, errors='coerce')
                        corr_matrix = df_corr_data.corr(method='spearman')
                        
                        st.markdown("### 📊 مصفوفة الارتباط (جدول)")
                        st.dataframe(corr_matrix.style.background_gradient(cmap='RdBu', axis=None, vmin=-1, vmax=1).format("{:.2f}"), use_container_width=True)
                        
                        st.markdown("### 🗺️ الخريطة الحرارية (Heatmap)")
                        fig4 = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu", zmin=-1, zmax=1)
                        st.plotly_chart(fig4, use_container_width=True)
                    except Exception:
                        st.error("⚠️ تعذر قياس الارتباط.")
                else:
                    st.warning("يرجى اختيار متغيرين على الأقل.")
    except Exception as e:
        st.error(f"حدث خطأ غير متوقع أثناء القراءة: {e}")
