import logging
import re
from typing import List, Dict, Optional

# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ResumeAnalyzer:
    def __init__(self):
        # Expandable list of known skills
        self.known_skills = [
            "Java", "PHP", "HTML", "CSS", "JavaScript", "Firebase", "MySQL",
            "AWS", "Android Studio", "Teamwork", "VS Code", "X Code", "Python", "Flask"
        ]

    def analyze_resume(self, text: str, job: Optional[Dict] = None) -> Dict:
        """
        Analyze resume text and return skill and contact insights.
        :param text: Cleaned extracted text from resume.
        :param job: Optional job dictionary with 'requirements' list.
        :return: Dictionary with analysis results and contact info.
        """
        if not text or not text.strip():
            logger.warning("⚠️ Empty resume text received for analysis.")
            raise ValueError("Resume text is empty or unreadable.")

        logger.info("🔍 Starting resume analysis...")

        extracted_skills = self._extract_skills(text)
        matched_skills = self._match_job_skills(extracted_skills, job)

        # --- Dynamic Scoring ---
        required_skills = job.get("requirements", []) if job else self.known_skills
        total_required = len(required_skills)
        matched_count = len(matched_skills)

        # Skill Score: % of required skills matched
        skills_score = int((matched_count / total_required) * 100) if total_required > 0 else 50

        # Experience Score: Based on word count (basic simulation)
        word_count = len(text.split())
        experience_score = min(100, max(30, word_count // 20))  # e.g. 1000 words → 50

        # Education Score: Based on degree keywords
        education_keywords = ['B.Sc', 'MCA', 'B.Tech', 'M.Tech', 'Bachelor', 'Master']
        education_score = 70 if any(keyword in text for keyword in education_keywords) else 50

        overall_score = int((skills_score + experience_score + education_score) / 3)

        contact_info = self._extract_contact_info(text)

        logger.info("✅ Resume analysis completed successfully.")

        return {
            "overall_score": overall_score,
            "skills_score": skills_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "extracted_skills": extracted_skills,
            "key_points": [
                "Strong technical foundation",
                "Good communication skills",
                "Experience with backend technologies"
            ],
            "recommendations": "Consider gaining experience with cloud platforms like AWS or GCP.",
            "contact_info": contact_info
        }

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract known skills present in the resume text.
        """
        found = []
        for skill in self.known_skills:
            if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
                found.append(skill)
        logger.info(f"✅ Skills extracted: {found}")
        return found

    def _match_job_skills(self, extracted_skills: List[str], job: Optional[Dict]) -> List[str]:
        """
        Match extracted skills with job-specific required skills.
        """
        if not job or not isinstance(job, dict) or not job.get("requirements"):
            return extracted_skills

        required = job["requirements"]
        matched = [skill for skill in extracted_skills if skill.lower() in map(str.lower, required)]
        logger.info(f"🎯 Matched job-required skills: {matched}")
        return matched

    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """
        Extract contact information (email, phone, and basic name inference).
        """
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)

        email = email_match.group(0) if email_match else "unknown@example.com"
        phone = phone_match.group(0) if phone_match else "000-000-0000"

        # Try to infer name
        name = "Unknown"
        lines = text.strip().splitlines()
        if lines:
            first_line = lines[0].strip()
            if 2 <= len(first_line.split()) <= 4 and not any(char.isdigit() for char in first_line):
                name = first_line
            elif email:
                name = email.split("@")[0].replace(".", " ").replace("_", " ").title()

        logger.info(f"📧 Extracted email: {email}, 📞 phone: {phone}, 👤 name: {name}")

        return {
            "name": name,
            "email": email,
            "phone": phone
        }
