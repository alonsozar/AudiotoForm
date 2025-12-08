from docx import Document
from io import BytesIO

def create_docx(data):
    """
    יוצר מסמך חדש מאפס (גיבוי למקרה שאין תבנית).
    """
    doc = Document()
    doc.add_heading('סיכום תיק אוטומטי', 0)
    
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'תוכן'
    hdr_cells[1].text = 'שדה'

    for key, value in data.items():
        row_cells = table.add_row().cells
        clean_key = key.replace("_", " ").title()
        row_cells[1].text = clean_key
        row_cells[0].text = str(value) if value else "לא צוין"

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def fill_template(template_file, data):
    """
    לוקח קובץ תבנית וממלא אותו בנתונים.
    מחפש מחרוזות בפורמט {{key}} ומחליף ב-value.
    """
    doc = Document(template_file)
    
    # פונקציית עזר להחלפה בתוך פסקה
    def replace_text_in_paragraph(paragraph, key, value):
        if key in paragraph.text:
            # שיטה פשוטה להחלפה (שומרת על עיצוב בסיסי)
            paragraph.text = paragraph.text.replace(key, str(value) if value else "")

    # הכנת המפתחות להחלפה (למשל: {{Client Name}})
    replacements = {f"{{{{{key}}}}}": value for key, value in data.items()}

    # 1. מעבר על פסקאות רגילות
    for paragraph in doc.paragraphs:
        for placeholder, value in replacements.items():
            replace_text_in_paragraph(paragraph, placeholder, value)

    # 2. מעבר על טבלאות (חשוב מאוד לטפסים משפטיים)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for placeholder, value in replacements.items():
                        replace_text_in_paragraph(paragraph, placeholder, value)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer