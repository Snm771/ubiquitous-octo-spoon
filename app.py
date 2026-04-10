import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

st.set_page_config(page_title="SmartStat Pro | الأكاديمية", page_icon="🎓", layout="wide")

# ==========================================
# 1. دالة ترميز ليكرت الصحيحة (حسب تحليل الخبير)
# ==========================================
def encode_likert(df):
    """ترميز إجابات ليكرت من نصي إلى رقمي حسب مقياس الخبير"""
    likert_map = {
        "راض جداً": 5, "راض جدا": 5,
        "راض": 4,
        "محايد": 3,
        "غير راض": 2,
        "غير راض جداً": 1, "غير راض جدا": 1
    }
    
    df_cleaned = df.copy()
    
    # تنظيف النصوص من المسافات الزائدة
    for col in df_cleaned.columns:
        df_cleaned[col] = df_cleaned[col].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )
    
    # استبدال القيم النصية بالرقمية
    df_cleaned = df_cleaned.replace(likert_map)
    
    # تحويل الأعمدة إلى رقمي حيثما أمكن
    for col in df_cleaned.columns:
        if col not in ['Timestamp', 'النوع', 'العمر']:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    
    return df_cleaned

# ==========================================
# 2. دالة حساب ألفا كرونباخ
# ==========================================
def calculate_cronbach_alpha(df, columns):
    """حساب معامل ألفا كرونباخ لمجموعة أعمدة"""
    try:
        data = df[columns].dropna()
        if len(data) > 1 and len(columns) > 1:
            alpha = pg.cronbach_alpha(data=data)[0]
            return round(alpha, 3)
    except:
        return None
    return None

# ==========================================
# 3. دالة حساب الإحصاء الوصفي المفصل
# ==========================================
def descriptive_stats(df, columns):
    """حساب المتوسط، الانحراف، الوزن النسبي لكل فقرة"""
    stats = []
    for col in columns:
        data = df[col].dropna()
        if len(data) > 0:
            mean_val = data.mean()
            std_val = data.std()
            # الوزن النسبي = (المتوسط / أعلى قيمة في المقياس) × 100
            relative_weight = (mean_val / 5) * 100
            stats.append({
                'الفقرة': col,
                'المتوسط': round(mean_val, 2),
                'الانحراف المعياري': round(std_val, 2),
                'الوزن النسبي (%)': round(relative_weight, 2)
            })
    return pd.DataFrame(stats)

# ==========================================
# 4. دالة إجراء T-test مع تنسيق النتائج
# ==========================================
def run_ttest(df, group_col, test_col, group1, group2):
    """إجراء اختبار T-test وتنسيق النتائج"""
    try:
        data1 = df[df[group_col] == group1][test_col].dropna()
        data2 = df[df[group_col] == group2][test_col].dropna()
        
        if len(data1) > 1 and len(data2) > 1:
            result = pg.ttest(data1, data2, correction='auto')
            
            p_val = result['p-val'].values[0]
            t_val = result['T'].values[0]
            cohen_d = result['cohen-d'].values[0] if 'cohen-d' in result.columns else 0
            
            significance = "✅ معنوي" if p_val < 0.05 else "❌ غير معنوي"
            
            return {
                'المتوسط 1': round(data1.mean(), 3),
                'المتوسط 2': round(data2.mean(), 3),
                'التباين 1': round(data1.var(), 3),
                'التباين 2': round(data2.var(), 3),
                'عدد 1': len(data1),
                'عدد 2': len(data2),
                'قيمة t': round(t_val, 3),
                'قيمة p': round(p_val, 4),
                "Cohen's d": round(cohen_d, 3),
                'الدلالة': significance
            }
    except Exception as e:
        return {'خطأ': str(e)}
    return None

# ==========================================
# واجهة المستخدم الرئيسية
# ==========================================
st.title("🎓 SmartStat Pro - تحليل استبيان المشكلات السلوكية والمناخ الأسري")
st.markdown("---")

uploaded_file = st.file_uploader("📁 قم برفع ملف البيانات (Excel)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # قراءة البيانات
        df_raw = pd.read_excel(uploaded_file)
        
        # ترميز ليكرت
        df = encode_likert(df_raw)
        
        # تعريف أعمدة المحاور
        behavioral_cols = [f'A{i}' for i in range(1, 21)]  # A1 إلى A20
        family_cols = [f'B{i}' for i in range(1, 14)]       # B1 إلى B13
        
        # حساب المجاميع
        df['مجموع المشكلات السلوكية'] = df[behavioral_cols].sum(axis=1)
        df['مجموع المناخ الأسري'] = df[family_cols].sum(axis=1)
        df['المتوسط السلوكي'] = df[behavioral_cols].mean(axis=1)
        df['المتوسط الأسري'] = df[family_cols].mean(axis=1)
        
        st.success("✅ تم تحميل البيانات وترميزها بنجاح!")
        
        # القائمة الجانبية
        st.sidebar.title("⚙️ لوحة التحكم")
        
        # عرض معلومات العينة
        st.sidebar.subheader("👥 معلومات العينة")
        if 'النوع' in df.columns:
            gender_counts = df['النوع'].value_counts()
            for g, c in gender_counts.items():
                st.sidebar.metric(f"{g}", f"{c} ({c/len(df)*100:.1f}%)")
        
        if 'العمر' in df.columns:
            age_counts = df['العمر'].value_counts()
            for a, c in age_counts.items():
                st.sidebar.metric(f"{a}", f"{c} ({c/len(df)*100:.1f}%)")
        
        # التبويبات الرئيسية
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📋 الإحصاء الوصفي",
            "🧪 الثبات (ألفا)",
            "🔗 الارتباط",
            "⚖️ الفروق حسب الجنس",
            "👵 الفروق حسب العمر",
            "📥 تصدير النتائج"
        ])
        
        # ==========================================
        # التبويب 1: الإحصاء الوصفي
        # ==========================================
        with tab1:
            st.subheader("📊 الإحصاء الوصفي للمحاور")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🔴 محور المشكلات السلوكية (20 فقرة)")
                beh_stats = descriptive_stats(df, behavioral_cols)
                st.dataframe(beh_stats.style.format({
                    'المتوسط': '{:.2f}',
                    'الانحراف المعياري': '{:.2f}',
                    'الوزن النسبي (%)': '{:.2f}'
                }), use_container_width=True, height=400)
                
                # ملخص المحور
                beh_mean = df['المتوسط السلوكي'].mean()
                beh_std = df['المتوسط السلوكي'].std()
                st.info(f"""
                **ملخص المحور السلوكي:**
                - المتوسط العام: **{beh_mean:.2f}**
                - الانحراف المعياري: **{beh_std:.2f}**
                - الوزن النسبي: **{(beh_mean/5)*100:.1f}%**
                """)
            
            with col2:
                st.markdown("### 🟢 محور المناخ الأسري (13 فقرة)")
                fam_stats = descriptive_stats(df, family_cols)
                st.dataframe(fam_stats.style.format({
                    'المتوسط': '{:.2f}',
                    'الانحراف المعياري': '{:.2f}',
                    'الوزن النسبي (%)': '{:.2f}'
                }), use_container_width=True, height=400)
                
                # ملخص المحور
                fam_mean = df['المتوسط الأسري'].mean()
                fam_std = df['المتوسط الأسري'].std()
                st.success(f"""
                **ملخص محور المناخ الأسري:**
                - المتوسط العام: **{fam_mean:.2f}**
                - الانحراف المعياري: **{fam_std:.2f}**
                - الوزن النسبي: **{(fam_mean/5)*100:.1f}%**
                """)
        
        # ==========================================
        # التبويب 2: معامل الثبات
        # ==========================================
        with tab2:
            st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                alpha_beh = calculate_cronbach_alpha(df, behavioral_cols)
                st.metric("محور المشكلات السلوكية", f"{alpha_beh if alpha_beh else 'N/A'}")
                if alpha_beh and alpha_beh >= 0.70:
                    st.success("✅ ثبات ممتاز (≥ 0.70)")
                elif alpha_beh and alpha_beh >= 0.60:
                    st.warning("⚠️ ثبات مقبول (≥ 0.60)")
                else:
                    st.error("❌ ثبات ضعيف")
            
            with col2:
                alpha_fam = calculate_cronbach_alpha(df, family_cols)
                st.metric("محور المناخ الأسري", f"{alpha_fam if alpha_fam else 'N/A'}")
                if alpha_fam and alpha_fam >= 0.70:
                    st.success("✅ ثبات ممتاز (≥ 0.70)")
                elif alpha_fam and alpha_fam >= 0.60:
                    st.warning("⚠️ ثبات مقبول (≥ 0.60)")
                else:
                    st.error("❌ ثبات ضعيف")
            
            st.markdown("---")
            st.info("💡 المعيار المقبول لألفا كرونباخ في البحث العلمي هو ≥ 0.60، والممتاز ≥ 0.70")
        
        # ==========================================
        # التبويب 3: الارتباط
        # ==========================================
        with tab3:
            st.subheader("🔗 معامل الارتباط بين المحورين")
            
            # حساب بيرسون وسبيرمان
            clean_data = df[['مجموع المشكلات السلوكية', 'مجموع المناخ الأسري']].dropna()
            
            if len(clean_data) > 2:
                pearson = pg.corr(clean_data['مجموع المشكلات السلوكية'], 
                                clean_data['مجموع المناخ الأسري'], 
                                method='pearson')
                spearman = pg.corr(clean_data['مجموع المشكلات السلوكية'], 
                                 clean_data['مجموع المناخ الأسري'], 
                                 method='spearman')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### معامل بيرسون (العلاقة الخطية)")
                    st.dataframe(pearson[['n', 'r', 'p-val', 'CI95%']].style.format({
                        'r': '{:.3f}',
                        'p-val': '{:.4f}'
                    }))
                    
                    r_val = pearson['r'].values[0]
                    if abs(r_val) >= 0.7:
                        st.success("🔗 علاقة قوية")
                    elif abs(r_val) >= 0.4:
                        st.info("🔗 علاقة متوسطة")
                    else:
                        st.warning("🔗 علاقة ضعيفة")
                
                with col2:
                    st.markdown("#### معامل سبيرمان (العلاقة الرتبية)")
                    st.dataframe(spearman[['n', 'r', 'p-val', 'CI95%']].style.format({
                        'r': '{:.3f}',
                        'p-val': '{:.4f}'
                    }))
                
                # رسم scatter
                st.markdown("### 📈 مخطط التشتت")
                fig = px.scatter(
                    clean_data,
                    x='مجموع المشكلات السلوكية',
                    y='مجموع المناخ الأسري',
                    trendline='ols',
                    title='العلاقة بين المشكلات السلوكية والمناخ الأسري',
                    labels={'مجموع المشكلات السلوكية': 'مجموع المشكلات السلوكية',
                           'مجموع المناخ الأسري': 'مجموع المناخ الأسري'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # ==========================================
        # التبويب 4: الفروق حسب الجنس
        # ==========================================
        with tab4:
            st.subheader("⚖️ اختبار الفروق حسب الجنس (ذكر ♂️ / أنثى ♀️)")
            
            if 'النوع' in df.columns and df['النوع'].nunique() >= 2:
                genders = df['النوع'].dropna().unique()
                st.info(f"الفئات: {', '.join(map(str, genders))}")
                
                # اختيار المتغير للتحليل
                test_var = st.radio(
                    "اختر المتغير للتحليل:",
                    ['مجموع المشكلات السلوكية', 'مجموع المناخ الأسري', 'المتوسط السلوكي', 'المتوسط الأسري'],
                    key='gender_test_var'
                )
                
                if len(genders) == 2:
                    result = run_ttest(df, 'النوع', test_var, genders[0], genders[1])
                    
                    if result and 'خطأ' not in result:
                        # عرض النتائج في جدول منسق
                        st.markdown("### 📋 نتائج اختبار T-test")
                        
                        result_df = pd.DataFrame([result])
                        st.dataframe(
                            result_df.style.applymap(
                                lambda x: 'background-color: #90EE90' if x == '✅ معنوي' else '',
                                subset=['الدلالة']
                            ).applymap(
                                lambda x: 'background-color: #FFB6C1' if x == '❌ غير معنوي' else '',
                                subset=['الدلالة']
                            ),
                            use_container_width=True
                        )
                        
                        # تفسير النتائج
                        st.markdown("### 📝 تفسير النتائج")
                        if result['قيمة p'] < 0.05:
                            st.success(f"""
                            ✅ **توجد فروق ذات دلالة إحصائية** عند مستوى دلالة 0.05
                            - قيمة t: **{result['قيمة t']}**
                            - قيمة p: **{result['قيمة p']}**
                            - حجم الأثر (Cohen's d): **{result["Cohen's d"]}**
                            """)
                        else:
                            st.info(f"""
                            ❌ **لا توجد فروق ذات دلالة إحصائية** عند مستوى دلالة 0.05
                            - قيمة t: **{result['قيمة t']}**
                            - قيمة p: **{result['قيمة p']}** (أكبر من 0.05)
                            - حجم الأثر (Cohen's d): **{result["Cohen's d"]}**
                            """)
                        
                        # رسم صندوقي
                        st.markdown("### 📊 التوزيع البياني")
                        fig = px.box(
                            df,
                            x='النوع',
                            y=test_var,
                            color='النوع',
                            points='all',
                            title=f'توزيع {test_var} حسب الجنس',
                            labels={'النوع': 'الجنس', test_var: test_var}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # جدول مقارنة مفصل (مثل تحليل الخبير)
                        st.markdown("### 📋 جدول المقارنة التفصيلي")
                        comp_data = []
                        for g in genders:
                            g_data = df[df['النوع'] == g][test_var].dropna()
                            comp_data.append({
                                'الفئة': g,
                                'العدد': len(g_data),
                                'المتوسط': f"{g_data.mean():.3f}",
                                'الانحراف': f"{g_data.std():.3f}",
                                'التباين': f"{g_data.var():.3f}",
                                'الحد الأدنى': int(g_data.min()),
                                'الحد الأقصى': int(g_data.max())
                            })
                        st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
            
            else:
                st.warning("⚠️ تأكد من وجود عمود 'النوع' وبه فئتين على الأقل")
        
        # ==========================================
        # التبويب 5: الفروق حسب العمر
        # ==========================================
        with tab5:
            st.subheader("👵 اختبار الفروق حسب الفئة العمرية")
            
            if 'العمر' in df.columns and df['العمر'].nunique() >= 2:
                ages = df['العمر'].dropna().unique()
                st.info(f"الفئات العمرية: {', '.join(map(str, ages))}")
                
                test_var = st.radio(
                    "اختر المتغير للتحليل:",
                    ['مجموع المشكلات السلوكية', 'مجموع المناخ الأسري', 'المتوسط السلوكي', 'المتوسط الأسري'],
                    key='age_test_var'
                )
                
                if len(ages) == 2:
                    result = run_ttest(df, 'العمر', test_var, ages[0], ages[1])
                    
                    if result and 'خطأ' not in result:
                        st.markdown("### 📋 نتائج اختبار T-test")
                        result_df = pd.DataFrame([result])
                        st.dataframe(
                            result_df.style.applymap(
                                lambda x: 'background-color: #90EE90' if x == '✅ معنوي' else '',
                                subset=['الدلالة']
                            ),
                            use_container_width=True
                        )
                        
                        st.markdown("### 📝 تفسير النتائج")
                        if result['قيمة p'] < 0.05:
                            st.success(f"""
                            ✅ **توجد فروق ذات دلالة إحصائية** بين الفئتين العمرية
                            - قيمة t: **{result['قيمة t']}** | قيمة p: **{result['قيمة p']}**
                            """)
                        else:
                            st.info(f"""
                            ❌ **لا توجد فروق ذات دلالة إحصائية** بين الفئتين العمرية
                            - قيمة p: **{result['قيمة p']}** (≥ 0.05)
                            """)
                        
                        # رسم
                        fig = px.box(
                            df,
                            x='العمر',
                            y=test_var,
                            color='العمر',
                            points='all',
                            title=f'توزيع {test_var} حسب الفئة العمرية'
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ تأكد من وجود عمود 'العمر' وبه فئتين على الأقل")
        
        # ==========================================
        # التبويب 6: تصدير النتائج
        # ==========================================
        with tab6:
            st.subheader("📥 تصدير نتائج التحليل")
            
            # تحضير بيانات التصدير
            export_data = {
                'معلومات العينة': {
                    'إجمالي العينة': len(df),
                    'عدد الذكور': len(df[df['النوع']=='ذكر']) if 'النوع' in df.columns else 0,
                    'عدد الإناث': len(df[df['النوع']=='أنثى']) if 'النوع' in df.columns else 0,
                },
                'معاملات الثبات': {
                    'ألفا - المشكلات السلوكية': calculate_cronbach_alpha(df, behavioral_cols),
                    'ألفا - المناخ الأسري': calculate_cronbach_alpha(df, family_cols),
                },
                'المتوسطات العامة': {
                    'متوسط المشكلات السلوكية': round(df['المتوسط السلوكي'].mean(), 3),
                    'متوسط المناخ الأسري': round(df['المتوسط الأسري'].mean(), 3),
                }
            }
            
            # عرض ملخص
            for section, data in export_data.items():
                st.markdown(f"#### {section}")
                for k, v in data.items():
                    st.write(f"- **{k}**: {v}")
            
            # زر تحميل
            summary_df = pd.DataFrame({
                'المؤشر': list(export_data['معلومات العينة'].keys()) + 
                         list(export_data['معاملات الثبات'].keys()) +
                         list(export_data['المتوسطات العامة'].keys()),
                'القيمة': list(export_data['معلومات العينة'].values()) + 
                         list(export_data['معاملات الثبات'].values()) +
                         list(export_data['المتوسطات العامة'].values())
            })
            
            csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 تحميل ملخص النتائج (CSV)",
                data=csv,
                file_name='نتائج_التحليل_الإحصائي.csv',
                mime='text/csv'
            )
            
            # تحميل البيانات المحللة
            df_export = df.copy()
            csv_full = df_export.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 تحميل البيانات مع المجاميع (CSV)",
                data=csv_full,
                file_name='البيانات_المحللة_كاملة.csv',
                mime='text/csv'
            )
    
    except Exception as e:
        st.error(f"❌ حدث خطأ: {e}")
        import traceback
        with st.expander("عرض تفاصيل الخطأ"):
            st.code(traceback.format_exc())
else:
    st.info("👆 يرجى رفع ملف Excel يحتوي على بيانات الاستبيان للبدء في التحليل")
    
    with st.expander("💡 تنسيق الملف المطلوب"):
        st.markdown("""
        **يجب أن يحتوي الملف على الأعمدة التالية:**
        
        | العمود | الوصف | مثال |
        |--------|--------|--------|
        | Timestamp | وقت الإجابة | 7/16/2025 23:26:18 |
        | النوع | جنس المشارك | ذكر / أنثى |
        | العمر | فئة المشارك العمرية | من 6 سنوات إلى 9 سنوات |
        | A1 - A20 | إجابات محور المشكلات السلوكية | راض جداً، راض، محايد... |
        | B1 - B13 | إجابات محور المناخ الأسري | راض جداً، راض، محايد... |
        
        **ملاحظات:**
        - تأكد من أن إجابات ليكرت مكتوبة بالعربية كما هي: `راض جداً`، `راض`، `محايد`، `غير راض`، `غير راض جداً`
        - لا تستخدم اختصارات أو رموز في إجابات ليكرت
        """)

# ==========================================
# تذييل الصفحة
# ==========================================
st.markdown("---")
st.caption("🎓 SmartStat Pro © 2025 | تم التطوير لدعم البحث العلمي في الجامعات العربية")
