import os
import html
import socket
from datetime import date, datetime
from urllib.parse import urlparse

import pandas as pd
import io
import json
import streamlit as st
import streamlit.components.v1 as components
import base64
from dotenv import load_dotenv
import httpx
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

try:
    import qrcode
    qrcode_import_error = False
except ImportError:
    qrcode = None
    qrcode_import_error = True

load_dotenv()

st.set_page_config(page_title="Shree Janta Secondary School", page_icon="🏫", layout="wide")

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception:
        return None


def get_static_qr_bytes():
    for filename in ["aa.png", "ii.png", "qr.jpeg"]:
        path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(path):
            try:
                with open(path, "rb") as image_file:
                    return image_file.read(), filename
            except Exception:
                continue
    return None, None


def render_school_logo_header():
    logo_base64 = get_image_base64(os.path.join(os.path.dirname(__file__), "a.png"))
    if logo_base64:
        st.markdown(
            "<div style='max-width:920px; margin:0 auto 24px auto; padding:18px; border-radius:24px; background:#ffffff; box-shadow:0 24px 80px rgba(15, 23, 42, 0.08); display:flex; justify-content:center; align-items:center;'>"
            f"<img src='data:image/png;base64,{logo_base64}' alt='School Logo' style='max-width:100%; height:auto; border-radius:18px; object-fit:contain; box-shadow:0 16px 40px rgba(15, 23, 42, 0.09);' />"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        try:
            st.image("a.png", width=920)
        except Exception:
            st.warning("School logo could not be loaded.")


st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --ink: #1f2937;
        --muted: #475569;
        --panel: #ffffff;
        --panel-soft: #f8fafc;
        --line: rgba(15, 23, 42, 0.08);
        --gold: #f59e0b;
        --gold-soft: rgba(245, 158, 11, 0.16);
        --accent-pink: #fb7185;
        --accent-pink-soft: rgba(251, 113, 133, 0.2);
        --premium: #8b5cf6;
        --premium-soft: rgba(139, 92, 246, 0.14);
        --primary: #16a34a;
        --primary-hover: #15803d;
        --success: #22c55e;
        --success-hover: #16a34a;
        --create: #10b981;
        --create-hover: #059669;
        --login: #16a34a; /* strong green for login CTAs */
        --login-hover: #12713a;
        --danger: #ef4444;
    }
    html, body, [class*="css"] {
        font-family: "Aptos", "Segoe UI", sans-serif;
        letter-spacing: 0.01em;
        background: #eff6ff;
        color: var(--ink);
    }
    .stApp {
        background:
            radial-gradient(circle at 70% 0%, rgba(251, 113, 133, 0.12), transparent 24%),
            linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        color: var(--ink);
    }
    .block-container {
        max-width: 1120px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
        margin: 0 auto;
    }
    h1, h2, h3 {
        color: var(--ink) !important;
        font-family: Georgia, "Times New Roman", serif;
        letter-spacing: 0;
    }
    h1 {
        font-size: clamp(2rem, 4vw, 3.5rem) !important;
        line-height: 1.05 !important;
        margin-bottom: 0.75rem !important;
    }
    h2 {
        font-size: 1.7rem !important;
        margin-top: 2rem !important;
    }
    h3 {
        font-size: 1.25rem !important;
    }
    p, label, .stCaption {
        color: var(--muted) !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(251, 113, 133, 0.1) 0%, #ffffff 100%);
        border-right: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: inset -4px 0 12px rgba(15, 23, 42, 0.05);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {
        color: var(--ink) !important;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.15rem !important;
        margin-bottom: 0.25rem !important;
        line-height: 1.2 !important;
    }
    [data-testid="stSidebar"] h2 {
        font-size: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.94);
        backdrop-filter: blur(14px);
        border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-top: 2px solid var(--gold);
        padding: 18px 20px;
        border-radius: 18px;
        box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
    }
    [data-testid="stMetricValue"] {
        color: var(--ink) !important;
        font-family: Georgia, "Times New Roman", serif;
    }
    div[data-testid="stForm"], .stExpander {
        background: var(--panel);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 16px;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.06);
        padding: 0.6rem;
    }
    input, textarea, [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: var(--ink) !important;
        border-color: var(--line) !important;
        border-radius: 8px !important;
    }
    input:focus, textarea:focus {
        border-color: var(--accent-pink) !important;
        box-shadow: 0 0 0 1px var(--accent-pink-soft) !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 10px;
        overflow: hidden;
    }
    [data-baseweb="tab-list"] {
        gap: 0.4rem;
        border-bottom: 1px solid rgba(0,0,0,0.08);
    }
    [data-baseweb="tab"] {
        color: var(--muted);
        padding: 0.75rem 1rem;
    }
    [aria-selected="true"] {
        color: var(--accent-pink) !important;
        border-bottom-color: var(--accent-pink) !important;
    }

    .stButton > button, .stDownloadButton > button {
        background: var(--primary);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        min-height: 44px;
        font-weight: 700;
        opacity: 1;
        box-shadow: 0 12px 28px rgba(16, 185, 129, 0.18);
        transition: transform 160ms ease, background 160ms ease, box-shadow 160ms ease;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        background: var(--primary-hover);
        transform: translateY(-1px);
        box-shadow: 0 16px 36px rgba(37, 99, 235, 0.18);
    }

    /* Download buttons use accent gold */
    .stDownloadButton > button {
        background: var(--gold) !important;
        color: #1f2937 !important;
        border: none !important;
    }
    .stDownloadButton > button:hover {
        background: #f59e0b !important;
    }

    /* Login buttons: use a green->teal gradient that complements the dashboard */
    button[aria-label="Login"],
    button[aria-label^="Login as"],
    .stButton > button[aria-label="Login"],
    .stButton > button[aria-label^="Login as"],
    [data-testid="stButton"] button[aria-label="Login"],
    [data-testid="stButton"] button[aria-label^="Login as"],
    .stButton button[aria-label="Login"],
    .stButton button[aria-label^="Login as"] {
        background: linear-gradient(90deg, var(--login), var(--create)) !important;
        color: #fff !important;
        border-color: transparent !important;
        box-shadow: 0 12px 30px rgba(16, 24, 40, 0.12) !important;
        font-weight: 800 !important;
        padding: 10px 18px !important;
        border-radius: 12px !important;
        text-transform: none !important;
    }

    button[aria-label="Login"]:hover,
    button[aria-label^="Login as"]:hover,
    .stButton > button[aria-label="Login"]:hover,
    .stButton > button[aria-label^="Login as"]:hover,
    [data-testid="stButton"] button[aria-label="Login"]:hover,
    [data-testid="stButton"] button[aria-label^="Login as"]:hover,
    .stButton button[aria-label="Login"]:hover,
    .stButton button[aria-label^="Login as"]:hover {
        filter: brightness(0.95) saturate(1.02) !important;
        transform: translateY(-1px) !important;
    }

    /* Other buttons keep the polished blue style */
    [data-testid="stButton"] button:not([aria-label^="Login"]),
    .stButton button:not([aria-label^="Login"]),
    .stButton > button:not([aria-label^="Login"]) {
        background: var(--primary) !important;
        color: #fff !important;
        border-color: var(--primary) !important;
    }

    [data-testid="stButton"] button[aria-label*="Create"],
    .stButton button[aria-label*="Create"],
    button[aria-label*="Create"] {
        background: linear-gradient(90deg, var(--login), var(--success)) !important;
        color: #fff !important;
        border-color: transparent !important;
        box-shadow: 0 10px 28px rgba(16,160,85,0.08) !important;
        font-weight: 700 !important;
        padding: 10px 16px !important;
        border-radius: 10px !important;
    }
    button[aria-label*="Create"]:hover {
        background: linear-gradient(90deg, var(--login-hover), var(--success)) !important;
    }

    button[aria-label*="Add"], button[aria-label*="Save"], button[aria-label*="Create"] {
        background: var(--success) !important;
        border-color: var(--success) !important;
        color: #fff !important;
    }
    button[aria-label*="Delete"], button[aria-label*="Remove"], button[aria-label*="Cancel"] {
        background: var(--danger) !important;
        border-color: var(--danger) !important;
        color: #fff !important;
    }
    [data-testid="stAlert"] {
        background: var(--panel-soft);
        border: 1px solid var(--line);
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Supabase configuration
# ---------------------------------------------------------

SIGNUP_TABLE = "student_signup"
ROLE_TABLES = {
    "admin": "admin_signup",
    "teacher": "teacher_signup",
    "principal": "principal_signup",
    "accountant": "accountant_signup",
    "librarian": "librarian_signup",
}

# ---------------------------------------------------------
# Supabase client and authentication helpers
# ---------------------------------------------------------


SUPABASE_CLIENT_STATE_KEY = "supabase_client"
SUPABASE_CLIENT_ERROR_KEY = "supabase_client_error"
SUPABASE_HTTP_TIMEOUT = 30.0


def _get_supabase_url():
    url = os.environ.get("SUPABASE_URL", "")
    return url.strip() or None


def _validate_supabase_url(supabase_url):
    parsed = urlparse(supabase_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            "SUPABASE_URL must be a valid URL including the scheme, e.g. https://<project>.supabase.co"
        )
    if parsed.hostname:
        try:
            socket.getaddrinfo(parsed.hostname, 443)
        except socket.gaierror as exc:
            raise ConnectionError(
                f"DNS lookup failed for Supabase host '{parsed.hostname}'. "
                "Check your internet connection and SUPABASE_URL."
            ) from exc
    return parsed


def _create_supabase_client():
    supabase_url = _get_supabase_url()
    supabase_key = os.environ.get("SUPABASE_KEY", "").strip()
    if not supabase_url or not supabase_key:
        if not supabase_url:
            st.error("SUPABASE_URL is missing. Set it in .env and restart the app.")
        if not supabase_key:
            st.error("SUPABASE_KEY is missing. Set it in .env and restart the app.")
        return None
    try:
        _validate_supabase_url(supabase_url)
        httpx_client = httpx.Client(
            timeout=httpx.Timeout(SUPABASE_HTTP_TIMEOUT, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=0, max_connections=10),
        )
        options = SyncClientOptions(
            httpx_client=httpx_client,
            postgrest_client_timeout=SUPABASE_HTTP_TIMEOUT,
            headers={"Connection": "close"},
        )
        return create_client(supabase_url, supabase_key, options=options)
    except Exception as exc:
        st.session_state[SUPABASE_CLIENT_ERROR_KEY] = str(exc)
        st.error(f"Could not create Supabase client: {exc}")
        return None


def get_supabase_client(force_refresh: bool = False):
    if force_refresh:
        st.session_state.pop(SUPABASE_CLIENT_STATE_KEY, None)
        st.session_state.pop(SUPABASE_CLIENT_ERROR_KEY, None)
    cached_error = st.session_state.get(SUPABASE_CLIENT_ERROR_KEY)
    if cached_error and not force_refresh:
        st.error(
            "Supabase client creation previously failed. "
            "Refresh the page or fix SUPABASE_URL / SUPABASE_KEY to retry."
        )
        return None
    supabase_client = st.session_state.get(SUPABASE_CLIENT_STATE_KEY)
    if supabase_client is None:
        supabase_client = _create_supabase_client()
        if supabase_client is not None:
            st.session_state[SUPABASE_CLIENT_STATE_KEY] = supabase_client
    return supabase_client


def seed_default_admin(supabase):
    try:
        st.session_state.admin_table_error = None
        admin_table = ROLE_TABLES["admin"]
        try:
            existing = supabase.table(admin_table).select("username").ilike("username", "admin").execute()
        except Exception as admin_table_error:
            if "PGRST205" not in str(admin_table_error) and "admin_signup" not in str(admin_table_error):
                raise
            admin_table = SIGNUP_TABLE
            existing = supabase.table(admin_table).select("username").ilike("username", "admin").execute()
        if not existing.data:
            admin_payload = {
                "full_name": "System Administrator",
                "phone": "",
                "email": "",
                "username": "admin",
                "password": "admin",
                "role": "admin",
            }
            if admin_table == SIGNUP_TABLE:
                admin_payload.update({
                    "admission_no": "",
                    "class_name": "",
                    "guardian_name": "",
                })
            supabase.table(admin_table).insert(admin_payload).execute()
    except Exception as exc:
        st.session_state.admin_table_error = str(exc)


def ensure_state():
    supabase = get_supabase_client()
    if supabase is None:
        st.error("Supabase is required. Set SUPABASE_URL and SUPABASE_KEY in .env.")
        st.stop()
    seed_default_admin(supabase)
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "current_role" not in st.session_state:
        st.session_state.current_role = None
    if "current_student_id" not in st.session_state:
        st.session_state.current_student_id = None
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"
    if "teacher_salary_payments_fallback" not in st.session_state:
        st.session_state.teacher_salary_payments_fallback = False


def load_students(supabase):
    return _load_table(supabase, "students", "created_at")


def load_attendance(supabase):
    return _load_table(supabase, "attendance", "attendance_date")


def load_fee_records(supabase):
    return _load_table(supabase, "fee_records", "payment_date")


def load_teachers(supabase):
    return _load_table(supabase, "teachers", "created_at")


def get_local_salary_payments_path():
    return os.path.join(os.path.dirname(__file__), "teacher_salary_payments_local.json")


def load_teacher_salary_payments_local():
    local_path = get_local_salary_payments_path()
    try:
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as fp:
                return json.load(fp) or []
    except Exception:
        pass
    return []


def save_teacher_salary_payment_local(payload):
    local_path = get_local_salary_payments_path()
    existing = load_teacher_salary_payments_local()
    existing.insert(0, payload)
    try:
        with open(local_path, "w", encoding="utf-8") as fp:
            json.dump(existing, fp, default=str, indent=2)
        return True
    except Exception as exc:
        st.error(f"Could not save local salary payment fallback: {exc}")
        return False


def load_teacher_salary_payments(supabase):
    try:
        response = supabase.table("teacher_salary_payments").select("*").order("payment_date", desc=True).execute()
        st.session_state.teacher_salary_payments_fallback = False
        return response.data or []
    except Exception as exc:
        if "PGRST205" in str(exc):
            st.session_state.teacher_salary_payments_fallback = True
            return load_teacher_salary_payments_local()
        st.error(f"Could not load teacher salary payments: {exc}")
        return []


def load_courses(supabase):
    return _load_table(supabase, "courses", "created_at")


def load_marks(supabase):
    return _load_table(supabase, "marks", "created_at")

# ---------------------------------------------------------
# Data loading functions
# ---------------------------------------------------------


def _load_table(supabase, table_name, order_column="created_at"):
    last_exception = None
    for attempt in range(2):
        if supabase is None:
            return []
        try:
            response = supabase.table(table_name).select("*").order(order_column, desc=True).execute()
            return response.data or []
        except Exception as exc:
            last_exception = exc
            error_text = str(exc)
            if attempt == 0 and (
                "ConnectionTerminated" in error_text
                or "Connection aborted" in error_text
                or isinstance(exc, httpx.HTTPError)
            ):
                st.session_state.pop(SUPABASE_CLIENT_STATE_KEY, None)
                supabase = get_supabase_client(force_refresh=True)
                continue
            st.error(f"Could not load {table_name} from Supabase: {exc}")
            return []
    st.error(f"Could not load {table_name} from Supabase after retries: {last_exception}")
    return []


def parse_fee_note(note):
    details = {
        "fee_category": "Unknown",
        "term": "",
        "due_date": "",
        "description": "",
        "note": "",
        "payment_method": "",
    }
    if not note:
        return details

    parts = [part.strip() for part in str(note).split("|") if part.strip()]
    if parts:
        details["fee_category"] = parts[0]
        for part in parts[1:]:
            if part.startswith("Term "):
                details["term"] = part
            elif part.startswith("Due "):
                details["due_date"] = part.replace("Due ", "", 1)
            elif part.startswith("Premium:"):
                details["description"] = part.replace("Premium:", "", 1).strip()
            elif part.startswith("Note:"):
                details["note"] = part.replace("Note:", "", 1).strip()
            elif part.startswith("Payment Method:"):
                details["payment_method"] = part.replace("Payment Method:", "", 1).strip()
            elif part.startswith("Online Payment:"):
                details["payment_method"] = part.replace("Online Payment:", "", 1).strip()
            else:
                if details["note"]:
                    details["note"] += " | " + part
                else:
                    details["note"] = part
    return details


def enrich_fee_records(fee_records, students):
    student_map = {str(student.get("id")): student for student in students}
    enriched = []
    for record in fee_records:
        note_data = parse_fee_note(record.get("note", ""))
        student = student_map.get(str(record.get("student_id")), {})
        payment_method = record.get("payment_method") or note_data.get("payment_method") or "Cash"
        enriched.append({
            "student_id": record.get("student_id"),
            "payment_date": record.get("payment_date"),
            "due_date": note_data["due_date"],
            "student_name": student.get("full_name", ""),
            "admission_no": student.get("admission_no", ""),
            "class_name": student.get("class_name", ""),
            "fee_category": note_data["fee_category"],
            "term": note_data["term"],
            "payment_method": payment_method,
            "amount": float(record.get("amount", 0) or 0),
            "status": record.get("status"),
            "description": note_data["description"],
            "note": note_data["note"],
            "raw_note": record.get("note", ""),
        })
    return enriched


def generate_qr_jpeg(payload):
    if qrcode_import_error or qrcode is None:
        return None
    try:
        qr_text = json.dumps(payload)
        qr_img = qrcode.make(qr_text).convert("RGB")
        buf = io.BytesIO()
        qr_img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        return None


def calculate_teacher_net_payment(base_amount, allowance, deduction, bonus):
    try:
        return float(base_amount or 0) + float(allowance or 0) + float(bonus or 0) - float(deduction or 0)
    except Exception:
        return float(base_amount or 0)


def load_library_books(supabase):
    return _load_table(supabase, "library_books")


def load_library_loans(supabase):
    return _load_table(supabase, "library_loans")

# ---------------------------------------------------------
# CRUD utility functions
# ---------------------------------------------------------


def save_record(supabase, table_name, payload):
    try:
        supabase.table(table_name).insert(payload).execute()
        return True
    except Exception as exc:
        st.error(f"Could not save {table_name}: {exc}")
        return False


def update_record(supabase, table_name, record_id, payload):
    try:
        supabase.table(table_name).update(payload).eq("id", record_id).execute()
        return True
    except Exception as exc:
        st.error(f"Could not update {table_name}: {exc}")
        return False

# ---------------------------------------------------------
# User management helpers
# ---------------------------------------------------------


def get_user_by_username(supabase, username, role=None):
    try:
        if role == "admin":
            tables = [ROLE_TABLES["admin"], SIGNUP_TABLE]
        elif role in ROLE_TABLES:
            tables = [ROLE_TABLES[role]]
        else:
            tables = [SIGNUP_TABLE, *ROLE_TABLES.values()]
        for table_name in tables:
            try:
                response = supabase.table(table_name).select("*").ilike("username", username).execute()
            except Exception:
                continue
            if not response.data:
                continue
            row = response.data[0]
            student_id = row.get("student_id")
            if student_id is None and row.get("admission_no"):
                student_response = supabase.table("students").select("id").eq("admission_no", row["admission_no"]).limit(1).execute()
                if student_response.data:
                    student_id = student_response.data[0].get("id")
            return {
                    "username": row.get("username"),
                    "password": row.get("password"),
                    "role": row.get("role"),
                    "full_name": row.get("full_name"),
                    "admission_no": row.get("admission_no"),
                    "class_name": row.get("class_name"),
                    "guardian_name": row.get("guardian_name"),
                    "phone": row.get("phone"),
                    "email": row.get("email"),
                    "student_id": student_id,
            }
    except Exception as exc:
        st.error(f"Could not look up user in Supabase: {exc}")
    return None


def create_user(supabase, username, password, role, student_id=None, staff_data=None):
    if not username or not password:
        st.error("Username and password are required")
        return False
    if get_user_by_username(supabase, username, role=role):
        st.error("That username already exists")
        return False

    staff_data = staff_data or {}
    try:
        payload = {
            "full_name": staff_data.get("full_name", ""),
            "phone": staff_data.get("phone", ""),
            "email": staff_data.get("email", ""),
            "username": username,
            "password": password,
            "role": role,
            "created_at": datetime.now().isoformat(),
        }
        if role == "teacher":
            payload["subject"] = staff_data.get("subject", "")
        supabase.table(ROLE_TABLES[role]).insert(payload).execute()
        return True
    except Exception as exc:
        st.error(f"Could not create the Supabase user: {exc}")
        return False


def add_student(supabase, student_data):
    try:
        supabase.table("students").insert(student_data).execute()
        return True
    except Exception as exc:
        st.error(f"Could not add student to Supabase: {exc}")
        return False


def update_student(supabase, student_id, student_data):
    try:
        supabase.table("students").update(student_data).eq("id", student_id).execute()
        return True
    except Exception as exc:
        st.error(f"Could not update student in Supabase: {exc}")
        return False


def delete_student(supabase, student_id):
    try:
        supabase.table("students").delete().eq("id", student_id).execute()
        return True
    except Exception as exc:
        st.error(f"Could not delete student from Supabase: {exc}")
        return False


def add_attendance(supabase, student_id, attendance_date, status):
    try:
        supabase.table("attendance").insert({"student_id": student_id, "attendance_date": str(attendance_date), "status": status}).execute()
        return True
    except Exception as exc:
        st.error(f"Could not record attendance in Supabase: {exc}")
        return False


def add_fee_record(supabase, student_id, amount, payment_date, status, payment_method, note):
    payload = {
        "student_id": student_id,
        "amount": amount,
        "payment_date": str(payment_date),
        "status": status,
        "note": note,
    }
    if payment_method is not None:
        payload["payment_method"] = payment_method
    try:
        supabase.table("fee_records").insert(payload).execute()
        return True
    except Exception as exc:
        error_text = str(exc)
        if "PGRST204" in error_text and "payment_method" in error_text:
            try:
                fallback_payload = payload.copy()
                fallback_payload.pop("payment_method", None)
                if payment_method:
                    fallback_payload["note"] = f"{note} | Payment Method: {payment_method}" if note else f"Payment Method: {payment_method}"
                supabase.table("fee_records").insert(fallback_payload).execute()
                return True
            except Exception as fallback_exc:
                st.error(f"Could not save fee record to Supabase after fallback: {fallback_exc}")
                return False
        st.error(f"Could not save fee record to Supabase: {exc}")
        return False


def add_teacher(supabase, full_name, subject, phone, email, salary=0.0):
    payload = {
        "full_name": full_name,
        "subject": subject,
        "phone": phone,
        "email": email,
        "salary": salary,
    }
    try:
        supabase.table("teachers").insert(payload).execute()
        return True
    except Exception as exc:
        st.error(f"Could not add teacher to Supabase: {exc}")
        return False


def add_course(supabase, course_name, class_name, teacher_name):
    try:
        supabase.table("courses").insert({"course_name": course_name, "class_name": class_name, "teacher_name": teacher_name}).execute()
        return True
    except Exception as exc:
        st.error(f"Could not add course to Supabase: {exc}")
        return False


def add_teacher_salary_payment(supabase, teacher_id, amount, payment_date, payment_month, note, payment_method="Cash", allowance=0.0, deduction=0.0, bonus=0.0):
    payload = {
        "teacher_id": teacher_id,
        "amount": float(amount or 0),
        "allowance": float(allowance or 0),
        "deduction": float(deduction or 0),
        "bonus": float(bonus or 0),
        "net_amount": calculate_teacher_net_payment(amount, allowance, deduction, bonus),
        "payment_date": str(payment_date),
        "payment_month": payment_month,
        "payment_method": payment_method,
        "note": note,
        "created_at": datetime.now().isoformat(),
    }

    def _build_note():
        note_parts = []
        if note:
            note_parts.append(str(note))
        if payment_method:
            note_parts.append(f"Payment Method: {payment_method}")
        if allowance or deduction or bonus:
            note_parts.append(
                f"Salary details: allowance={allowance}, deduction={deduction}, bonus={bonus}"
            )
        return " | ".join(note_parts)

    def _attempt_save(payload_to_try, warning_msg=None, error_msg=None):
        try:
            supabase.table("teacher_salary_payments").insert(payload_to_try).execute()
            if warning_msg:
                st.warning(warning_msg)
            return True
        except Exception as attempt_exc:
            if error_msg:
                st.error(error_msg.format(attempt_exc))
            return False

    try:
        supabase.table("teacher_salary_payments").insert(payload).execute()
        return True
    except Exception as exc:
        error_text = str(exc)
        if "PGRST205" in error_text:
            if save_teacher_salary_payment_local(payload):
                st.warning(
                    "Teacher salary table is missing in Supabase. Payment was saved locally to teacher_salary_payments_local.json."
                )
                return True
        if "PGRST204" in error_text:
            fallback_note = _build_note()
            reduced_payload = {
                "teacher_id": teacher_id,
                "amount": float(amount or 0),
                "note": fallback_note,
            }
            if payment_date:
                reduced_payload["payment_date"] = str(payment_date)
            if payment_month:
                reduced_payload["payment_month"] = payment_month

            if _attempt_save(
                reduced_payload,
                warning_msg=(
                    "Teacher salary payments schema is missing some fields. Payment was saved with details in note."
                ),
            ):
                return True

            minimal_payload = {
                "teacher_id": teacher_id,
                "amount": float(amount or 0),
                "note": fallback_note,
            }
            if _attempt_save(
                minimal_payload,
                warning_msg=(
                    "Teacher salary payments schema is missing many fields. Payment was saved with the minimal available schema."
                ),
            ):
                return True

            if save_teacher_salary_payment_local({**minimal_payload, "created_at": datetime.now().isoformat()}):
                st.warning(
                    "Teacher salary payments schema is missing too many fields. Payment was saved locally to teacher_salary_payments_local.json."
                )
                return True
            st.error("Could not save teacher salary payment after fallback.")
            return False

        st.error(f"Could not save teacher salary payment: {exc}")
        return False


def add_mark(supabase, student_id, subject, score, term):
    try:
        supabase.table("marks").insert({"student_id": student_id, "subject": subject, "score": score, "term": term}).execute()
        return True
    except Exception as exc:
        st.error(f"Could not add mark to Supabase: {exc}")
        return False


def register_user(supabase, username, password, role="student", student_id=None, student_data=None):
    if role in {"teacher", "accountant", "principal", "librarian"}:
        st.error("Staff accounts must be created by an administrator")
        return False
    if not username or not password:
        st.error("Username and password are required")
        return False

    existing_user = get_user_by_username(supabase, username)
    if existing_user:
        st.error("That username already exists")
        return False

    try:
        payload = {
            "username": username,
            "password": password,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "admission_no": "",
            "class_name": "",
            "guardian_name": "",
        }
        if student_data:
            payload.update({
                "full_name": student_data.get("full_name", ""),
                "phone": student_data.get("phone", ""),
                "email": student_data.get("email", ""),
            })
            if role == "student":
                payload.update({
                    "admission_no": student_data.get("admission_no", ""),
                    "class_name": student_data.get("class_name", ""),
                    "guardian_name": student_data.get("guardian_name", ""),
                })
        supabase.table(SIGNUP_TABLE).insert(payload).execute()
    except Exception as exc:
        st.error(f"Failed to register user: {exc}")
        return False

    st.session_state.authenticated = True
    st.session_state.current_user = username
    st.session_state.current_role = role
    st.session_state.current_student_id = student_id
    if role in ["admin", "principal"]:
        st.session_state.page = "Dashboard"
    elif role == "teacher":
        st.session_state.page = "Attendance"
    elif role == "accountant":
        st.session_state.page = "Fees"
    elif role == "librarian":
        st.session_state.page = "Library"
    else:
        st.session_state.page = "Student Home"
    st.success("Account created and signed in successfully")
    return True


def login_user(supabase, username, password, role=None):
    seed_default_admin(supabase)
    user = get_user_by_username(supabase, username, role=role)
    if user and user.get("password") == password:
        if role and user.get("role") != role:
            st.error("Invalid login type for this account")
            return False

        st.session_state.authenticated = True
        st.session_state.current_user = username
        st.session_state.current_role = user.get("role")
        st.session_state.current_student_id = user.get("student_id")
        if user.get("role") in ["admin", "principal"]:
            st.session_state.page = "Dashboard"
        elif user.get("role") == "teacher":
            st.session_state.page = "Attendance"
        elif user.get("role") == "accountant":
            st.session_state.page = "Fees"
        elif user.get("role") == "librarian":
            st.session_state.page = "Library"
        else:
            st.session_state.page = "Student Home"
        st.success("Logged in successfully")
        return True

    st.error("Invalid username or password")
    return False


def logout_user():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_role = None
    st.session_state.current_student_id = None
    st.session_state.page = "Login"
    st.session_state.auth_view = "login"


# ---------------------------------------------------------
# UI page renderers
# ---------------------------------------------------------

# ---------------------------------------------------------
# Authentication pages
# ---------------------------------------------------------

def render_login_page():
    st.markdown(
            "<div style='padding:28px 32px; border-radius:28px; background:linear-gradient(135deg, rgba(139,92,246,0.20), rgba(16,185,129,0.12)); margin-bottom:24px;'>"
        "<div style='max-width:1120px;'>"
        "<h1 style='margin:0; font-size:3rem; color:#111827;'>Welcome to Shree Janta Secondary School</h1>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    logo_base64 = get_image_base64(os.path.join(os.path.dirname(__file__), "a.png"))
    if logo_base64:
        st.markdown(
            "<div style='max-width:920px; margin:0 auto 24px auto; padding:18px; border-radius:24px; background:#ffffff; box-shadow:0 24px 80px rgba(15, 23, 42, 0.08); display:flex; justify-content:center; align-items:center;'>"
            f"<img src='data:image/png;base64,{logo_base64}' alt='School Logo' style='max-width:100%; height:auto; border-radius:18px; object-fit:contain; box-shadow:0 16px 40px rgba(15, 23, 42, 0.09);' />"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        try:
            st.image("a.png", width=920)
        except Exception:
            st.warning("School logo could not be loaded.")

    supabase = get_supabase_client()
    students = load_students(supabase) if supabase else []
    attendance_records = load_attendance(supabase) if supabase else []
    fee_records = load_fee_records(supabase) if supabase else []

    total_students = len(students)
    attendance_rate = 0.0
    if attendance_records:
        present = sum(1 for record in attendance_records if record.get("status") == "Present")
        total_attendance = len(attendance_records)
        if total_attendance:
            attendance_rate = min(100.0, max(0.0, (present / total_attendance) * 100))
    fee_current_status = "Live" if fee_records else "No data"
    pending_fees = sum(1 for record in fee_records if record.get("status") in {"Pending", "Overdue"})
    fee_summary = f"{pending_fees} pending" if pending_fees else "All clear"

    cols = st.columns([1.5, 1])
    with cols[0]:
        st.markdown(
            "<div style='display:grid; gap:18px; margin-bottom:24px;'>"
            "<div style='padding:22px; border-radius:24px; background:#ffffff; box-shadow:0 18px 35px rgba(15,23,42,0.06);'>"
            "<div style='font-size:1.35rem; color:#111827; font-weight:800; white-space:nowrap;'>Success is built one disciplined day at a time</div>"
            "</div>"
            "<div style='display:grid; gap:12px; grid-template-columns: repeat(3, minmax(0, 1fr));'>"
            "<div style='padding:18px; border-radius:20px; background:rgba(243,244,255,0.9); border:1px solid rgba(16,185,129,0.12);'>"
            "<div style='font-size:0.8rem; color:#6b7280;'>Students</div>"
            f"<div style='font-size:1.55rem; font-weight:700; color:#16a34a;'>{html.escape(str(total_students))}</div>"
            "</div>"
            "<div style='padding:18px; border-radius:20px; background:rgba(236,253,245,0.9); border:1px solid rgba(16,185,129,0.12);'>"
            "<div style='font-size:0.8rem; color:#6b7280;'>Attendance</div>"
            f"<div style='font-size:1.55rem; font-weight:700; color:#16a34a;'>{html.escape(f'{attendance_rate:.0f}%')}</div>"
            "</div>"
            "<div style='padding:18px; border-radius:20px; background:rgba(255,247,237,0.9); border:1px solid rgba(245,158,11,0.12);'>"
            "<div style='font-size:0.8rem; color:#6b7280;'>Fee Tracking</div>"
            f"<div style='font-size:1.55rem; font-weight:700; color:#b45309;'>{html.escape(fee_summary)}</div>"
            "</div>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        # removed the small 'Premium access' panel to keep the login hub focused
        if st.button("➕ Create Account", use_container_width=True):
            st.session_state.auth_view = "signup"
            st.rerun()

    with cols[1]:
        st.markdown(
            "<div style='padding:22px; border-radius:24px; background:#ffffff; box-shadow:0 18px 35px rgba(15,23,42,0.06);'>"
            "<div style='font-size:1.2rem; font-weight:700; color:#111827; margin-bottom:16px;'>Sign in to your role</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        supabase = get_supabase_client()
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["Admin", "Teacher", "Accountant", "Principal", "Student", "Librarian"]
        )

        with tab1:
            with st.form("admin_login_form"):
                admin_username = st.text_input("Admin Username", key="admin_username")
                admin_password = st.text_input("Admin Password", type="password", key="admin_password")
                submitted = st.form_submit_button("Login as Admin")
                if submitted and login_user(supabase, admin_username, admin_password, role="admin"):
                    st.rerun()

        with tab2:
            with st.form("teacher_login_form"):
                teacher_login_username = st.text_input("Username", key="teacher_login_username")
                teacher_login_password = st.text_input("Password", type="password", key="teacher_login_password")
                teacher_login_submitted = st.form_submit_button("Login as Teacher")
                if teacher_login_submitted and login_user(supabase, teacher_login_username, teacher_login_password, role="teacher"):
                    st.rerun()

        with tab3:
            with st.form("accountant_login_form"):
                accountant_login_username = st.text_input("Username", key="accountant_login_username")
                accountant_login_password = st.text_input("Password", type="password", key="accountant_login_password")
                accountant_login_submitted = st.form_submit_button("Login as Accountant")
                if accountant_login_submitted and login_user(supabase, accountant_login_username, accountant_login_password, role="accountant"):
                    st.rerun()

        with tab4:
            with st.form("principal_login_form"):
                principal_login_username = st.text_input("Username", key="principal_login_username")
                principal_login_password = st.text_input("Password", type="password", key="principal_login_password")
                principal_login_submitted = st.form_submit_button("Login as Principal")
                if principal_login_submitted and login_user(supabase, principal_login_username, principal_login_password, role="principal"):
                    st.rerun()

        with tab5:
            with st.form("student_login_form"):
                student_username = st.text_input("Username", key="student_login_username")
                student_password = st.text_input("Password", type="password", key="student_login_password")
                submitted = st.form_submit_button("Login as Student")
                if submitted and login_user(supabase, student_username, student_password, role="student"):
                    st.rerun()

        with tab6:
            with st.form("librarian_login_form"):
                librarian_username = st.text_input("Username", key="librarian_login_username")
                librarian_password = st.text_input("Password", type="password", key="librarian_login_password")
                librarian_submitted = st.form_submit_button("Login as Librarian")
                if librarian_submitted and login_user(supabase, librarian_username, librarian_password, role="librarian"):
                    st.rerun()

# ---------------------------------------------------------
# Staff management pages
# ---------------------------------------------------------

def render_staff_accounts(supabase):
    if st.session_state.get("current_role") != "admin":
        st.error("Only an administrator can create staff accounts.")
        return

    st.title("👥 Staff Accounts")
    tab1, tab2, tab3, tab4 = st.tabs(["Add Teacher", "Add Accountant", "Add Principal", "Add Librarian"])
    with tab1:
        with st.form("admin_add_teacher_account"):
            full_name = st.text_input("Full Name", key="admin_teacher_name")
            subject = st.text_input("Subject", key="admin_teacher_subject")
            phone = st.text_input("Phone", key="admin_teacher_phone")
            email = st.text_input("Email", key="admin_teacher_email")
            salary = st.number_input("Salary", min_value=0.0, step=500.0, value=0.0, key="admin_teacher_salary")
            username = st.text_input("Username", key="admin_teacher_username")
            password = st.text_input("Password", type="password", key="admin_teacher_password")
            submitted = st.form_submit_button("Create Teacher Account")
            if submitted and full_name and username and password:
                if create_user(supabase, username, password, "teacher", staff_data={"full_name": full_name, "subject": subject, "phone": phone, "email": email}):
                    add_teacher(supabase, full_name, subject, phone, email, salary)
                    st.success("Teacher account created")
    with tab2:
        with st.form("admin_add_accountant_account"):
            full_name = st.text_input("Full Name", key="admin_accountant_name")
            phone = st.text_input("Phone", key="admin_accountant_phone")
            email = st.text_input("Email", key="admin_accountant_email")
            username = st.text_input("Username", key="admin_accountant_username")
            password = st.text_input("Password", type="password", key="admin_accountant_password")
            submitted = st.form_submit_button("Create Accountant Account")
            if submitted:
                if not full_name or not username or not password:
                    st.error("Full name, username, and password are required")
                elif create_user(supabase, username, password, "accountant", staff_data={"full_name": full_name, "phone": phone, "email": email}):
                    st.success("Accountant account created")

    with tab3:
        with st.form("admin_add_principal_account"):
            full_name = st.text_input("Full Name", key="admin_principal_name")
            phone = st.text_input("Phone", key="admin_principal_phone")
            email = st.text_input("Email", key="admin_principal_email")
            username = st.text_input("Username", key="admin_principal_username")
            password = st.text_input("Password", type="password", key="admin_principal_password")
            submitted = st.form_submit_button("Create Principal Account")
            if submitted:
                if not full_name or not username or not password:
                    st.error("Full name, username, and password are required")
                elif create_user(supabase, username, password, "principal", staff_data={"full_name": full_name, "phone": phone, "email": email}):
                    st.success("Principal account created")

    with tab4:
        with st.form("admin_add_librarian_account"):
            full_name = st.text_input("Full Name", key="admin_librarian_name")
            phone = st.text_input("Phone", key="admin_librarian_phone")
            email = st.text_input("Email", key="admin_librarian_email")
            username = st.text_input("Username", key="admin_librarian_username")
            password = st.text_input("Password", type="password", key="admin_librarian_password")
            submitted = st.form_submit_button("Create Librarian Account")
            if submitted:
                if not full_name or not username or not password:
                    st.error("Full name, username, and password are required")
                elif create_user(supabase, username, password, "librarian", staff_data={"full_name": full_name, "phone": phone, "email": email}):
                    st.success("Librarian account created")


# ---------------------------------------------------------
# Student signup pages
# ---------------------------------------------------------

def render_signup_page():
    st.title("🏫 Create Your School Account")
    st.caption("Register as a student. Staff accounts are created by an administrator.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Students", "100+", "Active")
    col2.metric("Attendance", "98%", "Stable")
    col3.metric("Fee Tracking", "Live", "Smart")

    st.write("")
    col_left, col_right = st.columns([1, 1])
    if col_left.button("Login", use_container_width=True):
        st.session_state.auth_view = "login"
        st.rerun()
    if col_right.button("Create Account", use_container_width=True, type="primary"):
        st.session_state.auth_view = "signup"
        st.rerun()

    supabase = get_supabase_client()
    tab1, tab2 = st.tabs(["Admin", "Student"])

    with tab1:
        st.info("Admin signup is not available here. Please use the admin login form.")

    with tab2:
        st.info("Teacher, accountant, principal, and librarian accounts must be created from the administrator Staff Accounts page.")
        with st.form("student_signup_form"):
            student_name = st.text_input("Full Name", key="student_signup_name")
            student_admission = st.text_input("Admission Number", key="student_signup_admission")
            student_class = st.text_input("Class", key="student_signup_class")
            guardian_name = st.text_input("Guardian Name", key="student_signup_guardian")
            student_phone = st.text_input("Phone", key="student_signup_phone")
            student_email = st.text_input("Email", key="student_signup_email")
            student_username = st.text_input("Username", key="student_signup_username")
            student_password = st.text_input("Password", type="password", key="student_signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="student_signup_confirm")
            submitted = st.form_submit_button("Register as Student")
            if submitted:
                if student_password != confirm_password:
                    st.error("Passwords do not match")
                elif not student_name or not student_admission or not student_class or not student_username:
                    st.error("Name, admission number, class, and username are required")
                else:
                    existing_student = None
                    try:
                        existing_response = supabase.table("students").select("id").eq("admission_no", student_admission).limit(1).execute()
                        if existing_response.data:
                            existing_student = existing_response.data[0]
                    except Exception:
                        existing_student = None

                    if existing_student:
                        st.error("A student with that admission number already exists. Please use a unique admission number.")
                    elif get_user_by_username(supabase, student_username):
                        st.error("That username already exists. Please choose a different username.")
                    else:
                        student_data = {
                            "full_name": student_name,
                            "admission_no": student_admission,
                            "class_name": student_class,
                            "guardian_name": guardian_name,
                            "phone": student_phone,
                            "email": student_email,
                            "created_at": datetime.now().isoformat(),
                        }
                        student_id = None
                        try:
                            response = supabase.table("students").insert(student_data).execute()
                            if response.data:
                                student_id = response.data[0].get("id")
                        except Exception as exc:
                            error_text = str(exc)
                            if "students_admission_no_key" in error_text or "duplicate key value" in error_text:
                                st.error("Admission number already exists. Please use a unique admission number.")
                            else:
                                st.error(f"Could not create the student record: {exc}")

                        if student_id and register_user(
                            supabase,
                            student_username,
                            student_password,
                            role="student",
                            student_id=student_id,
                            student_data=student_data,
                        ):
                            st.rerun()

# ---------------------------------------------------------
# Dashboard pages
# ---------------------------------------------------------

def render_dashboard(students, attendance_records, fee_records, marks, teachers, courses):
    render_school_logo_header()
    st.title("🏆 Executive Performance Dashboard")
    st.markdown(
        "<div style='font-size:0.95rem; color:#475569; margin-bottom:14px;'>A premium leadership dashboard with clear direction, current performance trends, and prioritized school health metrics.</div>",
        unsafe_allow_html=True,
    )

    total_students = len(students)
    attendance_present = sum(1 for entry in attendance_records if entry.get("status") == "Present")
    attendance_absent = len(attendance_records) - attendance_present
    pending_fees = sum(float(entry.get("amount", 0)) for entry in fee_records if entry.get("status") == "Pending")
    average_score = round(sum(int(entry.get("score", 0)) for entry in marks) / len(marks), 1) if marks else 0
    attendance_rate = round(attendance_present / max(1, attendance_present + attendance_absent) * 100, 1) if (attendance_present + attendance_absent) else 0
    total_paid = sum(float(entry.get("amount", 0)) for entry in fee_records if entry.get("status") == "Paid") if fee_records else 0

    st.markdown(
        f"<div style='display:grid; grid-template-columns: 1.3fr 0.7fr; gap:24px; margin-bottom:24px;'>"
        f"<div style='padding:24px; border-radius:24px; background:linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,250,252,0.98)); border:1px solid rgba(139,92,246,0.18); box-shadow:0 24px 60px rgba(139,92,246,0.08);'>"
        f"<div style='display:flex; align-items:center; gap:16px; margin-bottom:18px;'>"
        f"<div style='width:64px; height:64px; background: rgba(139,92,246,0.15); border-radius:18px; display:flex; align-items:center; justify-content:center; font-size:1.8rem;'>📊</div>"
        f"<div><div style='font-size:1.8rem; font-weight:800; color:#111827;'>Premium School Pulse</div>"
        f"<div style='color:#475569; margin-top:4px;'>Executive metrics with revenue, attendance and academic score visibility.</div></div></div>"
        f"<div style='display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:16px;'>"
        f"<div style='padding:18px; border-radius:18px; background:#fff; border:1px solid rgba(16,185,129,0.14);'>"
        f"<div style='color:#475569; font-size:0.9rem;'>Attendance Rate</div>"
        f"<div style='font-size:2rem; font-weight:800; color:#16a34a; margin-top:8px;'>{attendance_rate:.1f}%</div>"
        f"</div>"
        f"<div style='padding:18px; border-radius:18px; background:#fff; border:1px solid rgba(34,197,94,0.14);'>"
        f"<div style='color:#475569; font-size:0.9rem;'>Fees Collected</div>"
        f"<div style='font-size:2rem; font-weight:800; color:#16a34a; margin-top:8px;'>₹{total_paid:,.0f}</div>"
        f"</div>"
        f"<div style='padding:18px; border-radius:18px; background:#fff; border:1px solid rgba(245,158,11,0.14);'>"
        f"<div style='color:#475569; font-size:0.9rem;'>Pending Fees</div>"
        f"<div style='font-size:2rem; font-weight:800; color:#b45309; margin-top:8px;'>₹{pending_fees:,.0f}</div>"
        f"</div>"
        f"</div></div>"
        f"<div style='padding:24px; border-radius:24px; background: linear-gradient(135deg, rgba(139,92,246,0.16), rgba(16,185,129,0.08)); border:1px solid rgba(139,92,246,0.18); box-shadow:0 24px 60px rgba(139,92,246,0.08);'>"
        f"<div style='font-size:1rem; font-weight:700; color:#111827; margin-bottom:12px;'>Leadership Snapshot</div>"
        f"<div style='display:flex; flex-direction:column; gap:12px;'>"
        f"<div style='background:#fff; border-radius:16px; padding:16px; border:1px solid rgba(139,92,246,0.12);'>"
        f"<div style='font-size:0.9rem; color:#475569;'>Total Teachers</div>"
        f"<div style='font-size:1.8rem; font-weight:800; color:#111827; margin-top:8px;'>{len(teachers)}</div>"
        f"</div>"
        f"<div style='background:#fff; border-radius:16px; padding:16px; border:1px solid rgba(34,197,94,0.12);'>"
        f"<div style='font-size:0.9rem; color:#475569;'>Average Score</div>"
        f"<div style='font-size:1.8rem; font-weight:800; color:#111827; margin-top:8px;'>{average_score:.1f}</div>"
        f"</div>"
        f"<div style='background:#fff; border-radius:16px; padding:16px; border:1px solid rgba(245,158,11,0.12);'>"
        f"<div style='font-size:0.9rem; color:#475569;'>Attendance Present</div>"
        f"<div style='font-size:1.8rem; font-weight:800; color:#111827; margin-top:8px;'>{attendance_present}</div>"
        f"</div>"
        f"</div></div></div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Performance Trend")
        fee_trend = []
        try:
            fee_df = pd.DataFrame(fee_records)
            if "payment_date" in fee_df.columns and not fee_df.empty:
                fee_df["payment_date"] = pd.to_datetime(fee_df["payment_date"], errors="coerce")
                fee_df = fee_df.dropna(subset=["payment_date"])
                fee_df["month"] = fee_df["payment_date"].dt.to_period("M").dt.to_timestamp()
                fee_trend = fee_df.groupby("month")["amount"].sum().reset_index()
        except Exception:
            fee_trend = []
        if not fee_trend.empty:
            st.line_chart(fee_trend.rename(columns={"month": "Date", "amount": "Fees Collected"}).set_index("Date"), use_container_width=True)
        else:
            st.info("Real-time fee trend data will appear once payments are recorded.")

    with col2:
        st.subheader("Quick Pulse")
        st.markdown(
            "<div style='display:grid; gap:16px;'>"
            "<div style='padding:18px; border-radius:20px; background:#ffffff; border:1px solid rgba(139,92,246,0.14);'>"
            "<div style='font-size:0.9rem; color:#475569;'>Active Classes</div>"
            "<div style='font-size:1.8rem; font-weight:800; color:#111827; margin-top:8px;'>{len(courses)}</div>"
            "</div>"
            "<div style='padding:18px; border-radius:20px; background:#ffffff; border:1px solid rgba(34,197,94,0.14);'>"
            "<div style='font-size:0.9rem; color:#475569;'>Real-time Alerts</div>"
            "<div style='font-size:1rem; margin-top:8px; color:#111827;'>"
            f"{'Low attendance detected' if attendance_rate < 75 else 'Attendance is stable'}<br>"
            f"{'Pending fee review required' if pending_fees > 0 else 'Fee collection on track'}"
            "</div>"
            "</div>"
            "<div style='padding:18px; border-radius:20px; background:#ffffff; border:1px solid rgba(245,158,11,0.14);'>"
            "<div style='font-size:0.9rem; color:#475569;'>Top Performance</div>"
            "<div style='font-size:1.8rem; font-weight:800; color:#111827; margin-top:8px;'>"
            f"{average_score}% avg" if average_score else "No score data"
            "</div>"
            "</div></div>",
            unsafe_allow_html=True,
        )

    st.subheader("Recent Student Activity")
    recent_students = pd.DataFrame(students[:5])
    if not recent_students.empty:
        st.dataframe(recent_students[["admission_no", "full_name", "class_name", "email"]], use_container_width=True)
    else:
        st.info("No student activity yet")


# ---------------------------------------------------------
# Student management pages
# ---------------------------------------------------------

def render_students(students, supabase, can_edit=True):
    st.title("🧑‍🎓 Students")
    if can_edit:
        with st.form("student_form"):
            full_name = st.text_input("Full Name")
            admission_no = st.text_input("Admission Number")
            class_name = st.text_input("Class")
            guardian_name = st.text_input("Guardian Name")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            submitted = st.form_submit_button("Add Student")
            if submitted:
                if not full_name or not admission_no or not class_name:
                    st.error("Full name, admission number, and class are required")
                else:
                    student_data = {
                        "full_name": full_name,
                        "admission_no": admission_no,
                        "class_name": class_name,
                        "guardian_name": guardian_name,
                        "phone": phone,
                        "email": email,
                        "created_at": datetime.now().isoformat(),
                    }
                    if add_student(supabase, student_data):
                        st.rerun()

    st.subheader("Student List")
    if students:
        student_df = pd.DataFrame(students)[["id", "admission_no", "full_name", "class_name", "guardian_name", "phone", "email"]]
        st.dataframe(student_df, use_container_width=True)

        if not can_edit:
            return

        st.markdown("---")
        st.subheader("Update or Delete Student")
        student_options = {f"{student['id']} - {student['full_name']}": student for student in students}
        selected_label = st.selectbox("Select Student to Manage", list(student_options.keys()), key="manage_student_select")
        selected_student = student_options[selected_label]

        full_name = st.text_input("Full Name", value=selected_student.get("full_name", ""), key=f"edit_full_name_{selected_student['id']}")
        admission_no = st.text_input("Admission Number", value=selected_student.get("admission_no", ""), key=f"edit_admission_no_{selected_student['id']}")
        class_name = st.text_input("Class", value=selected_student.get("class_name", ""), key=f"edit_class_name_{selected_student['id']}")
        guardian_name = st.text_input("Guardian Name", value=selected_student.get("guardian_name", ""), key=f"edit_guardian_name_{selected_student['id']}")
        phone = st.text_input("Phone", value=selected_student.get("phone", ""), key=f"edit_phone_{selected_student['id']}")
        email = st.text_input("Email", value=selected_student.get("email", ""), key=f"edit_email_{selected_student['id']}")

        col1, col2 = st.columns(2)
        if col1.button("Update Student", key=f"update_student_{selected_student['id']}"):
            if not full_name or not admission_no or not class_name:
                st.error("Full name, admission number, and class are required")
            else:
                updated_data = {
                    "full_name": full_name,
                    "admission_no": admission_no,
                    "class_name": class_name,
                    "guardian_name": guardian_name,
                    "phone": phone,
                    "email": email,
                }
                if update_student(supabase, selected_student["id"], updated_data):
                    st.rerun()

        if col2.button("Delete Student", type="secondary", key=f"delete_student_{selected_student['id']}"):
            if delete_student(supabase, selected_student["id"]):
                st.rerun()
    else:
        st.info("No students available")


def render_student_details(students, attendance_records, marks, supabase, can_edit=True):
    st.title("🧑‍🎓 Student Details & Marks")
    if students:
        student_names = {student["full_name"]: student for student in students}
        selected_name = st.selectbox("Select Student", list(student_names.keys()))
        student = student_names[selected_name]
        st.subheader(student["full_name"])
        st.write(f"Admission No: {student.get('admission_no')}")
        st.write(f"Class: {student.get('class_name')}")
        st.write(f"Guardian: {student.get('guardian_name')}")
        st.write(f"Phone: {student.get('phone')}")
        st.write(f"Email: {student.get('email')}")

        student_marks = [mark for mark in marks if mark.get("student_id") == student["id"]]
        student_attendance = [entry for entry in attendance_records if entry.get("student_id") == student["id"]]
        avg_score = round(sum(int(mark.get("score", 0)) for mark in student_marks) / len(student_marks), 1) if student_marks else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Attendance", len(student_attendance))
        col2.metric("Marks Added", len(student_marks))
        col3.metric("Average Score", avg_score)

        if can_edit:
            with st.form("marks_form"):
                subject = st.text_input("Subject")
                score = st.number_input("Score", min_value=0, max_value=100, step=1)
                term = st.text_input("Term")
                submitted = st.form_submit_button("Add Mark")
                if submitted and subject and term:
                    if add_mark(supabase, student["id"], subject, score, term):
                        st.rerun()

        st.subheader("Marks")
        if student_marks:
            marks_df = pd.DataFrame(student_marks)
            st.dataframe(marks_df[["subject", "score", "term"]], use_container_width=True)
        else:
            st.info("No marks recorded yet")
    else:
        st.info("No students to display")


# ---------------------------------------------------------
# Attendance pages
# ---------------------------------------------------------

def render_attendance(students, attendance_records, supabase, can_edit=True):
    st.title("📝 Attendance")
    if not students:
        st.info("Add students first")
        return

    present_count = sum(1 for entry in attendance_records if entry.get("status") == "Present")
    absent_count = sum(1 for entry in attendance_records if entry.get("status") == "Absent")
    late_count = sum(1 for entry in attendance_records if entry.get("status") == "Late")

    col1, col2, col3 = st.columns(3)
    col1.metric("Present", present_count)
    col2.metric("Absent", absent_count)
    col3.metric("Late", late_count)

    class_names = sorted({student.get("class_name", "Unassigned") for student in students})
    selected_class = st.selectbox("Choose Class", class_names, key="attendance_class")
    class_students = [student for student in students if student.get("class_name", "Unassigned") == selected_class]

    st.subheader(f"Students in {selected_class}")
    student_list = pd.DataFrame(
        [
            {
                "id": student.get("id"),
                "full_name": student.get("full_name"),
                "admission_no": student.get("admission_no"),
                "class_name": student.get("class_name"),
            }
            for student in class_students
        ]
    )
    if not student_list.empty:
        st.dataframe(student_list, use_container_width=True, hide_index=True)

    if class_students:
        student_options = {
            f"{student.get('full_name')} ({student.get('admission_no')})": student
            for student in class_students
        }
        selected_name = st.selectbox("Open Student Attendance", list(student_options.keys()), key="attendance_student")
        selected_student = student_options[selected_name]
        selected_student_id = selected_student.get("id")
        selected_records = [
            record for record in attendance_records
            if str(record.get("student_id")) == str(selected_student_id)
        ]
        st.subheader(f"Attendance: {selected_student.get('full_name')}")
        if selected_records:
            st.dataframe(
                pd.DataFrame(selected_records)[["attendance_date", "status"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No attendance records for this student")

    if can_edit and class_students:
        attendance_date = st.date_input("Attendance Date", value=date.today(), key="attendance_date")
        status = st.selectbox("Status", ["Present", "Absent", "Late"], key="attendance_status")

        if st.button("Mark Attendance"):
            if add_attendance(supabase, selected_student_id, attendance_date, status):
                st.success("Attendance recorded")
                st.rerun()

    st.subheader("Attendance Records")
    if attendance_records:
        df = pd.DataFrame(attendance_records)
        st.dataframe(df[["attendance_date", "student_id", "status"]], use_container_width=True, hide_index=True)
    else:
        st.info("No attendance records yet")


# ---------------------------------------------------------
# Course pages
# ---------------------------------------------------------

def render_courses(courses, supabase, can_edit=True):
    render_school_logo_header()
    st.title("📚 Courses")
    if can_edit:
        with st.form("course_form"):
            course_name = st.text_input("Course Name")
            class_name = st.text_input("Class")
            teacher_name = st.text_input("Teacher Name")
            submitted = st.form_submit_button("Add Course")
            if submitted and course_name and class_name:
                if add_course(supabase, course_name, class_name, teacher_name):
                    st.rerun()

    st.subheader("Course List")
    if courses:
        st.dataframe(pd.DataFrame(courses), use_container_width=True)
    else:
        st.info("No courses created yet")


# ---------------------------------------------------------
# Fee management pages
# ---------------------------------------------------------

def render_fees(students, fee_records, supabase, can_edit=True):
    render_school_logo_header()
    st.title("💰 Fees")

    def calculate_fee_summary(records):
        paid = sum(float(record.get("amount", 0) or 0) for record in records if record.get("status") == "Paid")
        due = sum(float(record.get("amount", 0) or 0) for record in records if record.get("status") in {"Pending", "Overdue"})
        overdue = sum(float(record.get("amount", 0) or 0) for record in records if record.get("status") == "Overdue")
        advance = max(paid - due, 0)
        return due + paid, due, paid, overdue, advance

    total_fee, due_total, paid_total, overdue_total, advance_total = calculate_fee_summary(fee_records)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.8])
    col1.metric("Total Fee", f"{total_fee:,.0f}")
    col2.metric("Due Fee", f"{due_total:,.0f}")
    col3.metric("Paid Fee", f"{paid_total:,.0f}")
    col4.metric("Overdue", f"{overdue_total:,.0f}")
    col5.metric("Advance", f"{advance_total:,.0f}")

    if students and can_edit:
        fee_student_options = {
            f"{student['full_name']} | {student.get('admission_no', 'N/A')} | {student.get('class_name', 'Unassigned')}": student["id"]
            for student in students
        }
        with st.form("fee_form"):
            left_col, right_col = st.columns(2)
            with left_col:
                selected_fee_name = st.selectbox("Select Student", list(fee_student_options.keys()), key="fee_student")
                fee_category = st.selectbox(
                    "Fee Category",
                    ["Tuition", "Premium", "Exam", "Library", "Miscellaneous"],
                    key="fee_category",
                )
                if fee_category == "Premium":
                    st.markdown(
                        "<div style='margin: 8px 0; padding: 8px 12px; display: inline-block; background: rgba(156, 39, 176, 0.12); color: #7b1fa2; border-radius: 999px; font-weight: 700;'>Premium Fee Selected</div>",
                        unsafe_allow_html=True,
                    )
                term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3", "Term 4"], key="fee_term")
                due_date = st.date_input("Due Date", value=date.today(), key="fee_due_date")
                payment_date = st.date_input("Payment Date", value=date.today(), key="fee_date")
            with right_col:
                amount = st.number_input("Amount", min_value=0.0, step=100.0)
                status = st.selectbox("Status", ["Paid", "Pending", "Overdue"], key="fee_status")
                payment_method = st.selectbox("Payment Method", ["Cash", "Online"], key="fee_payment_method")
                online_option = None
                if payment_method == "Online":
                    online_option = st.selectbox("Online Payment Type", ["Esawa"], key="fee_online_option")
                    image_file = "aa.png"
                    image_path = os.path.join(os.path.dirname(__file__), image_file)
                    if os.path.exists(image_path):
                        st.image(image_path, caption=f"{online_option} Payment", width=300)
                    else:
                        st.warning(f"Could not load payment image: {image_file}")
                note = st.text_area("Note")
                premium_description = ""
                if fee_category == "Premium":
                    premium_description = st.text_input("Premium Fee Description", key="premium_description")

            submitted = st.form_submit_button("Save Fee Record")
            if submitted:
                combined_note = f"{fee_category} | {term} | Due {due_date}"
                if premium_description:
                    combined_note += f" | Premium: {premium_description}"
                if payment_method == "Online" and online_option:
                    combined_note += f" | Online Payment: {online_option}"
                if note:
                    combined_note += f" | Note: {note}"
                payment_method_to_save = online_option if payment_method == "Online" and online_option else payment_method
                if add_fee_record(
                    supabase,
                    fee_student_options[selected_fee_name],
                    amount,
                    payment_date,
                    status,
                    payment_method_to_save,
                    combined_note,
                ):
                    st.success("Fee record saved for high school fee tracking")
                    st.rerun()

        selected_student_records = [
            record for record in fee_records
            if str(record.get("student_id")) == str(fee_student_options[selected_fee_name])
        ]
        preview_records = [*selected_student_records, {"amount": amount, "status": status}]
        preview_total, preview_due, preview_paid, _, preview_advance = calculate_fee_summary(preview_records)
        st.caption(
            f"Live preview: Total {preview_total:,.2f} | Due {preview_due:,.2f} | "
            f"Paid {preview_paid:,.2f} | Advance {preview_advance:,.2f}"
        )
    else:
        st.info("Add students first")

    enriched_fees = enrich_fee_records(fee_records, students)
    if enriched_fees:
        fee_df = pd.DataFrame(enriched_fees)
        display_cols = [
            "payment_date", "due_date", "student_name", "admission_no", "class_name",
            "fee_category", "term", "payment_method", "amount", "status", "description", "note"
        ]
        st.subheader("Fee Records")
        st.dataframe(fee_df[display_cols], use_container_width=True, hide_index=True)

        outstanding_df = fee_df[fee_df["status"].isin(["Pending", "Overdue"])]
        st.subheader("Outstanding Fees")
        if not outstanding_df.empty:
            st.dataframe(outstanding_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.success("No outstanding fees at the moment")

        receipt_student_options = {
            f"{student.get('full_name')} ({student.get('admission_no')})": student
            for student in students
            if any(str(record.get("student_id")) == str(student.get("id")) for record in fee_records)
        }
        if receipt_student_options:
            selected_receipt_label = st.selectbox("Select Student Receipt", list(receipt_student_options), key="fee_receipt_student")
            selected_receipt_student = receipt_student_options[selected_receipt_label]
            selected_receipt_records = [
                record for record in enriched_fees
                if str(record.get("student_id")) == str(selected_receipt_student.get("id"))
            ]
            receipt_total = sum(record["amount"] for record in selected_receipt_records)
            receipt_paid = sum(record["amount"] for record in selected_receipt_records if record.get("status") == "Paid")
            receipt_due = sum(record["amount"] for record in selected_receipt_records if record.get("status") in {"Pending", "Overdue"})
            receipt_advance = max(receipt_paid - receipt_due, 0)
            receipt_rows = "".join(
                f"<tr><td>{html.escape(str(record.get('payment_date', '')))}</td>"
                f"<td>{html.escape(str(record.get('fee_category', '')))}</td>"
                f"<td>{html.escape(str(record.get('term', '')))}</td>"
                f"<td>{html.escape(str(record.get('payment_method', '')))}</td>"
                f"<td>{html.escape(str(record.get('status', '')))}</td>"
                f"<td>{float(record.get('amount', 0)):,.2f}</td></tr>"
                for record in selected_receipt_records
            )
            receipt_method = ", ".join(
                sorted(
                    {str(record.get('payment_method', '')) for record in selected_receipt_records if record.get('payment_method')}
                )
            ) or "Cash"
            selected_term = selected_receipt_records[0].get("term", "") if selected_receipt_records else ""
            selected_category = selected_receipt_records[0].get("fee_category", "") if selected_receipt_records else ""
            selected_due_date = selected_receipt_records[0].get("due_date", "") if selected_receipt_records else ""
            receipt_html = f"""
            <button onclick="printFeeReceipt()" style="padding:11px 18px;cursor:pointer;background:#c8a45d;color:#17130b;border:0;border-radius:6px;font-weight:700">Print Fee Receipt</button>
            <script>
            function printFeeReceipt() {{
                const receipt = document.getElementById('fee-receipt').outerHTML;
                const styles = document.getElementById('fee-receipt-styles').innerHTML;
                const printWindow = window.open('', '_blank', 'noopener,noreferrer,width=900,height=700') || window.parent.open('', '_blank');
                if (!printWindow) {{
                    window.print();
                    return;
                }}
                printWindow.document.write('<html><head><title>School Fee Receipt</title><style>' + styles + '</style></head><body>' + receipt + '</body></html>');
                printWindow.document.close();
                printWindow.onload = () => setTimeout(() => printWindow.print(), 250);
            }}
            </script>
            <style id="fee-receipt-styles">
                body {{ margin:0; background:#eeeae2; font-family:Arial,sans-serif; color:#25231f; }}
                .invoice {{ max-width:760px; margin:20px auto; background:#fff; padding:42px; box-shadow:0 8px 30px #bbb; }}
                .brand {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #c8a45d; padding-bottom:20px; }}
                .brand h1 {{ margin:0; font-family:Georgia,serif; font-size:30px; letter-spacing:1px; }}
                .brand p {{ margin:6px 0 0; color:#7b756b; }}
                .receipt-label {{ text-align:right; color:#9b7938; font-weight:700; letter-spacing:2px; text-transform:uppercase; }}
                .meta {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:26px 0; color:#555; }}
                .meta strong {{ color:#222; display:block; margin-top:3px; }}
                table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
                th {{ background:#25231f; color:#fff; text-align:left; padding:12px; font-size:12px; text-transform:uppercase; letter-spacing:1px; }}
                td {{ padding:13px 12px; border-bottom:1px solid #e5e0d7; }}
                td:last-child, th:last-child {{ text-align:right; }}
                .totals {{ margin:24px 0 0 auto; max-width:300px; }}
                .totals div {{ display:flex; justify-content:space-between; padding:7px 0; }}
                .grand {{ border-top:2px solid #c8a45d; font-size:18px; font-weight:700; padding-top:12px !important; }}
                .footer {{ margin-top:38px; color:#8a847a; font-size:12px; text-align:center; }}
                @media print {{ body {{ background:#fff; }} .invoice {{ margin:0; box-shadow:none; max-width:none; }} }}
            </style>
            <div id="fee-receipt" class="invoice">
                <div class="brand"><div><h1>Shree Janta Secondary School</h1><p>School Management Information System</p></div><div class="receipt-label">Fee Receipt</div></div>
                <div class="meta"><div>Student<strong>{html.escape(str(selected_receipt_student.get('full_name', '')))}</strong></div><div>Admission No<strong>{html.escape(str(selected_receipt_student.get('admission_no', '')))}</strong></div></div>
                <div class="meta"><div>Class<strong>{html.escape(str(selected_receipt_student.get('class_name', '')))}</strong></div><div>Term<strong>{html.escape(str(selected_term))}</strong></div></div>
                <div class="meta"><div>Method<strong>{html.escape(receipt_method)}</strong></div><div>Status<strong>{html.escape(str(selected_receipt_records[0].get('status', '') if selected_receipt_records else ''))}</strong></div></div>
                <table><tr><th>Date</th><th>Category</th><th>Term</th><th>Method</th><th>Status</th><th>Amount</th></tr>{receipt_rows}</table>
                <div class="totals"><div><span>Total Fee</span><strong>{receipt_total:,.2f}</strong></div><div><span>Paid</span><strong>{receipt_paid:,.2f}</strong></div><div><span>Advance</span><strong>{receipt_advance:,.2f}</strong></div><div class="grand"><span>Due</span><strong>{receipt_due:,.2f}</strong></div></div>
                <div class="footer">Thank you for choosing Shree Janta Secondary School</div>
            </div>
            """
            components.html(receipt_html, height=460, scrolling=True)
    else:
        st.subheader("Fee Records")
        st.info("No fee records yet")


# ---------------------------------------------------------
# Teacher management pages
# ---------------------------------------------------------

def render_teachers(teachers, supabase, can_edit=True):
    render_school_logo_header()
    st.title("👩‍🏫 Teachers")
    if can_edit:
        with st.form("teacher_form"):
            full_name = st.text_input("Teacher Name")
            subject = st.text_input("Subject")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            salary = st.number_input("Salary", min_value=0.0, step=500.0, value=0.0)
            submitted = st.form_submit_button("Add Teacher")
            if submitted and full_name:
                if add_teacher(supabase, full_name, subject, phone, email, salary):
                    st.rerun()

    st.subheader("Teacher List")
    if teachers:
        teacher_df = pd.DataFrame(teachers)
        if "salary" not in teacher_df.columns:
            teacher_df["salary"] = 0.0
        st.dataframe(teacher_df[["full_name", "subject", "phone", "email", "salary"]], use_container_width=True)
    else:
        st.info("No teachers added yet")


# ---------------------------------------------------------
# Payroll pages
# ---------------------------------------------------------

def render_teacher_payroll(teachers, salary_payments, supabase):
    render_school_logo_header()
    st.title("💼 Executive Teacher Payroll")
    st.markdown(
        "<div style='font-size:0.95rem; color:#475569; margin-bottom:14px;'>High-end payroll management for teachers with real-time payout tracking, payment summary, and premium payment controls.</div>",
        unsafe_allow_html=True,
    )
    if not teachers:
        st.info("Add teachers first on the Teachers page before recording salary payments.")
        return

    with st.expander("Premium Payroll Quick Actions", expanded=True):
        st.markdown(
            "<div style='padding:18px; border-radius:20px; background: linear-gradient(135deg, rgba(139,92,246,0.12), rgba(34,197,94,0.08)); border:1px solid rgba(139,92,246,0.18); margin-bottom:16px;'>"
            "<strong style='color:#111827;'>Manage teacher payouts with clear tracking, premium analytics, and built-in approval readiness.</strong>"
            "</div>",
            unsafe_allow_html=True,
        )
        with st.form("teacher_salary_payment_form"):
            selected_teacher = st.selectbox(
                "Teacher",
                teachers,
                format_func=lambda t: f"{t.get('full_name', 'Unnamed')} ({t.get('subject', 'N/A')})",
            )
            payment_month = st.text_input("Payment Month", value=datetime.now().strftime("%B %Y"))
            payment_date = st.date_input("Payment Date", value=date.today())
            default_salary = float(selected_teacher.get("salary", 0.0) or 0.0)
            amount = st.number_input("Base Salary", min_value=0.0, value=default_salary, step=100.0)
            allowance = st.number_input("Allowance", min_value=0.0, value=0.0, step=50.0)
            deduction = st.number_input("Deduction", min_value=0.0, value=0.0, step=50.0)
            bonus = st.number_input("Bonus", min_value=0.0, value=0.0, step=50.0)
            payment_method = st.selectbox(
                "Payment Method",
                ["Cash", "Esawa", "Bank Transfer", "Cheque"],
                index=0,
            )
            net_amount = calculate_teacher_net_payment(amount, allowance, deduction, bonus)
            st.write(f"**Calculated Net Payment:** ₹{net_amount:,.2f}")
            note = st.text_area("Note", help="Optional payment note or payroll remark.")
            submitted = st.form_submit_button("Record Salary Payment")
            if submitted:
                if add_teacher_salary_payment(
                    supabase,
                    selected_teacher.get("id"),
                    amount,
                    payment_date,
                    payment_month,
                    note,
                    payment_method=payment_method,
                    allowance=allowance,
                    deduction=deduction,
                    bonus=bonus,
                ):
                    st.success("Salary payment recorded")
                    rerun = getattr(st, "experimental_rerun", None)
                    if callable(rerun):
                        rerun()

    if salary_payments:
        enriched = []
        teacher_map = {str(t.get("id")): t for t in teachers}
        for payment in salary_payments:
            teacher = teacher_map.get(str(payment.get("teacher_id")), {})
            enriched.append({
                "Teacher": teacher.get("full_name", "Unknown"),
                "Subject": teacher.get("subject", ""),
                "Payment Month": payment.get("payment_month", ""),
                "Payment Date": payment.get("payment_date", ""),
                "Payment Method": payment.get("payment_method", "Cash"),
                "Base Salary": float(payment.get("amount", 0) or 0),
                "Allowance": float(payment.get("allowance", 0) or 0),
                "Deduction": float(payment.get("deduction", 0) or 0),
                "Bonus": float(payment.get("bonus", 0) or 0),
                "Net Pay": float(payment.get("net_amount", 0) or calculate_teacher_net_payment(payment.get("amount", 0), payment.get("allowance", 0), payment.get("deduction", 0), payment.get("bonus", 0))),
                "Note": payment.get("note", ""),
            })

        total_payout = sum(item["Net Pay"] for item in enriched)
        top_earners = (
            pd.DataFrame(enriched)
            .groupby("Teacher", as_index=False)["Net Pay"]
            .sum()
            .sort_values("Net Pay", ascending=False)
            .head(3)
        )

        st.markdown(
            "<div style='margin-top:18px;padding:20px;border-radius:22px;background: rgba(139,92,246,0.08); border:1px solid rgba(139,92,246,0.18);'>"
            "<strong style='color:#111827;'>Payroll Trend</strong>"
            "<p style='margin:6px 0 0; color:#475569;'>Track teacher payment volume and recent payout activity.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        salary_df = pd.DataFrame(enriched)
        payroll_trend = []
        try:
            if "Payment Date" in salary_df.columns and not salary_df.empty:
                salary_df["Payment Date"] = pd.to_datetime(salary_df["Payment Date"], errors="coerce")
                salary_df = salary_df.dropna(subset=["Payment Date"])
                salary_df["month"] = salary_df["Payment Date"].dt.to_period("M").dt.to_timestamp()
                payroll_trend = salary_df.groupby("month")["Net Pay"].sum().reset_index()
        except Exception:
            payroll_trend = []

        if not payroll_trend.empty:
            st.line_chart(payroll_trend.rename(columns={"month": "Date"}).set_index("Date"), use_container_width=True)
        else:
            st.info("Payroll trend data will appear once salary payments are recorded.")

        st.subheader("Top Paid Teachers")
        st.dataframe(top_earners, use_container_width=True)

        st.subheader("Salary Payment History")
        st.dataframe(pd.DataFrame(enriched), use_container_width=True)

        st.subheader("Teacher Payroll Report")
        payroll_rows = "".join(
            f"<tr>"
            f"<td>{html.escape(str(record.get('Teacher', '')))}</td>"
            f"<td>{html.escape(str(record.get('Subject', '')))}</td>"
            f"<td>{html.escape(str(record.get('Payment Month', '')))}</td>"
            f"<td>{html.escape(str(record.get('Payment Date', '')))}</td>"
            f"<td>{html.escape(str(record.get('Payment Method', 'Cash')))}</td>"
            f"<td>{float(record.get('Base Salary', 0)):,.2f}</td>"
            f"<td>{float(record.get('Allowance', 0)):,.2f}</td>"
            f"<td>{float(record.get('Deduction', 0)):,.2f}</td>"
            f"<td>{float(record.get('Bonus', 0)):,.2f}</td>"
            f"<td>{float(record.get('Net Pay', 0)):,.2f}</td>"
            f"<td>{html.escape(str(record.get('Note', '')))}</td>"
            f"</tr>"
            for record in enriched
        )
        report_html = f"""
        <button onclick="printPayrollReport()" style="padding:11px 18px;cursor:pointer;background:#16a34a;color:#ffffff;border:0;border-radius:6px;font-weight:700">Print Full Payroll Report</button>
        <script>
        function printPayrollReport() {{
            const report = document.getElementById('payroll-report').outerHTML;
            const styles = document.getElementById('payroll-report-styles').innerHTML;
            const printWindow = window.open('', '_blank', 'noopener,noreferrer,width=1200,height=900') || window.parent.open('', '_blank');
            if (!printWindow) {{ window.print(); return; }}
            printWindow.document.write('<html><head><title>Teacher Payroll Report</title><style>' + styles + '</style></head><body>' + report + '</body></html>');
            printWindow.document.close();
            printWindow.onload = () => setTimeout(() => printWindow.print(), 250);
        }}
        </script>
        <style id="payroll-report-styles">
            body {{ margin:0; background:#f3f4f6; font-family:Arial,Helvetica,sans-serif; color:#111827; }}
            .report {{ width:100%; padding:24px; background:#fff; box-sizing:border-box; }}
            .header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:20px; margin-bottom:20px; }}
            .header h1 {{ margin:0; font-size:28px; letter-spacing:0.5px; }}
            .header p {{ margin:6px 0 0; color:#475569; }}
            .meta {{ display:flex; flex-wrap:wrap; gap:16px; color:#475569; font-size:0.95rem; margin-bottom:18px; }}
            .meta div {{ min-width:180px; }}
            table {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:0.92rem; }}
            th, td {{ padding:12px 10px; border:1px solid #dde2e8; }}
            th {{ background:#111827; color:#ffffff; text-align:left; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.04em; }}
            td {{ color:#1f2937; }}
            tbody tr:nth-child(odd) {{ background:#fbfaf8; }}
            .footer {{ margin-top:24px; color:#475569; font-size:0.9rem; }}
            @page {{ size: landscape; margin: 18mm; }}
            @media print {{
                body {{ background:#fff; }}
                .report {{ box-shadow:none; margin:0; padding:0; }}
                .header, .meta, .footer {{ page-break-inside: avoid; }}
                table {{ page-break-inside: auto; }}
                tr {{ page-break-inside: avoid; page-break-after: auto; }}
            }}
        </style>
        <div id="payroll-report" class="report">
            <div class="header"><div><h1>Teacher Payroll Report</h1><p>Comprehensive salary record for all teachers.</p></div><div><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</div></div>
            <div class="meta"><div><strong>Total Records</strong><br>{len(enriched)}</div><div><strong>Total Payout</strong><br>₹{total_payout:,.2f}</div></div>
            <table>
                <thead>
                    <tr>
                        <th>Teacher</th>
                        <th>Subject</th>
                        <th>Payment Month</th>
                        <th>Payment Date</th>
                        <th>Payment Method</th>
                        <th>Base Salary</th>
                        <th>Allowance</th>
                        <th>Deduction</th>
                        <th>Bonus</th>
                        <th>Net Pay</th>
                        <th>Note</th>
                    </tr>
                </thead>
                <tbody>
                    {payroll_rows}
                </tbody>
            </table>
            <div class="footer">Shree Janta Secondary School – payroll report generated for review and printing.</div>
        </div>
        """
        components.html(report_html, height=680, scrolling=True)
    else:
        st.info("No salary payments recorded yet.")


# ---------------------------------------------------------
# Reports pages
# ---------------------------------------------------------

def render_reports(students, attendance_records, fee_records, marks):
    render_school_logo_header()
    st.title("📈 Reports & Analytics")
    if marks:
        marks_df = pd.DataFrame(marks)
        st.subheader("Average Scores by Subject")
        st.bar_chart(marks_df.groupby("subject")["score"].mean(), use_container_width=True)
    else:
        st.info("No marks yet")

    pending = [record for record in fee_records if record.get("status") == "Pending"]
    st.subheader("Pending Fees")
    if pending:
        st.dataframe(pd.DataFrame(pending)[["student_id", "amount", "payment_date", "note"]], use_container_width=True)
    else:
        st.info("No pending fees")

    st.subheader("Attendance Summary")
    if attendance_records:
        st.dataframe(pd.DataFrame(attendance_records)[["attendance_date", "student_id", "status"]], use_container_width=True)
    else:
        st.info("No attendance data")


# ---------------------------------------------------------
# Library pages
# ---------------------------------------------------------

def render_library(books, loans, students, supabase, can_edit=True, can_manage_fines=False):
    render_school_logo_header()
    st.title("📖 Library")
    if can_edit:
        with st.expander("Add Book"):
            with st.form("library_book_form"):
                title = st.text_input("Title")
                author = st.text_input("Author")
                isbn = st.text_input("ISBN")
                copies = st.number_input("Total Copies", min_value=1, step=1)
                submitted = st.form_submit_button("Add Book")
                if submitted and title:
                    if save_record(
                        supabase,
                        "library_books",
                        {
                            "title": title,
                            "author": author,
                            "isbn": isbn,
                            "total_copies": copies,
                            "available_copies": copies,
                            "created_at": datetime.now().isoformat(),
                        },
                    ):
                        st.rerun()

    st.subheader("Book Catalogue")
    if books:
        st.dataframe(pd.DataFrame(books)[["id", "title", "author", "isbn", "total_copies", "available_copies"]], use_container_width=True)
    else:
        st.info("No books added yet")

    if can_edit and books and students:
        st.subheader("Issue Book")
        available_books = [book for book in books if int(book.get("available_copies", 0)) > 0]
        if available_books:
            book_options = {f"{book['title']} ({book['available_copies']} available)": book for book in available_books}
            student_options = {student["full_name"]: student for student in students}
            selected_book = st.selectbox("Book", list(book_options), key="issue_book")
            selected_student = st.selectbox("Student", list(student_options), key="issue_student")
            due_date = st.date_input("Due Date", value=date.today(), key="issue_due_date")
            if st.button("Issue Book"):
                book = book_options[selected_book]
                student = student_options[selected_student]
                if save_record(
                    supabase,
                    "library_loans",
                    {
                        "book_id": book["id"],
                        "student_id": student["id"],
                        "issue_date": str(date.today()),
                        "due_date": str(due_date),
                        "status": "Issued",
                        "fine_amount": 0,
                        "created_at": datetime.now().isoformat(),
                    },
                ) and update_record(
                    supabase,
                    "library_books",
                    book["id"],
                    {"available_copies": int(book["available_copies"]) - 1},
                ):
                    st.rerun()
        else:
            st.info("All books are currently issued")

    st.subheader("Loans and Fine Management")
    if loans:
        loan_df = pd.DataFrame(loans)
        st.dataframe(loan_df, use_container_width=True)
        active_loans = [loan for loan in loans if loan.get("status") != "Returned"]
        if not can_edit:
            active_loans = []
        if active_loans:
            loan_options = {f"Loan {loan['id']} - Book {loan['book_id']} / Student {loan['student_id']}": loan for loan in active_loans}
            selected_loan_label = st.selectbox("Loan to return", list(loan_options), key="return_loan")
            if st.button("Return Book"):
                loan = loan_options[selected_loan_label]
                book = next((item for item in books if item.get("id") == loan.get("book_id")), None)
                updated = update_record(
                    supabase,
                    "library_loans",
                    loan["id"],
                    {"return_date": str(date.today()), "status": "Returned"},
                )
                if updated and book:
                    updated = update_record(
                        supabase,
                        "library_books",
                        book["id"],
                        {"available_copies": int(book["available_copies"]) + 1},
                    )
                if updated:
                    st.rerun()
    else:
        st.info("No loans yet")


# ---------------------------------------------------------
# Library fine management pages
# ---------------------------------------------------------

    if can_manage_fines and loans:
        st.subheader("Fine Management")
        fine_options = {f"Loan {loan['id']} / Student {loan['student_id']}": loan for loan in loans}
        selected_fine_label = st.selectbox("Select Loan", list(fine_options), key="fine_loan")
        selected_fine_loan = fine_options[selected_fine_label]
        fine_amount = st.number_input(
            "Fine Amount",
            min_value=0.0,
            value=float(selected_fine_loan.get("fine_amount", 0) or 0),
            step=10.0,
            key="fine_amount",
        )
        if st.button("Save Fine"):
            if update_record(supabase, "library_loans", selected_fine_loan["id"], {"fine_amount": fine_amount}):
                st.success("Fine saved")
                st.rerun()

    if can_manage_fines and loans:
        student_by_id = {str(student.get("id")): student for student in students}
        book_by_id = {str(book.get("id")): book for book in books}
        fine_students = {
            f"{student.get('full_name', 'Student')} (ID {student.get('id')})": student
            for student in students
            if any(
                str(loan.get('student_id')) == str(student.get('id'))
                and float(loan.get('fine_amount', 0) or 0) > 0
                for loan in loans
            )
        }

        if fine_students:
            selected_fine_student_label = st.selectbox(
                "Select Student for Fine Receipt",
                list(fine_students),
                key="fine_receipt_student",
            )
            selected_fine_student = fine_students[selected_fine_student_label]
            student_loans = [
                loan
                for loan in loans
                if str(loan.get('student_id')) == str(selected_fine_student.get('id'))
            ]
            fine_total = sum(float(loan.get("fine_amount", 0) or 0) for loan in student_loans)
            bill_rows = "".join(
                f"<tr><td>{html.escape(str(selected_fine_student.get('full_name', '')))}</td>"
                f"<td>{html.escape(str(book_by_id.get(str(loan.get('book_id')), {}).get('title', loan.get('book_id', ''))))}</td>"
                f"<td>{html.escape(str(loan.get('issue_date', '')))}</td>"
                f"<td>{html.escape(str(loan.get('return_date') or loan.get('due_date', '')))}</td>"
                f"<td>{html.escape(str(loan.get('status', '')))}</td>"
                f"<td>{float(loan.get('fine_amount', 0) or 0):,.2f}</td></tr>"
                for loan in student_loans
            )
            qr_payload = {
                "type": "library_fine_receipt",
                "student_id": selected_fine_student.get("id"),
                "student_name": selected_fine_student.get("full_name"),
                "total_fine": fine_total,
                "generated_at": datetime.now().isoformat(),
            }
            qr_bytes, qr_name = get_static_qr_bytes()
            if not qr_bytes:
                qr_bytes = generate_qr_jpeg(qr_payload)
                qr_name = "qr.jpeg"

            fine_bill_html = f"""
            <button onclick="printFineReceipt()" style="padding:11px 18px;cursor:pointer;background:#c8a45d;color:#17130b;border:0;border-radius:6px;font-weight:700">Print Fine Receipt</button>
            <script>
            function printFineReceipt() {{
                const receipt = document.getElementById('fine-receipt').outerHTML;
                const styles = document.getElementById('fine-receipt-styles').innerHTML;
                const printWindow = window.open('', '_blank', 'noopener,noreferrer,width=900,height=700') || window.parent.open('', '_blank');
                if (!printWindow) {{
                    window.print();
                    return;
                }}
                printWindow.document.write('<html><head><title>Library Fine Receipt</title><style>' + styles + '</style></head><body>' + receipt + '</body></html>');
                printWindow.document.close();
                printWindow.onload = () => setTimeout(() => printWindow.print(), 250);
            }}
            </script>
            <style id="fine-receipt-styles">
                body {{ margin:0; background:#eeeae2; font-family:Arial,sans-serif; color:#25231f; }}
                .invoice {{ max-width:760px; margin:20px auto; background:#fff; padding:42px; box-shadow:0 8px 30px #bbb; }}
                .brand {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #c8a45d; padding-bottom:20px; }}
                .brand h1 {{ margin:0; font-family:Georgia,serif; font-size:30px; letter-spacing:1px; }}
                .brand p {{ margin:6px 0 0; color:#7b756b; }}
                .receipt-label {{ text-align:right; color:#9b7938; font-weight:700; letter-spacing:2px; text-transform:uppercase; }}
                .meta {{ margin:26px 0; color:#555; }}
                .meta strong {{ color:#222; display:block; margin-top:3px; }}
                table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
                th {{ background:#25231f; color:#fff; text-align:left; padding:12px 9px; font-size:11px; text-transform:uppercase; letter-spacing:.7px; }}
                td {{ padding:13px 9px; border-bottom:1px solid #e5e0d7; }}
                td:last-child, th:last-child {{ text-align:right; }}
                .grand {{ margin:24px 0 0 auto; max-width:300px; border-top:2px solid #c8a45d; display:flex; justify-content:space-between; padding-top:12px; font-size:18px; font-weight:700; }}
                .footer {{ margin-top:38px; color:#8a847a; font-size:12px; text-align:center; }}
                @media print {{ body {{ background:#fff; }} .invoice {{ margin:0; box-shadow:none; max-width:none; }} }}
            </style>
            <div id="fine-receipt" class="invoice">
                <div class="brand"><div><h1>Shree Janta Secondary School</h1><p>School Management Information System</p></div><div class="receipt-label">Fine Receipt</div></div>
                <div class="meta"><div>Student<strong>{html.escape(str(selected_fine_student.get('full_name', '')))}</strong></div><div>Generated<strong>{html.escape(str(date.today()))}</strong></div></div>
                <table><tr><th>Student</th><th>Book</th><th>Issued</th><th>Returned/Due</th><th>Status</th><th>Fine</th></tr>{bill_rows}</table>
                <div class="grand"><span>Total Fine</span><strong>{fine_total:,.2f}</strong></div>
                <div class="footer">Library fine receipt for selected student</div>
            </div>
            """
            components.html(fine_bill_html, height=520, scrolling=True)
            if qr_bytes:
                st.markdown("### Library Fine QR")
                st.image(qr_bytes, width=120)
                st.download_button(
                    "Download Library Fine QR",
                    data=qr_bytes,
                    file_name=qr_name or "library_fine_qr.png",
                    mime="image/png" if (qr_name or "").lower().endswith(".png") else "image/jpeg",
                )
        else:
            st.info("No student fines are currently available for receipt generation.")

# ---------------------------------------------------------
# Student dashboard pages
# ---------------------------------------------------------

def render_student_home(students, attendance_records, fee_records, marks, books, loans, supabase):
    render_school_logo_header()
    st.title("🎓 Student Dashboard")
    st.write(f"Welcome, {st.session_state.current_user}")
    student_id = st.session_state.current_student_id
    student = next((s for s in students if s.get("id") == student_id), None)

    if student:
        st.subheader(student.get("full_name"))
        st.write(f"Admission No: {student.get('admission_no')}")
        st.write(f"Class: {student.get('class_name')}")
        st.write(f"Guardian: {student.get('guardian_name')}")
        st.write(f"Phone: {student.get('phone')}")
        st.write(f"Email: {student.get('email')}")

        sticker_html = f"""
        <div style='margin:18px 0; display:flex; flex-wrap:wrap; gap:12px;'>
            <div style='padding:16px 20px; border-radius:22px; background:linear-gradient(135deg, #eef2ff, #dbeafe); border:1px solid #c7d2fe; min-width:220px;'>
                <div style='font-size:0.75rem; letter-spacing:0.12em; text-transform:uppercase; color:#4338ca; font-weight:700;'>Student Sticker</div>
                <div style='margin-top:8px; font-size:1.1rem; font-weight:800; color:#1e293b;'>{html.escape(student.get('full_name',''))}</div>
                <div style='margin-top:6px; color:#475569;'>Class {html.escape(student.get('class_name','N/A'))} • {html.escape(student.get('admission_no','N/A'))}</div>
            </div>
            <div style='padding:16px 20px; border-radius:22px; background:#ecfdf5; border:1px solid #86efac; min-width:220px;'>
                <div style='font-size:0.75rem; letter-spacing:0.12em; text-transform:uppercase; color:#15803d; font-weight:700;'>Attendance</div>
                <div style='margin-top:8px; font-size:1.6rem; font-weight:800; color:#065f46;'>
                    {len([r for r in attendance_records if r.get('student_id') == student_id and r.get('status') == 'Present'])}
                </div>
                <div style='margin-top:6px; color:#475569;'>Present days recorded</div>
            </div>
        </div>
        """
        components.html(sticker_html, height=170, scrolling=False)

    student_attendance = [record for record in attendance_records if record.get("student_id") == student_id]
    student_marks = [record for record in marks if record.get("student_id") == student_id]
    student_fees = [record for record in fee_records if record.get("student_id") == student_id]
    student_loans = [record for record in loans if record.get("student_id") == student_id]

    if student_attendance:
        st.subheader("Your Attendance")
        st.dataframe(pd.DataFrame(student_attendance)[["attendance_date", "status"]], use_container_width=True)
    if student_marks:
        st.subheader("Your Marks")
        st.dataframe(pd.DataFrame(student_marks)[["subject", "score", "term"]], use_container_width=True)
    if student_fees:
        st.subheader("Your Fee Records")
        st.dataframe(pd.DataFrame(student_fees)[["payment_date", "amount", "status", "note"]], use_container_width=True)
    st.subheader("Library Books")
    if books:
        st.dataframe(pd.DataFrame(books)[["title", "author", "available_copies"]], use_container_width=True)
    else:
        st.info("No library books available")
    if student_loans:
        st.subheader("Your Library Loans")
        st.dataframe(pd.DataFrame(student_loans)[["book_id", "issue_date", "due_date", "status", "fine_amount"]], use_container_width=True)

    if st.button("Logout"):
        logout_user()
        st.rerun()

    # Rating widget for students to rate the school/app experience
    try:
        st.subheader("Rate Your Experience")
        col1, col2 = st.columns([3, 1])
        with col1:
            rating = st.slider("How would you rate your experience?", 1, 5, 4, key="user_rating")
            comment = st.text_area("Optional comments", key="rating_comment")
        with col2:
            if st.button("Submit Rating", key="submit_rating"):
                payload = {
                    "student_id": student_id,
                    "rating": int(rating),
                    "comment": comment or "",
                    "created_at": datetime.now().isoformat(),
                }
                if save_record(supabase, "ratings", payload):
                    st.success("Thanks for your feedback!")
                    # refresh to show updated averages
                    st.rerun()

        # show average rating if available
        try:
            resp = supabase.table("ratings").select("rating").eq("student_id", student_id).execute()
            ratings = resp.data or []
            if ratings:
                avg = round(sum(int(r.get("rating", 0)) for r in ratings) / len(ratings), 2)
                st.caption(f"Average rating: {avg} ({len(ratings)} responses)")
        except Exception:
            pass
    except Exception:
        pass


# ---------------------------------------------------------
# Main application entry
# ---------------------------------------------------------

def main():
    ensure_state()
    supabase = get_supabase_client()

    if not st.session_state.authenticated:
        if st.session_state.auth_view == "signup":
            render_signup_page()
        else:
            render_login_page()
        return

    st.sidebar.markdown(
        "<div style='font-size:1.1rem; font-weight:700; line-height:1.2; margin-bottom:0.5rem;'>Shree Janta Secondary School</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.write(f"Signed in as: {st.session_state.current_user} ({st.session_state.current_role})")

    if st.session_state.current_role == "admin":
        page_options = ["Staff Accounts", "Courses", "Teachers", "Payroll", "Logout"]
    elif st.session_state.current_role == "principal":
        page_options = ["Dashboard", "Students", "Attendance", "Student Details & Marks", "Courses", "Fees", "Teachers", "Payroll", "Reports", "Library", "Logout"]
    elif st.session_state.current_role == "teacher":
        page_options = ["Attendance", "Logout"]
    elif st.session_state.current_role == "accountant":
        page_options = ["Fees", "Students", "Payroll", "Library", "Logout"]
    elif st.session_state.current_role == "librarian":
        page_options = ["Library", "Logout"]
    else:
        page_options = ["Student Home", "Logout"]

    page = st.sidebar.radio("Navigation", page_options, index=0)
    st.session_state.page = page

    students = load_students(supabase)
    attendance_records = load_attendance(supabase)
    fee_records = load_fee_records(supabase)
    courses = load_courses(supabase)
    marks = load_marks(supabase)
    teachers = load_teachers(supabase)
    teacher_salary_payments = load_teacher_salary_payments(supabase)
    books = load_library_books(supabase)
    loans = load_library_loans(supabase)

    if page == "Staff Accounts":
        render_staff_accounts(supabase)
    elif page == "Dashboard":
        render_dashboard(students, attendance_records, fee_records, marks, teachers, courses)
    elif page == "Students":
        render_students(students, supabase, can_edit=st.session_state.current_role in {"accountant"})
    elif page == "Attendance":
        render_attendance(students, attendance_records, supabase, can_edit=st.session_state.current_role == "teacher")
    elif page == "Student Details & Marks":
        render_student_details(students, attendance_records, marks, supabase, can_edit=st.session_state.current_role == "accountant")
    elif page == "Courses":
        render_courses(courses, supabase, can_edit=st.session_state.current_role == "admin")
    elif page == "Fees":
        render_fees(students, fee_records, supabase, can_edit=st.session_state.current_role == "accountant")
    
    elif page == "Teachers":
        render_teachers(teachers, supabase, can_edit=st.session_state.current_role == "admin")
    elif page == "Payroll":
        render_teacher_payroll(teachers, teacher_salary_payments, supabase)
    elif page == "Reports":
        render_reports(students, attendance_records, fee_records, marks)
    elif page == "Student Home":
        render_student_home(students, attendance_records, fee_records, marks, books, loans, supabase)
    elif page == "Library":
        render_library(
            books,
            loans,
            students,
            supabase,
            can_edit=st.session_state.current_role == "librarian",
            can_manage_fines=st.session_state.current_role == "accountant",
        )
    elif page == "Logout":
        render_logout_page()


# ---------------------------------------------------------
# Logout pages
# ---------------------------------------------------------

def render_logout_page():
    st.title("🚪 Logout")
    st.write("You are about to sign out of the EMIS dashboard.")
    if st.button("Logout"):
        logout_user()
        st.rerun()


if __name__ == "__main__":
    main()
