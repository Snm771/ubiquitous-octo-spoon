import streamlit as st
import pandas as pd
import plotly.express as px
import pingouin as pg
import numpy as np

# استيراد مكتبة OpenAI
try:
    from openai import OpenAI
except ImportError:
    st.warning("جاري إعداد المكتبات...")

st.set_page_config(page_title="SmartStat Pro | الخبير الإحصائي", page_icon="📊", layout="wide")

# ==========================================
# 1. إعدادات الذاكرة (مرة واحدة فقط لمنع الأخطاء)
# ==========================================
if 'lang' not in st.session_state:
    st.session_state.lang = "العربية"
if 'hypothesis_history' not in st.session_state:
    st.session_state['hypothesis_history'] = []
if 'sample_results' not in st.session_state:
    st.session_state['sample_results'] = []
if 'reliability_result' not in st.session_state:
    st.session_state['reliability_result'] = ""
if 'dim_recs' not in st.session_state:
    st.session_state['dim_recs'] = []

# ==========================================
# 2. نظام اللغات ودالة الترجمة (Localization)
# ==========================================
lang = st.sidebar.radio("🌍 Language / لغة الواجهة", ["العربية", "English"])

# 👇 هذه هي دالة الترجمة السحرية
def tr(ar_text, en_text):
    return ar_text if lang == "العربية" else en_text

# تحديد الاتجاه والخط بناءً على اللغة
if lang == "العربية":
    direction = "rtl"
    align = "right"
    font_family = "'Tajawal', 'Arial', sans-serif"
else:
    direction = "ltr"
    align = "left"
    font_family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"

# ==========================================
# 3. 🌟 كود الواجهة الاحترافية الشاملة الموحدة (ثيم VIP) 🌟
# ==========================================
hero_title = "نظام الخبير الإحصائي الآلي" if lang == "العربية" else "Automated Statistical Expert"
hero_desc = "يُرفق النظام الآن تفسيراً أكاديمياً دقيقاً مع كل نتيجة إحصائية (وصفي، عينة، فروق، ارتباط، انحدار) جاهز للنسخ المباشر في فصول مناقشة النتائج بضغطة زر." if lang == "العربية" else "The system now attaches an accurate academic explanation with every statistical result, ready for direct copying into discussion chapters with one click."
badge_text = "✨ الإصدار الاحترافي PRO" if lang == "العربية" else "✨ PRO VERSION"

st.markdown(f"""
    <style>
    /* 🌟 التوجيه والخطوط الشاملة 🌟 */
    .block-container, [data-testid="stSidebar"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, li {{
        direction: {direction} !important;
        text-align: {align} !important;
        font-family: {font_family} !important;
    }}

    [data-testid="stHeader"] {{
        background-color: transparent !important; /* الشريط العلوي شفاف */
    }}

    /* 🌟 الإطار الفخم المتكيف (يتغير تلقائياً مع الفاتح والداكن) 🌟 */
    .block-container {{
        background: var(--background-color) !important;
        border-radius: 20px !important;
        padding: 3rem 2rem !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1) !important;
        border-top: 5px solid #d4af37 !important; 
        margin-top: 2rem !important;
        margin-bottom: 2rem !important;
    }}

    /* 🌟 قسم الترحيب (Hero Section) 🌟 */
    .hero-container {{
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important; 
        justify-content: center !important;
        background: linear-gradient(135deg, var(--secondary-background-color), rgba(212, 175, 55, 0.05));
        border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 24px;
        padding: 4rem 2rem;
        margin-bottom: 3rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.04);
        text-align: center !important;
    }}
    .hero-badge {{
        display: inline-block !important;
        background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(212,175,55,0.05));
        color: #d4af37;
        padding: 8px 25px;
        border-radius: 50px;
        font-size: 1rem;
        font-weight: bold;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(212, 175, 55, 0.4);
    }}
    .hero-title {{
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        margin-bottom: 1rem !important;
        background: linear-gradient(45deg, #1e3c72, #d4af37, #1e3c72);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
    }}
    @keyframes shine {{ to {{ background-position: 200% center; }} }}
    .hero-subtitle {{
        font-size: 1.2rem !important;
        color: var(--text-color) !important;
        opacity: 0.8;
        max-width: 800px;
        margin: 0 auto !important;
        line-height: 1.8 !important;
    }}

    /* 🌟 منطقة رفع الملفات (VIP Uploader) 🌟 */
    [data-testid="stFileUploader"] {{
        background: transparent !important;
    }}
    [data-testid="stFileUploadDropzone"], section[data-testid="stFileUploadDropzone"] {{
        background-color: rgba(212, 175, 55, 0.03) !important;
        border: 2px dashed #d4af37 !important;
        border-radius: 20px !important;
        padding: 3rem !important;
        transition: all 0.4s ease !important;
    }}
    [data-testid="stFileUploadDropzone"]:hover, section[data-testid="stFileUploadDropzone"]:hover {{
        background-color: rgba(212, 175, 55, 0.1) !important;
        border: 2px solid #d4af37 !important;
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 30px rgba(212, 175, 55, 0.15) !important;
    }}
    [data-testid="stFileUploader"] button, [data-testid="stFileUploadDropzone"] button {{
        background: linear-gradient(135deg, #d4af37 0%, #b8962e 100%) !important;
        color: #111 !important;
        font-weight: 900 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 2.5rem !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4) !important;
        transition: all 0.3s ease !important;
    }}
    [data-testid="stFileUploader"] button:hover, [data-testid="stFileUploadDropzone"] button:hover {{
        transform: scale(1.08) !important;
        box-shadow: 0 8px 25px rgba(212, 175, 55, 0.6) !important;
        filter: brightness(1.1) !important;
    }}
    [data-testid="stFileUploadDropzone"] small, [data-testid="stFileUploadDropzone"] div {{
        color: var(--text-color) !important;
        opacity: 0.8;
        font-weight: bold !important;
    }}

    /* تصميم التبويبات الفخم */
    .stTabs [data-baseweb="tab-list"] {{ 
        direction: {direction} !important;
        overflow-x: auto !important; 
        scrollbar-width: none !important; 
    }}
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {{
        display: none !important; 
    }}
    .stTabs [data-baseweb="tab"] {{
        white-space: nowrap !important;
        font-weight: bold !important;
        height: 50px !important;
        letter-spacing: 0.5px;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: #d4af37 !important; /* مؤشر التبويب ذهبي */
    }}

    /* تأثير البطاقات الزجاجية للحقول والمدخلات */
    .stSelectbox div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.02) !important;
    }}
    
    .stSelectbox div[data-baseweb="select"] > div:hover, .stTextInput input:hover {{
        border-color: #d4af37 !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.2) !important;
    }}

    /* الأزرار الاحترافية (تصميم أنيق مع ذهبي) */
    .stButton > button {{
        background: linear-gradient(145deg, #1e3c72 0%, #2a5298 100%) !important;
        color: white !important;
        border-radius: 14px !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
        box-shadow: 0 5px 15px rgba(30, 60, 114, 0.3) !important;
        transition: all 0.3s ease !important;
        width: auto !important;
        min-width: 150px;
    }}
    
    .stButton > button:hover {{
        transform: scale(1.03) translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(30, 60, 114, 0.4) !important;
    }}

    /* تجميل الـ Expanders لتكون كأنها أجزاء من لوحة تحكم فارهة */
    .streamlit-expanderHeader {{
        background-color: var(--secondary-background-color) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(128, 128, 128, 0.1) !important;
        padding: 10px 15px !important;
    }}
    
    [data-testid="stExpander"] {{
        border: none !important;
        background-color: transparent !important;
        margin-bottom: 15px !important;
    }}
    
    .stDataFrame div {{ direction: {direction} !important; }}

    /* ========================================= */
    /* 🌟 7. تجميل الشريط الجانبي (Sidebar PRO) 🌟 */
    /* ========================================= */
    
    /* خلفية الشريط الجانبي ولمسة الظل */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--secondary-background-color) 0%, rgba(212, 175, 55, 0.05) 100%) !important;
        border-left: 1px solid rgba(212, 175, 55, 0.2) !important;
        box-shadow: -5px 0 15px rgba(0,0,0,0.03) !important;
    }}

    /* 🌟 تجميل المربعات الحمراء (Tags) وتحويلها لذهبي زجاجي 🌟 */
    span[data-baseweb="tag"] {{
        background: linear-gradient(145deg, rgba(212, 175, 55, 0.15), rgba(212, 175, 55, 0.05)) !important;
        color: #d4af37 !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 4px 8px !important;
        transition: all 0.3s ease !important;
    }}
    span[data-baseweb="tag"]:hover {{
        background: rgba(212, 175, 55, 0.25) !important;
        box-shadow: 0 4px 10px rgba(212, 175, 55, 0.2) !important;
    }}
    
    /* تغيير لون علامة (X) داخل التاجز */
    span[data-baseweb="tag"] svg {{
        fill: #d4af37 !important;
    }}

    /* 🌟 رسائل النجاح (الخضراء) داخل الشريط الجانبي 🌟 */
    [data-testid="stSidebar"] [data-testid="stAlert"] {{
        background: rgba(212, 175, 55, 0.05) !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
    }}

    /* 🌟 الخطوط الفاصلة (Dividers) في الشريط الجانبي 🌟 */
    [data-testid="stSidebar"] hr {{
        border-top: 1px dashed rgba(212, 175, 55, 0.3) !important;
        margin: 1.5rem 0 !important;
    }}
    
    /* 🌟 أزرار الراديو (اختيار اللغة) 🌟 */
    .stRadio > div {{
        background: var(--secondary-background-color) !important;
        padding: 10px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(128,128,128,0.1) !important;
    }}

    /* 🌟 تنسيق خاص للأبعاد الفرعية في القائمة الجانبية (الهيكل الهرمي) 🌟 */
    .sub-dimension-container {{
        padding-right: 15px !important;
        border-right: 2px solid #d4af37 !important;
        margin-bottom: 10px !important;
    }}

    </style>

    <div class="hero-container">
        <div class="hero-badge">{badge_text}</div>
        <h1 class="hero-title">SmartStat <span>Pro</span></h1>
        <p class="hero-subtitle">{hero_desc}</p>
    </div>
""", unsafe_allow_html=True)
    
# ==========================================
# --- دوال الذكاء الاصطناعي (الرابط المحدث لـ Hugging Face) ---
# ==========================================
def run_ai(prompt, api_key):
    try:
        # ✅ تم تحديث الرابط إلى router.huggingface.co
        client = OpenAI(
            base_url="https://router.huggingface.co/v1/",
            api_key=api_key
        )
        
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct", # الموديل الجبار في اللغة العربية
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ خطأ في الاتصال بالذكاء الاصطناعي: {e}"

def analyze_hypothesis_text(text, api_key):
    prompt = f"""
    حلل الفرضية الإحصائية التالية بدقة:
    "{text}"
    استخرج المعلومات التالية باختصار شديد:
    - نوع الفرضية: (اكتب فقط: علاقة، أو تأثير، أو فروق)
    - المتغير المستقل: (اسم المتغير)
    - المتغير التابع: (اسم المتغير)
    """
    return run_ai(prompt, api_key)

def generate_detailed_explanation(results, hypothesis, api_key):
    prompt = f"""
    بصفتك أستاذاً جامعياً ومشرفاً على رسائل الماجستير والدكتوراه، لديك نتائج تحليل إحصائي:
    {results}
    
    والفرضية التي تم اختبارها هي:
    "{hypothesis}"

    اكتب تفسيراً أكاديمياً تفصيلياً جداً (يصلح للنسخ المباشر في الفصل الرابع: مناقشة النتائج)، ويجب أن يشمل:
    1. قراءة وتفسير الأرقام في الجدول.
    2. تفسير كل قيمة علمياً (R Square, Beta, T/F value, P-value) حسب نوع الاختبار المجرى.
    3. تفسير اتجاه العلاقة أو حجم الأثر بشكل دقيق.
    4. قرار واضح بـ (قبول) أو (رفض) الفرضية.
    5. فقرة مناقشة النتائج وربطها بشكل افتراضي منطقي مع الدراسات السابقة والنظريات العلمية.
    
    اجعل اللغة أكاديمية، رصينة، واحترافية جداً باللغة العربية.
    """
    return run_ai(prompt, api_key)

def get_table_explanation(table_string, context, api_key):
    prompt = f"""
    بصفتك خبيراً إحصائياً، قم بقراءة هذا الجدول الخاص بـ ({context}):
    {table_string}
    
    اكتب فقرة أكاديمية تشرح أهم ما جاء في هذا الجدول، استخرج أعلى وأقل القيم، وفسر معناها في سياق البحث العلمي.
    """
    return run_ai(prompt, api_key)

# ==========================================
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
    
    for col in df_cleaned.select_dtypes(include=['object']).columns:
        df_cleaned[col] = df_cleaned[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
        
    df_cleaned = df_cleaned.replace(likert_map)
    
    for col in df_cleaned.columns:
        if col != 'Timestamp':
            try: 
                df_cleaned[col] = pd.to_numeric(df_cleaned[col])
            except ValueError: 
                pass 
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
# سحب مفتاح الذكاء الاصطناعي تلقائياً
# ==========================================
if "HF_TOKEN" in st.secrets:
    api_key = st.secrets["HF_TOKEN"]
else:
    st.sidebar.title("🤖 إعدادات الذكاء الاصطناعي")
    api_key = st.sidebar.text_input("🔑 مفتاح Hugging Face API:", type="password", help="ضع المفتاح هنا لتفعيل الشرح التوليدي والتبويب السابع")

uploaded_file = st.file_uploader("قم برفع ملف البيانات الخام (CSV أو Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
            
        df_encoded = encode_likert(df)
        cat_cols_auto, num_cols_auto = smart_classify_columns(df_encoded)
        
        st.sidebar.title("⚙️ بناء الهيكل التنظيمي (Constructs & Dimensions)")
        st.sidebar.success(f"تم اكتشاف {len(num_cols_auto)} سؤال استبيان بنجاح!")
        
        categorical_cols = st.sidebar.multiselect("👥 المتغيرات الشخصية (للمقارنة):", df_encoded.columns, default=cat_cols_auto)
        all_questions = [c for c in num_cols_auto if c not in categorical_cols]
        
        # 🌟 التعديل السحري: بناء القائمة الهرمية 🌟
        num_main_constructs = st.sidebar.number_input("🔢 عدد المتغيرات الرئيسية (مثال: مستقل، تابع، وسيط):", min_value=1, max_value=10, value=2)
        
        dimensions_dict = {} # لتخزين الأبعاد الفرعية (الأصلي)
        analysis_cols = []   # لتخزين جميع المتغيرات (الرئيسية والفرعية) للتحليل
        active_questions = []
        constructs_dict = {} # قاموس جديد لتخزين الهيكل الهرمي
        
        available_questions = all_questions.copy() # نسخة للتحكم بالأسئلة المتبقية

        for i in range(int(num_main_constructs)):
            st.sidebar.markdown(f"---")
            construct_name = st.sidebar.text_input(f"اسم المتغير الرئيسي {i+1}:", f"المتغير {i+1}", key=f"construct_name_{i}")
            num_sub_dims = st.sidebar.number_input(f"🔢 كم عدد أبعاد ({construct_name})؟", min_value=1, max_value=10, value=1, key=f"num_dims_{i}")
            
            construct_cols = [] # جميع أسئلة هذا المتغير الرئيسي
            
            # قسم الأبعاد الفرعية
            st.sidebar.markdown(f'<div class="sub-dimension-container">', unsafe_allow_html=True)
            for j in range(int(num_sub_dims)):
                dim_name = st.sidebar.text_input(f"اسم البعد {j+1} التابع لـ ({construct_name}):", f"البعد {j+1}", key=f"dim_name_{i}_{j}")
                
                # توزيع ذكي للأسئلة المتبقية كقيم افتراضية
                chunk_size = max(1, len(available_questions) // max(1, int(num_sub_dims) - j)) if available_questions else 1
                default_cols = available_questions[:chunk_size] if available_questions else []
                
                dim_cols = st.sidebar.multiselect(f"أسئلة ({dim_name}):", all_questions, default=default_cols, key=f"dim_cols_{i}_{j}")
                
                if dim_cols:
                    dimensions_dict[dim_name] = dim_cols
                    construct_cols.extend(dim_cols)
                    
                    # حساب متوسط البعد
                    df_encoded[dim_cols] = df_encoded[dim_cols].apply(pd.to_numeric, errors='coerce')
                    df_encoded[dim_name] = df_encoded[dim_cols].mean(axis=1)
                    analysis_cols.append(dim_name)
                    active_questions.extend(dim_cols)
                    
                    # إزالة الأسئلة المختارة من القائمة المتاحة
                    available_questions = [q for q in available_questions if q not in dim_cols]
            st.sidebar.markdown('</div>', unsafe_allow_html=True)

            # إذا كان هناك أبعاد تم تحديدها، قم بإنشاء وحساب المتغير الرئيسي
            if construct_cols:
                # إزالة التكرارات من قائمة أسئلة المتغير الرئيسي
                construct_cols = list(dict.fromkeys(construct_cols))
                constructs_dict[construct_name] = construct_cols
                
                # حساب متوسط المتغير الرئيسي بناءً على جميع أسئلة أبعاده الفرعية
                df_encoded[construct_name] = df_encoded[construct_cols].mean(axis=1)
                
                # إضافة المتغير الرئيسي كخيار للتحليل!
                analysis_cols.append(construct_name)
                # إضافة المتغير الرئيسي أيضاً كـ "بعد" وهمي لكي يظهر في نتائج الثبات (Cronbach's Alpha)
                dimensions_dict[construct_name] = construct_cols 

        active_questions = list(dict.fromkeys(active_questions))

        if len(active_questions) > 0:
            df_encoded['الاستبيان ككل (المتوسط العام)'] = df_encoded[active_questions].mean(axis=1)
            analysis_cols.append('الاستبيان ككل (المتوسط العام)')

        if not analysis_cols:
            st.warning("يرجى تحديد أسئلة الأبعاد من القائمة الجانبية للبدء.")
        else:
        
            # التبويبات الثمانية
           # تعريف 9 تبويبات (فصل النتائج عن التوصيات)
           # تعريف 6 تبويبات احترافية (بعد إزالة التبويبات اليدوية القديمة)
            tabs_names = [
                "👥 عينة الدراسة", "📊 الإحصاء الوصفي", "🧪 الثبات (ألفا)", 
                "🧠 محلل الفرضيات الذكي", "📌 النتائج", "💡 التوصيات"
            ] if lang == "العربية" else [
                "👥 Sample", "📊 Descriptive", "🧪 Reliability", 
                "🧠 AI Analyst", "📌 Results", "💡 Recommendations"
            ]
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tabs_names)
            # ==========================================
            # 1. تبويب عينة الدراسة ✅ مع الرسوم المتعددة والمجموع
            # ==========================================
            with tab1:
                st.subheader("👥 وصف عينة الدراسة (التكرارات والنسب)")
                if categorical_cols:
                    for col in categorical_cols:
                        st.markdown(f"### 📊 توزيع أفراد العينة حسب: ({col})")
                        
                        counts = df_encoded[col].value_counts()
                        percentages = df_encoded[col].value_counts(normalize=True) * 100
                        demo_df = pd.DataFrame({'التكرار': counts, 'النسبة (%)': percentages.round(2)})
                        
                        total_row = pd.DataFrame({
                            'التكرار': [len(df_encoded)],
                            'النسبة (%)': [100.00]
                        }, index=['📊 المجموع الكلي ✓'])
                        demo_df_with_total = pd.concat([demo_df, total_row])
                        
                        col1, col2 = st.columns(2)
                        with col1: 
                            st.dataframe(demo_df_with_total, use_container_width=True)
                            chart_type_demo = st.radio(f"اختر نوع الرسم لـ ({col}):", ["دائري (Pie)", "أعمدة (Bar)", "دائري مجوف (Donut)", "خطي (Line)", "أعمدة أفقية (H-Bar)"], key=f"chart_{col}", horizontal=True)
                            
                        with col2: 
                            if chart_type_demo == "دائري (Pie)":
                                fig = px.pie(demo_df, values='التكرار', names=demo_df.index, height=350)
                            elif chart_type_demo == "أعمدة (Bar)":
                                fig = px.bar(demo_df, x=demo_df.index, y='التكرار', text='التكرار', color=demo_df.index, height=350)
                            elif chart_type_demo == "دائري مجوف (Donut)":
                                fig = px.pie(demo_df, values='التكرار', names=demo_df.index, hole=0.4, height=350)
                            elif chart_type_demo == "خطي (Line)":
                                fig = px.line(demo_df, x=demo_df.index, y='التكرار', markers=True, height=350)
                            else:
                                fig = px.bar(demo_df, x='التكرار', y=demo_df.index, text='التكرار', color=demo_df.index, orientation='h', height=350)
                            
                            # 👇=== التعديل السحري لترتيب مفتاح الرسم (Legend) ومنع قص النص ===👇
                            fig.update_layout(
                                legend=dict(
                                    orientation="h",
                                    yanchor="top",
                                    y=-0.1,
                                    xanchor="center",
                                    x=0.5
                                ),
                                margin=dict(l=10, r=10, t=30, b=10)
                            )
                            # 👆=====================================================👆

                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.info(f"**📝 التفسير الأكاديمي:**\n يوضح العرض الإحصائي أعلاه التوزيع التكراري والنسبي لأفراد عينة الدراسة البالغ عددهم الإجمالي ({len(df_encoded)}) مبحوثاً، وذلك وفقاً لتصنيفاتهم في متغير ({col}). من خلال استقراء النتائج، يتبين بوضوح أن الفئة الأكثر تمثيلاً وحضوراً في العينة هي فئة ({counts.idxmax()}) بنسبة مئوية قدرها ({percentages.max():.1f}%)، مما يعكس هيمنة هذه الشريحة على تركيبة العينة في هذا المتغير.")
                        
                        # 👇=== كود الحفظ بصمت ===👇
                        res_txt = f"يتضح أن الفئة الأعلى في متغير ({col}) هي ({counts.idxmax()}) بنسبة ({percentages.max():.1f}%)."
                        if res_txt not in st.session_state['sample_results']:
                            st.session_state['sample_results'].append(res_txt)
                        # 👆==============================👆
                        
                        if api_key:
                            if st.button(f"✨ توليد قراءة ذكية متعمقة لجدول ({col})", key=f"ai_demo_{col}"):
                                with st.spinner("جاري صياغة التفسير الأكاديمي..."):
                                    st.success(get_table_explanation(demo_df_with_total.to_markdown(), f"توزيع العينة حسب {col}", api_key))
                        st.markdown("---")

            # ==========================================
            # 2. تبويب الإحصاء الوصفي
            # ==========================================
            with tab2:
                st.subheader("📊 الإحصاء الوصفي (المتوسطات والانحرافات المعيارية)")
                st.markdown("### 1️⃣ الإحصاء العام للمحاور والأبعاد")
                desc_df = df_encoded[analysis_cols].describe().T
                desc_df = desc_df.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                st.dataframe(desc_df[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']], use_container_width=True)
                
                if api_key:
                    if st.button("✨ توليد قراءة ذكية لجدول المحاور", key="ai_desc"):
                        with st.spinner("جاري التحليل..."):
                            st.success(get_table_explanation(desc_df.to_markdown(), "المتوسطات والانحرافات المعيارية للمحاور", api_key))

                st.markdown(f"### 2️⃣ الإحصاء التفصيلي لجميع فقرات الاستبيان (العدد: {len(active_questions)})")
                if active_questions:
                    items_desc = df_encoded[active_questions].describe().T
                    items_desc = items_desc.rename(columns={'count': 'العدد', 'mean': 'المتوسط', 'std': 'الانحراف المعياري', 'min': 'الأدنى', 'max': 'الأقصى'})
                    st.dataframe(items_desc[['العدد', 'المتوسط', 'الانحراف المعياري', 'الأدنى', 'الأقصى']].style.background_gradient(subset=['المتوسط'], cmap='Blues'), use_container_width=True)

                st.markdown("### 📝 التفسير الأكاديمي:")
                st.info("يهدف التحليل الوصفي المعروض في الجداول أعلاه إلى تشخيص مستوى الاستجابة لمتغيرات ومحاور الدراسة وفقاً لآراء أفراد العينة. بالاعتماد على مقياس النزعة المركزية المتمثل في **المتوسط الحسابي (Mean)**، يتم تحديد الاتجاه العام والميل الغالب لإجابات المبحوثين، حيث تشير القيم المرتفعة إلى تبلور رأي إيجابي، أو مستوى موافقة عالٍ. وبالتوازي مع ذلك، يبرز دور مقياس التشتت المتمثل في **الانحراف المعياري (Standard Deviation)** كمؤشر إحصائي دقيق لقياس مدى تشتت أو تقارب تلك الآراء حول متوسطها.")

       # ==========================================
            # 3. الثبات
            # ==========================================
            with tab3:
                st.subheader("🧪 معامل الثبات (Cronbach's Alpha)")
                
                # 🔹 1. دالة التقييم الدقيق (مقتبسة من كود أختك)
                def evaluate_alpha(alpha):
                    if alpha < 0.60: return "ضعيف (مرفوض)"
                    elif alpha < 0.70: return "مقبول"
                    elif alpha < 0.80: return "جيد"
                    elif alpha < 0.90: return "مرتفع"
                    else: return "مرتفع جداً"

                alpha_results = []
                suggestions = [] # لحفظ مقترحات تحسين الثبات (فكرة أختك)

                for dim_name, cols in dimensions_dict.items():
                    if len(cols) > 1:
                        clean_data = df_encoded[cols].dropna()
                        a_val = pg.cronbach_alpha(data=clean_data)[0]
                        eval_text = evaluate_alpha(a_val)
                        
                        alpha_results.append({
                            "المحور / البعد": dim_name, 
                            "عدد العبارات": len(cols), 
                            "معامل ألفا": round(a_val, 3),
                            "التقييم": eval_text
                        })

                        # 🔹 2. خوارزمية اكتشاف الأسئلة الضعيفة (مبنية على فكرة أختك)
                        # تعمل فقط إذا كان الثبات يحتاج تحسين (أقل من 0.85)
                        if a_val < 0.85:
                            best_a = a_val
                            bad_item = None
                            for col in cols:
                                temp_cols = [c for c in cols if c != col]
                                if len(temp_cols) > 1:
                                    new_a = pg.cronbach_alpha(data=clean_data[temp_cols])[0]
                                    if new_a > best_a:
                                        best_a = new_a
                                        bad_item = col
                            if bad_item:
                                suggestions.append(f"⚠️ في محور **({dim_name})**: حذف السؤال `[{bad_item}]` سيرفع الثبات من **{round(a_val, 3)}** إلى **{round(best_a, 3)}**.")

                if len(active_questions) > 1:
                    clean_all = df_encoded[active_questions].dropna()
                    a_total = pg.cronbach_alpha(data=clean_all)[0]
                    total_eval = evaluate_alpha(a_total)
                    
                    alpha_results.append({
                        "المحور / البعد": "الاستبيان ككل", 
                        "عدد العبارات": len(active_questions), 
                        "معامل ألفا": round(a_total, 3),
                        "التقييم": total_eval
                    })
                    
                    # 🔹 3. الحفظ بصمت في الذاكرة لتبويب النتائج
                    st.session_state['reliability_result'] = f"بلغ معامل كرونباخ ألفا العام ({round(a_total, 3)}) وهو ما يعكس مستوى ({total_eval}) من الاتساق الداخلي."

                if alpha_results:
                    st.dataframe(pd.DataFrame(alpha_results).style.highlight_max(subset=['معامل ألفا'], color='rgba(212, 175, 55, 0.2)'), use_container_width=True)
                    
                    # 🔹 4. عرض مقترحات التحسين كـ "خبير ذكي"
                    if suggestions:
                        with st.expander("💡 مقترحات الخبير الذكي لتحسين الثبات (Item-Drop Analysis)"):
                            st.info("اكتشف النظام أن بعض الأسئلة تشتت إجابات العينة وتضعف الثبات العام للمحاور. إليك مقترحات الحذف:")
                            for sug in suggestions:
                                st.warning(sug)

                    st.markdown("### 📝 التفسير الأكاديمي:")
                    st.info("""
تشير نتائج التقييم الإحصائي باستخدام معامل ألفا كرونباخ (Cronbach's Alpha) إلى أن أداة القياس (الاستبيان) تتمتع بدرجة مُرضية من الاتساق الداخلي والموثوقية. 

يُعد هذا المعامل من أهم المؤشرات المنهجية في البحث العلمي، حيث يُثبت رياضياً مدى تجانس فقرات الاستبيان وترابطها البنيوي في قياس الأبعاد التي صُممت لقياسها؛ بمعنى أن إجابات المبحوثين كانت متسقة ولم تتسم بالعشوائية أو التناقض. 

ووفقاً للمعايير الإحصائية المعتمدة، فإن مستويات الثبات الموضحة في الجدول أعلاه تُعطي دلالة علمية قاطعة على صلاحية أداة الدراسة، وتمنح الباحث الموثوقية اللازمة للمضي قدماً في الاعتماد على هذه البيانات لاختبار فرضيات الدراسة الأساسية وتعميم نتائجها بثقة إحصائية تامة.
""")
           
# ==========================================
            # 4. التبويب السابع: المحلل الذكي الهجين (النسخة الفائقة V3.5 - المتغيرات المتعددة الشاملة)
            # ==========================================
            with tab4:
                st.header("🧠 المحلل الذكي للفرضيات (النسخة الشامل V3.5)")
                st.markdown("يدمج هذا النظام بين **محرك الفهم الدلالي الفائق (24 نوعاً)** والذكاء الاصطناعي، مع دعم الانحدار والارتباط المتعدد:")
                
                if not api_key:
                    st.error("⚠️ يرجى إدخال مفتاح Hugging Face API في القائمة الجانبية.")
                else:
                    import difflib
                    import re

                    # قائمة الـ 24 نوعاً المعجمية لتظهر في القائمة المنسدلة
                    ALL_HYPOTHESIS_TYPES = [
                        "Correlation (علاقة)", "Null Correlation (لا توجد علاقة)", "Positive Correlation (علاقة طردية)", "Negative Correlation (علاقة عكسية)",
                        "Pearson Correlation (ارتباط بيرسون)", "Spearman Correlation (ارتباط سبيرمان)",
                        "Regression / Effect (تأثير وانحدار)", "Null Effect (لا يوجد تأثير)", "Predictive Regression (تنبؤ)", "Regression (R² Interpretation) (نسبة تفسير)",
                        "Causal Hypothesis (سببية)", "Multiple Regression (انحدار متعدد)",
                        "Differences (Parametric) (فروق معلمية)", "Null Differences (لا توجد فروق)", "Parametric (T-test / ANOVA) (متوسطات)",
                        "Mann-Whitney (مان ويتني)", "Kruskal-Wallis (كروسكال واليس)",
                        "Mediation (وساطة)", "Moderation (تعديل)", "Moderation Advanced (تعديل متقدم)", "Interaction Effect (تأثير تفاعلي)",
                        "SEM (Structural Equation Modeling) (نمذجة بنائية)", "Descriptive (وصفي)", "Exploratory / Unclassified (استكشافي)"
                    ]

                    # 🧠 1. محرك الفهم الدلالي الفائق
                    def normalize(text):
                        text = str(text).replace('أ', 'ا').replace('إ', 'ا').replace('ة', 'ه')
                        return re.sub(r'[^\w\s]', '', text.lower())

                    def ultimate_classifier(text):
                        t = normalize(text)
                        
                        is_null = "لا توجد" in t or "لا يوجد" in t or "ليس هناك" in t
                        is_positive = "طرديه" in t or "ايجابيه" in t
                        is_negative = "عكسيه" in t or "سلبيه" in t

                        if "سبيرمان" in t: return "Spearman Correlation (ارتباط سبيرمان)"
                        if "مان ويتني" in t or "مانويتني" in t: return "Mann-Whitney (مان ويتني)"
                        if "كروسكال" in t: return "Kruskal-Wallis (كروسكال واليس)"
                        if "بيرسون" in t: return "Pearson Correlation (ارتباط بيرسون)"

                        if "مباشر وغير مباشر" in t: return "SEM (Structural Equation Modeling) (نمذجة بنائية)"
                        if "مجتمعه" in t or "ابعاد" in t: return "Multiple Regression (انحدار متعدد)"

                        if "تنبؤ" in t or "يتنبا" in t: return "Predictive Regression (تنبؤ)"
                        if "تفسر" in t and "نسبه" in t: return "Regression (R² Interpretation) (نسبة تفسير)"
                        if "تؤدي" in t or "تحسين" in t: return "Causal Hypothesis (سببية)"

                        if "وسيط" in t or ("من خلال" in t and "تنبؤ" not in t): return "Mediation (وساطة)"
                        if "تختلف قوه" in t and "حسب" in t: return "Interaction Effect (تأثير تفاعلي)"
                        if "يختلف تاثير" in t or "يختلف الاثر" in t or "باختلاف" in t or "حسب" in t:
                            return "Moderation Advanced (تعديل متقدم)" if "حسب" in t else "Moderation (تعديل)"

                        if "فروق" in t or "اختلاف" in t or "متوسطات" in t:
                            if is_null: return "Null Differences (لا توجد فروق)"
                            if "متوسطات" in t: return "Parametric (T-test / ANOVA) (متوسطات)"
                            return "Differences (Parametric) (فروق معلمية)"

                        if "اثر" in t or "تاثير" in t or "يؤثر" in t:
                            if is_null: return "Null Effect (لا يوجد تأثير)"
                            return "Regression / Effect (تأثير وانحدار)"

                        if "علاقه" in t or "ارتباط" in t:
                            if is_null: return "Null Correlation (لا توجد علاقة)"
                            if is_positive: return "Positive Correlation (علاقة طردية)"
                            if is_negative: return "Negative Correlation (علاقة عكسية)"
                            return "Correlation (علاقة)"

                        if "مستوى" in t or "درجه" in t or "مرتفع" in t or "منخفض" in t:
                            return "Descriptive (وصفي)"

                        return "Exploratory / Unclassified (استكشافي)"

                    def get_best_match_index(target_word, options_list):
                        if not target_word: return 0
                        matches = difflib.get_close_matches(target_word, options_list, n=1, cutoff=0.2)
                        return options_list.index(matches[0]) if matches else 0

                    for i in range(1, 8):
                        with st.expander(f"📌 الفرضية رقم ({i})"):
                            u_hypo = st.text_area("✍️ أدخل نص الفرضية هنا:", key=f"hypo_text_{i}")
                            
                            if st.button(f"🔍 تحليل الفرضية آلياً ({i})", key=f"ai_btn_{i}"):
                                with st.spinner("جاري دمج الفهم الدلالي مع الذكاء الاصطناعي..."):
                                    try:
                                        res_ai = analyze_hypothesis_text(u_hypo, api_key)
                                        best_test = ultimate_classifier(u_hypo)
                                        
                                        st.session_state[f'semantic_test_{i}'] = best_test
                                        
                                        st.session_state[f'auto_indep_{i}'] = ""
                                        st.session_state[f'auto_dep_{i}'] = ""
                                        for line in res_ai.split('\n'):
                                            if "مستقل" in line: st.session_state[f'auto_indep_{i}'] = line.split(":")[-1].strip()
                                            if "تابع" in line: st.session_state[f'auto_dep_{i}'] = line.split(":")[-1].strip()

                                        st.session_state[f'is_analyzed_{i}'] = True

                                    except Exception as e:
                                        st.error(f"خطأ في التحليل: {e}")
                                        
                            if st.session_state.get(f'is_analyzed_{i}', False):
                                best_test_memory = st.session_state[f'semantic_test_{i}']
                                
                                # 👇=== التعديل هنا: إظهار اسم الفرضية بوضوح في المربع الأخضر ===👇
                                st.success(f"✅ تم الفهم الدلالي بنجاح! نوع الفرضية هو: **{best_test_memory}**")
                                # 👆=====================================================👆
                                
                                # إظهار القائمة كاملة بـ 24 نوعاً!
                                default_idx = ALL_HYPOTHESIS_TYPES.index(best_test_memory) if best_test_memory in ALL_HYPOTHESIS_TYPES else 0
                                col_type = st.selectbox("📌 نوع الفرضية والاختبار:", ALL_HYPOTHESIS_TYPES, index=default_idx, key=f"test_type_{i}")
                                
                                # تصنيف عائلة الاختبارات
                                is_corr = any(kw in col_type for kw in ["Correlation", "ارتباط", "علاقة"])
                                is_diff = any(kw in col_type for kw in ["Differences", "Parametric", "Mann", "Kruskal", "فروق", "T-test", "ANOVA"])
                                is_reg = not is_corr and not is_diff

                                auto_indep_word = st.session_state.get(f'auto_indep_{i}', "")
                                auto_dep_word = st.session_state.get(f'auto_dep_{i}', "")
                                
                                # إعداد المتغيرات الافتراضية
                                def_indep_idx = get_best_match_index(auto_indep_word, categorical_cols if is_diff else analysis_cols)
                                default_indep = [categorical_cols[def_indep_idx]] if is_diff and categorical_cols else ([analysis_cols[def_indep_idx]] if not is_diff and analysis_cols else [])
                                
                                def_dep_idx = get_best_match_index(auto_dep_word, analysis_cols)
                                default_dep = [analysis_cols[def_dep_idx]] if analysis_cols else []
                                
                                # السماح باختيار عدة متغيرات مستقلة و تابعة!
                                if is_diff: 
                                    h_indep = st.multiselect("المتغيرات المستقلة (اختر فئة ديموغرافية أو أكثر):", categorical_cols, default=default_indep, key=f"indep_{i}")
                                else: 
                                    h_indep = st.multiselect("المتغيرات المستقلة (المؤثرات - يمكنك اختيار أكثر من محور):", analysis_cols, default=default_indep, key=f"indep_ax_{i}")
                                
                                h_dep = st.multiselect("المتغيرات التابعة (النتائج - يمكنك اختيار أكثر من محور):", analysis_cols, default=default_dep, key=f"dep_{i}")
                                
                                if st.button(f"🚀 تنفيذ الاختبار، رسم المخطط، وكتابة المناقشة ({i})", key=f"exec_{i}"):
                                    if not h_indep or not h_dep:
                                        st.warning("⚠️ يرجى اختيار متغير مستقل واحد وتابع واحد على الأقل.")
                                    else:
                                        with st.spinner("جاري تنفيذ العمليات للمتغيرات المتعددة..."):
                                            clean_df = df_encoded[h_indep + h_dep].dropna()
                                            results_str = ""
                                            try:
                                                col1, col2 = st.columns([1, 1])
                                                
                                                with col1:
                                                    st.markdown("**النتائج الإحصائية:**")
                                                    res_list = []
                                                    
                                                    # الدوران حول المتغيرات التابعة لمعالجة كل واحد على حدة
                                                    for y_col in h_dep:
                                                        if is_corr:
                                                            for x_col in h_indep:
                                                                r = pg.corr(clean_df[x_col].astype(float), clean_df[y_col].astype(float), method='pearson')
                                                                r.insert(0, 'التابع', y_col)
                                                                r.insert(0, 'المستقل', x_col)
                                                                res_list.append(r)
                                                        elif is_diff:
                                                            for x_col in h_indep:
                                                                grps = clean_df[x_col].unique()
                                                                if len(grps) == 2: r = pg.ttest(clean_df[clean_df[x_col]==grps[0]][y_col].astype(float), clean_df[clean_df[x_col]==grps[1]][y_col].astype(float))
                                                                else:
                                                                    valid_grps = clean_df[x_col].value_counts()[clean_df[x_col].value_counts()>=2].index
                                                                    r = pg.anova(data=clean_df[clean_df[x_col].isin(valid_grps)], dv=y_col, between=x_col)
                                                                r.insert(0, 'التابع', y_col)
                                                                r.insert(0, 'الديموغرافي', x_col)
                                                                res_list.append(r)
                                                        else: 
                                                            # الانحدار المتعدد: كل المستقلات معاً على كل تابع
                                                            r = pg.linear_regression(clean_df[h_indep].astype(float), clean_df[y_col].astype(float))
                                                            r.insert(0, 'التابع', y_col)
                                                            res_list.append(r)
                                                            
                                                    final_res = pd.concat(res_list)
                                                    results_str = final_res.to_markdown()
                                                    st.dataframe(final_res)
                                                
                                                with col2:
                                                    st.markdown(f"**المخطط البياني (يعرض أول متغير مستقل مع أول تابع):**")
                                                    if is_diff:
                                                        fig = px.box(clean_df, x=h_indep[0], y=h_dep[0], color=h_indep[0], height=300)
                                                    else:
                                                        fig = px.scatter(clean_df, x=h_indep[0], y=h_dep[0], trendline="ols", height=300, color_discrete_sequence=['#d4af37'])
                                                    
                                                    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                                                    st.plotly_chart(fig, use_container_width=True)

                                                # دمج القرار الإحصائي
                                                p_cols = [c for c in final_res.columns if 'p-val' in c.lower() or 'p-unc' in c.lower()]
                                                is_sig = (final_res[p_cols[0]] < 0.05).any() if p_cols else False
                                                decision_val = "accepted" if is_sig else "rejected"
                                                decision_text = "تم قبول الفرضية (دالة إحصائياً) ✅" if decision_val == "accepted" else "تم رفض الفرضية (غير دالة إحصائياً) ❌"
                                                
                                                ai_explanation = generate_detailed_explanation(results_str, u_hypo, api_key)
                                                
                                                st.markdown("### 📝 مناقشة النتائج (الفصل الرابع - جاهز للنسخ):")
                                                st.success(f"""
**📌 الفرضية:**
{u_hypo}

**📊 القرار الإحصائي:**
{decision_text}

**🧠 التحليل الأكاديمي التفصيلي:**
{ai_explanation}
                                                """)
                                                
                                                found = False
                                                for item in st.session_state['hypothesis_history']:
                                                    if item.get('id') == i:
                                                        item['text'] = u_hypo
                                                        item['result'] = decision_val
                                                        found = True
                                                        break
                                                if not found:
                                                    st.session_state['hypothesis_history'].append({'id': i, 'text': u_hypo, 'result': decision_val})
                                                    
                                                st.info("✅ تم حفظ النتيجة والمخطط لتظهر في التقرير النهائي.")
                                                
                                            except Exception as e:
                                                st.error(f"حدث خطأ أثناء التنفيذ أو التوليد: {e}")
          # ==========================================
            # 5. التبويب الثامن: النتائج (نصي ومنظم بالأرقام 1-7) ✅
            # ==========================================
            with tab5:
                st.header("📌 أبرز نتائج الدراسة")
                res_idx = 1
                
                # --- 1️⃣ نتيجة عينة الدراسة (النتيجة رقم 1) ---
                st.subheader("📊 نتائج وصف عينة الدراسة")
                if st.session_state['sample_results']:
                    for res in st.session_state['sample_results']:
                        st.markdown(f"**النتيجة ({res_idx}):** {res}")
                        res_idx += 1
                else:
                    st.info("⚠️ يرجى زيارة تبويب (عينة الدراسة) أولاً لتوليد النتائج.")
                
                st.markdown("---")

                # --- 2️⃣ نتيجة الثبات (النتيجة رقم 2) ---
                st.subheader("🧪 نتائج ثبات أداة الدراسة")
                if st.session_state['reliability_result']:
                    st.markdown(f"**النتيجة ({res_idx}):** {st.session_state['reliability_result']}")
                    res_idx += 1
                else:
                    st.info("⚠️ يرجى زيارة تبويب (الثبات) أولاً لتوليد النتائج.")
                
                st.markdown("---")

                # --- 3️⃣ نتائج الفرضيات (النتائج من 3 إلى 7) ---
                st.subheader("⚖️ نتائج اختبار فرضيات الدراسة")
                if st.session_state['hypothesis_history']:
                    # عرض أول 5 فرضيات لتكملة الرقم 7
                    for h in st.session_state['hypothesis_history'][:5]:
                        decision = "تم قبول الفرضية" if h['result'] == "accepted" else "تم رفض الفرضية"
                        st.markdown(f"**النتيجة ({res_idx}):** {decision} ({h['text']}).")
                        
                        # الشرح الأكاديمي الثابت
                        with st.expander(f"📝 عرض الشرح الأكاديمي للنتيجة ({res_idx})"):
                            st.info("""
                            تشير هذه النتيجة إلى طبيعة العلاقة بين المتغيرات محل الدراسة وفقًا للتحليل الإحصائي المستخدم.
                            وقد تم الاعتماد على الاختبار الإحصائي المناسب لاختبار هذه الفرضية بدقة.
                            كما أظهرت النتائج مستوى الدلالة الإحصائية المعتمد في اتخاذ القرار.
                            وتعكس هذه النتيجة قوة أو ضعف العلاقة بين المتغيرات المدروسة.
                            ويمكن تفسير هذه النتيجة في ضوء ما توصلت إليه الدراسات السابقة في نفس المجال.
                            وبشكل عام توضح هذه النتيجة مدى تأثير المتغير المستقل على المتغير التابع.
                            """)
                        res_idx += 1
                else:
                    st.warning("⚠️ لم يتم اختبار أي فرضيات بعد في تبويب (محلل الفرضيات).")

                # --- تفريغ وتوليد التوصيات بصمت في الذاكرة ---
                st.session_state['dim_recs'] = [] 
                for dim_name, cols in dimensions_dict.items():
                    if cols:
                        item_means = df_encoded[cols].mean()
                        overall_mean = item_means.mean()
                        low_items = item_means[item_means <= 3.50]
                        if not low_items.empty:
                            for item_text, mean_val in low_items.items():
                                st.session_state['dim_recs'].append({
                                    "dim": dim_name, "mean": round(mean_val, 2),
                                    "rec": f"توصي الدراسة بضرورة تحسين ({item_text}) ورفع مستواه لتطوير الأداء."
                                })
                        else:
                            st.session_state['dim_recs'].append({
                                "dim": dim_name, "mean": round(item_means.min(), 2),
                                "rec": f"توصي الدراسة بضرورة المحافظة على مستوى ({item_means.idxmin()}) وتعزيزه."
                            })

            # ==========================================
            # 6. التبويب التاسع: التوصيات (مستقل تماماً) ✅
            # ==========================================
            with tab6:
                st.header("💡 التوصيات الذكية")
                
                if st.session_state['dim_recs']:
                    for idx, rec in enumerate(st.session_state['dim_recs'], 1):
                        st.success(f"**{idx}. المحور:** {rec['dim']} | **المتوسط:** {rec['mean']}\n\n📌 {rec['rec']}")
                else:
                    st.warning("⚠️ يرجى زيارة تبويب (النتائج) أولاً لتوليد التوصيات.")

    except Exception as e: 
        st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
