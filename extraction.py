from openai import OpenAI
import streamlit as st
import json
from datetime import datetime

def extract_info(text, schema_description):
    try:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
        else:
            return {"error": "Missing API Key"}

        client = OpenAI(api_key=api_key)
        current_date = datetime.now().strftime("%d/%m/%Y")

        # --- הוראות "חריפות" יותר לתיקון שגיאות ---
        system_prompt = f"""
        You are an expert Legal Secretary.
        Current Date: {current_date}.
        
        YOUR GOAL:
        Convert raw, messy transcription into a clean JSON for a legal document.
        
        CRITICAL INSTRUCTIONS FOR TEXT CORRECTION:
        The input text comes from automated speech recognition (Whisper) and contains phonetic errors.
        You MUST correct these errors based on context before extracting data.
        
        Examples of corrections you must apply:
        - "שרמתי" -> "שהרמתי" (I lifted)
        - "נפלתי בגלל שמן" -> "החלקתי עקב שמן" (More formal)
        - "לו הלכתי" -> "לא הלכתי" (Negation)
        - "עם תלך" -> "אם תלך" (Condition)
        
        Output format: Strict JSON based on the keys provided by the user.
        """

        user_prompt = f"""
        Field Definitions (JSON Schema):
        {schema_description}

        Raw Transcription:
        "{text}"
        
        Return ONLY the JSON.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        
        content = response.choices[0].message.content
        return json.loads(content.replace('```json', '').replace('```', '').strip())

    except Exception as e:
        return {"error": str(e)}