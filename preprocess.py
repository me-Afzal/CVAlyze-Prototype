import fitz
import pdfplumber
from docx import Document
import os
import unicodedata
import re
import io
from geopy.geocoders import Nominatim
from genderize import Genderize

# Extract text from various document formats
# Currently supports PDF, DOCX, and TXT files
def extract_text_from_pdf(pdf_path):
    final_text = ""
    all_links = set()

    # Step 1: Extract embedded hyperlinks
    with fitz.open(pdf_path) as doc:
        for page in doc:
            for link in page.get_links():
                uri = link.get("uri")
                if uri and uri.startswith("http"):
                    all_links.add(uri.strip())

    # Step 2: Detect plain-text URLs (more comprehensive)
    url_pattern = re.compile(
        r'(https?://[^\s]+|www\.[^\s]+|\b[\w-]+\.(?:vercel|netlify|github|streamlit|huggingface|render|heroku|io|app|ai|com|org)\b[^\s]*)',
        re.IGNORECASE
    )

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            # Step 3: Extract any URLs written in text
            found_urls = url_pattern.findall(text)
            for u in found_urls:
                clean_url = u.strip(").,;:!?")
                all_links.add(clean_url)

            # Step 4: Clean formatting junk
            text = re.sub(r"\(cid:\d+\)", "", text)
            text = re.sub(r"\s+", " ", text)

            # Step 5: Insert top-level links (only once)
            if i == 1:
                top_links = []
                for link in all_links:
                    if any(
                        k in link.lower()
                        for k in [
                            "linkedin",
                            "github",
                            "portfolio",
                            "vercel",
                            "netlify",
                            "streamlit",
                            "huggingface",
                            "render",
                            "demo",
                            "live",
                            "project",
                        ]
                    ):
                        top_links.append(link)

                if top_links:
                    text = text.strip() + "\n\nLinks: " + ", ".join(sorted(top_links))

            final_text += f"\n\n--- Page {i} ---\n{text.strip()}"

    return final_text.strip()

#Extract details from docx
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Main function to extract text based on file extension
## extract function 
def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError("Unsupported file format: " + ext)

#Clean text
def clean_text(text: str) -> str:
    """Clean and normalize extracted CV text for LLM extraction."""
    
    # Normalize Unicode and typographic symbols
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\(cid:\d+\)", "", text)
    text = re.sub(r"â€“|â€”|–|—", "-", text)
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r"•+", "•", text)
    text = re.sub(r"---\s*Page\s*\d+\s*---", " ", text)

    # Replace known icons/emojis with labels
    replacements = {
        "📍": "Location:",
        "📧": "Email:",
        "📱": "Phone:",
        "🌐": "Website:",
        "💼": "LinkedIn:",
        "🐙": "GitHub:",
        "🏠": "Address:",
        "☎️": "Phone:",
        "✉️": "Email:",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # Normalize bullets, newlines, and separators
    text = re.sub(r'[\u2022\u25CF\u25A0•▪]', '-', text)  # normalize bullets
    text = re.sub(r'[-_]{3,}', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # Strip emojis or pictographs (catch-all)
    text = re.sub(r'[\U00010000-\U0010ffff]', ' ', text)  # remove all emojis

    # Remove stray non-ASCII junk but keep letters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Normalize punctuation & spacing
    text = re.sub(r'\s([,.!?;:])', r'\1', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()

    return text

# Initialize geolocator for location extraction
geolocator = Nominatim(user_agent="cv_app")

def get_lat_lon(location):
    default_lat, default_lon, default_country = 20.5937, 78.9629, "India"  # Approx center of India
    try:
        # If location is missing or empty, return defaults
        if not location:
            return default_lat, default_lon, default_country
        
        loc = geolocator.geocode(location, addressdetails=True)
        
        if loc:
            latitude = loc.latitude
            longitude = loc.longitude
            # Get country if available, else use default
            country = loc.raw.get("address", {}).get("country", default_country)
            return latitude, longitude, country
        else:
            # If geocoding fails (invalid location), return defaults
            return default_lat, default_lon, default_country
    except Exception as e:
        print(f"Error geocoding location '{location}': {e}")
        # On exception, return defaults
        return default_lat, default_lon, default_country


# Find Gender
# Initialize Genderize once (to avoid repeated API calls)
genderize = Genderize()
def get_gender(name):
    try:
        result = genderize.get([name])[0]  # Genderize expects a list
        gender = result['gender']
        if gender is None:
            return 'unknown'
        return gender
    except:
        return 'unknown'