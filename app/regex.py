import re

def extract_name(text):
    header = text.split("Location")[0].split("Email")[0].split("Phone")[0]
    # Remove unwanted keywords
    header = re.sub(r"(Curriculum Vitae|Resume)", "", header, flags=re.I)
    # Regex for name pattern
    match = re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+| [A-Z]\.?){0,2}", header)
    if match:
        return match.group(0).strip()
    return None

def extract_email(text):
    match = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match[0] if match else None

def extract_phone(text):
    match = re.findall(r"\+?\d[\d\s\-]{8,}\d", text)
    return match[0] if match else None


def extract_location(text):
    # Match "Location" (case-insensitive) or emoji, followed by colon/dash/space
    # Capture until |, newline, or common section header
    pattern = r"(?:Location|📍|Place|Based in|Current Location)\s*[:\-]?\s*([A-Za-z0-9\s,.\-]+?)(?=\s*(?:\||Email|Profile|Education|Experience|Achievements|$))"
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_skills(text):
    skills = []

    # Match "Skills" or "Technical Skills" until next section like "Professional", "Experience", "Education"
    match = re.search(
        r"(Technical\s+Skills|Skills)[:\s-]*(.+?)(?=(Professional|Experience|Achievements|Education|Profile|$))",
        text,
        re.IGNORECASE | re.DOTALL
    )
    
    if match:
        raw_skills = match.group(2).strip()

        # Split by common separators
        candidates = re.split(r"\n|,|•|-", raw_skills)

        # Clean up each skill
        for s in candidates:
            s = s.strip(" -•\t")
            if s:  # keep only non-empty
                skills.append(s)
    
    return skills

def extract_education(text):
    # Extract block between Education and next section
    match = re.search(
        r"Education[:\s-]*(.+?)(?=(Certifications|Skills|Experience|Profile|Projects|$))",
        text,
        re.IGNORECASE | re.DOTALL
    )
    
    education_entries = []
    if match:
        raw_edu = match.group(1).strip()

        # Split based on year OR degree keywords
        parts = re.split(r"(?=(B\.Sc|M\.Sc|MBA|B\.Tech|M\.Tech|PhD|B\.Com|Bachelor|Master|Doctorate))", raw_edu)

        # Merge back correctly
        combined = []
        buffer = ""
        for part in parts:
            if re.search(r"(B\.Sc|M\.Sc|MBA|B\.Tech|M\.Tech|PhD|B\.Com|Bachelor|Master|Doctorate)", part, re.IGNORECASE):
                if buffer:
                    combined.append(buffer.strip())
                buffer = part
            else:
                buffer += " " + part
        if buffer:
            combined.append(buffer.strip())

        # Clean and filter with year
        for c in combined:
            if re.search(r"(19|20)\d{2}", c):
                education_entries.append(c.strip())
    
    return education_entries

def extract_links(text):
    links = {}

    # LinkedIn
    linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s|]+"
    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        url = linkedin_match.group(0).strip(".,;")
        if not url.startswith("http"):
            url = "https://" + url
        links["linkedin"] = url

    # GitHub
    github_pattern = r"(?:https?://)?(?:www\.)?github\.com/[^\s|]+"
    github_match = re.search(github_pattern, text, re.IGNORECASE)
    if github_match:
        url = github_match.group(0).strip(".,;")
        if not url.startswith("http"):
            url = "https://" + url
        links["github"] = url

    # Personal websites (require www or http/https, ignore emails)
    website_pattern = r"(?:https?://|www\.)[a-zA-Z0-9\-]+\.[a-z]{2,}(?:/[^\s|]*)?"
    website_matches = re.findall(website_pattern, text)
    websites = []
    for site in website_matches:
        site = site.strip(".,;")
        # skip linkedin, github, or emails
        if "linkedin.com" in site.lower() or "github.com" in site.lower() or "@" in site.lower():
            continue
        # add https if missing
        if not site.startswith("http"):
            site = "https://" + site
        websites.append(site)

    if websites:
        links["websites"] = websites

    return links if links else {}

def extract_projects(text):
    match = re.search(
        r"Projects[:\s-]*(.+?)(?=(Certifications|Achievements|Education|Skills|Work Experience|Profile|$))",
        text,
        re.IGNORECASE | re.DOTALL
    )
    projects = []
    if match:
        raw = match.group(1).strip()
        # Split only at " - " or "•", avoid hyphens inside words
        projects = [p.strip(" -•\t") for p in re.split(r"\s-\s|•", raw) if p.strip()]
    return projects


def extract_certifications(text):
    match = re.search(
        r"Certifications[:\s-]*(.+?)(?=(Achievements|Projects|Education|Skills|Work Experience|Profile|$))",
        text,
        re.IGNORECASE | re.DOTALL
    )
    certs = []
    if match:
        raw = match.group(1).strip()
        # Try splitting at common certification delimiters or capitalized start of each certificate
        # Add space before "AWS", "Google", "Advanced", "Microsoft" if missing
        raw = re.sub(r'\s(?=(AWS|Google|Advanced|Microsoft|IBM))', r'\n', raw)
        # Now split by newline
        certs = [c.strip(" -•\t") for c in raw.split("\n") if c.strip()]
    return certs



def extract_achievements(text):
    match = re.search(
        r"Achievements[:\s-]*(.+?)(?=(Certifications|Projects|Education|Skills|Work Experience|Profile|$))",
        text,
        re.IGNORECASE | re.DOTALL
    )
    achievements = []
    if match:
        raw = match.group(1).strip()
        achievements = [a.strip(" -•\t") for a in re.split(r"\s-\s|•|\n", raw) if a.strip()]
    return achievements
