"""Gemini AI service for generating cover letters and customized resumes."""
import os
import google.generativeai as genai
from datetime import datetime
import json


class GeminiService:
    """AI-powered content generation using Google Gemini with fallback models."""

    # List of models to try in order (newest to oldest)
    MODELS = [
        'gemini-2.0-flash-exp',      # Latest experimental
        'gemini-1.5-flash',           # Stable fast model
        'gemini-1.5-flash-8b',        # Smaller fast model
        'gemini-1.5-pro',             # High quality model
        'gemini-1.0-pro',             # Legacy stable model
    ]

    def __init__(self):
        """Initialize Gemini API with fallback model support."""
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY or GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Try to initialize Gemini models with fallback support."""
        import logging
        logger = logging.getLogger(__name__)

        for model_name in self.MODELS:
            try:
                logger.info(f"Trying to initialize model: {model_name}")
                model = genai.GenerativeModel(model_name)

                # Test the model with a simple request
                test_response = model.generate_content("Hello")
                if test_response.text:
                    logger.info(f"✅ Successfully initialized model: {model_name}")
                    return model

            except Exception as e:
                logger.warning(f"❌ Failed to initialize {model_name}: {str(e)}")
                continue

        # If all models fail, raise error
        raise ValueError(f"Failed to initialize any Gemini model. Tried: {', '.join(self.MODELS)}")

    def generate_cover_letter(self, job_data, user_profile):
        """
        Generate a personalized cover letter for a job application.

        Args:
            job_data: Job posting details (title, company, description, requirements)
            user_profile: User's profile data (experience, skills, education)

        Returns:
            dict: Generated cover letter with metadata
        """
        try:
            prompt = self._build_cover_letter_prompt(job_data, user_profile)
            response = self.model.generate_content(prompt)

            cover_letter = response.text.strip()

            return {
                'success': True,
                'coverLetter': cover_letter,
                'generatedAt': datetime.utcnow(),
                'jobId': job_data.get('id'),
                'metadata': {
                    'jobTitle': job_data.get('title'),
                    'company': job_data.get('company', {}).get('name'),
                    'wordCount': len(cover_letter.split()),
                    'model': 'gemini-pro'
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate cover letter: {str(e)}'
            }

    def _build_cover_letter_prompt(self, job_data, user_profile):
        """Build the prompt for cover letter generation."""

        # Extract user info
        user_name = f"{user_profile.get('profile', {}).get('firstName', '')} {user_profile.get('profile', {}).get('lastName', '')}".strip()
        user_experience = user_profile.get('workExperience', [])
        user_skills = [skill.get('name', '') for skill in user_profile.get('skills', [])]
        user_education = user_profile.get('education', [])

        # Extract job info
        job_title = job_data.get('title', '')
        company_name = job_data.get('company', {}).get('name', '')
        job_description = job_data.get('description', '')
        requirements = job_data.get('requirements', [])

        # Build comprehensive prompt
        prompt = f"""
You are an expert career advisor and cover letter writer. Generate a compelling, personalized cover letter for the following job application.

JOB DETAILS:
- Position: {job_title}
- Company: {company_name}
- Job Description: {job_description}
- Key Requirements: {', '.join(requirements) if requirements else 'See description'}

CANDIDATE PROFILE:
- Name: {user_name}
- Current Role: {user_experience[0].get('title') if user_experience else 'N/A'}
- Current Company: {user_experience[0].get('company') if user_experience else 'N/A'}
- Key Skills: {', '.join(user_skills[:10])}
- Education: {user_education[0].get('degree') + ' in ' + user_education[0].get('field') if user_education else 'N/A'}

INSTRUCTIONS:
1. Write a professional, engaging cover letter (300-400 words)
2. Start with a strong opening that shows enthusiasm for the role
3. Highlight 2-3 relevant experiences that match the job requirements
4. Demonstrate knowledge of the company (use general industry knowledge)
5. Explain why you're a great fit for this specific role
6. Include specific examples of achievements when possible
7. Close with a call to action
8. Use confident, active language
9. Avoid clichés and generic phrases
10. Make it ATS-friendly (use keywords from job description)
11. Maintain a professional yet personable tone
12. Use proper business letter format

IMPORTANT:
- DO NOT include the sender's or recipient's address (email systems will add that)
- DO NOT include date (will be added automatically)
- Start directly with "Dear Hiring Manager," or "Dear [Company] Team,"
- Be specific and unique - avoid generic phrases like "hard-working team player"
- Quantify achievements where possible (e.g., "increased sales by 30%")
- Show genuine interest in the company and role
- End with a professional closing like "Sincerely," followed by the candidate's name

Generate the cover letter now:
"""

        return prompt

    def customize_resume_content(self, job_data, user_profile, original_resume):
        """
        Generate customized resume content tailored to a specific job.

        Args:
            job_data: Job posting details
            user_profile: User's profile data
            original_resume: User's base resume data

        Returns:
            dict: Customized resume content
        """
        try:
            prompt = self._build_resume_customization_prompt(job_data, user_profile, original_resume)
            response = self.model.generate_content(prompt)

            result_text = response.text.strip()

            # Clean up markdown if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            customized_data = json.loads(result_text.strip())

            return {
                'success': True,
                'customizedResume': customized_data,
                'generatedAt': datetime.utcnow(),
                'jobId': job_data.get('id'),
                'metadata': {
                    'jobTitle': job_data.get('title'),
                    'company': job_data.get('company', {}).get('name'),
                    'model': 'gemini-pro'
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to customize resume: {str(e)}'
            }

    def _build_resume_customization_prompt(self, job_data, user_profile, original_resume):
        """Build the prompt for resume customization."""

        job_title = job_data.get('title', '')
        job_description = job_data.get('description', '')
        requirements = job_data.get('requirements', [])

        prompt = f"""
You are an expert resume writer and career coach. Customize the following resume to be highly relevant for this specific job posting.

JOB POSTING:
- Title: {job_title}
- Description: {job_description}
- Requirements: {', '.join(requirements)}

CURRENT RESUME DATA:
{json.dumps(original_resume, indent=2)}

TASK:
Optimize this resume for the target job by:

1. PROFESSIONAL SUMMARY:
   - Rewrite summary to emphasize relevant experience for THIS role
   - Include keywords from job description
   - Keep it to 3-4 powerful sentences

2. WORK EXPERIENCE:
   - Reorder or emphasize bullet points that match job requirements
   - Rephrase achievements to align with job description language
   - Add quantifiable metrics where possible
   - Ensure relevant experience is prominently featured

3. SKILLS:
   - Reorder skills to put most relevant ones first
   - Match skill names to those used in job posting
   - Group related skills effectively

4. KEYWORDS:
   - Identify and incorporate key phrases from job description
   - Ensure ATS compatibility
   - Natural integration of keywords

IMPORTANT:
- DO NOT fabricate experience or skills
- DO NOT change dates or factual information
- DO change phrasing, emphasis, and order to highlight relevance
- Keep the same basic structure and truthfulness
- Focus on relevance and keyword optimization

Return ONLY a JSON object with the customized resume data in this structure:
{{
    "summary": "Customized professional summary",
    "workExperience": [...],  // Reordered and optimized
    "skills": [...],  // Reordered by relevance
    "education": [...],  // Keep mostly same
    "keywords": ["keyword1", "keyword2"],  // Key terms from job posting
    "matchScore": 0.85  // Estimated match score (0.0-1.0)
}}
"""

        return prompt

    def analyze_skill_match(self, job_data, user_skills):
        """
        Analyze how well user's skills match job requirements.

        Args:
            job_data: Job posting data
            user_skills: List of user's skills

        Returns:
            dict: Match analysis with missing skills and recommendations
        """
        try:
            prompt = self._build_skill_analysis_prompt(job_data, user_skills)
            response = self.model.generate_content(prompt)

            result_text = response.text.strip()

            # Clean up markdown
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            analysis = json.loads(result_text.strip())

            return {
                'success': True,
                'analysis': analysis,
                'analyzedAt': datetime.utcnow()
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to analyze skill match: {str(e)}'
            }

    def _build_skill_analysis_prompt(self, job_data, user_skills):
        """Build the prompt for skill match analysis."""

        job_title = job_data.get('title', '')
        requirements = job_data.get('requirements', [])
        description = job_data.get('description', '')

        user_skill_names = [skill.get('name', '') if isinstance(skill, dict) else skill for skill in user_skills]

        prompt = f"""
You are an expert career analyst. Analyze the skill match between the candidate and job requirements.

JOB REQUIREMENTS:
- Title: {job_title}
- Requirements: {', '.join(requirements)}
- Description: {description}

CANDIDATE'S SKILLS:
{', '.join(user_skill_names)}

TASK:
Perform a comprehensive skill gap analysis.

Return ONLY a JSON object with this structure:
{{
    "matchScore": 0.75,  // Overall match (0.0-1.0)
    "matchingSkills": ["skill1", "skill2"],  // Skills candidate has that job requires
    "missingSkills": [
        {{
            "skill": "Skill Name",
            "priority": "high",  // high/medium/low
            "category": "technical",  // technical/soft/domain
            "reason": "Why this skill is important for the role"
        }}
    ],
    "transferableSkills": ["skill1", "skill2"],  // Candidate's skills that are valuable but not exact matches
    "recommendations": [
        "Short, actionable recommendation 1",
        "Short, actionable recommendation 2"
    ],
    "overallAssessment": "Brief assessment of candidate's fit for this role"
}}
"""

        return prompt

    def generate_interview_prep(self, job_data, user_profile):
        """
        Generate interview preparation materials.

        Args:
            job_data: Job posting details
            user_profile: User's profile

        Returns:
            dict: Interview questions and suggested answers
        """
        try:
            prompt = f"""
You are an interview coach. Generate interview preparation materials for this job:

Job Title: {job_data.get('title')}
Company: {job_data.get('company', {}).get('name')}
Description: {job_data.get('description')}

Candidate Background:
- Current Role: {user_profile.get('professional', {}).get('currentRole')}
- Experience: {user_profile.get('professional', {}).get('yearsOfExperience')} years

Generate:
1. 5 likely interview questions for this role
2. Suggested answer framework for each (not full answers, just key points)
3. 3 questions the candidate should ask the interviewer
4. Key achievements to emphasize

Return as JSON:
{{
    "likelyQuestions": [
        {{"question": "...", "answerFramework": ["point 1", "point 2"]}}
    ],
    "questionsToAsk": ["question 1", "question 2", "question 3"],
    "achievementsToHighlight": ["achievement 1", "achievement 2"],
    "preparationTips": ["tip 1", "tip 2"]
}}
"""

            response = self.model.generate_content(prompt)
            result = response.text.strip()

            # Clean up markdown
            if result.startswith('```json'):
                result = result[7:]
            if result.startswith('```'):
                result = result[3:]
            if result.endswith('```'):
                result = result[:-3]

            prep_data = json.loads(result.strip())

            return {
                'success': True,
                'interviewPrep': prep_data,
                'generatedAt': datetime.utcnow()
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate interview prep: {str(e)}'
            }

    def optimize_for_ats(self, resume_content):
        """
        Optimize resume content for Applicant Tracking Systems.

        Args:
            resume_content: Resume text or structured data

        Returns:
            dict: ATS optimization suggestions
        """
        try:
            prompt = f"""
You are an ATS (Applicant Tracking System) expert. Analyze this resume and provide optimization suggestions.

Resume Content:
{json.dumps(resume_content, indent=2) if isinstance(resume_content, dict) else resume_content}

Analyze for:
1. Keyword density
2. Format compatibility
3. Section headers
4. Contact information placement
5. File format recommendations
6. Common ATS parsing issues

Return JSON:
{{
    "atsScore": 0.85,  // 0.0-1.0
    "issues": [
        {{"issue": "Problem description", "severity": "high/medium/low", "fix": "How to fix"}}
    ],
    "recommendations": ["recommendation 1", "recommendation 2"],
    "formatSuggestions": ["suggestion 1", "suggestion 2"]
}}
"""

            response = self.model.generate_content(prompt)
            result = response.text.strip()

            # Clean markdown
            if result.startswith('```json'):
                result = result[7:]
            if result.startswith('```'):
                result = result[3:]
            if result.endswith('```'):
                result = result[:-3]

            analysis = json.loads(result.strip())

            return {
                'success': True,
                'atsAnalysis': analysis,
                'analyzedAt': datetime.utcnow()
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to analyze ATS compatibility: {str(e)}'
            }
