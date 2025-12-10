from openai import OpenAI
import streamlit as st
import os
from pydub import AudioSegment
import math

def transcribe_audio(audio_file):
    """
    מתמלל אודיו. אם הקובץ גדול/ארוך, חותך אותו לחלקים ושולח בחלקים.
    """
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)

    # שמירת הקובץ זמנית כדי שנוכל לעבד אותו
    file_ext = audio_file.name.split('.')[-1]
    temp_filename = f"temp_audio.{file_ext}"
    
    with open(temp_filename, "wb") as f:
        f.write(audio_file.getbuffer())

    try:
        # טעינת האודיו ובדיקת אורך
        audio = AudioSegment.from_file(temp_filename)
        duration_ms = len(audio)
        
        # הגדרת אורך מקסימלי לחלק (10 דקות = 600,000 מילישניות)
        chunk_length_ms = 10 * 60 * 1000
        chunks = math.ceil(duration_ms / chunk_length_ms)

        full_transcript = ""

        if chunks > 1:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(chunks):
                status_text.text(f"מתמלל חלק {i+1} מתוך {chunks}...")
                
                start_time = i * chunk_length_ms
                end_time = min((i + 1) * chunk_length_ms, duration_ms)
                
                chunk = audio[start_time:end_time]
                chunk_filename = f"chunk_{i}.{file_ext}"
                chunk.export(chunk_filename, format=file_ext)
                
                with open(chunk_filename, "rb") as audio_chunk:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_chunk,
                        language="he"
                    )
                    full_transcript += transcript.text + " "
                
                # ניקוי קובץ זמני
                os.remove(chunk_filename)
                progress_bar.progress((i + 1) / chunks)
            
            status_text.empty()
            progress_bar.empty()
            
        else:
            # קובץ קצר - תמלול רגיל
            with open(temp_filename, "rb") as audio_file_ready:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file_ready,
                    language="he"
                )
                full_transcript = transcript.text

        return full_transcript

    except Exception as e:
        return f"Error: {str(e)}"
        
    finally:
        # ניקוי הקובץ הראשי
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
