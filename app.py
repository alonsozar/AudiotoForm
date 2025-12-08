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

    /* יישור לימין - בצורה חכמה שלא שוברת את המובייל */
    .stApp {
        background-color: #f8f9fa;
        direction: rtl; 
        text-align: right;
    }

    /* תיקון ספציפי למובייל (מסכים צרים) */
    @media only screen and (max-width: 600px) {
        /* ביטול כפיית RTL על אלמנטים מסוימים שנשברים */
        .stTextInput > div > div > input {
            direction: rtl; 
        }
        /* הקטנת כותרות כדי שלא יחרגו מהמסך */
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.2rem !important; }
        
        /* ריווח טוב יותר בצדדים */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 2rem !important;
        }
        
        /* התאמת כפתורים למסך מלא */
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

    /* הסתרת אלמנטים מיותרים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* עיצוב שדות קלט */
    .stTextInput input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# --- סרגל צד (Sidebar) ---
with st.sidebar:
    st.title("⚙️ הגדרות מערכת")
    
    st.markdown("### 📄 תבנית מסמך")
    st.info("ניתן להעלות תבנית Word מותאמת אישית. אם לא תועלה תבנית, המערכת תשתמש בתבנית ברירת המחדל.")
    template_file = st.file_uploader("העלה תבנית (.docx)", type=["docx"])
    
    st.markdown("---")
    
    st.markdown("### 🎯 שדות לחילוץ")
    # הגדרת הסכמה (Schema) - המפתחות באנגלית לטובת הקוד, התיאור בעברית לטובת ה-AI
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
# כותרת ראשית
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("## ⚖️") 
with col_title:
    st.title("LegalAI | מערכת קליטת תיק")
    st.markdown("הפוך שיחת ייעוץ לטיוטה משפטית מוכנה - בשניות.")

st.markdown("---")

# בחירה בין העלאה להקלטה
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
    
    # כפתור הפעלה ראשי
    if st.button("🚀 הפעל ניתוח AI", use_container_width=True):
        
        # אזור סטטוס מעוצב
        with st.status("🤖 המערכת מעבדת את הנתונים...", expanded=True) as status:
            st.write("📝 מתמלל את השיחה לטקסט...")
            transcribed_text = transcribe_audio(audio_file)
            st.write("✅ תמלול הסתיים.")
            
            st.write("🧠 מנתח הקשר משפטי ומחלץ ישויות...")
            extracted_data = extract_info(transcribed_text, schema)
            st.write("✅ חילוץ נתונים הסתיים.")
            
            status.update(label="תהליך העיבוד הושלם בהצלחה!", state="complete", expanded=False)

        # הצגת התמלול
        with st.expander("📄 הצג תמלול מלא של השיחה"):
            st.info(transcribed_text)

        # בדיקת שגיאות
        if "error" in extracted_data:
            st.error(f"שגיאה בחילוץ הנתונים: {extracted_data['error']}")
        else:
            st.markdown("---")
            st.subheader("✏️ בדיקת נתונים לפני יצירת מסמך")
            st.caption("ניתן לערוך את השדות ידנית לפני ההורדה")
            
            # טופס עריכה דינמי
            edited_data = {}
            
            # מילון תרגום למשתמש (כדי שיראה עברית ולא מפתחות באנגלית)
            labels = {
                "client_name": "שם הלקוח",
                "id_number": "תעודת זהות",
                "event_date": "תאריך אירוע",
                "main_complaint": "תיאור המקרה",
                "requested_re
