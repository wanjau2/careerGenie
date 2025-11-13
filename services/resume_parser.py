"""Resume parsing service with AI-powered extraction."""
import os
import re
from datetime import datetime
import PyPDF2
import pdfplumber
from docx import Document
import google.generativeai as genai
from config.settings import Config


class ResumeParser:
    """Parse resumes and extract structured data."""

    def __init__(self):
        """Initialize resume parser with Gemini API."""
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            # Updated to use gemini-1.5-flash (gemini-pro is deprecated)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("Warning: GOOGLE_GEMINI_API_KEY not set. AI parsing will be disabled.")

    def parse_resume(self, file_path):
        """
        Parse resume from file and extract structured data.

        Args:
            file_path: Path to resume file (PDF or DOCX)

        Returns:
            dict: Structured resume data
        """
        try:
            # Extract text from file
            text = self._extract_text(file_path)

            if not text:
                return {'error': 'Could not extract text from resume'}

            # Use AI to parse if available, otherwise use rule-based parsing
            if self.model:
                parsed_data = self._ai_parse(text)
            else:
                parsed_data = self._rule_based_parse(text)

            # Add metadata
            parsed_data['parsedAt'] = datetime.utcnow()
            parsed_data['originalFile'] = file_path
            parsed_data['rawText'] = text

            return parsed_data

        except Exception as e:
            return {'error': f'Failed to parse resume: {str(e)}'}

    def parse_resume_text(self, text):
        """
        Parse resume from text string and extract structured data.

        Args:
            text: Resume text content

        Returns:
            dict: Structured resume data
        """
        try:
            if not text:
                return {'error': 'Empty text provided'}

            # Use AI to parse if available, otherwise use rule-based parsing
            if self.model:
                parsed_data = self._ai_parse(text)
            else:
                parsed_data = self._rule_based_parse(text)

            # Add metadata
            parsed_data['parsedAt'] = datetime.utcnow()
            parsed_data['raw_text'] = text

            return parsed_data

        except Exception as e:
            return {'error': f'Failed to parse resume text: {str(e)}'}

    def _extract_text(self, file_path):
        """Extract text from PDF or DOCX file."""
        extension = os.path.splitext(file_path)[1].lower()

        if extension == '.pdf':
            return self._extract_from_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _extract_from_pdf(self, file_path):
        """Extract text from PDF using multiple methods."""
        text = ""

        # Try pdfplumber first (better for complex PDFs)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2")

        # Fallback to PyPDF2
        if not text:
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
            except Exception as e:
                print(f"PyPDF2 also failed: {e}")

        return text.strip()

    def _extract_from_docx(self, file_path):
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")

    def _ai_parse(self, text):
        """Use Gemini AI to parse resume text."""
        try:
            prompt = f"""
You are an expert resume parser. Analyze the following resume text and extract structured information in JSON format.

Resume Text:
{text}

Extract and return ONLY a valid JSON object with the following structure:
{{
    "contactInfo": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "+1234567890",
        "location": {{"city": "City", "state": "State", "country": "Country"}},
        "linkedin": "LinkedIn URL",
        "github": "GitHub URL",
        "portfolio": "Portfolio URL"
    }},
    "summary": "Professional summary/objective text",
    "workExperience": [
        {{
            "company": "Company Name",
            "title": "Job Title",
            "startDate": "MM/YYYY",
            "endDate": "MM/YYYY or Present",
            "location": "City, State",
            "description": "Job description",
            "achievements": ["Achievement 1", "Achievement 2"],
            "skills": ["Skill 1", "Skill 2"]
        }}
    ],
    "education": [
        {{
            "institution": "University Name",
            "degree": "Degree Type",
            "field": "Field of Study",
            "startDate": "MM/YYYY",
            "endDate": "MM/YYYY",
            "gpa": "3.8/4.0",
            "achievements": ["Honor", "Award"]
        }}
    ],
    "skills": [
        {{"name": "Skill Name", "category": "technical/soft/domain", "proficiency": "expert/advanced/intermediate/beginner"}}
    ],
    "certifications": [
        {{"name": "Certification Name", "issuer": "Issuing Organization", "issueDate": "MM/YYYY", "expiryDate": "MM/YYYY", "credentialId": "ID"}}
    ],
    "languages": [
        {{"language": "Language Name", "proficiency": "native/professional/conversational/basic"}}
    ],
    "projects": [
        {{"name": "Project Name", "description": "Description", "technologies": ["Tech 1"], "link": "URL"}}
    ],
    "publications": [
        {{"title": "Publication Title", "publisher": "Publisher", "date": "MM/YYYY", "link": "URL"}}
    ],
    "awards": [
        {{"name": "Award Name", "issuer": "Issuing Organization", "date": "MM/YYYY", "description": "Description"}}
    ]
}}

Return ONLY the JSON object, no additional text.
"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up response (remove markdown code blocks if present)
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            import json
            parsed_data = json.loads(result_text.strip())

            return parsed_data

        except Exception as e:
            print(f"AI parsing failed: {e}, falling back to rule-based parsing")
            return self._rule_based_parse(text)

    def _rule_based_parse(self, text):
        """Fallback rule-based parsing when AI is not available."""
        parsed = {
            'contactInfo': self._extract_contact_info(text),
            'summary': self._extract_summary(text),
            'workExperience': self._extract_work_experience(text),
            'education': self._extract_education(text),
            'skills': self._extract_skills(text),
            'certifications': [],
            'languages': [],
            'projects': [],
            'publications': [],
            'awards': []
        }

        return parsed

    def _extract_contact_info(self, text):
        """Extract contact information using regex."""
        contact = {}

        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact['email'] = email_match.group()

        # Phone
        phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact['phone'] = phone_match.group()

        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w\-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact['linkedin'] = f"https://{linkedin_match.group()}"

        # GitHub
        github_pattern = r'github\.com/[\w\-]+'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            contact['github'] = f"https://{github_match.group()}"

        # Name (first line or before email)
        lines = text.split('\n')
        if lines:
            contact['name'] = lines[0].strip()

        return contact

    def _extract_summary(self, text):
        """Extract professional summary/objective."""
        summary_keywords = ['summary', 'objective', 'profile', 'about']

        for keyword in summary_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?=\n\n|\n[A-Z]{{2,}}|$)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_work_experience(self, text):
        """Extract work experience entries."""
        # This is a simplified version - real implementation would be more sophisticated
        experience = []

        # Look for common experience section headers
        exp_pattern = r'(?:EXPERIENCE|WORK HISTORY|EMPLOYMENT)(.*?)(?=EDUCATION|SKILLS|$)'
        match = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            exp_section = match.group(1)
            # Split into individual jobs (this is very basic)
            jobs = exp_section.split('\n\n')

            for job in jobs:
                if len(job.strip()) > 20:  # Minimum length for a job entry
                    experience.append({
                        'description': job.strip(),
                        'company': '',  # Would need more sophisticated parsing
                        'title': '',
                        'startDate': '',
                        'endDate': ''
                    })

        return experience

    def _extract_education(self, text):
        """Extract education entries."""
        education = []

        edu_pattern = r'(?:EDUCATION)(.*?)(?=EXPERIENCE|SKILLS|$)'
        match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            edu_section = match.group(1)
            # Basic parsing - would need improvement
            entries = edu_section.split('\n\n')

            for entry in entries:
                if len(entry.strip()) > 20:
                    education.append({
                        'description': entry.strip(),
                        'institution': '',
                        'degree': '',
                        'field': '',
                        'startDate': '',
                        'endDate': ''
                    })

        return education

    def _extract_skills(self, text):
        """Extract skills."""
        skills = []

        skills_pattern = r'(?:SKILLS|TECHNICAL SKILLS)(.*?)(?=\n[A-Z]{{2,}}|$)'
        match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            skills_section = match.group(1)
            # Split by common delimiters
            skill_items = re.split(r'[,\n•·\-]', skills_section)

            for item in skill_items:
                skill_name = item.strip()
                if skill_name and len(skill_name) > 2:
                    skills.append({
                        'name': skill_name,
                        'category': 'technical',
                        'proficiency': 'intermediate'
                    })

        return skills

    def merge_with_linkedin(self, parsed_resume, linkedin_data):
        """
        Merge parsed resume data with LinkedIn profile data.

        Args:
            parsed_resume: Parsed resume data
            linkedin_data: LinkedIn API response

        Returns:
            dict: Merged data with conflict resolution
        """
        merged = parsed_resume.copy()

        # Prefer LinkedIn for contact info (more up-to-date)
        if linkedin_data:
            if 'emailAddress' in linkedin_data:
                merged['contactInfo']['email'] = linkedin_data['emailAddress']

            if 'publicProfileUrl' in linkedin_data:
                merged['contactInfo']['linkedin'] = linkedin_data['publicProfileUrl']

            # Merge work experience
            if 'positions' in linkedin_data:
                linkedin_exp = []
                for pos in linkedin_data['positions'].get('values', []):
                    linkedin_exp.append({
                        'company': pos.get('company', {}).get('name', ''),
                        'title': pos.get('title', ''),
                        'startDate': f"{pos.get('startDate', {}).get('month', '')}/{pos.get('startDate', {}).get('year', '')}",
                        'endDate': 'Present' if pos.get('isCurrent') else f"{pos.get('endDate', {}).get('month', '')}/{pos.get('endDate', {}).get('year', '')}",
                        'description': pos.get('summary', ''),
                        'source': 'linkedin'
                    })

                # Combine with parsed experience
                merged['workExperience'] = linkedin_exp + merged.get('workExperience', [])

        return merged
