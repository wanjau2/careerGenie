"""Resume parsing service with enhanced rule-based extraction.

Based on best practices from:
- StackOverflow discussions on resume parsing
- Medium tutorials on NLP-based extraction
- GitHub projects like pyresparser and resume_parser.py
"""
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import PyPDF2
import pdfplumber
from docx import Document
import phonenumbers
import spacy

# Try to load spaCy model, download if not available
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy English model...")
    os.system("python3 -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


class ResumeParser:
    """Parse resumes and extract structured data using rule-based methods."""

    # Common tech skills database (expandable)
    TECH_SKILLS = {
        'languages': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php',
                      'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab', 'sql', 'html',
                      'css', 'dart', 'perl', 'shell', 'bash'],
        'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
                       'express', 'nodejs', 'nest.js', 'laravel', 'rails', 'asp.net', 'flutter',
                       'react native', 'tensorflow', 'pytorch', 'keras', 'scikit-learn'],
        'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'oracle',
                      'sql server', 'dynamodb', 'elasticsearch', 'neo4j', 'sqlite'],
        'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins',
                  'terraform', 'ansible', 'circleci', 'travis ci', 'github actions'],
        'tools': ['git', 'jira', 'confluence', 'slack', 'postman', 'swagger', 'figma',
                  'adobe xd', 'photoshop', 'illustrator', 'tableau', 'power bi'],
        'concepts': ['machine learning', 'deep learning', 'data science', 'devops', 'ci/cd',
                     'microservices', 'rest api', 'graphql', 'agile', 'scrum', 'tdd', 'bdd']
    }

    # Section headers mapping
    SECTION_HEADERS = {
        'experience': r'(?i)(?:work\s+)?(?:experience|employment|work\s+history|professional\s+experience)',
        'education': r'(?i)(?:education|academic|qualifications|academic\s+background)',
        'skills': r'(?i)(?:skills|technical\s+skills|competencies|expertise|technologies)',
        'projects': r'(?i)(?:projects|personal\s+projects|portfolio)',
        'certifications': r'(?i)(?:certifications?|certificates?|licenses?)',
        'summary': r'(?i)(?:summary|objective|profile|about\s+me)',
        'awards': r'(?i)(?:awards?|honors?|achievements?)',
        'publications': r'(?i)(?:publications?|papers?|research)',
        'languages': r'(?i)(?:languages?|linguistic\s+skills?)'
    }

    def __init__(self):
        """Initialize resume parser."""
        self.all_skills = self._flatten_skills()

    def _flatten_skills(self) -> List[str]:
        """Flatten all skills into a single searchable list."""
        skills = []
        for category in self.TECH_SKILLS.values():
            skills.extend(category)
        return skills

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
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

            # Use enhanced rule-based parsing
            parsed_data = self._enhanced_parse(text)

            # Add metadata
            parsed_data['parsedAt'] = datetime.utcnow().isoformat()
            parsed_data['originalFile'] = os.path.basename(file_path)
            parsed_data['rawText'] = text[:500]  # First 500 chars for reference

            return parsed_data

        except Exception as e:
            return {'error': f'Failed to parse resume: {str(e)}'}

    def parse_resume_text(self, text: str) -> Dict[str, Any]:
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

            parsed_data = self._enhanced_parse(text)
            parsed_data['parsedAt'] = datetime.utcnow().isoformat()
            parsed_data['rawText'] = text[:500]

            return parsed_data

        except Exception as e:
            return {'error': f'Failed to parse resume text: {str(e)}'}

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX file."""
        extension = os.path.splitext(file_path)[1].lower()

        if extension == '.pdf':
            return self._extract_from_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods."""
        text = ""

        # Try pdfplumber first (better for complex PDFs)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2")

        # Fallback to PyPDF2
        if not text:
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"PyPDF2 also failed: {e}")

        return text.strip()

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")

    def _enhanced_parse(self, text: str) -> Dict[str, Any]:
        """
        Enhanced rule-based parsing using regex, NLP, and pattern matching.

        Based on best practices from StackOverflow and tech blogs.
        """
        # Split text into sections
        sections = self._split_into_sections(text)

        # Extract structured data
        parsed = {
            'personalInfo': self._extract_personal_info(text, sections),
            'summary': self._extract_summary(text, sections),
            'experiences': self._extract_experiences(text, sections),
            'education': self._extract_education(text, sections),
            'skills': self._extract_skills_enhanced(text, sections),
            'certifications': self._extract_certifications(text, sections),
            'projects': self._extract_projects(text, sections),
            'awards': self._extract_awards(text, sections),
            'languages': self._extract_languages(text, sections),
        }

        return parsed

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Split resume text into sections based on headers.

        Uses regex patterns to identify section boundaries.
        """
        sections = {}

        # Find all section headers and their positions
        header_positions = []
        for section_name, pattern in self.SECTION_HEADERS.items():
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                header_positions.append((match.start(), match.end(), section_name))

        # Sort by position
        header_positions.sort(key=lambda x: x[0])

        # Extract section content between headers
        for i, (start, end, section_name) in enumerate(header_positions):
            # Get text from end of header to start of next header (or end of text)
            if i + 1 < len(header_positions):
                section_text = text[end:header_positions[i + 1][0]]
            else:
                section_text = text[end:]

            sections[section_name] = section_text.strip()

        return sections

    def _extract_personal_info(self, text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract personal information using regex and NLP.

        Patterns based on StackOverflow best practices:
        - https://stackoverflow.com/questions/38636967/
        - https://medium.com/@branzoldecode/phone-number-and-email-extractor
        """
        info = {}

        # Extract name using spaCy NER (first PERSON entity, typically at the top)
        doc = nlp(text[:500])  # Check first 500 chars
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                info['fullName'] = ent.text.strip()
                break

        # If no name found via NER, use first line
        if 'fullName' not in info:
            first_line = text.split('\n')[0].strip()
            if len(first_line) < 50 and len(first_line.split()) <= 4:
                info['fullName'] = first_line

        # Email using comprehensive regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            info['email'] = email_match.group()

        # Phone using phonenumbers library for better accuracy
        phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
        phone_matches = re.finditer(phone_pattern, text)
        for match in phone_matches:
            try:
                # Try to parse and validate phone number
                phone_str = match.group()
                parsed_phone = phonenumbers.parse(phone_str, None)
                if phonenumbers.is_valid_number(parsed_phone):
                    info['phone'] = phonenumbers.format_number(
                        parsed_phone,
                        phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    )
                    break
            except:
                # If parsing fails, use raw match
                info['phone'] = match.group().strip()
                break

        # LinkedIn
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            url = linkedin_match.group()
            if not url.startswith('http'):
                url = 'https://' + url
            info['linkedin'] = url

        # GitHub
        github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            url = github_match.group()
            if not url.startswith('http'):
                url = 'https://' + url
            info['github'] = url

        # Portfolio/Website
        portfolio_pattern = r'(?:https?://)?(?:www\.)?[\w\-]+\.(?:com|io|dev|me|net)/[\w\-/]*'
        portfolio_match = re.search(portfolio_pattern, text)
        if portfolio_match:
            url = portfolio_match.group()
            # Exclude common social media sites
            if not any(site in url.lower() for site in ['linkedin', 'github', 'facebook', 'twitter']):
                if not url.startswith('http'):
                    url = 'https://' + url
                info['portfolio'] = url

        # Location using spaCy NER
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Geopolitical Entity
                info['location'] = ent.text
                break

        return info

    def _extract_summary(self, text: str, sections: Dict[str, str]) -> str:
        """Extract professional summary/objective."""
        if 'summary' in sections:
            summary = sections['summary']
            # Clean up and return first paragraph
            lines = [line.strip() for line in summary.split('\n') if line.strip()]
            return ' '.join(lines[:3])  # First 3 lines max

        return ""

    def _extract_experiences(self, text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract work experience entries.

        Uses pattern matching for job titles, companies, dates.
        Based on: https://github.com/arunppsg/resume-parser
        """
        experiences = []

        if 'experience' not in sections:
            return experiences

        exp_text = sections['experience']

        # Split into individual job entries (separated by blank lines or dates)
        # Date pattern: Month Year or MM/YYYY
        date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\d{1,2}/\d{4}'

        # Find all date ranges
        date_ranges = list(re.finditer(
            rf'({date_pattern})\s*(?:-|–|to)\s*(?:({date_pattern})|Present|Current)',
            exp_text,
            re.IGNORECASE
        ))

        # Extract job entries based on date positions
        for i, date_match in enumerate(date_ranges):
            start_pos = date_match.start()

            # Look backwards for company/title (usually within 200 chars before date)
            lookback_start = max(0, start_pos - 200)
            header_text = exp_text[lookback_start:start_pos]

            # Look forward for description (until next date or end)
            if i + 1 < len(date_ranges):
                end_pos = date_ranges[i + 1].start()
            else:
                end_pos = len(exp_text)

            description_text = exp_text[date_match.end():end_pos]

            # Extract company and title from header
            lines = [l.strip() for l in header_text.split('\n') if l.strip()]
            title = lines[-2] if len(lines) >= 2 else ""
            company = lines[-1] if len(lines) >= 1 else ""

            # Use spaCy to find organization names
            doc = nlp(header_text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    company = ent.text
                    break

            # Extract bullet points/achievements
            achievements = []
            bullet_pattern = r'^[\s]*[•\-\*◦]\s*(.+)$'
            for line in description_text.split('\n'):
                match = re.match(bullet_pattern, line)
                if match:
                    achievements.append(match.group(1).strip())

            experiences.append({
                'title': title,
                'company': company,
                'startDate': date_match.group(1),
                'endDate': date_match.group(2) or 'Present',
                'description': description_text.strip()[:500],  # First 500 chars
                'achievements': achievements,
            })

        return experiences

    def _extract_education(self, text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract education entries."""
        education = []

        if 'education' not in sections:
            return education

        edu_text = sections['education']

        # Common degree patterns
        degree_pattern = r'(?:Bachelor|Master|PhD|Ph\.D\.|B\.S\.|B\.A\.|M\.S\.|M\.A\.|MBA)(?:\s+of\s+)?(?:\s+Science|\s+Arts)?(?:\s+in\s+)?([A-Za-z\s]+)?'

        # Date pattern
        date_pattern = r'(\d{4})\s*(?:-|–|to)\s*(\d{4}|Present)'

        # Split by dates or blank lines
        entries = re.split(r'\n\s*\n', edu_text)

        for entry in entries:
            if len(entry.strip()) < 10:
                continue

            edu_entry = {}

            # Extract degree
            degree_match = re.search(degree_pattern, entry, re.IGNORECASE)
            if degree_match:
                edu_entry['degree'] = degree_match.group(0)
                if degree_match.group(1):
                    edu_entry['field'] = degree_match.group(1).strip()

            # Extract institution using spaCy
            doc = nlp(entry)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    edu_entry['institution'] = ent.text
                    break

            # Extract dates
            date_match = re.search(date_pattern, entry)
            if date_match:
                edu_entry['startDate'] = date_match.group(1)
                edu_entry['endDate'] = date_match.group(2)

            # Extract GPA if present
            gpa_pattern = r'GPA[:\s]+([0-9.]+)'
            gpa_match = re.search(gpa_pattern, entry, re.IGNORECASE)
            if gpa_match:
                edu_entry['gpa'] = gpa_match.group(1)

            if edu_entry:
                education.append(edu_entry)

        return education

    def _extract_skills_enhanced(self, text: str, sections: Dict[str, str]) -> List[str]:
        """
        Extract skills using multiple methods.

        Based on: https://www.affinda.com/blog/extract-skills-from-a-resume-using-python
        """
        skills = set()

        # Method 1: From skills section if available
        if 'skills' in sections:
            skills_text = sections['skills'].lower()

            # Split by common delimiters
            skill_items = re.split(r'[,\n•·\-\|/]', skills_text)
            for item in skill_items:
                skill = item.strip()
                if skill and len(skill) > 1 and len(skill) < 30:
                    skills.add(skill.title())

        # Method 2: Match against known skills database
        text_lower = text.lower()
        for skill in self.all_skills:
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(skill)}\b'
            if re.search(pattern, text_lower):
                skills.add(skill.title())

        # Method 3: Extract from experience section (tools/technologies mentioned)
        if 'experience' in sections:
            exp_doc = nlp(sections['experience'])
            for chunk in exp_doc.noun_chunks:
                text_chunk = chunk.text.lower()
                # Check if it matches common tech patterns
                if any(tech_word in text_chunk for tech_word in ['framework', 'library', 'tool', 'language', 'technology']):
                    skills.add(chunk.text.title())

        return sorted(list(skills))

    def _extract_certifications(self, text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract certifications."""
        certifications = []

        if 'certifications' not in sections:
            return certifications

        cert_text = sections['certifications']
        lines = [l.strip() for l in cert_text.split('\n') if l.strip()]

        for line in lines:
            # Skip bullet points
            line = re.sub(r'^[•\-\*◦]\s*', '', line)

            cert = {'name': line}

            # Extract date if present
            date_match = re.search(r'(\d{4})', line)
            if date_match:
                cert['issueDate'] = date_match.group(1)

            # Extract issuer (common cert providers)
            issuers = ['AWS', 'Microsoft', 'Google', 'Oracle', 'Cisco', 'CompTIA', 'PMI', 'Scrum']
            for issuer in issuers:
                if issuer.lower() in line.lower():
                    cert['issuer'] = issuer
                    break

            certifications.append(cert)

        return certifications

    def _extract_projects(self, text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract project information."""
        projects = []

        if 'projects' not in sections:
            return projects

        proj_text = sections['projects']

        # Split by project entries (usually separated by blank lines)
        entries = re.split(r'\n\s*\n', proj_text)

        for entry in entries:
            if len(entry.strip()) < 20:
                continue

            lines = [l.strip() for l in entry.split('\n') if l.strip()]

            project = {
                'name': lines[0] if lines else '',
                'description': ' '.join(lines[1:]) if len(lines) > 1 else '',
            }

            # Extract URL if present
            url_match = re.search(r'https?://[^\s]+', entry)
            if url_match:
                project['url'] = url_match.group()

            # Extract technologies mentioned
            technologies = []
            for skill in self.all_skills:
                if skill.lower() in entry.lower():
                    technologies.append(skill.title())
            project['technologies'] = technologies

            projects.append(project)

        return projects

    def _extract_awards(self, text: str, sections: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract awards and honors."""
        awards = []

        if 'awards' not in sections:
            return awards

        awards_text = sections['awards']
        lines = [l.strip() for l in awards_text.split('\n') if l.strip()]

        for line in lines:
            # Skip bullet points
            line = re.sub(r'^[•\-\*◦]\s*', '', line)

            if len(line) > 5:
                award = {'name': line}

                # Extract date if present
                date_match = re.search(r'(\d{4})', line)
                if date_match:
                    award['date'] = date_match.group(1)

                awards.append(award)

        return awards

    def _extract_languages(self, text: str, sections: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract language proficiencies."""
        languages = []

        if 'languages' not in sections:
            return languages

        lang_text = sections['languages']

        # Common proficiency levels
        proficiency_pattern = r'(Native|Fluent|Professional|Conversational|Basic|Elementary)'

        lines = [l.strip() for l in lang_text.split('\n') if l.strip()]

        for line in lines:
            # Skip bullet points
            line = re.sub(r'^[•\-\*◦]\s*', '', line)

            if len(line) > 2:
                lang = {'language': line}

                # Extract proficiency if mentioned
                prof_match = re.search(proficiency_pattern, line, re.IGNORECASE)
                if prof_match:
                    lang['proficiency'] = prof_match.group(1).lower()
                    # Remove proficiency from language name
                    lang['language'] = re.sub(proficiency_pattern, '', line, flags=re.IGNORECASE).strip(' -:,()')

                languages.append(lang)

        return languages

    def merge_with_linkedin(self, parsed_resume: Dict, linkedin_data: Dict) -> Dict:
        """
        Merge parsed resume data with LinkedIn profile data.

        Args:
            parsed_resume: Parsed resume data
            linkedin_data: LinkedIn API response

        Returns:
            dict: Merged data with conflict resolution
        """
        merged = parsed_resume.copy()

        if not linkedin_data:
            return merged

        # Prefer LinkedIn for contact info (more up-to-date)
        if 'emailAddress' in linkedin_data:
            merged['personalInfo']['email'] = linkedin_data['emailAddress']

        if 'publicProfileUrl' in linkedin_data:
            merged['personalInfo']['linkedin'] = linkedin_data['publicProfileUrl']

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
            merged['experiences'] = linkedin_exp + merged.get('experiences', [])

        return merged
