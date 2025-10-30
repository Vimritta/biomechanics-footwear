# app_streamlit.py
import streamlit as st
from PIL import Image
import pandas as pd
import random
import os
import json

st.set_page_config(page_title="FootFit Analyzer", layout="wide")

# ---- small config ----
FOOT_ICONS = {
    "Flat Arch": "https://i.imgur.com/7yGQ6wM.png",
    "Normal Arch": "https://i.imgur.com/4Vw9h2x.png",
    "High Arch": "https://i.imgur.com/9N2r8sA.png"
}
SHOE_IMAGES = {
    "Running shoes": ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80"],
    "Cross-training shoes": ["https://images.unsplash.com/photo-1528701800489-4764b29a34a5?w=800&q=80"],
    "Casual/fashion sneakers": ["https://images.unsplash.com/photo-1519741492222-37a3b7a5f7a8?w=800&q=80"],
    "Sandals or slippers": ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80"]
}
ANIM_GIF_WALK = "https://media.giphy.com/media/3o7aD6d2hQ2Xw2p7T2/giphy.gif"

# ---- biomechanics rule engine ----
def biomechanics_recommender(age_cat, gender, weight_cat, foot_type, activity_level, chosen_pref=None):
    shoe = "Casual/fashion sneakers"
    arch_support = "Normal"
    cushioning = "Moderate"
    materials = []
    justifications = []

    if activity_level == "High":
        shoe = "Running shoes"
    elif activity_level == "Moderate":
        shoe = "Cross-training shoes"
    else:
        shoe = "Casual/fashion sneakers"

    if foot_type == "Flat Arch":
        arch_support = "High"
        materials.append("Dual-density EVA midsole")
        justifications.append("provides firmer medial support to reduce overpronation and increase arch stability")
    elif foot_type == "High Arch":
        arch_support = "Low to Moderate"
        cushioning = "High"
        materials.append("Plush EVA or PU foam with rocker geometry")
        justifications.append("increases shock absorption for high arches and promotes even load distribution")
    else:
        arch_support = "Normal"
        materials.append("Responsive EVA foam")
        justifications.append("balanced cushioning and flexibility for normal arches")

    if weight_cat in ["71–90 kg", "Over 90 kg"]:
        cushioning = "High"
        materials.append("High-rebound EVA or Gel-based units")
        justifications.append("extra cushioning to reduce peak plantar pressures for heavier users")
    elif weight_cat == "Under 50 kg":
        materials.append("Lightweight foam (PEBA or low-density EVA)")
        justifications.append("keeps shoes light for lighter users")

    if age_cat in ["51–65", "over 65"]:
        cushioning = "High"
        materials.append("Soft PU or memory foam top-layer")
        justifications.append("additional comfort and pressure relief for older feet")

    if shoe == "Running shoes":
        materials.append("Engineered mesh upper")
        justifications.append("improves breathability and reduces weight during running")
    elif shoe == "Cross-training shoes":
        materials.append("Reinforced TPU overlays")
        justifications.append("provides lateral stability for multi-directional movement")
    elif shoe == "Sandals or slippers":
        materials.append("Cork or EVA footbed")
        justifications.append("conforms to foot shape and provides cushioning for casual wear")

    seen = set()
    materials_unique = [m for m in materials if not (m in seen or seen.add(m))]
    justs_unique = []
    for m in materials_unique:
        for jm, jj in zip(materials, justifications):
            if jm == m:
                justs_unique.append(jj)
                break

    material_bold = "**" + ", ".join(materials_unique[:2]) + "**"
    justification_text = " ".join(["*"+j+".*" for j in justs_unique[:3]])

    if chosen_pref:
        shoe = chosen_pref

    return {
        "shoe_category": shoe,
        "arch_support": arch_support,
        "cushioning": cushioning,
        "material": material_bold,
        "justification": justification_text
    }

# ---- UI helpers ----
def set_theme(activity_level):
    if activity_level == "Low":
        color = "#DCEEFB"
    elif activity_level == "Moderate":
        color = "#E6F9E6"
    else:
        color = "#FFE8D6"
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {color}; }}
        .summary-card {{ border-radius:12px; padding:18px; box-shadow:0 4px 12px rgba(0,0,0,0.06); }}
        .foot-type {{ border-radius:10px; padding:6px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def random_tip():
    tips = [
        "Stretch your calves daily to reduce heel strain.",
        "Avoid wearing worn-out shoes for long walks; replace midsoles every ~300-500 miles.",
        "Alternate shoe types across the week to avoid repetitive stress.",
        "Check shoe fit in the evening when feet are slightly swollen.",
        "Use orthotic inserts if you have persistent arch pain (consult a professional)."
    ]
    return random.choice(tips)

# ---- page header ----
st.markdown("""
<div style="display:flex; align-items:center;">
  <img src="https://i.imgur.com/TKQF3xP.png" alt="logo" width="64" style="margin-right:12px;">
  <h1 style="margin:0;">FootFit Analyzer</h1>
  <div style="margin-left:auto; color:gray;">Biomechanics-based footwear profiling</div>
</div>
""", unsafe_allow_html=True)

# ---- Wizard ----
if "step" not in st.session_state:
    st.session_state.step = 1
if "inputs" not in st.session_state:
    st.session_state.inputs = {}

def go_next():
    st.session_state.step += 1
def go_back():
    if st.session_state.step > 1:
        st.session_state.step -= 1

cols = st.columns([1,1,1])
with cols[0]:
    st.markdown(f"**Step {st.session_state.step} / 3**")

# ---- Step 1: Personal Info (sliders) ----
if st.session_state.step == 1:
    st.header("Step 1 — Personal Info")
    age_map = {0:"under 18",1:"18-25",2:"26-35",3:"36-50",4:"51–65",5:"over 65"}
    age_idx = st.slider("Age group (drag to select)", 0,5,2)
    age_cat = age_map[age_idx]
    gender_idx = st.slider("Gender (0 = Male, 1 = Female)", 0,1,0)
    gender = "Male" if gender_idx == 0 else "Female"
    weight_map = {0:"Under 50 kg",1:"50–70 kg",2:"71–90 kg",3:"Over 90 kg"}
    w_idx = st.slider("Weight category (0-3)", 0,3,1)
    weight_cat = weight_map[w_idx]
    activity_map = {0:"Low",1:"Moderate",2:"High"}
    act_idx = st.slider("Daily activity level (0=Low,1=Moderate,2=High)", 0,2,1)
    activity_level = activity_map[act_idx]
    st.session_state.inputs.update({
        "age_cat": age_cat,
        "gender": gender,
        "weight_cat": weight_cat,
        "activity_level": activity_level
    })
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Next — Foot details"):
            go_next()

# ---- Step 2: Foot details ----
elif st.session_state.step == 2:
    st.header("Step 2 — Foot details")
    foot_choice = st.radio("Foot Type", options=["Flat Arch","Normal Arch","High Arch"], index=1, horizontal=True)
    col1,col2,col3 = st.columns(3)
    for i, ft in enumerate(["Flat Arch","Normal Arch","High Arch"]):
        img_url = FOOT_ICONS[ft]
        target = [col1,col2,col3][i]
        with target:
            st.markdown(f"<div class='foot-type' style='text-align:center; border:2px solid {'#1f77b4' if foot_choice==ft else 'transparent'}; padding:8px;'><img src='{img_url}' width=120 /><div>{ft}</div></div>", unsafe_allow_html=True)
    shoe_pref = st.selectbox("Preferred footwear type (optional)", options=["Auto detect","Running shoes","Cross-training shoes","Casual/fashion sneakers","Sandals or slippers"])
    st.session_state.inputs.update({
        "foot_type": foot_choice,
        "shoe_pref": shoe_pref if shoe_pref!="Auto detect" else None
    })
    c1,c2 = st.columns([1,1])
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if st.button("Next — Recommendation"):
            go_next()

# ---- Step 3: Recommendation ----
elif st.session_state.step == 3:
    st.header("Step 3 — Recommendation")
    inputs = st.session_state.inputs
    age_cat = inputs.get("age_cat","26-35")
    gender = inputs.get("gender","Male")
    weight_cat = inputs.get("weight_cat","50–70 kg")
    activity_level = inputs.get("activity_level","Moderate")
    foot_type = inputs.get("foot_type","Normal Arch")
    shoe_pref = inputs.get("shoe_pref", None)
    set_theme(activity_level)
    if st.button("Analyze"):
        st.image(ANIM_GIF_WALK, width=240)
        result = biomechanics_recommender(age_cat, gender, weight_cat, foot_type, activity_level, chosen_pref=shoe_pref)
        st.markdown(f"""
        <div class="summary-card" style="background: white;">
          <h2>👣 Biomechanics Summary</h2>
          <p><strong>Recommended shoe type:</strong> 👟 {result['shoe_category']}</p>
          <p><strong>Arch support:</strong> 🦶 {result['arch_support']}</p>
          <p><strong>Cushioning:</strong> 💪 {result['cushioning']}</p>
          <p><strong>Material recommendation:</strong> {result['material']}</p>
          <p style="color:#555;">{result['justification']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("💡 Tip of the Day — " + random_tip())
        st.subheader("👟 Virtual Shoe Wall")
        images = SHOE_IMAGES.get(result['shoe_category'], [])
        cols = st.columns(3)
        for i,img in enumerate(images[:3]):
            with cols[i % 3]:
                st.image(img, caption=result['shoe_category'], use_column_width=True)
        st.subheader("👣 Foot Type Visual")
        st.markdown(f"<img src='{FOOT_ICONS[foot_type]}' width=140 />", unsafe_allow_html=True)
        st.markdown("### Material & Why")
        st.markdown(f"{result['material']} — _{result['justification']}_")
        if st.checkbox("🔊 Read recommendation aloud (TTS)"):
            speak_text = f"Recommended {result['shoe_category']}. Arch support {result['arch_support']}. Cushioning {result['cushioning']}."
            tts_html = f\"\"\"<script>
            const msg = new SpeechSynthesisUtterance({json.dumps(speak_text)});
            msg.rate = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(msg);
            </script>\"\"\"
            st.components.v1.html(tts_html, height=0)
    c1,c2 = st.columns([1,1])
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if st.button("Start Over"):
            st.session_state.step = 1
            st.session_state.inputs = {}
