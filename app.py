import streamlit as st
from transcription import transcribe_audio
from extraction import extract_info
from utils import create_docx, fill_template
import os

# --- הגדרת דף בסיסית ---
st.set_page_config(
    page_title="LegalAI Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- עיצוב CSS מתקדם (כולל תיקון למובייל) ---
st.markdown("""
<style>
    /* ייבוא פונט מודרני */
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');

    /* הגדרות בסיס לכל המכשירים */
    html, body, [class*="css"] {
        font-family: 'Heebo', sans-serif;
    }

    /* יישור לימין */
    .stApp {
        background-color: #f8f9fa;
        direction: rtl; 
        text-align: right;
    }

    /* תיקון ספציפי למובייל */
    @media only screen and (max-width: 600px) {
        .stTextInput > div > div > input {
            direction: rtl; 
        }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        
        div.stButton > button {
            width: 100% !important;
        }
    }

    /* עיצוב כותרות */
    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 700;
        text-align: right;
    }

    /* כפתורים מעוצבים */
    div.stButton > button {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stTextInput input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# --- סרגל צד ---
with st.sidebar:
    st.title("⚙️ הגדרות מערכת")
    
    st.markdown("### 📄 תבנית מסמך")
    st.info("ניתן להעלות תבנית Word מותאמת אישית.")
    template_file = st.file_uploader("העלה תבנית (.docx)", type=["docx"])
    
    st.markdown("---")
    
    st.markdown("### 🎯 שדות לחילוץ")
    default_schema = """
    {
        "client_name": "שם הלקוח המלא",
        "id_number": "מספר תעודת זהות (אם הוזכר)",
        "event_date": "תאריך האירוע (בפורמט DD/MM/YYYY)",
        "main_complaint": "תיאור העובדות והמקרה (תקן שגיאות כתיב ונסח בשפה משפטית)",
        "requested_remedy": "הסעד או הפיצוי המבוקש"
    }
    """
    schema = st.text_area("הגדרת JSON:", value=default_schema, height=250)

# --- מסך ראשי ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("## ⚖️") 
with col_title:
    st.title("LegalAI | מערכת קליטת תיק")
    st.markdown("הפוך שיחת ייעוץ לטיוטה משפטית מוכנה - בשניות.")

st.markdown("---")

tab_upload, tab_record = st.tabs(["📁 העלאת קובץ", "🎙️ הקלטה חיה"])

audio_file = None

with tab_upload:
    uploaded_file = st.file_uploader("בחר קובץ", type=["mp3", "wav"], label_visibility="collapsed")
    if uploaded_file:
        audio_file = uploaded_file
        st.success(f"קובץ נטען: {uploaded_file.name}")

with tab_record:
    audio_recording = st.audio_input("לחץ להקלטה")
    if audio_recording:
        audio_file = audio_recording

# --- לוגיקה עסקית ---
if audio_file is not None:
    st.markdown("### 🎧 האזנה וניתוח")
    st.audio(audio_file, format="audio/wav")
    
    if st.button("🚀 הפעל ניתוח AI", use_container_width=True):
        
        with st.status("🤖 המערכת מעבדת את הנתונים...", expanded=True) as status:
            st.write("📝 מתמלל את השיחה לטקסט...")
            transcribed_text = transcribe_audio(audio_file)
            st.write("✅ תמלול הסתיים.")
            
            st.write("🧠 מנתח הקשר משפטי ומחלץ ישויות...")
            extracted_data = extract_info(transcribed_text, schema)
            st.write("✅ חילוץ נתונים הסתיים.")
            
            status.update(label="תהליך העיבוד הושלם בהצלחה!", state="complete", expanded=False)

        with st.expander("📄 הצג תמלול מלא של השיחה"):
            st.info(transcribed_text)

        if "error" in extracted_data:
            st.error(f"שגיאה בחילוץ הנתונים: {extracted_data['error']}")
        else:
            st.markdown("---")
            st.subheader("✏️ בדיקת נתונים לפני יצירת מסמך")
            st.caption("ניתן לערוך את השדות ידנית לפני ההורדה")
            
            edited_data = {}
            
            # --- התיקון נמצא כאן ---
            labels = {
                "client_name": "שם הלקוח",
                "id_number": "תעודת זהות",
                "event_date": "תאריך אירוע",
                "main_complaint": "תיאור המקרה",
                "requested_remedy": "סעד מבוקש"
            }
            
            for key, value in extracted_data.items():
                label = labels.get(key, key)
                if len(str(value)) > 50:
                    edited_data[key] = st.text_area(label, value)
                else:
                    edited_data[key] = st.text_input(label, value)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # בחירת תבנית
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_template_path = os.path.join(current_dir, "default_template.docx")

            final_doc = None
            filename = "document.docx"

            if template_file:
                st.toast("משתמש בתבנית שהעלית...", icon="📂")
                final_doc = fill_template(template_file, edited_data)
                filename = "custom_legal_form.docx"
            
            elif os.path.exists(default_template_path):
                st.info("משתמש בתבנית ברירת מחדל (דמו).")
                final_doc = fill_template(default_template_path, edited_data)
                filename = "legal_case_draft.docx"
                
            else:
                st.warning("לא נמצאה תבנית - יוצר מסמך נתונים בסיסי.")
                final_doc = create_docx(edited_data)
                filename = "generic_data.docx"

            if final_doc:
                st.download_button(
                    label="📥 הורד מסמך מוכן (Word)",
                    data=final_doc,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )
