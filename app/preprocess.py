import pdfplumber
from docx import Document
import os
import re
import io
from geopy.geocoders import Nominatim

# Extract text from various document formats
# Currently supports PDF, DOCX, and TXT files

# Extract details from pdf
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

#Extract details from docx
def extract_text_from_docx(uploaded_file):
    # Read DOCX from memory
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # Reset pointer so Streamlit uploader still works later
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

# Main function to extract text based on file extension
def extract_text(uploaded_file):
    """Extract text from uploaded CV file directly from memory (no saving)."""
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(uploaded_file)
    elif ext == ".docx":
        return extract_text_from_docx(uploaded_file)
    elif ext == ".txt":
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file format: " + ext)
    
def clean_text(text):
    # Remove unwanted characters like (cid:127)
    text = re.sub(r"\(cid:\d+\)", "", text)
    
    # Replace emojis/symbols with words
    replacements = {
        "📍": "Location:",
        "📧": "Email:",
        "📱": "Phone:",
        "🌐": "Website:",
        "💼": "LinkedIn:",
        "🐙": "GitHub:"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Normalize spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Initialize geolocator for location extraction
geolocator = Nominatim(user_agent="cv_app")

def get_lat_lon(location):
    try:
        loc = geolocator.geocode(location)
        if loc:
            return loc.latitude, loc.longitude
    except:
        return None, None
    return None, None    