import re
import json
import requests

class CvExtractor:
    def __init__(self):
        self.api_key = "AIzaSyAJ726_24AIorqSWJx4ZO-a8_Fci8BIRAc"

    # ---------- Post-process empty lists as None ----------
    def clean_empty_lists_as_none(self, data):
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, str) and value.strip().lower() == "null":
                data[key] = None
            elif isinstance(value, str) and value.strip() == "":
                data[key] = None
            elif isinstance(value, list):
                # Check if list is empty or contains only null/None
                if len(value) == 0:
                    data[key] = None
                elif all((v is None) or (isinstance(v, str) and v.strip().lower() == "null") for v in value):
                    data[key] = None
        return data
    # ---------- Normalize GitHub and LinkedIn links ----------
    def normalize_links(self, data):
        github = data.get("github_link")
        if github and not github.startswith("http"):
            data["github_link"] = "https://" + github.strip()

        linkedin = data.get("linkedin_link")
        if linkedin and not linkedin.startswith("http"):
            data["linkedin_link"] = "https://" + linkedin.strip()

        return data

    # ---------- Main extraction ----------
    def extract(self, text):
        combined_prompt = """
You are a fast, precise resume information extraction system. Your **ONLY** output must be a single JSON object.

**Required JSON Keys:** [name, profession, phone_number, email, location, github_link, linkedin_link, skills, education, experience, projects, certifications, achievements]

**Extraction Rules (Minimal Factual Lists - STRICT JSON NULL/ARRAY):**

1.  **Personal Info:** Return concise string value or **null** if missing. **location** must be the personal contact address **ONLY**. **IGNORE** all job/education/project locations.
    * ***github\_link and linkedin\_link:*** Search the entire text for URLs containing 'github.com' or 'linkedin.com/in/' and extract them. If multiple are found, use the first one. Use **null** if not found.
2.  **skills:** Extract all technical/professional skills as a **list of strings**. Use **[]** (empty list) if none found.
3.  **education, experience, certifications, achievements:** Return each as a **list of single-line strings**. **NO SUMMARIES/EXPLANATIONS.**
    * If a section is missing, return **[]** (empty list).
    * **education:** Format: [Degree/Program – Institution (Year Range)]. Include all programs/levels.
    * **experience:** Format: [Role – Organization].
    * **certifications:** Format: [Certification Title or Issuer]. ***Only include certifications EXPLICITLY listed as such.***
    * **achievements:** Format: **[Key Result, max 10 words]**. Summarize core action/outcome.
4.  **projects:** Return a **list of objects**. Use **[]** (empty list) if no projects.
    * Each object **must** adhere to: `{"name": "...", "links": [...]}`.
    * **The `links` list MUST only contain project-specific URLs (GitHub/demo).** **Exclude all other links.** If no project-specific link is found, the `links` key must be **null**.

**Final Mandate (For Maximum Speed and Precision):**
* Output is **STRICTLY JSON** (no preamble/postscript).
* **Missing list fields MUST use `[]`. Missing single-value fields MUST use `null`.**
* Keep all values **EXTREMELY CONCISE AND MINIMAL.**

**Text sections:**
"""
        combined_prompt += text

        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json", "X-goog-api-key": self.api_key}
        payload = {"contents": [{"parts": [{"text": combined_prompt}]}]}

        # ---------- Call Gemini API ----------
        try:
            response = requests.post(api_url, headers=headers, json=payload).json()
            raw_text = response["candidates"][0]["content"]["parts"][0]["text"]
            clean_json_text = re.sub(r"^```[a-zA-Z]*|```$", "", raw_text).strip()
            data = json.loads(clean_json_text)
            data = self.clean_empty_lists_as_none(data)
            data = self.normalize_links(data)
            return data
        except Exception as e:
            print(f"Error extracting sections: {e}")
            fallback_keys = ["name","profession","phone_number","email","location","github_link","linkedin_link",
                             "skills","education","experience","projects","certifications","achievements"]
            return {key: None for key in fallback_keys}
