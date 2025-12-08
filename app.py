import streamlit as st
from transcription import transcribe_audio
from extraction import extract_info
from utils import create_docx, fill_template
import os

st.set_page_config(page_title="LegalAI Pro", page_icon="⚖️", layout="wide")

# עיצוב (אותו עיצוב כמו קודם)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Heebo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #2c3e50; }
    div.stButton > button { background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%); color: white; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ הגדרות")
    st.info("העלה תבנית Word עם הסימונים: {{client_name}}, {{event_date}} וכו'.")
    template_file = st.file_uploader("תבנית (.docx)", type=["docx"])
    
    # --- התיקון הקריטי: הגדרה מפורשת של המפתחות באנגלית ---
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

st.title("⚖️ LegalAI | מערכת קליטת תיק")

# טאבים
tab_upload, tab_record = st.tabs(["📁 העלאה", "🎙️ הקלטה"])
audio_file = None
with tab_upload:
    audio_file = st.file_uploader("", type=["mp3", "wav"])
with tab_record:
    audio_rec = st.audio_input("הקלט")
    if audio_rec: audio_file = audio_rec

if audio_file:
    st.audio(audio_file, format="audio/wav")
    if st.button("🚀 הפעל ניתוח", use_container_width=True):
        
        with st.status("מעבד...", expanded=True) as status:
            st.write("📝 מתמלל...")
            transcribed_text = transcribe_audio(audio_file)
            st.write("🧠 מנתח ומחלץ...")
            extracted_data = extract_info(transcribed_text, schema)
            status.update(label="הושלם!", state="complete", expanded=False)

        if "error" in extracted_data:
            st.error(extracted_data['error'])
        else:
            st.success("הנתונים חולצו. נא לבדוק לפני יצירת המסמך:")
            
            # עריכה
            edited_data = {}
            # מילון תרגום למשתמש (כדי שלא יראה אנגלית בעיניים)
            labels = {
                "client_name": "שם הלקוח",
                "id_number": "תעודת זהות",
                "event_date": "תאריך אירוע",
                "main_complaint": "תיאור המקרה",
                "requested_remedy": "סעד מבוקש"
            }
            
            for key, value in extracted_data.items():
                # משתמשים בתווית בעברית אם קיימת, אחרת במפתח באנגלית
                label = labels.get(key, key)
                edited_data[key] = st.text_area(label, value)

            # יצירת מסמך
           # --- לוגיקה חכמה לבחירת תבנית ---
            if template_file:
                # אפשרות 1: המשתמש העלה תבנית ספציפית
                st.toast("משתמש בתבנית שהעלית...", icon="📂")
                final_doc = fill_template(template_file, edited_data)
                filename = "custom_legal_form.docx"
            
            elif os.path.exists("default_template.docx"):
                # אפשרות 2: שימוש בתבנית הדמו המובנית (הפתרון לטלפון!)
                st.info("משתמש בתבנית ברירת מחדל (דמו).")
                final_doc = fill_template("default_template.docx", edited_data)
                filename = "demo_legal_form.docx"
                
            else:
                # אפשרות 3: אין שום תבנית - יצירת מסמך גנרי
                st.warning("לא נמצאה תבנית - יוצר מסמך נתונים בסיסי.")
                final_doc = create_docx(edited_data)
                filename = "generic_data.docx"

            # כפתור הורדה
            st.download_button(
                label="📥 הורד מסמך מוכן (Word)",
                data=final_doc,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )