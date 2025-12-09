"""
🌿 My Green Doctor - Plant Disease Detection App
================================================
A lightweight, educational web application that helps farmers and students
identify plant diseases from leaf photos using Google's Gemini Vision AI.

Developed by: Lamisa Banu
Purpose: Educational tool for plant health awareness
"""

import streamlit as st
from PIL import Image
import google.generativeai as genai
import io

# =============================================================================
# CONFIGURATION
# =============================================================================

# Page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="🌿 My Green Doctor",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Constants for image processing
MAX_IMAGE_SIZE = (800, 800)  # Max dimensions for resizing
JPEG_QUALITY = 85  # Quality for JPEG compression

# System prompt for the AI - defines the expert behavior
SYSTEM_PROMPT = """You are an expert agricultural scientist and plant pathologist with decades of experience in diagnosing plant diseases from visual symptoms.

Analyze the provided image and respond in the following structured format:

## 🔍 Classification
[Choose one: "🟢 Healthy", "🟡 Potentially Diseased", or "⚪ Not a Plant"]

## 🦠 Disease Name
[If diseased, provide the most likely disease name. If healthy, write "N/A". If not a plant, write "N/A"]

## 📊 Confidence Level
[Provide your confidence as: "High (80-100%)", "Medium (50-79%)", or "Low (below 50%)"]

## 💡 Recommended Actions
[Provide 1-2 simple, actionable tips appropriate for farmers or students. Keep it practical and easy to understand.]

## 📝 Brief Explanation
[In 2-3 sentences, explain what you observed in the image that led to your diagnosis.]

---
⚠️ **DISCLAIMER**: This analysis is for EDUCATIONAL PURPOSES ONLY. It should not replace professional agricultural advice. Always consult with a local agricultural extension officer or plant pathologist for accurate diagnosis and treatment recommendations.
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_api_key():
    """
    Check if the Gemini API key is configured in Streamlit secrets.
    Returns the API key if found, None otherwise.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if api_key and api_key.strip() and api_key != "your-gemini-api-key-here":
            return api_key.strip()
        return None
    except Exception:
        return None


def resize_image(image: Image.Image) -> Image.Image:
    """
    Resize image to optimize bandwidth while maintaining aspect ratio.
    This helps reduce API costs and speeds up processing.
    """
    # Convert to RGB if necessary (handles PNG with transparency)
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    
    # Only resize if image is larger than max size
    if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
        image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
    
    return image


def image_to_bytes(image: Image.Image) -> bytes:
    """
    Convert PIL Image to bytes for API transmission.
    Uses JPEG compression to reduce file size.
    """
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    buffer.seek(0)
    return buffer.getvalue()


def analyze_plant_image(image: Image.Image, api_key: str) -> str:
    """
    Send the image to Gemini API for analysis.
    Returns the AI's diagnosis as a string.
    """
    try:
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize the model - using gemini-2.0-flash for speed and cost efficiency
        # Note: Model names may change; alternatives include 'gemini-1.5-flash-latest', 'gemini-pro-vision'
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Prepare the image for the API
        processed_image = resize_image(image)
        
        # Generate the response
        response = model.generate_content(
            [SYSTEM_PROMPT, processed_image],
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent results
                max_output_tokens=1024
            )
        )
        
        return response.text
    
    except Exception as e:
        error_message = str(e)
        if "API_KEY" in error_message.upper() or "AUTHENTICATION" in error_message.upper():
            return "❌ **API Key Error**: Your API key appears to be invalid. Please check your configuration."
        elif "QUOTA" in error_message.upper() or "LIMIT" in error_message.upper():
            return "❌ **Quota Exceeded**: API usage limit reached. Please try again later."
        else:
            return f"❌ **Error**: An unexpected error occurred: {error_message}"


# =============================================================================
# MAIN APPLICATION UI
# =============================================================================

def main():
    """Main application entry point."""
    
    # Header section
    st.title("🌿 My Green Doctor")
    st.markdown("##### *Your AI-powered plant health assistant*")
    st.markdown("---")
    
    # Check for API key first
    api_key = check_api_key()
    
    if not api_key:
        st.error("🔑 **API Key Not Configured**")
        st.markdown("""
        To use this app, you need to configure your Google Gemini API key:
        
        **For Local Development:**
        1. Create a file `.streamlit/secrets.toml` in your project directory
        2. Add: `GEMINI_API_KEY = "your-api-key-here"`
        
        **For Streamlit Cloud:**
        1. Go to your app settings → Secrets
        2. Add: `GEMINI_API_KEY = "your-api-key-here"`
        
        **Get your free API key at:** [Google AI Studio](https://makersuite.google.com/app/apikey)
        """)
        return

    # Instructions section
    st.info("📸 **How to use:** Take a photo of a plant leaf or upload an image, and I'll help identify if it's healthy or diseased!")

    # Image input section - tabs for camera and upload
    tab_camera, tab_upload = st.tabs(["📷 Take Photo", "📁 Upload Image"])

    image = None

    with tab_camera:
        st.markdown("*Use your device camera to capture a plant leaf*")
        camera_image = st.camera_input("Take a picture of the plant leaf", key="camera")
        if camera_image is not None:
            image = Image.open(camera_image)

    with tab_upload:
        st.markdown("*Upload an existing photo from your device*")
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png", "webp"],
            key="uploader"
        )
        if uploaded_file is not None:
            image = Image.open(uploaded_file)

    # Display and analyze the image
    if image is not None:
        st.markdown("---")
        st.subheader("📷 Your Image")

        # Display the original image
        st.image(image, caption="Uploaded plant image", use_container_width=True)

        # Analyze button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button(
                "🔬 Analyze Plant Health",
                type="primary",
                use_container_width=True
            )

        if analyze_button:
            st.markdown("---")
            st.subheader("🩺 Diagnosis Report")

            # Show a spinner while processing
            with st.spinner("🔍 Analyzing your plant image... This may take a few seconds."):
                result = analyze_plant_image(image, api_key)

            # Display the result
            st.markdown(result)

            # Add a helpful footer
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; color: gray; font-size: 0.9em;'>
            💡 <b>Tip:</b> For best results, ensure good lighting and capture the affected areas clearly.
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🌿 <b>My Green Doctor</b> | Educational Plant Health Tool<br>
    Developed by <b>Lamisa Banu</b><br>
    Powered by Google Gemini AI | Built with Streamlit
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# RUN THE APP
# =============================================================================

if __name__ == "__main__":
    main()

