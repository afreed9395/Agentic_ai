import datetime

import requests
import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()
API_URL = "https://agentic-ai-dufp.onrender.com"




@st.cache_data(show_spinner="Building PDF…")
def _plan_pdf_bytes(plan: str, request: str, generated_iso: str) -> bytes:
    from utils.plan_pdf import render_travel_plan_pdf

    return render_travel_plan_pdf(
        plan,
        request,
        datetime.datetime.fromisoformat(generated_iso),
    )


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.75rem;
                padding-bottom: 3rem;
                max-width: 72rem;
            }
            h1.tp-hero {
                font-weight: 700;
                letter-spacing: -0.03em;
                margin-bottom: 0.2rem !important;
                background: linear-gradient(115deg, #f0f4f8 0%, #2eb398 55%, #1a9a86 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .tp-sub {
                color: #7a8fa3;
                font-size: 1.05rem;
                margin-bottom: 1.25rem;
            }
            /* Slightly tighter markdown for long itineraries */
            [data-testid="stMarkdownContainer"] h2 {
                margin-top: 1.1rem;
                padding-bottom: 0.2rem;
                border-bottom: 1px solid rgba(46, 179, 152, 0.25);
            }
            [data-testid="stMarkdownContainer"] hr {
                margin: 1rem 0;
                border: none;
                border-top: 1px solid rgba(120, 140, 160, 0.25);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_inject_styles()

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None
if "last_meta" not in st.session_state:
    st.session_state.last_meta = None

with st.sidebar:
    st.markdown("### About")
    st.caption(
        "The agent may call tools for weather, places, currency, and estimates. "
        "Treat every figure as approximate until you confirm it yourself."
    )
    st.divider()
    st.markdown("**Backend**")
    st.code(API_URL, language=None)
    st.caption("Start with: `uvicorn main:app --host 0.0.0.0 --port 8000`")

st.markdown('<h1 class="tp-hero">Travel Planner</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="tp-sub">Describe where you want to go, how long, and your budget — get a structured markdown itinerary.</p>',
    unsafe_allow_html=True,
)

col_form, col_result = st.columns([1, 1.4], gap="large")

with col_form:
    st.markdown("##### Your trip")
    with st.form("trip_form", border=True):
        user_input = st.text_area(
            "Trip details",
            height=170,
            placeholder="Example: 5 days in Goa under ₹20,000 — beaches plus quieter spots.",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(
            "Generate plan",
            type="primary",
            use_container_width=True,
        )

with col_result:
    st.markdown("##### Itinerary")

    if submitted and user_input.strip():
        try:
            with st.spinner("Calling the travel agent — this can take a minute…"):
                payload = {"query": user_input.strip()}
                response = requests.post(f"{API_URL}/query", json=payload, timeout=300)

            if response.status_code == 200:
                answer = response.json().get("response", "No answer returned.")
                st.session_state.last_plan = answer
                st.session_state.last_meta = {
                    "time": datetime.datetime.now(),
                    "query": user_input.strip(),
                }
                st.success("Plan ready — scroll to read.")
            else:
                st.error(f"**{response.status_code}** — {response.text}")
        except requests.RequestException as e:
            st.error(
                f"Could not reach the API at `{API_URL}`. Is the server running?\n\n{e}"
            )

    if st.session_state.last_plan and st.session_state.last_meta:
        meta = st.session_state.last_meta
        q_preview = meta["query"]
        if len(q_preview) > 220:
            q_preview = q_preview[:220] + "…"

        with st.container(border=True):
            c1, c2, c3 = st.columns([2.2, 1, 1])
            with c1:
                st.caption("**Your request**")
                st.text(q_preview)
            with c2:
                st.caption("Generated")
                st.write(meta["time"].strftime("%Y-%m-%d\n%H:%M"))
            with c3:
                st.caption("Export")
                try:
                    pdf_bytes = _plan_pdf_bytes(
                        st.session_state.last_plan,
                        st.session_state.last_meta["query"],
                        meta["time"].isoformat(),
                    )
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"travel_plan_{meta['time'].strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_travel_plan_pdf",
                    )
                except Exception as ex:
                    st.caption(f"PDF failed: {ex}")

            st.divider()
            st.markdown(st.session_state.last_plan)

        st.info(
            "This itinerary is AI-generated. Double-check prices, weather, hours, and bookings before you travel."
        )
    elif not (submitted and user_input.strip()):
        st.caption("Submit the form on the left — the full markdown plan will render here.")
