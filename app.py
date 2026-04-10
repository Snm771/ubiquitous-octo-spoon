import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

st.set_page_config(page_title="SmartStat Pro | الأكاديمية", page_icon="🎓", layout="wide")

# ==========================================
# 1. دالة ترميز ليكرت الصحيحة
# ==========================================
def encode_likert(df):
    """ترميز إجابات ليكرت من نصي إلى رقمي"""
    likert_map = {
        "راض جداً": 5, "راض جدا": 5,
        "راض": 4,
        "محايد": 3,
        "غير راض": 2,
        "غير راض جداً": 1, "غير راض جدا": 1
    }
    
    df_cleaned = df.copy()
    
    # تنظيف النصوص
    for col in df_cleaned.columns:
        df_cleaned[col] = df_cleaned[col].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )
    
    # استبدال القيم
    df_cleaned = df_cleaned.replace(likert_map)
    
    # تحويل للأرقام
    for col in df_cleaned.columns:
        if col not in ['Timestamp', 'النوع', 'العمر']:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    
    return df_cleaned

# ==========================================
# 2. دالة تحديد الأعمدة تلقائياً
# ==========================================
def identify_columns(df):
    """تحديد أعمدة المشكلات السلوكية والمناخ الأسري تلقائياً"""
    cols = df.columns.tolist()
    
    # استبعاد الأعمدة الديموغرافية
    demo_cols = ['Timestamp', 'النوع', 'العمر', 'type', 'age', 'gender']
    data_cols = [c for c in cols if c not in demo_cols]
    
    # أول 20 عمود = المشكلات السلوكية
    # الباقي = المناخ الأسري
    behavioral_cols = data_cols[:20] if len(data_cols) >= 20 else data_cols
    family_cols = data_cols[20:] if len(data_cols) > 20 else []
    
    return behavioral_cols, family_cols

# ==========================================
# 3. دالة حساب ألفا كرونباخ
# ==========================================
def calculate_cronbach_alpha(df, columns):
    """حساب معامل ألفا كرونباخ"""
    try:
        data = df[columns].dropna()
        if len(data) > 1 and len(columns) > 1:
            alpha = pg.cronbach_alpha(data=data)[0]
            return round(alpha, 3)
    except:
        return None
    return None

# ==========================================
# 4. دالة الإحصاء الوصفي
# ==========================================
def descriptive_stats(df, columns):
    """حساب المتوسط، الانحراف، الوزن النسبي"""
    stats = []
    for col in columns:
        data = df[col].dropna()
        if len(data) > 0:
            mean_val = data.mean()
            std_val = data.std()
            relative_weight = (mean_val / 5) * 100
            stats.append({
                'الفقرة': col,
                'المتوسط': round(mean_val, 2),
                'الانحراف المعياري': round(std_val, 2),
                'الوزن النسبي (%)': round(relative_weight, 2)
            })
    return pd.DataFrame(stats)

# ==========================================
# 5. دالة T-test
# ==========================================
def run_ttest(df, group_col, test_col, group1, group2):
    """إجراء اختبار T-test"""
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
# الواجهة الرئيسية
# ==========================================
st.title("🎓 SmartStat Pro - تحليل الاستبيان")
st.markdown("---")

uploaded_file = st.file_uploader("📁 رفع الملف (Excel)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # قراءة البيانات
        df_raw = pd.read_excel(uploaded_file)
        
        # عرض معلومات عن الأعمدة
        st.info(f"📋 عدد الأعمدة في الملف: {len(df_raw.columns)}")
        with st.expander("عرض أسماء الأعمدة"):
            st.write(list(df_raw.columns))
        
        # ترميز ليكرت
        df = encode_likert(df_raw)
        
        # تحديد الأعمدة تلقائياً
        behavioral_cols, family_cols = identify_columns(df)
        
        st.success(f"✅ تم التعرف على:")
        st.write(f"- **محور المشكلات السلوكية**: {len(behavioral_cols)} فقرة")
        st.write(f"- **محور المناخ الأسري**: {len(family_cols)} فقرة")
        
        # حساب المجاميع
        if behavioral_cols:
            df['مجموع المشكلات السلوكية'] = df[behavioral_cols].sum(axis=1)
            df['المتوسط السلوكي'] = df[behavioral_cols].mean(axis=1)
        
        if family_cols:
            df['مجموع المناخ الأسري'] = df[family_cols].sum(axis=1)
            df['المتوسط الأسري'] = df[family_cols].mean(axis=1)
        
        # القائمة الجانبية
        st.sidebar.title("⚙️ لوحة التحكم")
        
        if 'النوع' in df.columns:
            gender_counts = df['النوع'].value_counts()
            st.sidebar.subheader("👥 النوع")
            for g, c in gender_counts.items():
                st.sidebar.metric(f"{g}", f"{c} ({c/len(df)*100:.1f}%)")
        
        if 'العمر' in df.columns:
            age_counts = df['العمر'].value_counts()
            st.sidebar.subheader("👵 العمر")
            for a, c in age_counts.items():
                st.sidebar.metric(f"{a}", f"{c} ({c/len(df)*100:.1f}%)")
        
        # التبويبات
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 الإحصاء الوصفي",
            "🧪 الثبات (ألفا)",
            "🔗 الارتباط",
            "⚖️ الفروق حسب الجنس",
            "👵 الفروق حسب العمر"
        ])
        
        # التبويب 1: الإحصاء الوصفي
        with tab1:
            st.subheader("📊 الإحصاء الوصفي")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if behavioral_cols:
                    st.markdown("### 🔴 المشكلات السلوكية")
                    beh_stats = descriptive_stats(df, behavioral_cols)
                    st.dataframe(beh_stats, use_container_width=True, height=400)
                    
                    beh_mean = df['المتوسط السلوكي'].mean() if 'المتوسط السلوكي' in df.columns else 0
                    st.info(f"**المتوسط العام**: {beh_mean:.2f}")
            
            with col2:
                if family_cols:
                    st.markdown("### 🟢 المناخ الأسري")
                    fam_stats = descriptive_stats(df, family_cols)
                    st.dataframe(fam_stats, use_container_width=True, height=400)
                    
                    fam_mean = df['المتوسط الأسري'].mean() if 'المتوسط الأسري' in df.columns else 0
                    st.success(f"**المتوسط العام**: {fam_mean:.2f}")
        
        # التبويب 2: الثبات
        with tab2:
            st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if behavioral_cols:
                    alpha_beh = calculate_cronbach_alpha(df, behavioral_cols)
                    st.metric("المشكلات السلوكية", f"{alpha_beh if alpha_beh else 'N/A'}")
                    if alpha_beh and alpha_beh >= 0.70:
                        st.success("✅ ثبات ممتاز")
                    elif alpha_beh and alpha_beh >= 0.60:
                        st.warning("⚠️ ثبات مقبول")
            
            with col2:
                if family_cols:
                    alpha_fam = calculate_cronbach_alpha(df, family_cols)
                    st.metric("المناخ الأسري", f"{alpha_fam if alpha_fam else 'N/A'}")
                    if alpha_fam and alpha_fam >= 0.70:
                        st.success("✅ ثبات ممتاز")
                    elif alpha_fam and alpha_fam >= 0.60:
                        st.warning("⚠️ ثبات مقبول")
        
        # التبويب 3: الارتباط
        with tab3:
            st.subheader("🔗 معامل الارتباط")
            
            if 'مجموع المشكلات السلوكية' in df.columns and 'مجموع المناخ الأسري' in df.columns:
                clean_data = df[['مجموع المشكلات السلوكية', 'مجموع المناخ الأسري']].dropna()
                
                if len(clean_data) > 2:
                    pearson = pg.corr(clean_data['مجموع المشكلات السلوكية'], 
                                    clean_data['مجموع المناخ الأسري'], 
                                    method='pearson')
                    
                    st.dataframe(pearson[['n', 'r', 'p-val']])
                    
                    r_val = pearson['r'].values[0]
                    if abs(r_val) >= 0.7:
                        st.success("🔗 علاقة قوية")
                    elif abs(r_val) >= 0.4:
                        st.info("🔗 علاقة متوسطة")
                    else:
                        st.warning("🔗 علاقة ضعيفة")
        
        # التبويب 4: الفروق حسب الجنس
        with tab4:
            st.subheader("⚖️ الفروق حسب الجنس")
            
            if 'النوع' in df.columns and df['النوع'].nunique() >= 2:
                genders = df['النوع'].dropna().unique()
                st.info(f"الفئات: {', '.join(map(str, genders))}")
                
                test_var = st.radio(
                    "اختر المتغير:",
                    ['مجموع المشكلات السلوكية', 'مجموع المناخ الأسري', 'المتوسط السلوكي', 'المتوسط الأسري'],
                    key='gender_test'
                )
                
                if test_var in df.columns and len(genders) == 2:
                    result = run_ttest(df, 'النوع', test_var, genders[0], genders[1])
                    
                    if result and 'خطأ' not in result:
                        st.dataframe(pd.DataFrame([result]), use_container_width=True)
                        
                        if result['قيمة p'] < 0.05:
                            st.success("✅ توجد فروق ذات دلالة إحصائية")
                        else:
                            st.info("❌ لا توجد فروق ذات دلالة إحصائية")
        
        # التبويب 5: الفروق حسب العمر
        with tab5:
            st.subheader("👵 الفروق حسب العمر")
            
            if 'العمر' in df.columns and df['العمر'].nunique() >= 2:
                ages = df['العمر'].dropna().unique()
                st.info(f"الفئات: {', '.join(map(str, ages))}")
                
                test_var = st.radio(
                    "اختر المتغير:",
                    ['مجموع المشكلات السلوكية', 'مجموع المناخ الأسري', 'المتوسط السلوكي', 'المتوسط الأسري'],
                    key='age_test'
                )
                
                if test_var in df.columns and len(ages) == 2:
                    result = run_ttest(df, 'العمر', test_var, ages[0], ages[1])
                    
                    if result and 'خطأ' not in result:
                        st.dataframe(pd.DataFrame([result]), use_container_width=True)
                        
                        if result['قيمة p'] < 0.05:
                            st.success("✅ توجد فروق ذات دلالة إحصائية")
                        else:
                            st.info("❌ لا توجد فروق ذات دلالة إحصائية")
    
    except Exception as e:
        st.error(f"❌ حدث خطأ: {e}")
        import traceback
        st.code(traceback.format_exc())
else:
    st.info("👆 ارفع الملف للبدء")
