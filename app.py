import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg

st.set_page_config(page_title="SmartStat Pro | النسخة الأكاديمية", page_icon="🎓", layout="wide")

# --- دالة التشفير الذكي (القاموس الشامل لمنع اختفاء الإحصائيات) ---
def encode_likert(df):
    likert_map = {
        # مقياس الموافقة
        "موافق بشدة": 5, "موافق": 4, "متوسط": 3, "محايد": 3, "غير موافق": 2, "غير موافق بشدة": 1, "لا أوافق": 2, "لا أوافق بشدة": 1,
        # مقياس الرضا
        "راض جدا": 5, "راض جداً": 5, "راض": 4, "غير راض": 2, "غير راض جدا": 1, "غير راض جداً": 1,
        # مقياس التكرار
        "دائما": 5, "دائماً": 5, "غالبا": 4, "غالباً": 4, "أحيانا": 3, "أحياناً": 3, "نادرا": 2, "نادراً": 2, "أبدا": 1, "أبداً": 1, "مطلقا": 1, "مطلقاً": 1,
        # مقياس الدرجة
        "بدرجة كبيرة جدا": 5, "بدرجة كبيرة جداً": 5, "بدرجة كبيرة": 4, "بدرجة متوسطة": 3, "بدرجة قليلة": 2, "بدرجة ضعيفة": 2, "بدرجة قليلة جدا": 1, "بدرجة ضعيفة جدا": 1,
        # مقياس ثنائي
        "نعم": 2, "لا": 1
    }
    
    df_cleaned = df.copy()
    # تنظيف المسافات الزائدة
    df_cleaned = df_cleaned.map(lambda x: x.strip() if isinstance(x, str) else x)
    df_cleaned = df_cleaned.replace(likert_map)
    
    # إجبار تحويل الأسئلة إلى أرقام
    for col in df_cleaned.columns:
        if col != 'Timestamp':
            try:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except ValueError:
                pass 
    return df_cleaned

st.title("🎓 SmartStat Pro - المحلل الإحصائي الأكاديمي الشامل")
st.markdown("---")

uploaded_file = st.file_uploader("قم برفع ملف البيانات (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # قراءة البيانات
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        
        # فصل المتغيرات تلقائياً
        numeric_cols = [c for c in df_encoded.select_dtypes(include=['number']).columns if c != 'Timestamp']
        categorical_cols = [c for c in df_encoded.select_dtypes(exclude=['number']).columns if c != 'Timestamp']

        st.success("✅ تم قراءة البيانات بنجاح! جميع الاختبارات جاهزة في التبويبات بالأسفل.")
        
        # --- إنشاء التبويبات ---
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "👥 البيانات الديموغرافية", 
            "📊 الإحصاء الوصفي", 
            "🧪 الثبات (ألفا كرونباخ)", 
            "⚖️ الفروق (T-test/ANOVA)", 
            "🔗 الارتباط (Pearson/Spearman)",
            "📈 الانحدار والتأثير (Regression)"
        ])

        # ==========================================
        # التبويب الأول: الديموغرافيا
        with tab1:
            st.subheader("👥 تحليل البيانات الشخصية والديموغرافية")
            if categorical_cols:
                demo_col = st.selectbox("اختر المتغير الديموغرافي:", categorical_cols)
                counts = df_encoded[demo_col].value_counts()
                percentages = df_encoded[demo_col].value_counts(normalize=True) * 100
                demo_df = pd.DataFrame({'العدد (التكرار)': counts, 'النسبة المئوية (%)': percentages.round(2)})
                
                col1, col2 = st.columns(2)
                with col1: st.dataframe(demo_df, use_container_width=True)
                with col2:
                    fig = px.pie(demo_df, values='العدد (التكرار)', names=demo_df.index, title=f"توزيع {demo_col}")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("لا توجد بيانات شخصية في الملف.")

        # ==========================================
        # التبويب الثاني: الإحصاء الوصفي
        with tab2:
            st.subheader("📊 الإحصاء الوصفي (المتوسطات والانحرافات)")
            if numeric_cols:
                desc_df = df_encoded[numeric_cols].describe().T
                desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط الحسابي', 'std': 'الانحراف المعياري', 'min': 'الحد الأدنى', 'max': 'الحد الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط الحسابي', 'الانحراف المعياري', 'الحد الأدنى', 'الحد الأقصى']], use_container_width=True)
                st.info("💡 **تلميح:** إذا كان المتوسط قريباً من 5، يعني أن الإجابات تميل بشدة للموافقة أو التكرار الدائم.")
            else:
                st.error("لم يتم التعرف على أسئلة مرقمة.")

        # ==========================================
        # التبويب الثالث: الثبات
        with tab3:
            st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
            if len(numeric_cols) > 1:
                try:
                    alpha_data = df_encoded[numeric_cols].dropna()
                    alpha_tuple = pg.cronbach_alpha(data=alpha_data)
                    alpha_val = alpha_tuple[0]
                    st.metric(label="قيمة ألفا كرونباخ", value=f"{alpha_val:.3f}")
                    if alpha_val >= 0.60: st.success("✅ الأداة (الاستبيان) تتمتع بثبات عالٍ ومقبول علمياً.")
                    else: st.warning("⚠️ درجة الثبات ضعيفة.")
                except Exception:
                    st.error("تعذر حساب الثبات لهذه البيانات.")

        # ==========================================
        # التبويب الرابع: الفروق (جميع الأسئلة في جدول واحد)
        with tab4:
            st.subheader("⚖️ اختبار الفروق وحجم الأثر (لجميع الأسئلة دفعة واحدة)")
            st.markdown("سيقوم التطبيق باختبار **جميع الأسئلة** معاً وإظهار النتيجة في جدول ملخص.")
            
            if categorical_cols and numeric_cols:
                group_col = st.selectbox("اختر المتغير المستقل (الذي تريد المقارنة بناءً عليه):", categorical_cols, key="dif_g")
                
                clean_for_groups = df_encoded.dropna(subset=[group_col])
                groups = clean_for_groups[group_col].unique()
                
                test_type = "T-test" if len(groups) == 2 else ("ANOVA" if len(groups) > 2 else "None")
                
                if test_type != "None":
                    st.info(f"نوع الاختبار المستخدم تلقائياً: **{test_type}** (لأن '{group_col}' يحتوي على {len(groups)} فئات).")
                    
                    results = []
                    
                    # حلقة تمر على جميع الأسئلة وتحسب لها T-test أو ANOVA
                    for col in numeric_cols:
                        clean_data = df_encoded[[group_col, col]].dropna()
                        grps = clean_data[group_col].unique()
                        
                        try:
                            if len(grps) == 2 and test_type == "T-test":
                                g1 = clean_data[clean_data[group_col] == grps[0]][col]
                                g2 = clean_data[clean_data[group_col] == grps[1]][col]
                                if len(g1) > 1 and len(g2) > 1:
                                    res = pg.ttest(g1, g2)
                                    pval = res['p-val'].values[0] if 'p-val' in res.columns else 1.0
                                    eff = res['cohen-d'].values[0] if 'cohen-d' in res.columns else 0.0
                                    sig = "دالة (يوجد فرق)" if pval < 0.05 else "غير دالة"
                                    results.append({"السؤال / المتغير": col, "P-value": round(pval, 3), "الدلالة": sig, "حجم الأثر": round(eff, 3)})
                                    
                            elif len(grps) > 2 and test_type == "ANOVA":
                                res = pg.anova(data=clean_data, dv=col, between=group_col)
                                pval = res['p-unc'].values[0] if 'p-unc' in res.columns else 1.0
                                eff = res['np2'].values[0] if 'np2' in res.columns else 0.0
                                sig = "دالة (يوجد فرق)" if pval < 0.05 else "غير دالة"
                                results.append({"السؤال / المتغير": col, "P-value": round(pval, 3), "الدلالة": sig, "حجم الأثر": round(eff, 3)})
                        except Exception:
                            pass 
                    
                    if results:
                        res_df = pd.DataFrame(results)
                        
                        # تلوين السطر الذي فيه فروق باللون الأخضر الفاتح
                        def highlight_sig(val):
                            return 'background-color: #d4edda' if val == 'دالة (يوجد فرق)' else ''
                        
                        st.dataframe(res_df.style.map(highlight_sig, subset=['الدلالة']), use_container_width=True)
                        
                        # رسم بياني اختياري
                        st.markdown("### 📊 رسم بياني تفصيلي:")
                        plot_col = st.selectbox("اختر سؤالاً من الجدول أعلاه لعرض رسمته:", res_df["السؤال / المتغير"].tolist())
                        if plot_col:
                            fig2 = px.box(df_encoded.dropna(subset=[group_col, plot_col]), x=group_col, y=plot_col, color=group_col)
                            st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.warning("تعذر حساب الفروق. تأكد من صحة البيانات.")
                else:
                    st.error("المتغير المستقل يجب أن يحتوي على مجموعتين على الأقل.")

        # ==========================================
        # التبويب الخامس: الارتباط (Pearson & Spearman)
        with tab5:
            st.subheader("🔗 قياس الارتباط (Pearson & Spearman)")
            st.markdown("في هذا القسم نعرض نوعين من الارتباط لتختار الأنسب لدراستك.")
            if len(numeric_cols) >= 2:
                v1 = st.selectbox("المتغير الأول (X):", numeric_cols, key="c1")
                v2 = st.selectbox("المتغير الثاني (Y):", numeric_cols, key="c2")
                
                if v1 != v2:
                    col_p, col_s = st.columns(2)
                    # --- بيرسون ---
                    with col_p:
                        st.markdown("#### 1️⃣ معامل بيرسون (Pearson)")
                        st.caption("يُستخدم للبيانات الكمية الموزعة طبيعياً.")
                        try:
                            res_p = pg.corr(df_encoded[v1], df_encoded[v2], method='pearson')
                            st.dataframe(res_p[['n', 'r', 'p-val']])
                            if res_p['p-val'].values[0] < 0.05: st.success(f"ارتباط دال إحصائياً. قوة العلاقة: {res_p['r'].values[0]:.2f}")
                            else: st.warning("لا يوجد ارتباط دال.")
                        except: st.error("تعذر الحساب.")
                    # --- سبيرمان ---
                    with col_s:
                        st.markdown("#### 2️⃣ معامل سبيرمان (Spearman)")
                        st.caption("يُستخدم للبيانات الرتبية (مثل مقياس ليكرت).")
                        try:
                            res_s = pg.corr(df_encoded[v1], df_encoded[v2], method='spearman')
                            st.dataframe(res_s[['n', 'r', 'p-val']])
                            if res_s['p-val'].values[0] < 0.05: st.success(f"ارتباط دال إحصائياً. قوة العلاقة: {res_s['r'].values[0]:.2f}")
                            else: st.warning("لا يوجد ارتباط دال.")
                        except: st.error("تعذر الحساب.")
                        
                    st.plotly_chart(px.scatter(df_encoded, x=v1, y=v2, trendline="ols"), use_container_width=True)

        # ==========================================
        # التبويب السادس: الانحدار والتأثير
        with tab6:
            st.subheader("📈 تحليل الانحدار والتنبؤ (Regression)")
            st.markdown("يقيس هذا الاختبار تأثير متغير مستقل أو أكثر (X) على متغير تابع (Y) لمعرفة مدى مساهمتها في النتيجة.")
            
            if len(numeric_cols) >= 2:
                dep_var = st.selectbox("اختر المتغير التابع (النتيجة المراد التأثير عليها / Y):", numeric_cols, key='reg_y')
                indep_vars = st.multiselect("اختر المتغيرات المستقلة (المؤثرات / X):", [c for c in numeric_cols if c != dep_var], key='reg_x')
                
                if indep_vars:
                    reg_data = df_encoded[[dep_var] + indep_vars].dropna()
                    if len(reg_data) > 2:
                        if len(indep_vars) == 1:
                            st.markdown("**نوع الاختبار:** `انحدار خطي بسيط (Simple Linear Regression)`")
                        else:
                            st.markdown("**نوع الاختبار:** `انحدار خطي متعدد (Multiple Linear Regression)`")
                        
                        try:
                            # حساب الانحدار
                            lm = pg.linear_regression(reg_data[indep_vars], reg_data[dep_var])
                            
                            # عرض النتيجة بخانة واضحة
                            st.dataframe(lm)
                            
                            r2 = lm['r2'].values[0] if 'r2' in lm.columns else 0
                            
                            st.info(f"💡 **تفسير حجم الأثر وقوة النموذج:** \nقيمة معامل التحديد (R²) هي **{r2:.3f}**. \nهذا يعني أن المتغيرات المستقلة التي اخترتها تُفسر وتتحكم بنسبة **({float(r2)*100:.1f}%)** من التغير الذي يحدث في المتغير التابع.")
                            
                        except Exception as e:
                            st.error(f"تعذر حساب الانحدار: {e}")
                    else:
                        st.warning("حجم العينة صغير جداً بعد استبعاد الإجابات المفقودة.")
                else:
                    st.info("يرجى اختيار متغير مستقل (مؤثر) واحد على الأقل لتشغيل الانحدار.")

    except Exception as e:
        st.error(f"حدث خطأ في القراءة: {e}")
