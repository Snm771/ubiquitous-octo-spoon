# =====================================================================
# 🚀 نظام AttendAI - إدارة الحضور والانصراف بالذكاء الاصطناعي (SaaS)
# =====================================================================

import os
import sys
import io
import re
import time
import json
import base64
import socket
import hashlib
import logging
import threading
import subprocess
from datetime import datetime

# 📦 التثبيت التلقائي لمكتبات الحماية والخزنة
def install_requirements():
    required_packages = {
        "python-dotenv": "dotenv",
        "wmi": "wmi",
        "bcrypt": "bcrypt",
        "Flask-Limiter": "flask_limiter",
        "openpyxl": "openpyxl" # مكتبة هامة للإكسل
    }
    for package, module in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            print(f"⏳ جاري تثبيت مكتبة الحماية ({package})...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

from dotenv import load_dotenv
import wmi
import bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import cv2
import numpy as np
import pandas as pd
import requests
import face_recognition

from tkinter import Tk, Label, Entry, Button, messagebox
from flask import Flask, request, jsonify, render_template_string, send_file, session, redirect, url_for

import firebase_admin
from firebase_admin import credentials, db

# تشغيل الخزنة السرية
load_dotenv()

# =====================================================================
# 🛡️ نظام المراقبة السرية (Audit Logging)
# =====================================================================
logging.basicConfig(
    filename='security_audit.log', 
    level=logging.WARNING, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# =====================================================================
# 🛡️ دوال الحماية المتقدمة (Validation, Sanitization, Hashing)
# =====================================================================
def hash_password(password):
    """تشفير الكلمات السرية باتجاه واحد"""
    return bcrypt.hashpw(str(password).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """التحقق من مطابقة الكلمة مع التشفير"""
    try:
        return bcrypt.checkpw(str(password).encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return str(password) == str(hashed)

def sanitize_input(text, allowed_type="text"):
    """تنظيف المدخلات والتحقق من الصيغ لمنع الحقن والتلاعب"""
    if text is None: return ""
    text = str(text).strip()
    
    if allowed_type == "pin":
        if not text.isdigit() or len(text) > 8: return ""
        return text
    elif allowed_type == "id":
        return re.sub(r'[^a-zA-Z0-9_-]', '', text)[:20]
    elif allowed_type == "name":
        return re.sub(r'[^\w\s\u0600-\u06FF]', '', text)[:50]
        
    return re.sub(r'[<>"\';=]', '', text)[:150]

# =====================================================================
# 🌐 1. تهيئة قاعدة البيانات (Firebase) - [مؤمنة بالخزنة]
# =====================================================================
CRED_PATH = os.getenv("FIREBASE_CRED_FILE", "attendancesystem-ab9bb-firebase-adminsdk-fbsvc-3f4f441a66.json")
DB_URL = os.getenv("FIREBASE_DB_URL", "https://attendancesystem-ab9bb-default-rtdb.firebaseio.com")

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH), {
        'databaseURL': DB_URL
    })

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except:
        return False

def get_hwid():
    try:
        c = wmi.WMI()
        for board in c.Win32_BaseBoard():
            return hashlib.sha256(board.SerialNumber.strip().encode()).hexdigest()[:12].upper()
    except:
        return "UNKNOWN_HWID"

# =====================================================================
# 🛡️ 2. نظام الحماية والتفعيل السحابي - [AttendAI Guard]
# =====================================================================
def online_activation_guard():
    hwid = get_hwid()
    lic_file = "locked.lic"
    saas_file = "saas_config.json"
    
    salt = os.getenv("HWID_SALT", "SOHAIB_SECURE_KEY_2026")
    
    if os.path.exists(lic_file) and os.path.exists(saas_file):
        with open(lic_file, "r") as f:
            if f.read().strip() == hashlib.sha256((hwid + salt).encode()).hexdigest()[:8].upper():
                return True

    root = Tk()
    root.title("تفعيل نظام AttendAI - نسخة الشركات")
    root.geometry("450x550") 
    root.configure(bg="#0f172a") 
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - 225
    y = (root.winfo_screenheight() // 2) - 275
    root.geometry(f'+{x}+{y}')

    Label(root, text="🌐 تفعيل نظام AttendAI", font=("Arial", 16, "bold"), bg="#0f172a", fg="#3b82f6").pack(pady=15)
    Label(root, text="الجهاز يحتاج إلى اتصال بالإنترنت لمرة واحدة فقط للتفعيل.", font=("Arial", 10), bg="#0f172a", fg="gray").pack()
    
    Label(root, text="(HWID) المعرف المادي لجهازك:", font=("Arial", 10, "bold"), bg="#0f172a", fg="white").pack(pady=(15, 0))
    hwid_display = Label(root, text=hwid, fg="#10b981", font=("Consolas", 14, "bold"), bg="#1e293b", padx=15, pady=8)
    hwid_display.pack(pady=5)

    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(hwid)
        messagebox.showinfo("تم النسخ", "تم نسخ معرف الجهاز بنجاح!\nيمكنك إرساله للمهندس صهيب.")

    Button(root, text="📋 نسخ المعرف", command=copy_to_clipboard, bg="#3b82f6", fg="white", font=("Arial", 10), relief="flat", padx=10).pack(pady=5)

    Label(root, text="(Company ID) معرف الشركة:", font=("Arial", 11, "bold"), bg="#0f172a", fg="white").pack(pady=(15, 5))
    entry_id = Entry(root, justify='center', font=("Arial", 14), width=25, bg="#1e293b", fg="white", insertbackground="white", relief="flat")
    entry_id.pack(ipady=5)

    Label(root, text="مفتاح التفعيل (Serial Key):", font=("Arial", 11, "bold"), bg="#0f172a", fg="white").pack(pady=(15, 5))
    entry_serial = Entry(root, justify='center', font=("Arial", 14), width=25, bg="#1e293b", fg="white", insertbackground="white", relief="flat")
    entry_serial.pack(ipady=5)

    def activate():
        if not check_internet():
            messagebox.showerror("خطأ في الشبكة", "❌ يرجى توصيل الكمبيوتر بالإنترنت للتحقق من الرخصة!")
            return
            
        comp_id = entry_id.get().strip()
        serial = entry_serial.get().strip()
        
        if not comp_id or not serial:
            messagebox.showwarning("تنبيه", "الرجاء إدخال جميع البيانات!")
            return

        try:
            license_ref = db.reference(f'Licenses/{comp_id}')
            license_data = license_ref.get()

            if not license_data:
                messagebox.showerror("خطأ", "❌ معرف الشركة غير صحيح!")
                return
                
            if str(license_data.get('serial_key')) != serial:
                messagebox.showerror("خطأ", "❌ مفتاح التفعيل غير صحيح!")
                return
                
            db_hwid = license_data.get('hwid', "")
            if db_hwid != "" and db_hwid != hwid:
                messagebox.showerror("مرفوض", "🚨 هذا المفتاح مستخدم ومسجل على كمبيوتر آخر!")
                return

            license_ref.update({'hwid': hwid})
            
            raw_admin_pass = license_data.get('admin_pass', '123')
            secure_admin_pass = hash_password(raw_admin_pass)

            config_data = {
                "company_id": comp_id,
                "company_name": license_data.get('company_name', 'مؤسسة غير محددة'),
                "admin_pass": secure_admin_pass,
                "tele_token": license_data.get('tele_token', ''),
                "chat_id": license_data.get('chat_id', ''),
                "enable_tele": True,
                "last_active_status": True 
            }
            with open(saas_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
                
            secure_key = hashlib.sha256((hwid + salt).encode()).hexdigest()[:8].upper()
            with open(lic_file, "w", encoding='utf-8') as f:
                f.write(secure_key)
                
            db.reference(f'Companies/{comp_id}/Settings').update({'admin_pass': secure_admin_pass})
                
            messagebox.showinfo("نجاح 🚀", f"تم التفعيل بنجاح!\nمرحباً بك في AttendAI: {config_data['company_name']}")
            root.destroy()

        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الاتصال بالسيرفر: {str(e)}")

    Button(root, text="✅ التحقق والتفعيل", command=activate, bg="#10b981", fg="white", font=("Arial", 12, "bold"), width=20, pady=8, relief="flat").pack(pady=20)
    
    Label(root, text="Developed by Sohaib Pro", font=("Arial", 9), bg="#0f172a", fg="gray").pack()
    Label(root, text="📞 الدعم الفني: 771669519", font=("Arial", 11, "bold"), bg="#0f172a", fg="#f59e0b").pack()

    root.mainloop()
    return os.path.exists(lic_file) and os.path.exists(saas_file)

if not online_activation_guard(): sys.exit()

# =====================================================================
# 🏢 3. إعدادات السيرفر الأساسية (Flask & Headers) - [مؤمنة]
# =====================================================================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "SOHAIB_PRO_SECRET_2026_ULTIMATE")
app.config['SESSION_PERMANENT'] = False

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Internal Server Error: {str(e)}")
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "❌ حدث خطأ داخلي في السيرفر."}), 500
    return "<h1 style='text-align:center; color:red; margin-top:50px;'>🛑 500 - Internal Server Error</h1>", 500

@app.errorhandler(429)
def ratelimit_handler(e):
    logging.warning(f"Rate limit exceeded by IP: {request.remote_addr}")
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "❌ تم حظرك مؤقتاً بسبب كثرة المحاولات!"}), 429
    return "<h1 style='text-align:center; color:red; margin-top:50px;'>🛑 تم حظرك مؤقتاً بسبب كثرة المحاولات. انتظر قليلاً.</h1>", 429

SAAS_CONFIG_FILE = 'saas_config.json'

def load_saas_config():
    if os.path.exists(SAAS_CONFIG_FILE):
        try:
            with open(SAAS_CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {"company_name": "مؤسسة غير محددة", "company_id": "DEFAULT_COMP", "tele_token": "", "chat_id": "", "admin_pass": hash_password("123"), "enable_tele": True, "last_active_status": True}

saas_cfg = load_saas_config()
COMPANY_ID = saas_cfg.get("company_id", "DEFAULT_COMP")

def get_db(path): 
    return db.reference(f'Companies/{COMPANY_ID}/{path}')

def is_system_active():
    cfg = load_saas_config()
    if check_internet():
        try:
            status = db.reference(f'Licenses/{COMPANY_ID}/is_active').get()
            if status is not None:
                cfg['last_active_status'] = status
                with open(SAAS_CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=4)
                return status
        except: pass
    return cfg.get('last_active_status', True)

def get_current_admin_pass():
    try:
        val = get_db('Settings/admin_pass').get()
        if val: return str(val)
    except: pass
    return saas_cfg.get("admin_pass", hash_password("123"))

def send_tel(msg):
    cfg = load_saas_config()
    if str(cfg.get("enable_tele", True)).lower() == 'false': return  
    token = cfg.get("tele_token")
    chat = cfg.get("chat_id")
    if not token or not chat: return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat, "text": msg}, timeout=5)
    except: pass

# =====================================================================
# 💾 4. نظام الأوفلاين والمزامنة (Offline Cache)
# =====================================================================
def update_local_cache(emps, sets, atts_today):
    try:
        with open('local_cache.json', 'w', encoding='utf-8') as f: 
            json.dump({'emps': emps, 'sets': sets, 'atts_today': atts_today}, f, ensure_ascii=False)
    except: pass

def get_offline_records():
    if not os.path.exists('offline_records.json'): return []
    try:
        with open('offline_records.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def clear_offline_records():
    if os.path.exists('offline_records.json'): os.remove('offline_records.json')

def save_offline_record(record):
    records = get_offline_records()
    records.append(record)
    with open('offline_records.json', 'w', encoding='utf-8') as f: json.dump(records, f, ensure_ascii=False)

def parse_time(t_str):
    try: h, m = map(int, t_str.split(':')); return h * 60 + m
    except: return 0

def process_sync():
    records = get_offline_records()
    if not records: return False
    sync_details = []
    for r in records:
        if r['type'] == 'in':
            get_db(f"Attendance/{r['date']}/{r['emp_id']}").update({'in_time': r['time'], 'in_min': r['min'], 'device_id': r.get('device_id', '-')})
        else:
            get_db(f"Attendance/{r['date']}/{r['emp_id']}").update({'out_time': r['time']})
        action_ar = "حضور ✅" if r['type'] == 'in' else "انصراف 🚪"
        sync_details.append(f"👤 {r['name']} | {action_ar} | ⏰ {r['time']}")
    clear_offline_records()
    msg_body = "\n".join(sync_details)
    send_tel(f"🤖 *مزامنة تلقائية للأوفلاين (AttendAI)* 🌐\nتم رفع ({len(records)}) سجلات معلقة:\n\n{msg_body}")
    return True

def auto_sync_worker():
    while True:
        time.sleep(20)
        try:
            if len(get_offline_records()) > 0 and check_internet(): process_sync()
        except: pass

# =====================================================================
# 📱 5. واجهات برمجة التطبيقات للجوال (Mobile APIs)
# =====================================================================
@app.route('/api/v1/status', methods=['GET'])
def app_status():
    sets = get_db('Settings').get() or {}
    is_bio = str(sets.get('req_bio', False)).lower() == 'true' or sets.get('req_bio') is True
    return jsonify({"req_bio": is_bio, "official_bssid": sets.get('official_bssid', ''), "announcement": sets.get('announcement', '')})

@app.route('/api/v1/update_bssid', methods=['POST'])
@limiter.limit("10 per minute")
def update_bssid_api():
    input_pass = request.json.get('admin_pass', '')
    if not check_password(input_pass, get_current_admin_pass()): 
        logging.warning(f"محاولة فاشلة لتحديث الراوتر من IP: {request.remote_addr}")
        return jsonify({"status": "error", "message": "❌ رمز الإدارة خطأ!"}), 401
    
    new_bssid = sanitize_input(request.json.get('bssid'))
    
    if check_internet():
        get_db('Settings').update({"official_bssid": new_bssid})
        
    try:
        with open('local_cache.json', 'r', encoding='utf-8') as f: cache = json.load(f)
        if 'sets' not in cache: cache['sets'] = {}
        cache['sets']['official_bssid'] = new_bssid
        with open('local_cache.json', 'w', encoding='utf-8') as f: json.dump(cache, f, ensure_ascii=False)
    except: pass

    return jsonify({"status": "success", "message": "✅ تم اعتماد راوتر الشركة لجميع الموظفين!"})

@app.route('/api/v1/mark/<emp_id>/<type>', methods=['POST'])
@limiter.limit("30 per minute")
def mark_logic(emp_id, type):
    req_data = request.json
    device_id = sanitize_input(req_data.get('device_id'))
    pin_input = sanitize_input(req_data.get('pin'), "pin") 
    image_data = req_data.get('image_data') 
    
    if not pin_input: return jsonify({"status": "error", "message": "❌ الرمز PIN غير صالح."})

    now = datetime.now()
    today, log_time, curr_min = now.strftime("%Y-%m-%d"), now.strftime("%I:%M:%S %p"), (now.hour * 60 + now.minute)
    days_ar = {"Saturday":"السبت", "Sunday":"الأحد", "Monday":"الإثنين", "Tuesday":"الثلاثاء", "Wednesday":"الأربعاء", "Thursday":"الخميس", "Friday":"الجمعة"}
    telegram_date = f"📅 {days_ar.get(now.strftime('%A'), '')}، {today}"
    is_online = check_internet()

    if is_online:
        emps, sets = get_db('Employees').get() or {}, get_db('Settings').get() or {"in_s": "08:00", "in_e": "09:00", "out_s": "16:00", "req_bio": False}
        atts_today = get_db(f'Attendance/{today}').get() or {}
        update_local_cache(emps, sets, atts_today)
    else:
        try:
            with open('local_cache.json', 'r', encoding='utf-8') as f: cache = json.load(f); emps, sets, atts_today = cache.get('emps', {}), cache.get('sets', {}), cache.get('atts_today', {})
        except: return jsonify({"status": "error", "message": "❌ لا يوجد إنترنت!"})

    today_record = atts_today.get(emp_id, {}) if isinstance(atts_today, dict) else {}
    emp_data = emps.get(emp_id)
    
    if not emp_data or not isinstance(emp_data, dict): return jsonify({"status": "error", "message": "❌ الموظف غير مسجل أو بياناته تالفة"})
    
    if not check_password(pin_input, str(emp_data.get('pin'))): 
        logging.warning(f"محاولة تحضير برمز خاطئ للموظف {emp_id} من IP: {request.remote_addr}")
        return jsonify({"status": "error", "message": "❌ الرمز PIN خطأ"})

    reg_id = emp_data.get('device_serial')
    if not reg_id:
        if not is_online: return jsonify({"status": "error", "message": "❌ ربط الجهاز لأول مرة يحتاج إنترنت."})
        if device_id and device_id != 'Unknown_Device':
            conflicting_user = next((info.get('full_name') for eid, info in emps.items() if isinstance(info, dict) and str(eid) != str(emp_id) and info.get('device_serial') == device_id), None)
            if conflicting_user: 
                send_tel(f"🚨 محاولة غش!\n👤 الموظف: {emp_data.get('full_name')}\n📱 حاول استخدام جوال محجوز للموظف: {conflicting_user}")
                return jsonify({"status": "error", "message": f"❌ محاولة مرفوضة! هذا الجهاز مربوط مسبقاً بالموظف: {conflicting_user}"})
        get_db(f'Employees/{emp_id}').update({'device_serial': device_id})
        reg_id = device_id 
        if type == "link" and not image_data: return jsonify({"status": "success", "message": "✅ تم ربط الحساب والجهاز بنجاح!"})
    elif reg_id != device_id: return jsonify({"status": "error", "message": "❌ هذا الحساب مرتبط بجوال آخر!"})

    is_bio_required = str(sets.get('req_bio', False)).lower() == 'true' or sets.get('req_bio') is True
    if is_bio_required and not image_data and type not in ['link_device', 'link']: return jsonify({"status": "error", "message": "❌ التحضير مرفوض! الإدارة تتطلب التقاط صورة."})
    if type == "link" and not image_data: return jsonify({"status": "success", "message": "✅ حسابك مرتبط مسبقاً وجاهز!"})

    if image_data:
        try:
            rgb_img = cv2.cvtColor(cv2.imdecode(np.frombuffer(base64.b64decode(image_data), np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_img)
            if len(face_encodings) == 0: return jsonify({"status": "error", "message": "❌ لم يتم التعرف على وجه بوضوح!"})
            elif len(face_encodings) > 1: return jsonify({"status": "error", "message": "❌ يوجد أكثر من شخص في الصورة!"})
            current_encoding = face_encodings[0]
            saved_encoding_list = emp_data.get('face_encoding')
            if not saved_encoding_list:
                if not is_online: return jsonify({"status": "error", "message": "❌ التسجيل لأول مرة يحتاج إنترنت."})
                face_already_exists, conflicting_name = False, ""
                for other_eid, other_data in emps.items():
                    if isinstance(other_data, dict) and str(other_eid) != str(emp_id) and other_data.get('face_encoding'):
                        if face_recognition.compare_faces([np.array(other_data['face_encoding'])], current_encoding, tolerance=0.45)[0]:
                            face_already_exists, conflicting_name = True, other_data.get('full_name', 'مجهول'); break
                if face_already_exists:
                    send_tel(f"🚨 محاولة انتحال شخصية!\nالموظف ({emp_data['full_name']}) حاول تسجيل وجه يعود للموظف ({conflicting_name})!")
                    return jsonify({"status": "error", "message": f"❌ محاولة مرفوضة! هذا الوجه مسجل مسبقاً للموظف: {conflicting_name}"})
                get_db(f'Employees/{emp_id}').update({'face_encoding': current_encoding.tolist()})
                send_tel(f"🧠 تم تثبيت القفل البيومتري للموظف: {emp_data['full_name']} (من جهازه المعتمد)")
                if type == 'link': return jsonify({"status": "success", "message": "✅ تم حفظ بصمة الوجه كقفل أساسي للحساب!"})
            else:
                if not face_recognition.compare_faces([np.array(saved_encoding_list)], current_encoding, tolerance=0.45)[0]: 
                    msg = "❌ محاولة مرفوضة! لديك بصمة مسجلة مسبقاً لا تطابق هذا الوجه." if type == 'link' else "❌ هذا ليس أنت! الوجه لا يتطابق مع البصمة الأصلية للحساب."
                    return jsonify({"status": "error", "message": msg})
                if type == 'link': return jsonify({"status": "success", "message": "✅ بصمة وجهك مطابقة وجاهزة."})
        except Exception: return jsonify({"status": "error", "message": "❌ خطأ أثناء تحليل الصورة!"})

    off_records = get_offline_records()
    has_in_offline = any(r['emp_id'] == emp_id and r['date'] == today and r['type'] == 'in' for r in off_records)
    has_out_offline = any(r['emp_id'] == emp_id and r['date'] == today and r['type'] == 'out' for r in off_records)
    has_in_online, has_out_online = "in_time" in today_record, "out_time" in today_record
    in_s_min, in_e_min, out_s_min = parse_time(sets.get('in_s', '08:00')), parse_time(sets.get('in_e', '09:00')), parse_time(sets.get('out_s', '16:00'))

    if type == "in":
        if has_in_online or has_in_offline: return jsonify({"status": "error", "message": "⚠️ سجلت حضورك مسبقاً!"})
        if not (in_s_min <= curr_min <= in_e_min): return jsonify({"status": "error", "message": "❌ خارج وقت الحضور"})
        if is_online:
            get_db(f'Attendance/{today}/{emp_id}').update({'in_time': log_time, 'in_min': curr_min, 'device_id': device_id})
            send_tel(f"✅ حضور: {emp_data['full_name']}\n⏰ الساعة: {log_time}\n{telegram_date}")
            msg = f"✅ تم الحضور\n⏰ {log_time}"
        else:
            save_offline_record({'emp_id': emp_id, 'name': emp_data['full_name'], 'type': 'in', 'date': today, 'time': log_time, 'min': curr_min, 'device_id': device_id})
            msg = f"⚠️ تم الحضور محلياً\n⏰ {log_time}"
        return jsonify({"status": "success", "message": msg})
    
    elif type == "out": 
        if not (has_in_online or has_in_offline): return jsonify({"status": "error", "message": "❌ سجل حضورك أولاً!"})
        if has_out_online or has_out_offline: return jsonify({"status": "error", "message": "⚠️ سجلت انصرافك مسبقاً!"})
        if curr_min < out_s_min: return jsonify({"status": "error", "message": "❌ لم يحن وقت الانصراف"})
        if is_online:
            get_db(f'Attendance/{today}/{emp_id}').update({'out_time': log_time})
            send_tel(f"🚪 انصراف: {emp_data['full_name']}\n⏰ الساعة: {log_time}\n{telegram_date}")
            msg = f"✅ تم الانصراف\n⏰ {log_time}"
        else:
            save_offline_record({'emp_id': emp_id, 'name': emp_data['full_name'], 'type': 'out', 'date': today, 'time': log_time, 'min': curr_min, 'device_id': device_id})
            msg = f"⚠️ تم الانصراف محلياً\n⏰ {log_time}"
        return jsonify({"status": "success", "message": msg})

# =====================================================================
# 🖥️ 6. لوحة تحكم السيرفر (Admin Dashboard & UI)
# =====================================================================
COMMON_ASSETS = '''
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --primary: #3b82f6; --accent: #10b981; --danger: #ef4444; --border: rgba(255,255,255,0.1); }
    .light-mode { --bg: #f1f5f9; --card: #ffffff; --text: #0f172a; --primary: #2563eb; --accent: #059669; --danger: #dc2626; --border: rgba(0,0,0,0.2); }
    body { background: var(--bg); color: var(--text); font-family: 'Poppins', Tahoma, sans-serif; transition: 0.3s; margin: 0; direction: rtl; }
    .glass { background: var(--card); border: 1px solid var(--border); border-radius: 24px; padding: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); margin-bottom: 20px; color: var(--text); }
    
    .header-box { background: var(--card); border: 2px solid rgba(59, 130, 246, 0.3); border-radius: 20px; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    .icon-box { background: linear-gradient(135deg, #2563eb, #10b981); width: 65px; height: 65px; border-radius: 16px; display: flex; justify-content: center; align-items: center; box-shadow: 0 5px 15px rgba(37, 99, 235, 0.4); }
    .icon-box i { color: white; font-size: 2.5rem; }
    
    .gradient-text { background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline-block; }
    .live-clock-top { font-size: 2.5rem; font-weight: 800; font-family: 'Courier New', Courier, monospace; margin: 0; display: inline-block; direction: ltr; } 
    .dev-credit { color: #64748b; font-size: 0.95rem; margin: 0; font-weight: bold; }
    
    .status-badge { padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; display: inline-flex; align-items: center; gap: 8px; margin-top: 5px; }
    .status-online { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; }
    .status-offline { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444; }
    
    .btn { padding: 12px; border-radius: 12px; border: none; cursor: pointer; font-weight: 700; transition: 0.3s; color: white; display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; margin: 10px 0; font-size: 1.05rem; }
    .btn-in { background: var(--primary); } .btn-out { background: var(--accent); } .btn-danger { background: var(--danger); } .btn-excel { background: #10b981; }
    input, textarea { background: rgba(128,128,128,0.1); border: 1px solid var(--border); color: var(--text); padding: 12px; border-radius: 10px; width: 100%; margin: 5px 0; box-sizing: border-box; font-family: inherit; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th { color: var(--primary); padding: 15px; border-bottom: 2px solid var(--border); background: rgba(128,128,128,0.05); text-align: start; }
    td { padding: 12px; border-bottom: 1px solid var(--border); text-align: start; color: var(--text); }
    
    .mode-btn { position: fixed; left: 20px; background: var(--card); border: 1px solid var(--border); padding: 10px; border-radius: 50%; cursor: pointer; color: var(--text); z-index: 1001; }
    .del-icon, .device-icon, .face-icon, .checkout-icon { cursor: pointer; font-size: 1.4rem; transition: 0.2s; margin: 0 8px; }
    .del-icon { color: var(--danger); } .device-icon { color: var(--primary); } .face-icon { color: #f59e0b; } .checkout-icon { color: #10b981; }
    .del-icon:hover, .device-icon:hover, .face-icon:hover, .checkout-icon:hover { transform: scale(1.2); }
    
    .switch-label {
        cursor: pointer; font-weight: bold; color: white; display: flex; align-items: center; justify-content: center; gap: 10px; margin: 15px 0 10px 0;
        background: linear-gradient(90deg, #3b82f6, #10b981); padding: 12px; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); transition: 0.3s; font-size: 1.05rem; width: 100%; box-sizing: border-box;
    }
    .switch-label:hover { filter: brightness(1.1); transform: scale(1.01); }
    .switch-label input { transform: scale(1.3); margin: 0; cursor: pointer; }
    
    .pin-badge { padding: 6px 12px; border-radius: 12px; font-weight: bold; font-family: monospace; font-size: 14px; display: inline-flex; align-items: center; gap: 8px; border: 1px solid transparent; transition: 0.3s; }
    .pin-linked { background: rgba(16, 185, 129, 0.1); color: #10b981; border-color: rgba(16, 185, 129, 0.3); }
    .pin-unlinked { background: rgba(239, 68, 68, 0.1); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
</style>
'''

@app.route('/admin', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    if not is_system_active():
        return "<h1 style='text-align:center; color:#ef4444; margin-top:100px; direction:rtl; font-family:sans-serif;'>🛑 تم إيقاف هذا النظام من قبل المزود.<br><br>يرجى التواصل مع المهندس صهيب.</h1>", 403

    if request.method == 'POST':
        input_pass = request.form.get('auth', '')
        if check_password(input_pass, get_current_admin_pass()): 
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        
        logging.warning(f"محاولة دخول خاطئة للإدارة من IP: {request.remote_addr}")
        return "<h1>الرمز خطأ!</h1>"
    
    html = f'''
    <html><head>{COMMON_ASSETS}</head>
    <body style="display:flex;justify-content:center;align-items:center;height:100vh;">
        <div class="glass" style="width:320px;text-align:center;">
            <h2 style="margin-bottom: 5px;"><i class="fas fa-fingerprint" style="color:var(--primary); text-shadow: 0 0 10px var(--primary);"></i> دخول AttendAI</h2>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 0; font-weight: bold;">Developed by Sohaib Pro | صهيب برو</p>
            <p style="color:var(--accent)">الشركة: {COMPANY_ID}</p>
            <form method="POST">
                <input type="password" name="auth" placeholder="الرمز">
                <button class="btn btn-in">دخول</button>
            </form>
        </div>
    </body></html>
    '''
    return render_template_string(html)

@app.route('/admin/export')
def export_excel():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    if not is_system_active(): return "🛑 النظام موقوف", 403 
    try:
        is_online = check_internet()
        report_data = []
        summary_data = {} 
        current_month = datetime.now().strftime("%Y-%m")

        if is_online:
            all_atts = get_db('Attendance').get() or {}
            emps = get_db('Employees').get() or {}
            try:
                with open('full_attendance_cache.json', 'w', encoding='utf-8') as f:
                    json.dump({'all_atts': all_atts}, f, ensure_ascii=False)
            except: pass
        else:
            try:
                with open('local_cache.json', 'r', encoding='utf-8') as f: emps = json.load(f).get('emps', {})
            except: emps = {}
            try:
                with open('full_attendance_cache.json', 'r', encoding='utf-8') as f: all_atts = json.load(f).get('all_atts', {})
            except: all_atts = {}

        if not isinstance(emps, dict): emps = {}
        if not isinstance(all_atts, dict): all_atts = {}

        for eid, info in emps.items():
            if not isinstance(info, dict): continue
            try: rate = float(info.get('daily_rate', 0))
            except: rate = 0.0
            summary_data[eid] = {"رقم الموظف": eid, "الاسم": info.get('full_name', 'مجهول'), "الراتب اليومي": rate, "أيام الحضور": 0, "الإجمالي المستحق": 0}

        merged_atts = {}
        for date, records in all_atts.items(): 
            if isinstance(records, dict): merged_atts[date] = records.copy()

        off_records = get_offline_records()
        for r in off_records:
            d, e = r['date'], r['emp_id']
            if d not in merged_atts: merged_atts[d] = {}
            if e not in merged_atts[d]: merged_atts[d][e] = {"in_time": "-", "out_time": "-", "device_id": r.get('device_id', '-')}
            if r['type'] == 'in': merged_atts[d][e]['in_time'] = r['time']
            if r['type'] == 'out': merged_atts[d][e]['out_time'] = r['time']
            merged_atts[d][e]['is_offline'] = True

        for date, records in merged_atts.items():
            if not isinstance(records, dict): continue
            for eid, rec in records.items():
                if not isinstance(rec, dict): continue
                emp_name = emps.get(eid, {}).get('full_name', 'مجهول') if isinstance(emps.get(eid), dict) else 'مجهول'
                status = "أوفلاين 📴" if rec.get('is_offline') else "أونلاين ☁️"
                report_data.append({"الاسم": emp_name, "التاريخ": date, "حضور": rec.get('in_time', '-'), "انصراف": rec.get('out_time', '-'), "التسجيل": status, "معرف الجهاز": rec.get('device_id', '-')})
                if date.startswith(current_month) and eid in summary_data:
                    if rec.get('in_time', '-') != '-' and rec.get('out_time', '-') != '-': summary_data[eid]["أيام الحضور"] += 1

        for eid in summary_data: summary_data[eid]["الإجمالي المستحق"] = summary_data[eid]["أيام الحضور"] * summary_data[eid]["الراتب اليومي"]

        if not report_data: return "<h1>لا توجد بيانات لتصديرها!</h1>"

        df_details = pd.DataFrame(report_data)
        df_details.sort_values(by=['الاسم', 'التاريخ'], inplace=True) 
        df_summary = pd.DataFrame(list(summary_data.values()))

        # 📊 إضافة الإحصاء الوصفي (Descriptive Statistics) بأمان باستخدام describe بدلاً من unique
        if not df_summary.empty:
            df_stats = df_summary.describe(include='all').reset_index()
            df_stats.rename(columns={'index': 'المقياس الإحصائي'}, inplace=True)
            df_stats.fillna("", inplace=True)
        else:
            df_stats = pd.DataFrame(["لا توجد بيانات كافية للإحصاء"])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_summary.to_excel(writer, index=False, sheet_name='الملخص المالي (الرواتب)')
            df_details.to_excel(writer, index=False, sheet_name='السجل اليومي المفصل')
            df_stats.to_excel(writer, index=False, sheet_name='الإحصاء الوصفي') # الشيت الجديد للإحصائيات
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'{COMPANY_ID}_Report_{datetime.now().strftime("%Y-%m-%d")}.xlsx')
    except Exception as e: return f"<h1>حدث خطأ أثناء تصدير الملف: {str(e)}</h1>"

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    if not is_system_active(): return redirect(url_for('admin_login'))
        
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    today_str = now.strftime("%Y-%m-%d")
    is_online = check_internet()

    # الحالة متصلة مع الترجمة
    status_html = f'<span class="status-badge status-online"><i class="fas fa-wifi"></i> <span data-i18n="status_online">متصل بالسحابة ✅</span></span>' if is_online else f'<span class="status-badge status-offline"><i class="fas fa-unlink"></i> <span data-i18n="status_offline">أوفلاين ⚠️</span></span>'

    if is_online:
        emps = get_db('Employees').get() or {}
        all_atts = get_db('Attendance').get() or {}
        sets = get_db('Settings').get() or {"in_s": "08:00", "in_e": "09:00", "out_s": "16:00", "req_bio": False}
        try:
            with open('full_attendance_cache.json', 'w', encoding='utf-8') as f:
                json.dump({'all_atts': all_atts}, f, ensure_ascii=False)
        except: pass
    else:
        try:
            with open('local_cache.json', 'r', encoding='utf-8') as f: 
                cache = json.load(f)
                emps = cache.get('emps', {})
                sets = cache.get('sets', {})
        except: 
            emps, sets = {}, {}
        try:
            with open('full_attendance_cache.json', 'r', encoding='utf-8') as f: all_atts = json.load(f).get('all_atts', {})
        except: all_atts = {}

    if not isinstance(emps, dict): emps = {}
    if not isinstance(all_atts, dict): all_atts = {}
    if not isinstance(sets, dict): sets = {}

    atts_today = all_atts.get(today_str, {})
    if not isinstance(atts_today, dict): atts_today = {}
        
    offline_count = len(get_offline_records())
    cfg = load_saas_config()
    current_announcement = sets.get('announcement', '')

    review_data = []
    for eid, info in emps.items():
        if not isinstance(info, dict): continue 
        
        days_count = 0
        try: rate = float(info.get('daily_rate', 0))
        except: rate = 0.0
        
        for date, records in all_atts.items():
            if isinstance(records, dict) and date.startswith(current_month) and eid in records:
                if isinstance(records[eid], dict) and "in_time" in records[eid] and "out_time" in records[eid]: 
                    days_count += 1 

        today_rec = atts_today.get(eid, {})
        if not isinstance(today_rec, dict): today_rec = {}

        in_time_str = today_rec.get('in_time', '-')
        out_time_str = today_rec.get('out_time', '-')
        needs_checkout = (in_time_str != '-') and (out_time_str == '-')
                    
        review_data.append({
            "id": eid, "name": info.get('full_name', '?'), "pin": "***", 
            "days": days_count, "rate": rate, "total": days_count * rate, 
            "serial": info.get('device_serial'), "has_face": bool(info.get('face_encoding')),
            "in_time": in_time_str, "out_time": out_time_str, "needs_checkout": needs_checkout
        })
    
    sync_btn = f'''<button onclick="syncOffline()" style="background:#10b981; color:white; border:none; padding:8px 15px; border-radius:10px; cursor:pointer; font-weight:bold;"><i class="fas fa-sync"></i> <span data-i18n="sync_btn">مزامنة الآن</span> ({offline_count})</button>''' if offline_count > 0 and is_online else ''

    html_template = f'''
    <html><head>{COMMON_ASSETS}</head><body class="dark-mode">
        <button class="mode-btn" onclick="document.body.classList.toggle('light-mode')" style="top: 20px;"><i class="fas fa-adjust"></i></button>
        <button class="mode-btn" onclick="toggleLanguage()" id="langBtn" style="top: 70px; font-weight: bold; font-family: Tahoma;">EN</button>

        <div class="container" style="padding:20px; max-width:1100px; margin:auto;">
            
            <div class="header-box">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div class="icon-box">
                        <i class="fas fa-fingerprint"></i>
                    </div>
                    <div style="display: flex; flex-direction: column; justify-content: center; text-align: start;">
                        <h1 class="gradient-text" style="margin: 0 0 5px 0; font-size: 2.2rem; font-weight: 800;"><span data-i18n="panel_title">AttendAI | لوحة التحكم</span></h1>
                        <p class="dev-credit gradient-text" style="opacity: 0.8;"><span data-i18n="dev_credit">Developed by Sohaib Pro | صهيب برو</span></p>
                    </div>
                </div>

                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px;">
                    <div class="live-clock-top gradient-text" id="clock">00:00:00</div>
                    <div style="display: flex; gap: 10px;">
                        {status_html}
                        {sync_btn}
                    </div>
                </div>
            </div>

            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:20px;">
                
                <div class="glass" style="background: rgba(59, 130, 246, 0.05); border-inline-start: 5px solid var(--primary); text-align: start;">
                    <h3 class="gradient-text" style="margin-top: 0;"><i class="fas fa-building"></i> <span data-i18n="lic_info_title">معلومات الترخيص (SaaS)</span></h3>
                    <p style="font-size: 16px; margin: 8px 0;"><b><span data-i18n="comp_name">اسم الشركة:</span></b> <span style="color:var(--text); font-weight:bold;">{{{{cfg.get('company_name', 'غير محدد')}}}}</span></p>
                    <p style="font-size: 16px; margin: 8px 0;"><b><span data-i18n="lic_num">رقم الترخيص:</span></b> <span style="color:var(--primary); font-family: monospace; font-size: 18px; font-weight:bold;">{{{{cfg.get('company_id', 'DEFAULT_COMP')}}}}</span></p>
                    <p style="font-size: 16px; margin: 8px 0;"><b><span data-i18n="bot_status">حالة البوت:</span></b> <span style="color:var(--accent);">{{{{ 'مربوط ✅' if cfg.get('tele_token') else 'غير مربوط ⚠️' }}}}</span></p>
                    <div style="background: rgba(0,0,0,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; border: 1px solid rgba(255,255,255,0.05);">
                        <p style="font-size:13px; color:gray; margin:0; line-height:1.6;">
                            <i class="fas fa-shield-alt" style="color:#f59e0b; font-size:16px;"></i> <span data-i18n="lic_desc">الترخيص محمي. لتعديل الميزات يرجى التواصل مع الدعم الفني:</span><br>
                            <span style="color:var(--primary); font-size:16px; display:inline-block; margin-top:8px; font-weight:bold; letter-spacing: 1px;"><i class="fas fa-phone-alt"></i> 771669519 (Sohaib Pro)</span>
                        </p>
                    </div>
                </div>

                <div class="glass">
                    <h3 class="gradient-text" style="margin-top:0;"><i class="fas fa-clock"></i> <span data-i18n="time_sets_title">إعدادات المواعيد والدوام</span></h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 10px; margin-bottom: 15px;">
                        <div><small style="color:gray; font-weight:bold;" data-i18n="in_lbl">دخول</small><input type="time" id="in_s" value="{{{{sets.get('in_s', '08:00')}}}}" style="padding: 5px; font-size:13px; text-align:center;"></div>
                        <div><small style="color:gray; font-weight:bold;" data-i18n="end_lbl">نهاية</small><input type="time" id="in_e" value="{{{{sets.get('in_e', '09:00')}}}}" style="padding: 5px; font-size:13px; text-align:center;"></div>
                        <div><small style="color:gray; font-weight:bold;" data-i18n="out_lbl">انصراف</small><input type="time" id="out_s" value="{{{{sets.get('out_s', '16:00')}}}}" style="padding: 5px; font-size:13px; text-align:center;"></div>
                    </div>
                    <label class="switch-label"><input type="checkbox" id="req_bio" {{{{ 'checked' if sets.get('req_bio') else '' }}}}> <span data-i18n="ai_lbl">إجبار الوجه (AI) 🤖</span></label>
                    <button class="btn btn-in" onclick="saveSets()"><i class="fas fa-save"></i> <span data-i18n="save_sets">حفظ المواعيد</span></button>
                    <button class="btn btn-excel" onclick="location.href='/admin/export'"><i class="fas fa-file-excel"></i> <span data-i18n="export_btn">استخراج تقرير Excel</span></button>
                    <hr style="opacity:0.1; margin:15px 0;">
                    <button class="btn" style="background:#f59e0b; color:white;" onclick="resetBSSID()"><i class="fas fa-wifi"></i> <span data-i18n="reset_router">تصفير راوتر الشركة (للمودم الجديد) 🛜</span></button>
                    <button class="btn btn-danger" onclick="clearAllData()" style="background:#dc2626; border: 2px solid #f87171;"><i class="fas fa-eraser"></i> <span data-i18n="reset_month">تصفير سجلات الشهر 🗑️</span></button>
                </div>
                
                <div class="glass" style="background: rgba(245, 158, 11, 0.05); border-inline-start: 5px solid #f59e0b;">
                    <h3 class="gradient-text" style="margin-top:0;"><i class="fas fa-bullhorn"></i> <span data-i18n="announce_title">بث تعميم للموظفين</span></h3>
                    <textarea id="announcementText" rows="2" data-i18n="announce_ph" placeholder="اكتب رسالة لتظهر في التطبيق لجميع الموظفين...">{{{{current_announcement}}}}</textarea>
                    <button class="btn" style="background:#f59e0b; color:white;" onclick="sendAnnouncement()"><i class="fas fa-paper-plane"></i> <span data-i18n="send_announce">إرسال التعميم</span></button>
                    <hr style="opacity:0.2; margin:20px 0; border-color:#f59e0b;">
                    <h3 class="gradient-text" style="margin-top:0; display:flex; justify-content:space-between; align-items:center;">
                        <span><i class="fab fa-telegram"></i> <span data-i18n="tele_title">إشعارات تليجرام</span></span>
                        <label style="font-size:14px; color:var(--text); cursor:pointer;"><input type="checkbox" id="enable_tele" {{{{ 'checked' if cfg.get('enable_tele', True) else '' }}}}> <span data-i18n="tele_enable">تفعيل</span></label>
                    </h3>
                    <input type="text" id="tele_token" data-i18n="tele_ph" placeholder="توكن البوت (Token)" value="{{{{cfg.get('tele_token', '')}}}}">
                    <input type="text" id="chat_id" data-i18n="chat_ph" placeholder="معرف المجموعة (Chat ID)" value="{{{{cfg.get('chat_id', '')}}}}">
                    <button class="btn" style="background:#3b82f6; color:white;" onclick="saveSets()"><i class="fas fa-save"></i> <span data-i18n="save_tele">حفظ وتفعيل الإشعارات</span></button>
                </div>

                <div class="glass">
                    <h3 class="gradient-text" style="margin-top:0;"><i class="fas fa-user-plus"></i> <span data-i18n="add_emp_title">إضافة موظف</span></h3>
                    <div style="display: flex; gap: 5px;">
                        <input id="newID" data-i18n="id_ph" placeholder="رقم الـ ID (إنجليزي/أرقام)" style="flex: 1;">
                        <input id="newPIN" data-i18n="pin_ph" placeholder="رمز PIN (أرقام فقط)" style="flex: 1;">
                    </div>
                    <input id="newName" data-i18n="name_ph" placeholder="الاسم الكامل">
                    <input id="newRate" data-i18n="rate_ph" placeholder="الراتب اليومي (بالريال)">
                    <button class="btn btn-in" onclick="addEmp()"><i class="fas fa-check-circle"></i> <span data-i18n="save_emp">حفظ الموظف</span></button>
                    <hr style="opacity:0.1; margin:15px 0;">
                    <h3 class="gradient-text" style="margin-top:0;"><i class="fas fa-key"></i> <span data-i18n="sec_title">حماية لوحة الإدارة</span></h3>
                    <input type="password" id="oldP" data-i18n="old_ph" placeholder="الرمز الحالي">
                    <input type="password" id="newP" data-i18n="new_ph" placeholder="الرمز الجديد">
                    <button class="btn btn-danger" onclick="changePass()"><i class="fas fa-lock"></i> <span data-i18n="change_pass">تغيير الرمز السري</span></button>
                </div>

                <div class="glass" style="grid-column: 1 / -1; overflow-x: auto;">
                    <h3 class="gradient-text" style="margin-top:0;">💰 <span data-i18n="summary_title">ملخص الرواتب والحضور</span></h3>
                    <table>
                        <thead><tr>
                            <th><span data-i18n="th_name">الاسم (ID)</span></th>
                            <th><span data-i18n="th_pin">الرمز / الربط</span></th>
                            <th><span data-i18n="th_days">الأيام</span></th>
                            <th><span data-i18n="th_total">المستحق</span></th>
                            <th><span data-i18n="th_in">حضور</span></th>
                            <th><span data-i18n="th_out">انصراف</span></th>
                            <th><span data-i18n="th_ctrl">تحكم</span></th>
                        </tr></thead>
                        <tbody>
                            {{% for item in review_data %}}
                            <tr>
                                <td><b>{{{{item.name}}}}</b> ({{{{item.id}}}})</td>
                                <td>
                                    <div class="pin-badge {{{{ 'pin-linked' if item.serial else 'pin-unlinked' }}}}">
                                        <i class="fas {{{{ 'fa-lock' if item.serial else 'fa-unlock' }}}}"></i>
                                        {{{{item.pin}}}}
                                    </div>
                                </td>
                                <td>{{{{item.days}}}} <span data-i18n="day_txt">يوم</span></td>
                                <td style="color:var(--accent); font-weight:bold;">{{{{item.total}}}} <span data-i18n="money_txt">ريال</span></td>
                                <td>{{{{item.in_time}}}}</td>
                                <td>{{{{item.out_time}}}}</td>
                                <td>
                                    {{% if item.needs_checkout %}}
                                    <i class="fas fa-sign-out-alt checkout-icon" onclick="manualCheckout('{{{{item.id}}}}', '{{{{item.name}}}}')"></i>
                                    {{% endif %}}
                                    <i class="fas fa-undo" style="cursor:pointer; color:#f59e0b; margin:0 8px;" onclick="resetSingle('{{{{item.id}}}}', '{{{{item.name}}}}')"></i>
                                    <i class="fas fa-mobile-alt device-icon" onclick="resetDevice('{{{{item.id}}}}')"></i>
                                    <i class="fas fa-user-times face-icon" onclick="resetFace('{{{{item.id}}}}')"></i>
                                    <i class="fas fa-trash-alt del-icon" onclick="deleteEmp('{{{{item.id}}}}')"></i>
                                </td>
                            </tr>
                            {{% endfor %}}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            // ==========================================
            // 🌍 نظام اللغات (Client-Side i18n)
            // ==========================================
            const translations = {{
                "ar": {{
                    "panel_title": "AttendAI | لوحة التحكم", "dev_credit": "Developed by Sohaib Pro | صهيب برو",
                    "lic_info_title": "معلومات الترخيص (SaaS)", "comp_name": "اسم الشركة:", "lic_num": "رقم الترخيص:",
                    "bot_status": "حالة البوت:", "lic_desc": "الترخيص محمي. لتعديل الميزات يرجى التواصل مع الدعم الفني:",
                    "time_sets_title": "إعدادات المواعيد والدوام", "in_lbl": "دخول", "end_lbl": "نهاية", "out_lbl": "انصراف",
                    "ai_lbl": "إجبار الوجه (AI) 🤖", "save_sets": "حفظ المواعيد", "export_btn": "استخراج تقرير Excel",
                    "reset_router": "تصفير راوتر الشركة (للمودم الجديد) 🛜", "reset_month": "تصفير سجلات الشهر 🗑️",
                    "announce_title": "بث تعميم للموظفين", "announce_ph": "اكتب رسالة لتظهر في التطبيق لجميع الموظفين...",
                    "send_announce": "إرسال التعميم", "tele_title": "إشعارات تليجرام", "tele_enable": "تفعيل",
                    "tele_ph": "توكن البوت (Token)", "chat_ph": "معرف المجموعة (Chat ID)", "save_tele": "حفظ وتفعيل الإشعارات",
                    "add_emp_title": "إضافة موظف", "id_ph": "رقم الـ ID (إنجليزي/أرقام)", "pin_ph": "رمز PIN (أرقام فقط)",
                    "name_ph": "الاسم الكامل", "rate_ph": "الراتب اليومي (بالريال)", "save_emp": "حفظ الموظف",
                    "sec_title": "حماية لوحة الإدارة", "old_ph": "الرمز الحالي", "new_ph": "الرمز الجديد",
                    "change_pass": "تغيير الرمز السري", "summary_title": "ملخص الرواتب والحضور", "th_name": "الاسم (ID)",
                    "th_pin": "الرمز / الربط", "th_days": "الأيام", "th_total": "المستحق", "th_in": "حضور", "th_out": "انصراف",
                    "th_ctrl": "تحكم", "status_online": "متصل بالسحابة ✅", "status_offline": "أوفلاين ⚠️", "sync_btn": "مزامنة الآن",
                    "day_txt": "يوم", "money_txt": "ريال", "lang_btn": "EN"
                }},
                "en": {{
                    "panel_title": "AttendAI | Dashboard", "dev_credit": "Developed by Sohaib Pro",
                    "lic_info_title": "License Info (SaaS)", "comp_name": "Company Name:", "lic_num": "License ID:",
                    "bot_status": "Bot Status:", "lic_desc": "License Protected. For modifications, contact Support:",
                    "time_sets_title": "Time & Attendance Settings", "in_lbl": "Check-in", "end_lbl": "End", "out_lbl": "Check-out",
                    "ai_lbl": "Force Face AI 🤖", "save_sets": "Save Settings", "export_btn": "Export Excel Report",
                    "reset_router": "Reset Company Router (BSSID) 🛜", "reset_month": "Clear Month Records 🗑️",
                    "announce_title": "Broadcast Announcement", "announce_ph": "Write a message to all employees...",
                    "send_announce": "Send Announcement", "tele_title": "Telegram Notifications", "tele_enable": "Enable",
                    "tele_ph": "Bot Token", "chat_ph": "Chat ID", "save_tele": "Save & Enable Alerts",
                    "add_emp_title": "Add Employee", "id_ph": "ID Number", "pin_ph": "PIN Code",
                    "name_ph": "Full Name", "rate_ph": "Daily Rate", "save_emp": "Save Employee",
                    "sec_title": "Panel Security", "old_ph": "Old Password", "new_ph": "New Password",
                    "change_pass": "Change Password", "summary_title": "Attendance & Payroll Summary", "th_name": "Name (ID)",
                    "th_pin": "PIN / Device", "th_days": "Days", "th_total": "Total", "th_in": "Check-in", "th_out": "Check-out",
                    "th_ctrl": "Controls", "status_online": "Cloud Connected ✅", "status_offline": "Offline ⚠️", "sync_btn": "Sync Now",
                    "day_txt": "Days", "money_txt": "SAR", "lang_btn": "عربي"
                }}
            }};

            function setLanguage(lang) {{
                document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
                document.documentElement.lang = lang;
                
                document.querySelectorAll('[data-i18n]').forEach(el => {{
                    const key = el.getAttribute('data-i18n');
                    if (translations[lang][key]) {{
                        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
                            el.placeholder = translations[lang][key];
                        }} else {{
                            el.innerText = translations[lang][key];
                        }}
                    }}
                }});
                
                const langBtn = document.getElementById('langBtn');
                if(langBtn) langBtn.innerText = translations[lang]["lang_btn"];
                localStorage.setItem('AttendAI_Lang', lang);
            }}

            function toggleLanguage() {{
                const currentLang = localStorage.getItem('AttendAI_Lang') || 'ar';
                setLanguage(currentLang === 'ar' ? 'en' : 'ar');
            }}

            window.addEventListener('DOMContentLoaded', () => {{
                setLanguage(localStorage.getItem('AttendAI_Lang') || 'ar');
            }});

            // ==========================================
            // 🕒 نظام الساعة وإصلاح المسافات
            // ==========================================
            setInterval(() => {{
                let timeStr = new Date().toLocaleTimeString('ar-EG');
                document.getElementById('clock').innerText = timeStr.replace(/\s+/g, ' '); 
            }}, 1000);

            // ==========================================
            // ⚙️ دوال التحكم والـ APIs
            // ==========================================
            function clearAllData() {{ if(confirm("❗ سيتم حذف جميع سجلات الحضور لهذه الشركة نهائياً! متأكد؟")) fetch('/admin/api/clear_all', {{method:'POST'}}).then(r=>r.json()).then(d=>{{ alert(d.message); location.reload(); }}); }}
            function resetBSSID() {{ if(confirm("🛜 هل تم تغيير راوتر الشركة؟ سيتم تصفير البصمة وسيقوم أول موظف يبصم بتسجيل الراوتر الجديد لجميع الموظفين.")) fetch('/admin/api/reset_bssid', {{method:'POST'}}).then(r=>r.json()).then(d=>{{ alert(d.message); location.reload(); }}); }}
            function sendAnnouncement() {{ fetch('/admin/api/announce', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{msg: document.getElementById('announcementText').value}})}}).then(r=>r.json()).then(d=>{{ alert(d.message); location.reload(); }}); }}
            function saveSets() {{ 
                const payload = {{
                    in_s: document.getElementById('in_s').value, in_e: document.getElementById('in_e').value, out_s: document.getElementById('out_s').value, 
                    req_bio: document.getElementById('req_bio').checked, tele_token: document.getElementById('tele_token').value,
                    chat_id: document.getElementById('chat_id').value, enable_tele: document.getElementById('enable_tele').checked
                }};
                fetch('/admin/api/save', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(payload) }}).then(()=>{{ alert("تم الحفظ بنجاح!"); location.reload(); }}); 
            }}
            function addEmp() {{ 
                const data = {{id:document.getElementById('newID').value, name:document.getElementById('newName').value, pin:document.getElementById('newPIN').value, rate:document.getElementById('newRate').value}};
                fetch('/admin/api/add_emp', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(data)}}).then(r=>r.json()).then(d=>{{ 
                    if(d.status === "error") alert(d.message); else location.reload(); 
                }}); 
            }}
            function deleteEmp(id) {{ if(confirm("حذف الموظف؟")) fetch('/admin/api/delete_emp', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{id:id}})}}).then(()=>location.reload()); }}
            function changePass() {{ 
                const oldP = document.getElementById('oldP').value, newP = document.getElementById('newP').value;
                if(!newP || !oldP) {{ alert("يرجى إدخال الرمز القديم والجديد!"); return; }}
                fetch('/admin/api/change_pass', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{old:oldP, new:newP}}) }}).then(r=>r.json()).then(d=>{{ alert(d.message); if(d.status === 'success') location.reload(); }}); 
            }}
            function resetDevice(id) {{ if(confirm("فك ارتباط الجهاز؟")) fetch('/admin/api/reset_device', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{id:id}})}}).then(()=>location.reload()); }}
            function resetFace(id) {{ if(confirm("حذف بصمة وجه الموظف؟")) fetch('/admin/api/reset_face', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{id:id}})}}).then(()=>location.reload()); }}
            function resetSingle(id, name) {{ if(confirm("إلغاء تحضير " + name + " لليوم؟")) fetch('/admin/api/reset_single', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{id:id}})}}).then(()=>location.reload()); }}
            function syncOffline() {{ fetch('/admin/api/sync_offline', {{method:'POST'}}).then(r=>r.json()).then(d=>{{alert(d.message); location.reload();}}); }}
            function manualCheckout(id, name) {{ if(confirm("تسجيل انصراف إداري للموظف " + name + "؟")) fetch('/admin/api/manual_checkout', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{id:id}})}}).then(r=>r.json()).then(d=>{{alert(d.message); location.reload();}}); }}
        </script>
    </body></html>
    '''
    return render_template_string(html_template, review_data=review_data, atts_today=atts_today, sets=sets, is_online=is_online, offline_count=offline_count, current_month=current_month, cfg=cfg, current_announcement=current_announcement)

# =====================================================================
# ⚙️ 7. مسارات التحكم للإدارة (Admin APIs)
# =====================================================================
@app.route('/admin/api/clear_all', methods=['POST'])
def clear_all_attendance():
    if not check_internet(): return jsonify({"message": "❌ التصفير يحتاج إنترنت!"})
    get_db('Attendance').delete()
    clear_offline_records()
    return jsonify({"message": "✅ تم تصفير السجلات بنجاح!"})

@app.route('/admin/api/reset_bssid', methods=['POST'])
def reset_bssid_api():
    if check_internet(): get_db('Settings').update({"official_bssid": ""})
    try:
        with open('local_cache.json', 'r', encoding='utf-8') as f: cache = json.load(f)
        if 'sets' not in cache: cache['sets'] = {}
        cache['sets']['official_bssid'] = ""
        with open('local_cache.json', 'w', encoding='utf-8') as f: json.dump(cache, f, ensure_ascii=False)
    except: pass
    return jsonify({"message": "✅ تم تصفير المودم بنجاح! يمكن لأول موظف يبصم الآن تسجيل المودم الجديد."})

@app.route('/admin/api/announce', methods=['POST'])
def announce_api():
    if not check_internet(): return jsonify({"message": "❌ يحتاج إنترنت!"})
    safe_msg = sanitize_input(request.json.get('msg', '')) # 🛡️ تنظيف التعميم
    get_db('Settings').update({"announcement": safe_msg})
    return jsonify({"message": "✅ تم تحديث التعميم للموظفين!"})

@app.route('/admin/api/manual_checkout', methods=['POST'])
def manual_checkout_api():
    if not check_internet(): return jsonify({"message": "❌ يحتاج إنترنت!"})
    emp_id = request.json['id']
    today = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime("%I:%M:%S %p")
    
    rec = get_db(f"Attendance/{today}/{emp_id}").get()
    if not isinstance(rec, dict) or 'in_time' not in rec: return jsonify({"message": "❌ لم يسجل حضور اليوم!"})
    if 'out_time' in rec: return jsonify({"message": "⚠️ لديه انصراف مسبقاً!"})
        
    get_db(f"Attendance/{today}/{emp_id}").update({'out_time': f"{now_time} (إدارة)"})
    return jsonify({"message": "✅ تم تسجيل الانصراف الإداري!"})

@app.route('/admin/api/sync_offline', methods=['POST'])
def sync_offline():
    if not check_internet(): return jsonify({"message": "❌ لا يوجد إنترنت!"})
    if process_sync(): return jsonify({"message": "✅ تمت المزامنة!"})
    return jsonify({"message": "⚠️ لا توجد سجلات معلقة."})

@app.route('/admin/api/save', methods=['POST'])
def save_api(): 
    data = request.json
    settings_data = {"in_s": data.get("in_s"), "in_e": data.get("in_e"), "out_s": data.get("out_s"), "req_bio": data.get("req_bio")}
    get_db('Settings').update(settings_data)
    try:
        with open(SAAS_CONFIG_FILE, 'r', encoding='utf-8') as f: config = json.load(f)
        config['tele_token'] = sanitize_input(data.get("tele_token", ""))
        config['chat_id'] = sanitize_input(data.get("chat_id", ""))
        config['enable_tele'] = data.get("enable_tele", True)
        with open(SAAS_CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, ensure_ascii=False, indent=4)
    except: pass
    return jsonify({"message": "✅ تم الحفظ"})

# 🛡️ التحقق الصارم والتشفير عند إضافة الموظف
@app.route('/admin/api/add_emp', methods=['POST'])
def add_emp_api(): 
    req = request.json
    if not req: return jsonify({"status": "error", "message": "بيانات فارغة!"}), 400

    emp_id = sanitize_input(req.get('id', ''), "id")
    emp_name = sanitize_input(req.get('name', ''), "name")
    emp_pin = sanitize_input(req.get('pin', ''), "pin")
    
    if not emp_id or not emp_name or not emp_pin:
        return jsonify({"status": "error", "message": "❌ بيانات غير صالحة! (الـ PIN أرقام فقط، الـ ID إنجليزي، والاسم صحيح)."})

    try: rate = float(req.get('rate', 0))
    except ValueError: rate = 0.0

    secure_pin = hash_password(emp_pin) # 🔐 تشفير الـ PIN
    
    get_db(f"Employees/{emp_id}").update({"full_name": emp_name, "pin": secure_pin, "daily_rate": rate})
    return jsonify({"status": "success", "message": "✅ تم الإضافة والتشفير بنجاح"})

@app.route('/admin/api/delete_emp', methods=['POST'])
def delete_emp_api(): 
    get_db(f"Employees/{request.json['id']}").delete()
    return jsonify({"message": "✅ تم الحذف"})

@app.route('/admin/api/change_pass', methods=['POST'])
def change_api():
    old_pass = request.json['old']
    if not check_password(old_pass, get_current_admin_pass()): 
        return jsonify({"status": "error", "message": "❌ الرمز الحالي خطأ!"})
        
    new_pass_raw = sanitize_input(request.json['new'])
    if len(new_pass_raw) < 4: return jsonify({"status": "error", "message": "❌ كلمة السر يجب أن تكون 4 رموز على الأقل!"})

    secure_new_pass = hash_password(new_pass_raw) # 🔐 تشفير كلمة السر الجديدة
    
    if check_internet(): get_db('Settings').update({"admin_pass": secure_new_pass})
    try:
        with open(SAAS_CONFIG_FILE, 'r', encoding='utf-8') as f: config = json.load(f)
        config['admin_pass'] = secure_new_pass
        with open(SAAS_CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, ensure_ascii=False)
    except: pass
    return jsonify({"status": "success", "message": "✅ تم تغيير رمز المدير وتشفيره بنجاح!"})

@app.route('/admin/api/reset_device', methods=['POST'])
def reset_device_api(): 
    get_db(f"Employees/{request.json['id']}").update({"device_serial": None})
    return jsonify({"status": "success"})

@app.route('/admin/api/reset_face', methods=['POST'])
def reset_face_api(): 
    get_db(f"Employees/{request.json['id']}/face_encoding").delete()
    return jsonify({"status": "success"})

@app.route('/admin/api/reset_single', methods=['POST'])
def reset_single_api(): 
    get_db(f"Attendance/{datetime.now().strftime('%Y-%m-%d')}/{request.json['id']}").delete()
    return jsonify({"status": "success"})

# =====================================================================
# 🚀 8. نقطة انطلاق السيرفر
# =====================================================================
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    try:
        from waitress import serve
    except ImportError:
        print("Installing Waitress Server... Please wait.")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "waitress"])
        from waitress import serve

    threading.Thread(target=auto_sync_worker, daemon=True).start()
    
    local_ip = get_local_ip()
    print("\n" + "="*60)
    print("🚀 AttendAI Server is RUNNING (Fort Knox Edition 🛡️)")
    print(f"🌍 Local Network URL (For Phones): http://{local_ip}:5000/admin")
    print(f"💻 This PC URL (For Admin)       : http://127.0.0.1:5000/admin")
    print("============================================================\n")
    
    serve(app, host='0.0.0.0', port=5000, threads=16)
