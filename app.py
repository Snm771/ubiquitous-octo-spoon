import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg

st.set_page_config(page_title="SmartStat Pro | الأكاديمية", page_icon="🎓", layout="wide")

# ==========================================
# 1. دالة ترميز ليكرت الصحيحة (حسب بياناتك)
# ==========================================
def encode_likert(df):
    """ترميز إجابات ليكرت من نصي إلى رقمي: راض جداً=5 ← غير راض جداً=1"""
    likert_map = {
        "راض جداً": 5, "راض جدا": 5,
        "راض": 4,
        "محايد": 3,
        "غير راض": 2,
        "غير راض جداً": 1, "غير راض جدا": 1
    }
    
    df_cleaned = df.copy()
    
    # تنظيف النصوص من المسافات
    for col in df_cleaned.columns:
        df_cleaned[col] = df_cleaned[col].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )
    
    # استبدال القيم النصية بالرقمية
    df_cleaned = df_cleaned.replace(likert_map)
    
    # تحويل الأعمدة إلى رقمي (ما عدا الديموغرافية)
    for col in df_cleaned.columns:
        if col not in ['Timestamp', 'النوع', 'العمر']:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    
    return df_cleaned

# ==========================================
# 2. دالة تحديد الأعمدة تلقائياً (بدون A1, A2...)
# ==========================================
def identify_question_columns(df):
    """تحديد أعمدة الأسئلة تلقائياً بناءً على الموقع"""
    cols = df.columns.tolist()
    
    # استبعاد الأعمدة الديموغرافية وثابتة
    exclude = ['Timestamp', 'النوع', 'العمر', 'النوع.1', 'العمر.1']
    question_cols = [c for c in cols if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
    
    # أول 20 عمود = المشكلات السلوكية، الباقي = المناخ الأسري
    behavioral = question_cols[:20] if len(question_cols) >= 20 else question_cols
    family = question_cols[20:33] if len(question_cols) > 20 else []
    
    return behavioral, family

# ==========================================
# 3. دالة حساب ألفا كرونباخ
# ==========================================
def calc_alpha(df, cols):
    try:
        data = df[cols].dropna()
        if len(data) > 1 and len(cols) > 1:
            return round(pg.cronbach_alpha(data=data)[0], 3)
    except:
        return None
    return None

# ==========================================
# 4. دالة T-test منسقة
# ==========================================
def run_ttest(df, group_col, test_col, g1, g2):
    try:
        d1 = df[df[group_col]==g1][test_col].dropna()
        d2 = df[df[group_col]==g2][test_col].dropna()
        if len(d1)>1 and len(d2)>1:
            res = pg.ttest(d1, d2, correction='auto')
            p = res['p-val'].values[0]
            return {
                'متوسط '+str(g1): round(d1.mean(),3),
                'متوسط '+str(g2): round(d2.mean(),3),
                'تباين '+str(g1): round(d1.var(),3),
                'تباين '+str(g2): round(d2.var(),3),
                'عدد '+str(g1): len(d1),
                'عدد '+str(g2): len(d2),
                't': round(res['T'].values[0],3),
                'p': round(p,4),
                'Cohen d': round(res['cohen-d'].values[0] if 'cohen-d' in res.columns else 0,3),
                'الدلالة': '✅ معنوي' if p<0.05 else '❌ غير معنوي'
            }
    except:
        return None
    return None

# ==========================================
# الواجهة الرئيسية (نفس كودك + إضافات)
# ==========================================
st.title("🎓 SmartStat Pro - المحلل الإحصائي الأكاديمي الشامل")
st.markdown("---")

uploaded_file = st.file_uploader("قم برفع ملف البيانات (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # قراءة البيانات
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # ترميز ليكرت
        df_encoded = encode_likert(df)
        
        # تحديد الأعمدة تلقائياً
        beh_cols, fam_cols = identify_question_columns(df_encoded)
        
        st.sidebar.title("⚙️ إعدادات المتغيرات")
        
        # المتغيرات الديموغرافية
        demo_cols = [c for c in df_encoded.columns if c in ['النوع', 'العمر'] and c in df_encoded.columns]
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات الديموغرافية:", df_encoded.columns, default=demo_cols)
        
        # أسئلة الاستبيان
        all_q_cols = beh_cols + fam_cols
        base_numeric_cols = st.sidebar.multiselect("🔢 أسئلة الاستبيان:", df_encoded.columns, default=all_q_cols)
        
        # حساب المجاميع
        if base_numeric_cols:
            df_encoded['المجموع الكلي'] = df_encoded[base_numeric_cols].sum(axis=1)
            if beh_cols:
                df_encoded['مجموع المشكلات السلوكية'] = df_encoded[beh_cols].sum(axis=1)
            if fam_cols:
                df_encoded['مجموع المناخ الأسري'] = df_encoded[fam_cols].sum(axis=1)
        
        st.success("✅ تم تحميل البيانات بنجاح!")
        
        # التبويبات (نفسها + تبويب جديد)
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "👥 الديموغرافيا", "📊 الوصفي", "🧪 الثبات", 
            "⚖️ الفروق", "🔗 الارتباط", "📈 الانحدار", "📊 مقارنة الجنس/العمر"
        ])
        
        # --- التبويب 1: الديموغرافيا ---
        with tab1:
            st.subheader("👥 التوزيع الديموغرافي")
            if 'النوع' in df_encoded.columns:
                col1, col2 = st.columns(2)
                with col1:
                    g_counts = df_encoded['النوع'].value_counts()
                    st.dataframe(pd.DataFrame({'العدد': g_counts, 'النسبة%': (g_counts/len(df_encoded)*100).round(1)}))
                with col2:
                    st.plotly_chart(px.pie(names=g_counts.index, values=g_counts.values, title='توزيع الجنس'), use_container_width=True)
            
            if 'العمر' in df_encoded.columns:
                col1, col2 = st.columns(2)
                with col1:
                    a_counts = df_encoded['العمر'].value_counts()
                    st.dataframe(pd.DataFrame({'العدد': a_counts, 'النسبة%': (a_counts/len(df_encoded)*100).round(1)}))
                with col2:
                    st.plotly_chart(px.pie(names=a_counts.index, values=a_counts.values, title='توزيع العمر'), use_container_width=True)
        
        # --- التبويب 2: الإحصاء الوصفي ---
        with tab2:
            st.subheader("📊 الإحصاء الوصفي")
            if base_numeric_cols:
                desc = df_encoded[base_numeric_cols].describe().T
                desc = desc.rename(columns={'count':'العدد','mean':'المتوسط','std':'انحراف','min':'أدنى','max':'أقصى'})
                st.dataframe(desc[['العدد','المتوسط','انحراف','أدنى','أقصى']], use_container_width=True)
        
        # --- التبويب 3: الثبات ---
        with tab3:
            st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
            col1, col2 = st.columns(2)
            with col1:
                if beh_cols:
                    a = calc_alpha(df_encoded, beh_cols)
                    st.metric("المشكلات السلوكية", f"{a if a else 'N/A'}")
                    if a and a>=0.7: st.success("✅ ممتاز")
                    elif a and a>=0.6: st.warning("⚠️ مقبول")
            with col2:
                if fam_cols:
                    a = calc_alpha(df_encoded, fam_cols)
                    st.metric("المناخ الأسري", f"{a if a else 'N/A'}")
                    if a and a>=0.7: st.success("✅ ممتاز")
                    elif a and a>=0.6: st.warning("⚠️ مقبول")
        
        # --- التبويب 4: الفروق ---
        with tab4:
            st.subheader("⚖️ اختبار الفروق")
            if categorical_cols and base_numeric_cols:
                gcol = st.selectbox("المتغير المستقل:", categorical_cols, key='fg')
                tcol = st.selectbox("المتغير التابع:", ['المجموع الكلي','مجموع المشكلات السلوكية','مجموع المناخ الأسري']+base_numeric_cols, key='ft')
                if tcol in df_encoded.columns:
                    clean = df_encoded[[gcol,tcol]].dropna()
                    groups = clean[gcol].unique()
                    if len(groups)==2:
                        res = pg.ttest(clean[clean[gcol]==groups[0]][tcol], clean[clean[gcol]==groups[1]][tcol])
                        st.dataframe(res)
                        p = res['p-val'].values[0]
                        st.success("✅ معنوي" if p<0.05 else "❌ غير معنوي")
                        st.plotly_chart(px.box(clean, x=gcol, y=tcol, color=gcol), use_container_width=True)
        
        # --- التبويب 5: الارتباط ---
        with tab5:
            st.subheader("🔗 معامل الارتباط")
            if 'مجموع المشكلات السلوكية' in df_encoded.columns and 'مجموع المناخ الأسري' in df_encoded.columns:
                cd = df_encoded[['مجموع المشكلات السلوكية','مجموع المناخ الأسري']].dropna()
                if len(cd)>2:
                    pr = pg.corr(cd['مجموع المشكلات السلوكية'], cd['مجموع المناخ الأسري'], method='pearson')
                    st.dataframe(pr[['n','r','p-val']])
                    r = pr['r'].values[0]
                    st.info(f"🔗 العلاقة: {'قوية' if abs(r)>=0.7 else 'متوسطة' if abs(r)>=0.4 else 'ضعيفة'} (r={r:.3f})")
                    st.plotly_chart(px.scatter(cd, x='مجموع المشكلات السلوكية', y='مجموع المناخ الأسري', trendline='ols'), use_container_width=True)
        
        # --- التبويب 6: الانحدار ---
        with tab6:
            st.subheader("📈 الانحدار")
            if len(base_numeric_cols)>=2:
                y = st.selectbox("المتغير التابع:", base_numeric_cols, key='ry')
                xs = st.multiselect("المتغيرات المستقلة:", [c for c in base_numeric_cols if c!=y], key='rx')
                if xs:
                    rd = df_encoded[[y]+xs].dropna()
                    if len(rd)>2:
                        lm = pg.linear_regression(rd[xs], rd[y])
                        st.dataframe(lm)
                        if 'r2' in lm.columns:
                            st.info(f"💡 R² = {lm['r2'].values[0]*100:.1f}%")
        
        # ==========================================
        # التبويب 7 الجديد: مقارنة مفصلة حسب الجنس والعمر
        # ==========================================
        with tab7:
            st.subheader("📊 مقارنة الذكور/الإناث والعمر (لكل سؤال)")
            
            if 'النوع' in df_encoded.columns and base_numeric_cols:
                genders = df_encoded['النوع'].dropna().unique()
                st.info(f"فئات الجنس: {', '.join(map(str, genders))}")
                
                # الجدول الشامل
                st.markdown("### 📋 جدول مقارنة جميع الأسئلة")
                comp_data = []
                for i,q in enumerate(base_numeric_cols,1):
                    row = {'#':i, 'السؤال':q}
                    for g in genders:
                        gd = df_encoded[df_encoded['النوع']==g][q].dropna()
                        if len(gd)>0:
                            row[f'متوسط({g})'] = f"{gd.mean():.2f}"
                            row[f'عدد({g})'] = len(gd)
                        else:
                            row[f'متوسط({g})'] = '-'
                            row[f'عدد({g})'] = 0
                    if len(genders)==2:
                        t = run_ttest(df_encoded, 'النوع', q, genders[0], genders[1])
                        if t:
                            row['p-value'] = f"{t['p']:.4f}"
                            row['الدلالة'] = t['الدلالة']
                    comp_data.append(row)
                
                comp_df = pd.DataFrame(comp_data)
                st.dataframe(comp_df.style.set_properties(**{'text-align':'center'}), use_container_width=True, height=500)
                
                # زر التصدير
                csv = comp_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 تحميل الجدول (CSV)", data=csv, file_name='مقارنة_الجنس.csv', mime='text/csv')
                
                # تحليل مفصل لسؤال
                st.markdown("### 🔍 تحليل مفصل لسؤال")
                sel_q = st.selectbox("اختر سؤالاً:", base_numeric_cols, key='sq')
                if sel_q and len(genders)==2:
                    c1,c2,c3 = st.columns(3)
                    with c1:
                        d1 = df_encoded[df_encoded['النوع']==genders[0]][sel_q].dropna()
                        st.metric(f"{genders[0]} - المتوسط", f"{d1.mean():.2f}" if len(d1)>0 else '-')
                        st.metric(f"{genders[0]} - العدد", len(d1))
                    with c2:
                        d2 = df_encoded[df_encoded['النوع']==genders[1]][sel_q].dropna()
                        st.metric(f"{genders[1]} - المتوسط", f"{d2.mean():.2f}" if len(d2)>0 else '-')
                        st.metric(f"{genders[1]} - العدد", len(d2))
                    with c3:
                        if len(d1)>1 and len(d2)>1:
                            t = run_ttest(df_encoded, 'النوع', sel_q, genders[0], genders[1])
                            if t:
                                st.metric("p-value", f"{t['p']:.4f}")
                                st.success(t['الدلالة'] if t['p']<0.05 else "❌ غير معنوي")
                    
                    st.plotly_chart(px.box(df_encoded, x='النوع', y=sel_q, color='النوع', points='all'), use_container_width=True)
            
            # تحليل العمر
            if 'العمر' in df_encoded.columns and base_numeric_cols:
                st.markdown("---")
                st.subheader("👵 مقارنة حسب الفئة العمرية")
                ages = df_encoded['العمر'].dropna().unique()
                st.info(f"فئات العمر: {', '.join(map(str, ages))}")
                
                if len(ages)==2 and base_numeric_cols:
                    sel_q2 = st.selectbox("اختر سؤالاً للمقارنة العمرية:", base_numeric_cols, key='sq2')
                    if sel_q2:
                        t = run_ttest(df_encoded, 'العمر', sel_q2, ages[0], ages[1])
                        if t:
                            st.dataframe(pd.DataFrame([t]), use_container_width=True)
                            st.success("✅ معنوي" if t['p']<0.05 else "❌ غير معنوي")
                        st.plotly_chart(px.box(df_encoded, x='العمر', y=sel_q2, color='العمر'), use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        import traceback
        with st.expander("تفاصيل الخطأ"):
            st.code(traceback.format_exc())
else:
    st.info("👆 ارفع ملف Excel أو CSV للبدء")

# تذييل
st.markdown("---")
st.caption("🎓 SmartStat Pro © 2025")
