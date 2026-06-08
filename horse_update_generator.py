"""
Horse Update Generator - Streamlit App
Converts unstructured horse updates into structured format for Slack listener.
"""

from datetime import date
import streamlit as st
from openai import OpenAI

# -----------------------------
# Config
# -----------------------------

TODAY = date.today().isoformat()
MODEL = "gpt-4o-mini"  # If this errors, switch back to "gpt-3.5-turbo"

try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except KeyError:
    st.error("OPENAI_API_KEY is missing from Streamlit Secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error initializing OpenAI client: {e}")
    st.stop()

SYSTEM_PROMPT = f"""
You are a horse racing operations assistant that converts unstructured horse updates into structured Slack-ready updates.

TODAY'S DATE:
{TODAY}

REQUIRED EVENT TYPES:
- breeze_report
- gate_report
- general_update
- horse_added
- race_plan_update
- result_update
- vet_update

REQUIRED FIELDS BY EVENT TYPE:
- horse_added: horse_id, name, sire, dam, consignor, sale, status
- general_update: horse_id, status, date
- breeze_report: horse_id, status, date, location, distance, time
- gate_report: horse_id, status, date, location
- vet_update: horse_id, status, date, vet_status
- race_plan_update: horse_id, status, date
- result_update: horse_id, status, date, race_track, finish_position

CRITICAL OUTPUT RULES:
1. First line of each update MUST be the event type.
2. Include ALL required fields for the chosen event type.
3. Use lowercase_with_underscores for keys.
4. Use UPPERCASE_WITH_UNDERSCORES for horse_id.
5. If a required field is missing, use unknown.
6. ALL events except horse_added MUST include a notes: section.
7. Output ONLY structured text. No markdown. No code fences. No explanations.

DATE RULES:
1. The date field should represent the date this update is being created/logged.
2. If the input gives a clear update date, use that date.
3. If the input does not give a clear update date, use TODAY'S DATE: {TODAY}.
4. If the input mentions a future event date, such as "exam on Thursday" or "race on 6/7", do NOT use that as the main date unless it is clearly the update date.
5. Put future event timing inside notes, race_date, or target_date if relevant.
6. NEVER copy dates from examples.
7. Date format must always be YYYY-MM-DD.

MULTIPLE HORSE RULES:
1. If the input mentions multiple horses, create one separate structured update for each horse.
2. Separate each structured update with one blank line.
3. Do not merge information from different horses.

STATUS VALUES:
Use the best matching status from this list:
new, in_training, entered, running, monitor, rehab, turned_out, back_galloping, under_evaluation, won, placed, off_turf, scratched

NOTES RULES:
1. The notes field is not just a short summary.
2. Preserve as much meaningful trainer commentary, sentiment, observations, and partner-facing color as possible.
3. Do not aggressively shorten updates.
4. Only remove repetition and unnecessary filler.
5. Preserve direct trainer quotes whenever possible.
6. Preserve details that owners/partners would care about.
7. Do not invent facts.

CLASSIFICATION GUIDANCE:
- Use vet_update for injuries, soreness, exams, scopes, lameness, chips, effusion, swelling, soundness, bloodwork, vet checks, or medical monitoring.
- Use breeze_report for workouts, breezes, timed works, or scheduled official breezes.
- Use gate_report for gate schooling, gate works, breaking, gate behavior, or gate approval.
- Use race_plan_update for entries, nominations, target races, possible races, scratches, race timing, or campaign plans.
- Use result_update for completed races and finishes.
- Use horse_added for newly acquired or newly added horses.
- Use general_update for general training, routine progress, behavior, shipping, or broad status updates that do not fit above.

EXAMPLE FORMAT ONLY — DO NOT COPY THE DATE:
vet_update
horse_id: EWING
status: monitor
date: YYYY-MM-DD
vet_status: scoped_clean
notes:
Scoped clean after galloping. Vet suspects old abscess burst rather than a new bleeding episode. Mark will enter for the 6/7 race if there are no additional issues.
"""

# -----------------------------
# Page config
# -----------------------------

st.set_page_config(
    page_title="Horse Update Generator",
    page_icon="🐴",
    layout="wide"
)

st.title("🐴 Horse Update Generator")
st.markdown("Convert unstructured updates into structured format for Slack")

with st.sidebar:
    st.header("📖 Instructions")
    st.markdown(f"""
    1. Paste an unstructured horse update
    2. Click **Generate Structured Update**
    3. Copy the output and paste into Slack
    4. The Slack listener will capture it automatically

    **Today's default update date:** `{TODAY}`

    **Expected output format:**
    ```
    event_type
    horse_id: HORSE_NAME
    status: in_training
    date: {TODAY}
    notes:
    Detailed notes here
    ```
    """)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Unstructured Update")
    raw_update = st.text_area(
        "Paste your unstructured horse update here",
        height=300,
        placeholder="Example: Golden Joker was not entered. Slightly off left hind..."
    )

with col2:
    st.subheader("✨ Structured Output")
    output_placeholder = st.empty()

if st.button("🔄 Generate Structured Update", type="primary"):
    if not raw_update.strip():
        st.error("❌ Please paste an update first")
    else:
        with st.spinner("🤖 Converting with AI..."):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": f"""
Convert the following unstructured update into structured Slack-ready update text.

Today's date is {TODAY}. If no clear update date is provided, use {TODAY} for the date field.

Unstructured update:
{raw_update}
"""
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1800
                )

                structured_text = response.choices[0].message.content.strip()

                with output_placeholder.container():
                    st.code(structured_text, language="text")

                    st.download_button(
                        label="⬇️ Download Structured Update",
                        data=structured_text,
                        file_name="structured_horse_update.txt",
                        mime="text/plain"
                    )

                    st.info("Copy this output and paste it directly into the structured Slack channel.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

st.divider()
st.markdown("""
**How it works:**
1. Reps paste raw updates here
2. AI structures them into Slack-ready text
3. Reps paste the output into Slack
4. The Slack-to-Postgres listener captures it
5. Data flows into PostgreSQL for PDFs, dashboards, and reporting
""")