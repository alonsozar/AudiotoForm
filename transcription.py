from openai import OpenAI
import streamlit as st
import os

def transcribe_audio(audio_file):
    """
    Transcribes audio file using OpenAI Whisper API.
    """
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)

    # If it's a file-like object from Streamlit, we might need to write it to temp or pass directly.
    # OpenAI client usually accepts open file handles. 
    # Streamlit UploadedFile is file-like.
    
    try:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            language="he" # Hinting Hebrew can help accuracy
        )
        return transcript.text
    except Exception as e:
        return f"Error during transcription: {str(e)}"
