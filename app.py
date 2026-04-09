import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg

st.set_page_config(page_title="SmartStat Pro", page_icon="🧠", layout="wide")

# --- دالة التشفير الذكي ---
def encode_likert(df):
    likert_map = {"موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1, "لا أوافق": 2, "لا أوافق بشدة": 1}
    df_cleaned = df.copy()
    df_cleaned = df_cleaned.replace(likert_map)
    for col in df_cleaned.columns:
        try:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col])
        except Exception:
            pass # ترك البيانات الديموغرافية (نصوص) كما هي
    return df_cleaned

st.title("🧠 SmartStat Pro - نظام التحليل الإحصائي الشامل")
st.markdown("---")

uploaded_file = st.file_uploader("قم برفع ملف البيانات (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # قراءة ومعالجة البيانات
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    df_encoded = encode_likert(df)
    
    # فصل المتغيرات (رقمية للاستبيان، ونصية للديموغرافيا)
    numeric_cols = [c for c in df_encoded.select_dtypes(include=['number']).columns if c != 'Timestamp']
    categorical_cols = [c for c in df_encoded.select_dtypes(exclude=['number']).columns if c != 'Timestamp']

    st.success("✅ تم معالجة البيانات بنجاح! اختر نوع التحليل من التبويبات بالأسفل:")
    
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
            st.warning("لا توجد بيانات نصية/ديموغرافية في الملف.")

    # ==========================================
    # التبويب الثاني: الإحصاء الوصفي
    with tab2:
        st.subheader("📊 الإحصاء الوصفي للمتغيرات الرقمية")
        if numeric_cols:
            desc_df = df_encoded[numeric_cols].describe().T
            desc_df = desc_df.rename(columns={
                'count': 'العدد (التكرار)', 'mean': 'المتوسط الحسابي', 
                'std': 'الانحراف المعياري', 'min': 'الحد الأدنى', 
                '25%': 'الربع الأول', '50%': 'الوسيط', 
                '75%': 'الربع الثالث', 'max': 'الحد الأقصى'
            })
            st.dataframe(desc_df[['العدد (التكرار)', 'المتوسط الحسابي', 'الانحراف المعياري', 'الحد الأدنى', 'الحد الأقصى']], use_container_width=True)
            st.info("💡 **تفسير:** المتوسط الحسابي يقيس متوسط إجابات العينة، بينما الانحراف المعياري يقيس مدى تشتت واختلاف الإجابات عن هذا المتوسط.")

    # ==========================================
    # التبويب الثالث: الثبات (ألفا كرونباخ)
    with tab3:
        st.subheader("🧪 قياس ثبات الاستبيان (Cronbach's Alpha)")
        if len(numeric_cols) > 1:
            try:
                alpha_tuple = pg.cronbach_alpha(data=df_encoded[numeric_cols])
                alpha_value = alpha_tuple[0]
                st.metric(label="قيمة معامل ألفا كرونباخ", value=f"{alpha_value:.3f}")
                
                if alpha_value >= 0.60:
                    st.success("✅ **تفسير النتيجة:** القيمة ممتازة (أكبر من 0.60). هذا يعني أن الاستبيان يتمتع بدرجة ثبات وموثوقية عالية، ويمكن الاعتماد على نتائجه.")
                else:
                    st.error("⚠️ **تفسير النتيجة:** القيمة ضعيفة (أقل من 0.60). قد يحتاج الاستبيان إلى تعديل أو مراجعة بعض الأسئلة.")
            except Exception:
                st.warning("⚠️ لا يمكن حساب معامل الثبات لهذه البيانات (قد تكون متطابقة تماماً أو تحتوي على قيم مفقودة كثيرة).")

    # ==========================================
    # التبويب الرابع: اختبار الفروق (T-test و ANOVA) مع الحماية
    with tab4:
        st.subheader("⚖️ اختبار الفروق الإحصائية وحجم الأثر")
        if categorical_cols and numeric_cols:
            group_col = st.selectbox("اختر المتغير المستقل (مثال: الجنس، المؤهل):", categorical_cols, key="diff_group")
            test_col = st.selectbox("اختر المتغير التابع (السؤال المراد قياسه):", numeric_cols, key="diff_test")
            
            clean_data = df_encoded[[group_col, test_col]].dropna()
            groups = clean_data[group_col].unique()
            
            try:
                if len(groups) == 2:
                    st.markdown(f"**نوع الاختبار الذكي:** `T-test`")
                    group1 = clean_data[clean_data[group_col] == groups[0]][test_col]
                    group2 = clean_data[clean_data[group_col] == groups[1]][test_col]
                    
                    if len(group1) < 2 or len(group2) < 2:
                        st.warning("⚠️ لا يمكن إجراء الاختبار: إحدى المجموعات لا تحتوي على عدد كافٍ من الأفراد.")
                    else:
                        res = pg.ttest(group1, group2)
                        st.dataframe(res)
                        
                        # سحب القيمة وحجم الأثر بأمان
                        p_val = res['p-val'].values[0] if 'p-val' in res.columns else 1.0
                        eff_size = res['cohen-d'].values[0] if 'cohen-d' in res.columns else 0.0
                        
                        st.markdown("### 📝 التفسير الآلي:")
                        if p_val < 0.05:
                            st.success(f"توجد فروق ذات دلالة إحصائية. حجم الأثر (Effect Size - Cohen's d) هو **{eff_size:.2f}**.")
                        else:
                            st.warning(f"لا توجد فروق ذات دلالة إحصائية. الإجابات متقاربة.")
                            
                        fig2 = px.box(clean_data, x=group_col, y=test_col, color=group_col, title=f"مقارنة حسب {group_col}")
                        st.plotly_chart(fig2)

                elif len(groups) > 2:
                    st.markdown(f"**نوع الاختبار الذكي:** `ANOVA`")
                    res = pg.anova(data=clean_data, dv=test_col, between=group_col)
                    st.dataframe(res)
                    
                    p_val = res['p-unc'].values[0] if 'p-unc' in res.columns else 1.0
                    
                    if p_val < 0.05:
                        st.success("توجد فروق ذات دلالة إحصائية بين المجموعات.")
                    else:
                        st.warning("لا توجد فروق ذات دلالة إحصائية بين المجموعات.")
                        
                    fig3 = px.box(clean_data, x=group_col, y=test_col, color=group_col)
                    st.plotly_chart(fig3)
                else:
                    st.info("لا توجد مجموعات كافية لإجراء الاختبار.")
            except Exception as e:
                st.error("⚠️ تعذر إجراء الاختبار الإحصائي لهذه المتغيرات. (السبب: البيانات غير كافية أو التباين صفر).")

    # ==========================================
    # التبويب الخامس: الارتباط (Spearman) مع الحماية
    with tab5:
        st.subheader("🔗 قياس الارتباط (Spearman Correlation)")
        
        if len(numeric_cols) >= 2:
            var1 = st.selectbox("المتغير الأول:", numeric_cols, key="corr1")
            var2 = st.selectbox("المتغير الثاني:", numeric_cols, key="corr2")
            
            if var1 != var2:
                try:
                    corr_res = pg.corr(df_encoded[var1], df_encoded[var2], method='spearman')
                    st.dataframe(corr_res)
                    
                    r_val = corr_res['r'].values[0] if 'r' in corr_res.columns else 0.0
                    p_val = corr_res['p-val'].values[0] if 'p-val' in corr_res.columns else 1.0
                    
                    direction = "طردية (كلما زاد الأول زاد الثاني)" if r_val > 0 else "عكسية (كلما زاد الأول نقص الثاني)"
                    
                    st.markdown("### 📝 التفسير الآلي:")
                    if p_val < 0.05:
                        st.success(f"✅ توجد علاقة ارتباط ذات دلالة إحصائية. نوع العلاقة: **{direction}** بقوة ({r_val:.2f}).")
                    else:
                        st.warning("⚠️ لا توجد علاقة ارتباط حقيقية بين المتغيرين (العلاقة معدومة أو غير دالة).")
                        
                    fig4 = px.scatter(df_encoded, x=var1, y=var2, trendline="ols")
                    st.plotly_chart(fig4)
                except Exception:
                    st.error("⚠️ تعذر قياس الارتباط لهذه المتغيرات (تأكد من عدم تطابق جميع الإجابات).")