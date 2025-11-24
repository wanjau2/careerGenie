"""Document generation service for resumes and cover letters."""
import os
from typing import Dict, Optional, List
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from services.gemini_service import GeminiService


class DocumentGenerator:
    """Generate professional resumes and cover letters."""

    def __init__(self):
        """Initialize document generator."""
        self.gemini = GeminiService()

    def generate_resume(
        self,
        user_data: Dict,
        format: str = 'pdf',
        template: str = 'modern'
    ) -> str:
        """
        Generate a professional resume from user data.

        Args:
            user_data: User profile and resume data
            format: Output format ('pdf' or 'docx')
            template: Resume template ('modern', 'classic', 'minimal')

        Returns:
            Path to generated resume file
        """
        if template == 'modern':
            return self._generate_modern_resume(user_data, format)
        elif template == 'classic':
            return self._generate_classic_resume(user_data, format)
        else:
            return self._generate_minimal_resume(user_data, format)

    def generate_cover_letter(
        self,
        user_data: Dict,
        job_data: Dict,
        format: str = 'pdf',
        custom_content: Optional[str] = None
    ) -> str:
        """
        Generate a tailored cover letter for a job application.

        Args:
            user_data: User profile data
            job_data: Job posting information
            format: Output format ('pdf' or 'docx')
            custom_content: Optional custom content to include

        Returns:
            Path to generated cover letter file
        """
        # Use AI to generate personalized cover letter content
        cover_letter_content = self._generate_cover_letter_content(
            user_data, job_data, custom_content
        )

        if format == 'pdf':
            return self._create_cover_letter_pdf(user_data, job_data, cover_letter_content)
        else:
            return self._create_cover_letter_docx(user_data, job_data, cover_letter_content)

    def _generate_modern_resume(self, user_data: Dict, format: str) -> str:
        """Generate modern style resume."""
        if format == 'pdf':
            return self._create_modern_resume_pdf(user_data)
        else:
            return self._create_modern_resume_docx(user_data)

    def _create_modern_resume_pdf(self, user_data: Dict) -> str:
        """Create modern resume in PDF format."""
        import tempfile

        # Create temp file
        temp_dir = tempfile.gettempdir()
        filename = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(temp_dir, filename)

        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            alignment=1  # Center
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#3498db'),
            spaceAfter=12,
            spaceBefore=12,
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=5
        )

        # Personal Info
        personal = user_data.get('personalInfo', {})
        name = personal.get('fullName', 'Your Name')
        story.append(Paragraph(name, title_style))

        contact_info = []
        if personal.get('email'):
            contact_info.append(personal['email'])
        if personal.get('phone'):
            contact_info.append(personal['phone'])
        if personal.get('location'):
            contact_info.append(personal['location'])

        if contact_info:
            contact_text = ' | '.join(contact_info)
            story.append(Paragraph(contact_text, styles['Normal']))

        story.append(Spacer(1, 0.2*inch))

        # Summary
        summary = user_data.get('summary', '')
        if summary:
            story.append(Paragraph('PROFESSIONAL SUMMARY', heading_style))
            story.append(Paragraph(summary, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

        # Work Experience
        experiences = user_data.get('experiences', [])
        if experiences:
            story.append(Paragraph('WORK EXPERIENCE', heading_style))
            for exp in experiences:
                title = exp.get('title', 'Position')
                company = exp.get('company', 'Company')
                dates = f"{exp.get('startDate', '')} - {exp.get('endDate', 'Present')}"

                story.append(Paragraph(f"<b>{title}</b> at {company}", styles['Normal']))
                story.append(Paragraph(f"<i>{dates}</i>", styles['Normal']))

                if exp.get('description'):
                    story.append(Paragraph(exp['description'], styles['Normal']))

                if exp.get('achievements'):
                    for achievement in exp['achievements']:
                        story.append(Paragraph(f"• {achievement}", styles['Normal']))

                story.append(Spacer(1, 0.1*inch))

        # Education
        education = user_data.get('education', [])
        if education:
            story.append(Paragraph('EDUCATION', heading_style))
            for edu in education:
                degree = edu.get('degree', 'Degree')
                institution = edu.get('institution', 'Institution')
                dates = f"{edu.get('startDate', '')} - {edu.get('endDate', '')}"

                story.append(Paragraph(f"<b>{degree}</b>", styles['Normal']))
                story.append(Paragraph(f"{institution} | {dates}", styles['Normal']))

                if edu.get('gpa'):
                    story.append(Paragraph(f"GPA: {edu['gpa']}", styles['Normal']))

                story.append(Spacer(1, 0.1*inch))

        # Skills
        skills = user_data.get('skills', [])
        if skills:
            story.append(Paragraph('SKILLS', heading_style))
            skills_text = ', '.join(skills[:20])  # Top 20 skills
            story.append(Paragraph(skills_text, styles['Normal']))

        # Build PDF
        doc.build(story)
        return filepath

    def _create_modern_resume_docx(self, user_data: Dict) -> str:
        """Create modern resume in DOCX format."""
        import tempfile

        # Create temp file
        temp_dir = tempfile.gettempdir()
        filename = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = os.path.join(temp_dir, filename)

        # Create document
        doc = Document()

        # Personal Info
        personal = user_data.get('personalInfo', {})
        name = personal.get('fullName', 'Your Name')

        heading = doc.add_heading(name, 0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Contact info
        contact_info = []
        if personal.get('email'):
            contact_info.append(personal['email'])
        if personal.get('phone'):
            contact_info.append(personal['phone'])
        if personal.get('location'):
            contact_info.append(personal['location'])

        if contact_info:
            contact_para = doc.add_paragraph(' | '.join(contact_info))
            contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Summary
        summary = user_data.get('summary', '')
        if summary:
            doc.add_heading('PROFESSIONAL SUMMARY', 1)
            doc.add_paragraph(summary)

        # Work Experience
        experiences = user_data.get('experiences', [])
        if experiences:
            doc.add_heading('WORK EXPERIENCE', 1)
            for exp in experiences:
                title = exp.get('title', 'Position')
                company = exp.get('company', 'Company')
                dates = f"{exp.get('startDate', '')} - {exp.get('endDate', 'Present')}"

                job_para = doc.add_paragraph()
                job_para.add_run(f"{title} at {company}").bold = True
                doc.add_paragraph(dates).italic = True

                if exp.get('description'):
                    doc.add_paragraph(exp['description'])

                if exp.get('achievements'):
                    for achievement in exp['achievements']:
                        doc.add_paragraph(achievement, style='List Bullet')

        # Education
        education = user_data.get('education', [])
        if education:
            doc.add_heading('EDUCATION', 1)
            for edu in education:
                degree = edu.get('degree', 'Degree')
                institution = edu.get('institution', 'Institution')
                dates = f"{edu.get('startDate', '')} - {edu.get('endDate', '')}"

                edu_para = doc.add_paragraph()
                edu_para.add_run(degree).bold = True
                doc.add_paragraph(f"{institution} | {dates}")

                if edu.get('gpa'):
                    doc.add_paragraph(f"GPA: {edu['gpa']}")

        # Skills
        skills = user_data.get('skills', [])
        if skills:
            doc.add_heading('SKILLS', 1)
            doc.add_paragraph(', '.join(skills[:20]))

        # Save document
        doc.save(filepath)
        return filepath

    def _generate_cover_letter_content(
        self,
        user_data: Dict,
        job_data: Dict,
        custom_content: Optional[str] = None
    ) -> str:
        """Generate personalized cover letter content using AI."""

        # Prepare data for AI
        personal = user_data.get('personalInfo', {})
        experiences = user_data.get('experiences', [])
        skills = user_data.get('skills', [])

        job_title = job_data.get('title', 'the position')
        company_name = job_data.get('company', 'your company')
        job_description = job_data.get('description', '')

        prompt = f"""Write a professional cover letter for the following job application:

Job Title: {job_title}
Company: {company_name}
Job Description: {job_description[:500]}

Applicant Information:
Name: {personal.get('fullName', 'the applicant')}
Skills: {', '.join(skills[:10])}
Recent Experience: {experiences[0].get('title', '') if experiences else 'N/A'} at {experiences[0].get('company', '') if experiences else 'N/A'}

Requirements:
1. Write a compelling opening paragraph that shows enthusiasm for the role
2. Highlight relevant skills and experiences that match the job requirements
3. Provide 2-3 specific examples of achievements that demonstrate value
4. Express genuine interest in the company and role
5. Include a strong closing paragraph with call to action
6. Keep it professional, confident, and concise (300-400 words)
7. Do NOT include address blocks or date (just the body content)

{f'Additional context to include: {custom_content}' if custom_content else ''}

Write ONLY the body paragraphs of the cover letter (no addresses, no date, no signature block):
"""

        try:
            response = self.gemini.generate_text(prompt)
            return response
        except Exception as e:
            # Fallback to template if AI fails
            return self._generate_template_cover_letter(user_data, job_data)

    def _generate_template_cover_letter(
        self,
        user_data: Dict,
        job_data: Dict
    ) -> str:
        """Generate a template-based cover letter as fallback."""
        personal = user_data.get('personalInfo', {})
        name = personal.get('fullName', 'the applicant')
        job_title = job_data.get('title', 'this position')
        company_name = job_data.get('company', 'your company')

        skills = user_data.get('skills', [])
        top_skills = ', '.join(skills[:5]) if skills else 'my diverse skill set'

        return f"""I am writing to express my strong interest in the {job_title} position at {company_name}. With my background in {top_skills}, I am excited about the opportunity to contribute to your team.

Throughout my career, I have developed a strong foundation in the skills required for this role. My experience has equipped me with the ability to tackle complex challenges and deliver results that drive business success. I am particularly drawn to {company_name} because of your commitment to excellence and innovation in the industry.

I am confident that my technical expertise and passion for continuous learning make me an ideal candidate for this position. I would welcome the opportunity to discuss how my skills and experiences align with your team's needs.

Thank you for considering my application. I look forward to the possibility of discussing this opportunity further."""

    def _create_cover_letter_pdf(
        self,
        user_data: Dict,
        job_data: Dict,
        content: str
    ) -> str:
        """Create cover letter in PDF format."""
        import tempfile

        temp_dir = tempfile.gettempdir()
        filename = f"cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(temp_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Header with contact info
        personal = user_data.get('personalInfo', {})
        name = personal.get('fullName', 'Your Name')

        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=11,
            alignment=0
        )

        story.append(Paragraph(name, header_style))
        if personal.get('email'):
            story.append(Paragraph(personal['email'], header_style))
        if personal.get('phone'):
            story.append(Paragraph(personal['phone'], header_style))

        story.append(Spacer(1, 0.3*inch))

        # Date
        today = datetime.now().strftime('%B %d, %Y')
        story.append(Paragraph(today, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        # Company info
        company_name = job_data.get('company', 'Hiring Manager')
        job_title = job_data.get('title', 'Position')

        story.append(Paragraph(f"Hiring Manager", styles['Normal']))
        story.append(Paragraph(company_name, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        # Salutation
        story.append(Paragraph(f"Dear Hiring Manager,", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))

        # Content paragraphs
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), styles['Normal']))
                story.append(Spacer(1, 0.1*inch))

        # Closing
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Sincerely,", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(name, styles['Normal']))

        doc.build(story)
        return filepath

    def _create_cover_letter_docx(
        self,
        user_data: Dict,
        job_data: Dict,
        content: str
    ) -> str:
        """Create cover letter in DOCX format."""
        import tempfile

        temp_dir = tempfile.gettempdir()
        filename = f"cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = os.path.join(temp_dir, filename)

        doc = Document()

        # Header with contact info
        personal = user_data.get('personalInfo', {})
        name = personal.get('fullName', 'Your Name')

        doc.add_paragraph(name)
        if personal.get('email'):
            doc.add_paragraph(personal['email'])
        if personal.get('phone'):
            doc.add_paragraph(personal['phone'])

        doc.add_paragraph()  # Blank line

        # Date
        today = datetime.now().strftime('%B %d, %Y')
        doc.add_paragraph(today)
        doc.add_paragraph()

        # Company info
        company_name = job_data.get('company', 'Hiring Manager')
        doc.add_paragraph('Hiring Manager')
        doc.add_paragraph(company_name)
        doc.add_paragraph()

        # Salutation
        doc.add_paragraph('Dear Hiring Manager,')
        doc.add_paragraph()

        # Content paragraphs
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                doc.add_paragraph(paragraph.strip())

        # Closing
        doc.add_paragraph()
        doc.add_paragraph('Sincerely,')
        doc.add_paragraph()
        doc.add_paragraph(name)

        doc.save(filepath)
        return filepath

    def _generate_classic_resume(self, user_data: Dict, format: str) -> str:
        """Generate classic style resume (similar to modern for now)."""
        return self._generate_modern_resume(user_data, format)

    def _generate_minimal_resume(self, user_data: Dict, format: str) -> str:
        """Generate minimal style resume (similar to modern for now)."""
        return self._generate_modern_resume(user_data, format)
