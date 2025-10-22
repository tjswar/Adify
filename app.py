import streamlit as st
import google.generativeai as genai
import pandas as pd
import textstat
from config import GEMINI_KEY

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
st.set_page_config(page_title="Ad-iFy", page_icon="💬", layout="centered")
st.title("💬 Ad-iFy: Ad Copy Optimizer & Variant Generator")

genai.configure(api_key=GEMINI_KEY)
MODEL_NAME = "gemini-2.5-flash"

# ─────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────
def safe_text(response):
    try:
        if getattr(response, "candidates", None):
            cand = response.candidates[0]
            parts = getattr(cand, "content", None)
            if parts and getattr(parts, "parts", None):
                text = "".join([p.text for p in parts.parts if hasattr(p, "text")])
                return text.strip()
    except Exception:
        return ""
    return ""

def generate_variants(product, audience, platform):
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
You are a professional digital marketing copywriter.
Generate exactly 5 ad copy variants for the product: "{product}".
Target audience: {audience}.
Platform: {platform}.

Each variant must:
- Be under 25 words
- Include a clear call-to-action
- Have a catchy tone suitable for {platform}

Output format strictly as:
1. <ad copy 1>
2. <ad copy 2>
3. <ad copy 3>
4. <ad copy 4>
5. <ad copy 5>
"""
    response = model.generate_content(prompt)
    return safe_text(response)

def score_variant(copy_text):
    # Simple heuristic scoring
    readability = textstat.flesch_reading_ease(copy_text)
    length_score = max(0, 100 - abs(len(copy_text.split()) - 15) * 3)  # ideal ~15 words
    cta_bonus = 20 if any(word in copy_text.lower() for word in ["buy", "shop", "try", "join", "learn", "discover"]) else 0
    total = readability * 0.5 + length_score * 0.3 + cta_bonus
    return round(total, 2)

# ─────────────────────────────────────────────
# APP UI
# ─────────────────────────────────────────────
st.markdown("### ✍️ Enter your marketing details")

product = st.text_input("Product / Service", placeholder="e.g. AI Resume Analyzer")
audience = st.text_input("Target Audience", placeholder="e.g. job seekers, college grads")
platform = st.selectbox("Platform", ["Facebook", "LinkedIn", "Instagram", "Google Ads", "Twitter / X"])

if st.button("🚀 Generate Ad Copy Variants"):
    if not product or not audience:
        st.warning("Please fill all fields before generating.")
        st.stop()

    with st.spinner("🧠 Crafting ad variants..."):
        result = generate_variants(product, audience, platform)

    st.subheader("✨ Generated Ad Copies")
    st.markdown(result)

    # Extract numbered lines
    variants = []
    for line in result.split("\n"):
        if line.strip().startswith(tuple(str(i) for i in range(1, 10))):
            text = line.split(".", 1)[-1].strip()
            if text:
                variants.append(text)

    if variants:
        scored = [{"Variant": v, "Score": score_variant(v)} for v in variants]
        df = pd.DataFrame(scored).sort_values(by="Score", ascending=False)
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Results (CSV)", csv, "ad_copy_variants.csv", "text/csv")

        best = df.iloc[0]["Variant"]
        st.success(f"🏆 Best Performing Ad Copy:\n\n**{best}**")
    else:
        st.error("Couldn't extract ad copies from response. Try again.")