"""Resume AI Service - Generation, Refinement, and Variations.

This service provides AI-powered resume operations:
1. Generation: Create professional resumes from user profile data
2. Refinement: Improve existing resumes with AI suggestions
3. Variations: Create multiple targeted versions for different job types

Uses multi-model Gemini AI with intelligent fallback.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from services.multi_model_ai import get_ai_service

logger = logging.getLogger(__name__)


class ResumeAIService:
    """AI-powered resume generation, refinement, and variation creation."""

    def __init__(self):
        """Initialize resume AI service."""
        self.ai = get_ai_service()

    def generate_resume(
        self,
        user_profile: Dict,
        job_target: Optional[Dict] = None,
        style: str = 'professional',
        format_type: str = 'modern'
    ) -> Dict:
        """
        Generate a complete resume from user profile data.

        Args:
            user_profile: User's profile data (skills, experience, education)
            job_target: Optional target job details to tailor the resume
            style: Resume style (professional, creative, technical, executive)
            format_type: Format type (modern, classic, minimal, bold)

        Returns:
            Dict containing generated resume data and metadata
        """
        logger.info(f"Generating {style} resume in {format_type} format")

        # Extract user information
        personal_info = self._extract_personal_info(user_profile)
        work_experience = user_profile.get('workExperience', [])
        education = user_profile.get('education', [])
        skills = user_profile.get('skills', [])
        certifications = user_profile.get('certifications', [])
        projects = user_profile.get('projects', [])

        # Build generation prompt
        prompt = self._build_generation_prompt(
            personal_info=personal_info,
            work_experience=work_experience,
            education=education,
            skills=skills,
            certifications=certifications,
            projects=projects,
            job_target=job_target,
            style=style,
            format_type=format_type
        )

        # Generate resume using AI
        resume_data, model_used = self.ai.generate_structured_json(
            prompt=prompt,
            task_type='generation',
            expected_keys=['personalInfo', 'summary', 'experience', 'education', 'skills']
        )

        # Add metadata
        resume_data['metadata'] = {
            'generatedAt': datetime.utcnow().isoformat(),
            'modelUsed': model_used,
            'style': style,
            'formatType': format_type,
            'targetJob': job_target.get('title') if job_target else None,
            'version': '1.0'
        }

        logger.info(f"Resume generated successfully using {model_used}")

        return resume_data

    def refine_resume(
        self,
        resume_data: Dict,
        refinement_goals: Optional[List[str]] = None,
        target_job: Optional[Dict] = None
    ) -> Dict:
        """
        Refine and improve an existing resume with AI suggestions.

        Args:
            resume_data: Existing resume data to refine
            refinement_goals: Specific goals (e.g., ['improve_impact', 'add_metrics', 'optimize_ats'])
            target_job: Optional job posting to tailor the resume towards

        Returns:
            Dict containing refined resume and improvement suggestions
        """
        logger.info(f"Refining resume with goals: {refinement_goals}")

        if refinement_goals is None:
            refinement_goals = [
                'improve_action_verbs',
                'quantify_achievements',
                'optimize_keywords',
                'enhance_readability',
                'ats_optimization'
            ]

        # Build refinement prompt
        prompt = self._build_refinement_prompt(
            resume_data=resume_data,
            refinement_goals=refinement_goals,
            target_job=target_job
        )

        # Refine using AI
        refined_data, model_used = self.ai.generate_structured_json(
            prompt=prompt,
            task_type='refinement',
            expected_keys=['refinedResume', 'improvements', 'suggestions']
        )

        # Add metadata
        refined_data['metadata'] = {
            'refinedAt': datetime.utcnow().isoformat(),
            'modelUsed': model_used,
            'refinementGoals': refinement_goals,
            'targetJob': target_job.get('title') if target_job else None,
            'originalVersion': resume_data.get('metadata', {}).get('version', 'unknown')
        }

        logger.info(f"Resume refined successfully using {model_used}")

        return refined_data

    def create_variations(
        self,
        base_resume: Dict,
        target_jobs: List[Dict],
        variations_count: int = 3
    ) -> List[Dict]:
        """
        Create multiple resume variations tailored for different job types.

        Args:
            base_resume: Base resume data to create variations from
            target_jobs: List of target job types/postings
            variations_count: Number of variations to create (default: 3)

        Returns:
            List of resume variations, each optimized for a specific job type
        """
        logger.info(f"Creating {variations_count} resume variations")

        variations = []

        # Limit to requested count or number of target jobs
        num_variations = min(variations_count, len(target_jobs)) if target_jobs else variations_count

        # If no specific jobs provided, create generic variations
        if not target_jobs:
            target_jobs = self._get_default_job_targets()

        for i in range(num_variations):
            target_job = target_jobs[i] if i < len(target_jobs) else target_jobs[0]

            logger.info(f"Creating variation {i + 1} for: {target_job.get('title', 'Generic')}")

            # Build variation prompt
            prompt = self._build_variation_prompt(
                base_resume=base_resume,
                target_job=target_job,
                variation_index=i
            )

            # Generate variation using AI
            try:
                variation_data, model_used = self.ai.generate_structured_json(
                    prompt=prompt,
                    task_type='variation',
                    expected_keys=['personalInfo', 'summary', 'experience', 'skills']
                )

                # Add metadata
                variation_data['metadata'] = {
                    'createdAt': datetime.utcnow().isoformat(),
                    'modelUsed': model_used,
                    'targetJob': target_job.get('title', 'Generic'),
                    'targetIndustry': target_job.get('industry', 'General'),
                    'variationIndex': i + 1,
                    'baseResumeVersion': base_resume.get('metadata', {}).get('version', 'unknown')
                }

                variations.append(variation_data)

            except Exception as e:
                logger.error(f"Failed to create variation {i + 1}: {str(e)}")
                # Continue with other variations

        logger.info(f"Successfully created {len(variations)} resume variations")

        return variations

    def analyze_resume(self, resume_data: Dict) -> Dict:
        """
        Analyze a resume and provide insights, scores, and recommendations.

        Args:
            resume_data: Resume data to analyze

        Returns:
            Dict containing analysis results, scores, and recommendations
        """
        logger.info("Analyzing resume")

        prompt = f"""Analyze the following resume and provide detailed feedback.

Resume Data:
{self._format_resume_for_prompt(resume_data)}

Please analyze the resume and provide:
1. Overall Score (0-100)
2. ATS Compatibility Score (0-100)
3. Impact Score (0-100)
4. Keyword Optimization (0-100)
5. Specific strengths (list)
6. Areas for improvement (list)
7. Missing elements (list)
8. Recommended additions (list)

Return your analysis as a JSON object with this structure:
{{
    "overallScore": 85,
    "scores": {{
        "atsCompatibility": 90,
        "impact": 80,
        "keywordOptimization": 85,
        "readability": 88,
        "completeness": 82
    }},
    "strengths": ["Strong action verbs", "Quantified achievements"],
    "improvements": ["Add more metrics", "Expand project descriptions"],
    "missingElements": ["Professional certifications section"],
    "recommendations": ["Include links to portfolio", "Add technical skills section"],
    "summary": "Overall, this is a strong resume with good structure..."
}}
"""

        analysis_data, model_used = self.ai.generate_structured_json(
            prompt=prompt,
            task_type='analysis',
            expected_keys=['overallScore', 'scores', 'strengths', 'improvements']
        )

        analysis_data['analyzedAt'] = datetime.utcnow().isoformat()
        analysis_data['modelUsed'] = model_used

        logger.info(f"Resume analyzed successfully using {model_used}")

        return analysis_data

    # ==================== Private Helper Methods ====================

    def _extract_personal_info(self, user_profile: Dict) -> Dict:
        """Extract personal information from user profile."""
        profile = user_profile.get('profile', {})

        return {
            'firstName': user_profile.get('firstName', ''),
            'lastName': user_profile.get('lastName', ''),
            'email': user_profile.get('email', ''),
            'phone': profile.get('phone', ''),
            'location': profile.get('location', {}),
            'linkedin': profile.get('linkedin', ''),
            'github': profile.get('github', ''),
            'portfolio': profile.get('portfolio', ''),
            'bio': profile.get('bio', ''),
            'jobTitle': profile.get('jobTitle', ''),
        }

    def _build_generation_prompt(
        self,
        personal_info: Dict,
        work_experience: List,
        education: List,
        skills: List,
        certifications: List,
        projects: List,
        job_target: Optional[Dict],
        style: str,
        format_type: str
    ) -> str:
        """Build comprehensive prompt for resume generation."""

        # Format skills
        skills_list = [s if isinstance(s, str) else s.get('name', '') for s in skills]

        prompt = f"""Generate a professional resume in JSON format based on the following information.

PERSONAL INFORMATION:
- Name: {personal_info.get('firstName', '')} {personal_info.get('lastName', '')}
- Email: {personal_info.get('email', '')}
- Phone: {personal_info.get('phone', '')}
- Location: {personal_info.get('location', {}).get('city', '')}, {personal_info.get('location', {}).get('country', '')}
- LinkedIn: {personal_info.get('linkedin', '')}
- GitHub: {personal_info.get('github', '')}
- Portfolio: {personal_info.get('portfolio', '')}
- Current Title: {personal_info.get('jobTitle', '')}

WORK EXPERIENCE:
{self._format_work_experience(work_experience)}

EDUCATION:
{self._format_education(education)}

SKILLS:
{', '.join(skills_list)}

CERTIFICATIONS:
{self._format_certifications(certifications)}

PROJECTS:
{self._format_projects(projects)}

"""

        if job_target:
            prompt += f"""
TARGET JOB:
- Title: {job_target.get('title', '')}
- Company: {job_target.get('company', '')}
- Description: {job_target.get('description', '')[:500]}
- Required Skills: {', '.join(job_target.get('skills', [])[:10])}

Please tailor the resume to match this job posting, emphasizing relevant experience and skills.
"""

        prompt += f"""
STYLE REQUIREMENTS:
- Style: {style} (professional, creative, technical, or executive)
- Format: {format_type} (modern, classic, minimal, or bold)

INSTRUCTIONS:
1. Create a compelling professional summary (3-4 sentences) that highlights key achievements and career goals
2. Format work experience with:
   - Strong action verbs (Led, Developed, Implemented, Optimized, etc.)
   - Quantified achievements with metrics (%, $, #)
   - Focus on impact and results, not just duties
   - Include relevant technologies and skills used
3. Organize skills into categories (Technical, Soft Skills, Tools, Languages)
4. Ensure ATS-friendly formatting with clear section headers
5. Optimize for keywords from the target job (if provided)
6. Keep bullet points concise (1-2 lines max)
7. Highlight most relevant and recent experience

Return the resume as a JSON object with this exact structure:
{{
    "personalInfo": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "+1234567890",
        "location": {{"city": "City", "state": "State", "country": "Country"}},
        "linkedin": "linkedin.com/in/username",
        "github": "github.com/username",
        "portfolio": "portfolio.com",
        "title": "Professional Title"
    }},
    "summary": "Compelling professional summary highlighting key achievements and career goals...",
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "location": "City, State",
            "startDate": "Jan 2020",
            "endDate": "Present",
            "current": true,
            "achievements": [
                "Led cross-functional team of 8 engineers to deliver product 2 months ahead of schedule",
                "Increased system performance by 45% through optimization of database queries",
                "Reduced deployment time by 60% by implementing CI/CD pipeline"
            ],
            "technologies": ["Python", "AWS", "Docker", "Kubernetes"]
        }}
    ],
    "education": [
        {{
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University Name",
            "location": "City, State",
            "graduationDate": "May 2019",
            "gpa": "3.8/4.0",
            "honors": ["Magna Cum Laude", "Dean's List"],
            "relevantCoursework": ["Data Structures", "Machine Learning"]
        }}
    ],
    "skills": {{
        "technical": ["Python", "JavaScript", "AWS", "Docker"],
        "frameworks": ["React", "Django", "Node.js"],
        "tools": ["Git", "JIRA", "Jenkins"],
        "soft": ["Leadership", "Communication", "Problem Solving"],
        "languages": ["English (Native)", "Spanish (Professional)"]
    }},
    "certifications": [
        {{
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "date": "Jan 2023",
            "credentialId": "ABC123",
            "url": "aws.amazon.com/verification/ABC123"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Built scalable microservices architecture serving 1M+ users",
            "technologies": ["Python", "Docker", "AWS"],
            "url": "github.com/username/project",
            "impact": "Reduced infrastructure costs by 40%"
        }}
    ]
}}

Important: Return ONLY the JSON object, no additional text or explanation.
"""

        return prompt

    def _build_refinement_prompt(
        self,
        resume_data: Dict,
        refinement_goals: List[str],
        target_job: Optional[Dict]
    ) -> str:
        """Build prompt for resume refinement."""

        prompt = f"""Refine and improve the following resume based on these goals: {', '.join(refinement_goals)}

CURRENT RESUME:
{self._format_resume_for_prompt(resume_data)}

"""

        if target_job:
            prompt += f"""
TARGET JOB:
- Title: {target_job.get('title', '')}
- Company: {target_job.get('company', '')}
- Description: {target_job.get('description', '')[:500]}
- Required Skills: {', '.join(target_job.get('skills', [])[:10])}

Please optimize the resume to match this job posting.
"""

        prompt += f"""
REFINEMENT GOALS EXPLAINED:
- improve_action_verbs: Replace weak verbs with strong, impactful action verbs
- quantify_achievements: Add metrics and numbers to demonstrate impact
- optimize_keywords: Include industry-relevant keywords for ATS systems
- enhance_readability: Improve clarity and flow of content
- ats_optimization: Ensure format is ATS-friendly with clear sections

REFINEMENT REQUIREMENTS:
1. Enhance bullet points with stronger action verbs (Led, Spearheaded, Architected, etc.)
2. Quantify achievements wherever possible (percentages, dollar amounts, team sizes)
3. Add relevant keywords from the target job description (if provided)
4. Improve phrasing for clarity and impact
5. Reorganize content to highlight most relevant experience
6. Remove redundancy and wordiness
7. Ensure consistent formatting and structure

Return your refinement as a JSON object:
{{
    "refinedResume": {{
        // Complete refined resume in same structure as original
        "personalInfo": {{}},
        "summary": "...",
        "experience": [],
        "education": [],
        "skills": {{}},
        "certifications": [],
        "projects": []
    }},
    "improvements": [
        {{
            "section": "experience",
            "itemIndex": 0,
            "field": "achievements[0]",
            "original": "Worked on database optimization",
            "improved": "Optimized database queries, reducing response time by 45% and improving system throughput by 2000 requests/sec",
            "reason": "Added quantifiable metrics and specific impact"
        }}
    ],
    "suggestions": [
        "Consider adding leadership metrics to management roles",
        "Include more technical details about architecture decisions",
        "Add links to GitHub projects for technical roles"
    ],
    "atsScore": 85,
    "impactScore": 78,
    "keywordMatch": 72
}}

Important: Return ONLY the JSON object.
"""

        return prompt

    def _build_variation_prompt(
        self,
        base_resume: Dict,
        target_job: Dict,
        variation_index: int
    ) -> str:
        """Build prompt for creating resume variation."""

        prompt = f"""Create a tailored resume variation optimized for this specific job posting.

BASE RESUME:
{self._format_resume_for_prompt(base_resume)}

TARGET JOB (Variation #{variation_index + 1}):
- Title: {target_job.get('title', 'Professional Role')}
- Company: {target_job.get('company', 'Target Company')}
- Industry: {target_job.get('industry', 'General')}
- Description: {target_job.get('description', '')[:500]}
- Required Skills: {', '.join(target_job.get('skills', [])[:15])}
- Responsibilities: {', '.join(target_job.get('responsibilities', [])[:5])}

VARIATION REQUIREMENTS:
1. Rewrite the professional summary to align with this specific role and company
2. Reorder and emphasize experience most relevant to this position
3. Adjust bullet points to highlight skills mentioned in the job description
4. Reorganize skills section to prioritize required/preferred skills
5. Add or emphasize projects related to this role
6. Incorporate keywords from the job description naturally
7. Maintain truthfulness - only emphasize, don't fabricate

IMPORTANT:
- Keep all factual information accurate (dates, companies, degrees, etc.)
- Only reorder, rewrite, and re-emphasize existing experience
- Focus on different aspects of the same experiences that match this role
- Ensure the resume still represents the candidate authentically

Return the tailored resume variation as a JSON object:
{{
    "personalInfo": {{
        "name": "...",
        "email": "...",
        "phone": "...",
        "location": {{}},
        "linkedin": "...",
        "github": "...",
        "title": "Title tailored to target role"
    }},
    "summary": "Professional summary specifically tailored to this role and company...",
    "experience": [
        // Same experiences, but reordered and rewritten to emphasize relevance
    ],
    "education": [],
    "skills": {{
        // Reorganized to prioritize skills mentioned in job description
    }},
    "certifications": [],
    "projects": [
        // Emphasize projects most relevant to this role
    ],
    "tailoringNotes": {{
        "matchedSkills": ["Python", "AWS", "Leadership"],
        "emphasizedExperience": ["Led cloud migration project", "Managed team of 5"],
        "keywordOptimization": 85,
        "relevanceScore": 92
    }}
}}

Important: Return ONLY the JSON object.
"""

        return prompt

    def _format_resume_for_prompt(self, resume_data: Dict) -> str:
        """Format resume data as readable text for prompts."""
        lines = []

        # Personal Info
        if 'personalInfo' in resume_data:
            info = resume_data['personalInfo']
            lines.append(f"Name: {info.get('name', '')}")
            lines.append(f"Title: {info.get('title', '')}")
            lines.append(f"Email: {info.get('email', '')}")
            lines.append(f"Location: {info.get('location', {})}")

        # Summary
        if 'summary' in resume_data:
            lines.append(f"\nSUMMARY:\n{resume_data['summary']}")

        # Experience
        if 'experience' in resume_data:
            lines.append("\nEXPERIENCE:")
            for exp in resume_data['experience']:
                lines.append(f"\n{exp.get('title', '')} at {exp.get('company', '')}")
                lines.append(f"{exp.get('startDate', '')} - {exp.get('endDate', '')}")
                for achievement in exp.get('achievements', []):
                    lines.append(f"  • {achievement}")

        # Education
        if 'education' in resume_data:
            lines.append("\nEDUCATION:")
            for edu in resume_data['education']:
                lines.append(f"{edu.get('degree', '')} - {edu.get('institution', '')}")

        # Skills
        if 'skills' in resume_data:
            lines.append(f"\nSKILLS: {resume_data['skills']}")

        return '\n'.join(lines)

    def _format_work_experience(self, work_experience: List) -> str:
        """Format work experience for prompt."""
        if not work_experience:
            return "No work experience provided"

        lines = []
        for exp in work_experience:
            title = exp.get('title', 'Position')
            company = exp.get('company', 'Company')
            start = exp.get('startDate', '')
            end = exp.get('endDate', 'Present')
            description = exp.get('description', '')
            achievements = exp.get('achievements', [])

            lines.append(f"- {title} at {company} ({start} - {end})")
            if description:
                lines.append(f"  Description: {description}")
            if achievements:
                lines.append("  Achievements:")
                for achievement in achievements:
                    lines.append(f"    • {achievement}")

        return '\n'.join(lines)

    def _format_education(self, education: List) -> str:
        """Format education for prompt."""
        if not education:
            return "No education provided"

        lines = []
        for edu in education:
            degree = edu.get('degree', 'Degree')
            institution = edu.get('institution', 'Institution')
            grad_date = edu.get('graduationDate', '')
            gpa = edu.get('gpa', '')

            lines.append(f"- {degree} from {institution} ({grad_date})")
            if gpa:
                lines.append(f"  GPA: {gpa}")

        return '\n'.join(lines)

    def _format_certifications(self, certifications: List) -> str:
        """Format certifications for prompt."""
        if not certifications:
            return "No certifications provided"

        # Handle both string and dict formats
        cert_list = []
        for cert in certifications:
            if isinstance(cert, str):
                cert_list.append(cert)
            elif isinstance(cert, dict):
                name = cert.get('name', '')
                issuer = cert.get('issuer', '')
                cert_list.append(f"{name} ({issuer})" if issuer else name)

        return '\n'.join([f"- {c}" for c in cert_list])

    def _format_projects(self, projects: List) -> str:
        """Format projects for prompt."""
        if not projects:
            return "No projects provided"

        lines = []
        for proj in projects:
            name = proj.get('name', 'Project')
            description = proj.get('description', '')
            technologies = proj.get('technologies', [])

            lines.append(f"- {name}")
            if description:
                lines.append(f"  {description}")
            if technologies:
                lines.append(f"  Technologies: {', '.join(technologies)}")

        return '\n'.join(lines)

    def _get_default_job_targets(self) -> List[Dict]:
        """Get default job targets for variations when none provided."""
        return [
            {
                'title': 'Senior Software Engineer',
                'industry': 'Technology',
                'skills': ['Python', 'JavaScript', 'AWS', 'Docker', 'Kubernetes'],
                'description': 'Looking for a senior engineer to lead technical initiatives'
            },
            {
                'title': 'Technical Lead',
                'industry': 'Technology',
                'skills': ['Leadership', 'Architecture', 'Mentoring', 'Agile', 'Cloud'],
                'description': 'Lead technical team and drive architectural decisions'
            },
            {
                'title': 'Full Stack Developer',
                'industry': 'Technology',
                'skills': ['React', 'Node.js', 'MongoDB', 'REST API', 'Git'],
                'description': 'Develop full-stack web applications with modern technologies'
            }
        ]


# Global singleton instance
_resume_ai_instance = None


def get_resume_ai_service() -> ResumeAIService:
    """Get or create the global resume AI service instance."""
    global _resume_ai_instance
    if _resume_ai_instance is None:
        _resume_ai_instance = ResumeAIService()
    return _resume_ai_instance
