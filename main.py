import streamlit as st
import requests
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import json
import google.generativeai as genai

# =========================
# ✅ CONFIG
# =========================
st.set_page_config(page_title="Chat with Graphs", layout="wide")
st.title("Chat with Graphs")
st.subheader("Ask questions about your image")

# ⚠️ لا تضع المفتاح هنا. استخدم Secrets بدل ذلك:
# Streamlit Cloud: Settings -> Secrets
# محلياً: .streamlit/secrets.toml
# GOOGLE_API_KEY="xxxx"
GOOGLE_API_KEY = st.secrets.get("AIzaSyBo6Ib6ZyioqY8fckhuuqULsB5y3Py9wuI", "")

if not GOOGLE_API_KEY:
    st.warning("AIzaSyBo6Ib6ZyioqY8fckhuuqULsB5y3Py9wuI (.streamlit/secrets.toml).")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
vision_model = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# ✅ HELPERS
# =========================
@st.cache_data(show_spinner=False)
def fetch_image(image_url: str):
    try:
        r = requests.get(image_url, timeout=15)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGB")
        return img
    except (requests.RequestException) as e:
        return f"Request error: {e}"
    except UnidentifiedImageError:
        return "Unidentified image format (not a valid image)."
    except Exception as e:
        return f"Unexpected error: {e}"

def save_interaction(image_url, question, answer, filename="saved_data.json"):
    data = {"image_url": image_url, "question": question, "answer": answer}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            if not isinstance(saved_data, list):
                saved_data = []
    except FileNotFoundError:
        saved_data = []
    except json.JSONDecodeError:
        saved_data = []

    saved_data.append(data)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(saved_data, f, indent=4, ensure_ascii=False)

# =========================
# ✅ APP
# =========================
def main():
    st.sidebar.subheader("Enter Image URL:")
    image_url = st.sidebar.text_input("Image URL", placeholder="https://...")

    image = None
    if image_url:
        fetched = fetch_image(image_url)
        if isinstance(fetched, Image.Image):
            image = fetched
            st.sidebar.image(image, caption="Image", use_container_width=True)
        else:
            st.sidebar.error(fetched)

    st.write("Ask any query about the image:")
    user_input = st.text_input("Your Query:")

    if st.button("Submit", type="primary", disabled=(image is None or not user_input.strip())):
        with st.spinner("Analyzing..."):
            try:
                response = vision_model.generate_content([user_input, image])
                answer = getattr(response, "text", "").strip()
                st.text_area("Model's Response:", value=answer, height=180)

                # ✅ save to json
                save_interaction(image_url, user_input, answer)
                st.success("Saved to saved_data.json")

            except Exception as e:
                st.error(f"Model error: {e}")

if __name__ == "__main__":
    main()

