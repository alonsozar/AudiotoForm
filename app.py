import streamlit as st
from transcription import transcribe_audio
from extraction import extract_info
from utils import create_docx, fill_template
import os
import zipfile
import io

# --- הגדרת דף ---
st.set_page_config(page_title="LegalAI Pro", page_icon="⚖️", layout="wide")

# --- עיצוב CSS (נשאר זהה למה שאהבת) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Heebo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #2c3e50; font-weight: 700; text-align: right; }
    div.stButton > button { background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%); color: white; width: 100%; border-radius: 12px; }
    @media only screen and (max-width: 600px) { .stTextInput > div > div > input { direction: rtl; } }
</style>
""", unsafe_allow_html=True)

# --- סרגל צד ---
with st.sidebar:
    st.title("⚙️ הגדרות תיק")
    
    st.markdown("### 📂 תבניות לטיפול")
    st.info("ניתן להעלות מספר קבצים במקביל (למשל: ייפוי כוח + כתב תביעה).")
    # שינוי: קבלת מספר קבצים
    uploaded_templates = st.file_uploader("העלה תבניות (.docx)", type=["docx"], accept_multiple_files=True)
    
    st.markdown("---")
    
    st.markdown("### 🎯 שדות לחילוץ")
    default_schema = """
    {
        "client_name": "שם הלקוח המלא",
        "id_number": "מספר תעודת זהות",
        "event_date": "תאריך האירוע (DD/MM/YYYY)",
        "main_complaint": "תיאור העובדות (בשפה משפטית)",
        "requested_remedy": "הסעד המבוקש"
    }
    """
    schema = st.text_area("הגדרת JSON:", value=default_schema, height=250)

# --- מסך ראשי ---
col1, col2 = st.columns([1, 5])
with col1: st.markdown("## ⚖️")
with col2: 
    st.title("LegalAI | מערכת לניהול תיק לקוח")
    st.markdown("הפקת סט מסמכים מלא מתוך הקלטת פגישה.")

st.markdown("---")

tab1, tab2 = st.tabs(["📁 העלאת הקלטה", "🎙️ הקלטה חיה"])
audio_file = None

with tab1:
    f = st.file_uploader("בחר קובץ", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    if f: audio_file = f
with tab2:
    r = st.audio_input("הקלט")
    if r: audio_file = r

# --- לוגיקה ---
if audio_file:
    st.audio(audio_file)
    
    if st.button("🚀 הפעל ניתוח מלא"):
        
        # 1. תמלול
        with st.status("🤖 המערכת עובדת...", expanded=True) as status:
            st.write("📝 מתמלל שיחה (עשוי לקחת זמן לקבצים גדולים)...")
            try:
                transcribed_text = transcribe_audio(audio_file)
                st.write("✅ תמלול הושלם.")
            except Exception as e:
                st.error(f"שגיאה בתמלול: {e}")
                st.stop()
            
            # 2. חילוץ
            st.write("🧠 מנתח הקשר משפטי...")
            extracted_data = extract_info(transcribed_text, schema)
            st.write("✅ ניתוח הושלם.")
            status.update(label="העיבוד הסתיים!", state="complete", expanded=False)

        # 3. עריכה
        if "error" in extracted_data:
            st.error(extracted_data['error'])
        else:
            st.subheader("✏️ אימות נתונים")
            
            edited_data = {}
            labels = {
                "client_name": "שם הלקוח",
                "id_number": "ת.ז", 
                "event_date": "תאריך",
                "main_complaint": "תיאור",
                "requested_remedy": "סעד"
            }
            
            for key, value in extracted_data.items():
                label = labels.get(key, key)
                val_str = str(value) if value else ""
                if len(val_str) > 50:
                    edited_data[key] = st.text_area(label, val_str)
                else:
                    edited_data[key] = st.text_input(label, val_str)
            
            st.markdown("---")
            
            # 4. יצירת המסמכים (טיפול בריבוי קבצים)
            zip_buffer = io.BytesIO()
            has_files = False

            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # לוגיקה: אם הועלו תבניות, נשתמש בהן. אם לא, נחפש ברירת מחדל.
                
                files_to_process = []
                
                if uploaded_templates:
                    # שימוש בתבניות שהמשתמש העלה
                    for t_file in uploaded_templates:
                        files_to_process.append((t_file.name, t_file))
                else:
                    # בדיקת ברירת מחדל
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    default_path = os.path.join(current_dir, "default_template.docx")
                    if os.path.exists(default_path):
                        files_to_process.append(("טופס_ברירת_מחדל.docx", default_path))
                
                # ביצוע המילוי לכל קובץ
                if files_to_process:
                    for filename, file_obj in files_to_process:
                        try:
                            # מילוי התבנית
                            filled_doc_io = fill_template(file_obj, edited_data)
                            # הוספה ל-ZIP
                            zf.writestr(filename, filled_doc_io.getvalue())
                            has_files = True
                        except Exception as e:
                            st.warning(f"לא הצלחתי לעבד את הקובץ {filename}: {e}")
                else:
                    # אין תבניות בכלל -> יוצר מסמך גנרי
                    generic_doc = create_docx(edited_data)
                    zf.writestr("סיכום_תיק_גנרי.docx", generic_doc.getvalue())
                    has_files = True

            # כפתור הורדה
            if has_files:
                zip_buffer.seek(0)
                st.download_button(
                    label="📦 הורד את כל מסמכי התיק (ZIP)",
                    data=zip_buffer,
                    file_name="legal_case_files.zip",
                    mime="application/zip",
                    type="primary"
                )
