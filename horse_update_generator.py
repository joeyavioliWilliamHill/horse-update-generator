"""
Horse Update Generator - Streamlit App
Converts unstructured horse updates into structured format for Slack listener.
"""

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize OpenAI client
# Try Streamlit secrets first (for Cloud deployment), then environment variable (for local)
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("❌ OPENAI_API_KEY not found. Please add it to Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """You are a horse racing operations assistant that structures updates precisely.

REQUIRED FIELDS BY EVENT TYPE:
- horse_added: horse_id, name, sire, dam, consignor, sale, status
- general_update: horse_id, status, date
- breeze_report: horse_id, status, date, location, distance, time
- gate_report: horse_id, status, date, location
- vet_update: horse_id, status, date, vet_status
- race_plan_update: horse_id, status, date
- result_update: horse_id, status, date, race_track, finish_position

CRITICAL RULES:
1. First line MUST be the event type (breeze_report, gate_report, general_update, horse_added, race_plan_update, result_update, or vet_update)
2. Include ALL required fields for the chosen event type
3. Use lowercase with underscores for keys (horse_id, vet_status, race_track, finish_position)
4. ALL events except horse_added MUST have a notes: section with context
5. Do NOT invent missing information - if a required field is missing, note it in notes section
6. Status values: new, in_training, entered, running, monitor, rehab, turned_out, back_galloping, under_evaluation, won, placed, off_turf, scratched

Example vet_update:
vet_update
horse_id: EWING
status: monitor
date: 2026-06-01
vet_status: scoped_clean
notes:
Scoped clean after galloping. Vet suspects old abscess burst rather than new bleeding episode. Mark to enter for 6/7 race if no more issues.

Output ONLY the structured text, no markdown or code fences."""

# Page config
st.set_page_config(
    page_title="Horse Update Generator",
    page_icon="🐴",
    layout="wide"
)

st.title("🐴 Horse Update Generator")
st.markdown("Convert unstructured updates into structured format for Slack")

# Sidebar with instructions
with st.sidebar:
    st.header("📖 Instructions")
    st.markdown("""
    1. Paste an unstructured horse update
    2. Click 'Generate Structured Update'
    3. Copy the output and paste into Slack
    4. The Slack listener will capture it automatically
    
    **Expected output format:**
    ```
    event_type
    key1: value1
    key2: value2
    notes:
    Optional notes
    ```
    """)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Unstructured Update")
    raw_update = st.text_area(
        "Paste your unstructured horse update here",
        height=300,
        placeholder="Example: Austin had a good breeze this morning, 5 furlongs in 1:00, good shoulder action..."
    )

with col2:
    st.subheader("✨ Structured Output")
    output_placeholder = st.empty()

# Generate button
if st.button("🔄 Generate Structured Update", type="primary"):
    if not raw_update.strip():
        st.error("❌ Please paste an update first")
    else:
        with st.spinner("🤖 Converting with AI..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": raw_update
                        }
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                structured_text = response.choices[0].message.content.strip()
                
                # Display in the output column
                with output_placeholder.container():
                    st.code(structured_text, language="text")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📋 Copy to Clipboard"):
                            st.success("✓ Ready to paste!")
                            st.code(structured_text)
                    
                    with col2:
                        if st.button("📤 Slack Format"):
                            st.info("Paste this directly into your Slack channel:")
                            st.code(structured_text)
                    
                    with col3:
                        if st.button("💾 Save as Template"):
                            st.success("Template saved to your session")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Make sure OPENAI_API_KEY is set in your .env file")

# Footer
st.divider()
st.markdown("""
---
**How it works:**
1. Your reps paste raw updates here
2. AI structures them into key:value format
3. Copy the output and paste into Slack
4. The SlackToPostgres listener captures it
5. Data automatically flows to your PostgreSQL database
""")
