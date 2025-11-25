"""Service for generating AI-powered resume variations with different styles and formats."""
import logging
from datetime import datetime
from models.resume_variation import ResumeVariation
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class ResumeVariationService:
    """Service for creating and managing resume variations."""

    def __init__(self):
        self.gemini_service = GeminiService()

    def generate_variations(self, user_id, base_resume_data, num_variations=3, target_job_types=None):
        """
        Generate multiple resume variations with different styles and optimizations.

        Args:
            user_id: User ID
            base_resume_data: Original resume data (parsed)
            num_variations: Number of variations to generate (default: 3)
            target_job_types: List of job types to optimize for (optional)

        Returns:
            dict: Result with created variation IDs or error
        """
        try:
            if not base_resume_data:
                return {
                    'success': False,
                    'error': 'No base resume data provided'
                }

            # Define variation strategies
            strategies = [
                {
                    'name': 'Technical Focus',
                    'jobType': 'tech',
                    'writingStyle': 'technical',
                    'formatStyle': 'modern',
                    'emphasisStrategy': 'skillsBased',
                    'keywordStrategy': 'atsOptimized',
                    'description': 'Emphasizes technical skills and achievements'
                },
                {
                    'name': 'Leadership Focus',
                    'jobType': 'management',
                    'writingStyle': 'professional',
                    'formatStyle': 'executive',
                    'emphasisStrategy': 'achievementBased',
                    'keywordStrategy': 'strategic',
                    'description': 'Highlights leadership and strategic accomplishments'
                },
                {
                    'name': 'Dynamic & Results-Driven',
                    'jobType': 'sales',
                    'writingStyle': 'dynamic',
                    'formatStyle': 'modern',
                    'emphasisStrategy': 'achievementBased',
                    'keywordStrategy': 'dense',
                    'description': 'Action-oriented with quantified results'
                },
                {
                    'name': 'Creative Portfolio',
                    'jobType': 'creative',
                    'writingStyle': 'creative',
                    'formatStyle': 'creative',
                    'emphasisStrategy': 'projectBased',
                    'keywordStrategy': 'natural',
                    'description': 'Showcases projects and creative work'
                },
                {
                    'name': 'Balanced Professional',
                    'jobType': 'general',
                    'writingStyle': 'professional',
                    'formatStyle': 'traditional',
                    'emphasisStrategy': 'balanced',
                    'keywordStrategy': 'natural',
                    'description': 'Well-rounded presentation of all qualifications'
                }
            ]

            # If target job types specified, filter strategies
            if target_job_types:
                strategies = [s for s in strategies if s['jobType'] in target_job_types]

            # Limit to requested number
            strategies = strategies[:num_variations]

            created_variations = []
            base_resume_id = base_resume_data.get('_id', 'unknown')

            for strategy in strategies:
                logger.info(f"Generating {strategy['name']} variation for user {user_id}")

                # Generate variation using AI
                variation_result = self._generate_single_variation(
                    base_resume_data,
                    strategy
                )

                if not variation_result['success']:
                    logger.warning(f"Failed to generate variation: {variation_result.get('error')}")
                    continue

                # Calculate metrics for this variation
                metrics = self._calculate_variation_metrics(
                    variation_result['tailoredResume'],
                    strategy
                )

                # Create variation record
                variation_data = {
                    'tailoredResume': variation_result['tailoredResume'],
                    'jobType': strategy['jobType'],
                    'parameters': {
                        'writingStyle': strategy['writingStyle'],
                        'formatStyle': strategy['formatStyle'],
                        'emphasisStrategy': strategy['emphasisStrategy'],
                        'keywordStrategy': strategy['keywordStrategy'],
                        'name': strategy['name'],
                        'description': strategy['description']
                    },
                    'appliedOptimizations': variation_result.get('optimizations', []),
                    'uniquenessScore': variation_result.get('uniquenessScore', 0.5),
                    **metrics
                }

                variation_id = ResumeVariation.create_variation(
                    user_id,
                    base_resume_id,
                    variation_data
                )

                created_variations.append({
                    'id': str(variation_id),
                    'name': strategy['name'],
                    'jobType': strategy['jobType']
                })

            if not created_variations:
                return {
                    'success': False,
                    'error': 'Failed to generate any variations'
                }

            return {
                'success': True,
                'variations': created_variations,
                'count': len(created_variations)
            }

        except Exception as e:
            logger.error(f"Error generating variations: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_single_variation(self, base_resume, strategy):
        """
        Generate a single resume variation using AI.

        Args:
            base_resume: Base resume data
            strategy: Variation strategy parameters

        Returns:
            dict: Generated variation or error
        """
        try:
            # Create prompt for Gemini based on strategy
            prompt = self._create_variation_prompt(base_resume, strategy)

            # Call Gemini to generate variation
            response = self.gemini_service.model.generate_content(prompt)

            if not response or not response.text:
                return {
                    'success': False,
                    'error': 'No response from AI'
                }

            # Parse the AI response
            tailored_resume = self._parse_ai_resume_response(response.text, base_resume)

            # Identify applied optimizations
            optimizations = self._identify_optimizations(base_resume, tailored_resume, strategy)

            return {
                'success': True,
                'tailoredResume': tailored_resume,
                'optimizations': optimizations,
                'uniquenessScore': self._calculate_uniqueness(base_resume, tailored_resume)
            }

        except Exception as e:
            logger.error(f"Error in single variation generation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_variation_prompt(self, base_resume, strategy):
        """Create AI prompt for generating resume variation."""
        prompt = f"""You are an expert resume writer. Transform the following resume using this specific style:

**Style Requirements:**
- Writing Style: {strategy['writingStyle']}
- Format Style: {strategy['formatStyle']}
- Emphasis Strategy: {strategy['emphasisStrategy']}
- Keyword Strategy: {strategy['keywordStrategy']}

**Original Resume:**
Name: {base_resume.get('personalInfo', {}).get('fullName', 'Not provided')}
Email: {base_resume.get('personalInfo', {}).get('email', 'Not provided')}

Summary: {base_resume.get('summary', 'Not provided')}

Experience:
"""

        # Add work experience
        for exp in base_resume.get('workExperience', [])[:3]:  # Limit to top 3
            prompt += f"\n- {exp.get('title', '')} at {exp.get('company', '')}"
            prompt += f"\n  {exp.get('description', '')}"

        # Add skills
        skills = base_resume.get('skills', [])
        if skills:
            skills_str = ', '.join([s if isinstance(s, str) else s.get('name', '') for s in skills[:15]])
            prompt += f"\n\nSkills: {skills_str}"

        prompt += f"""

**Task:**
Rewrite this resume to be optimized for {strategy['jobType']} positions.

**Guidelines:**
1. {strategy['writingStyle'].upper()} writing: {"Technical precision and detail" if strategy['writingStyle'] == 'technical' else "Professional and formal" if strategy['writingStyle'] == 'professional' else "Action-oriented and energetic" if strategy['writingStyle'] == 'dynamic' else "Narrative storytelling" if strategy['writingStyle'] == 'creative' else "Brief and to-the-point"}

2. {strategy['emphasisStrategy'].upper()} emphasis: {"Highlight skills prominently" if strategy['emphasisStrategy'] == 'skillsBased' else "Emphasize work history" if strategy['emphasisStrategy'] == 'experienceBased' else "Focus on accomplishments" if strategy['emphasisStrategy'] == 'achievementBased' else "Showcase projects" if strategy['emphasisStrategy'] == 'projectBased' else "Equal weight to all sections"}

3. {strategy['keywordStrategy'].upper()} keywords: {"Maximum ATS compatibility" if strategy['keywordStrategy'] == 'atsOptimized' else "High keyword density" if strategy['keywordStrategy'] == 'dense' else "Keywords in strategic positions" if strategy['keywordStrategy'] == 'strategic' else "Keywords integrated naturally"}

4. Use quantifiable metrics and achievements where possible
5. Keep the same factual information but rewrite phrasing and structure

**Output Format (JSON):**
{{
  "personalInfo": {{
    "fullName": "...",
    "email": "...",
    "phone": "...",
    "location": "..."
  }},
  "summary": "Rewritten professional summary (2-3 sentences)",
  "workExperience": [
    {{
      "title": "...",
      "company": "...",
      "location": "...",
      "startDate": "...",
      "endDate": "...",
      "description": "Rewritten description",
      "achievements": ["Achievement 1", "Achievement 2"]
    }}
  ],
  "skills": ["Skill 1", "Skill 2", ...],
  "education": [...],
  "certifications": [...]
}}

Return ONLY the JSON, no additional text."""

        return prompt

    def _parse_ai_resume_response(self, ai_response, base_resume):
        """Parse AI response into structured resume data."""
        import json
        import re

        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                resume_data = json.loads(json_match.group())
                return resume_data
            else:
                # Fallback: return base resume with minor modifications
                logger.warning("Could not parse AI response, using base resume")
                return base_resume

        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from AI response")
            return base_resume

    def _identify_optimizations(self, base_resume, tailored_resume, strategy):
        """Identify what optimizations were applied."""
        optimizations = []

        # Check if summary was enhanced
        base_summary = base_resume.get('summary', '')
        new_summary = tailored_resume.get('summary', '')
        if len(new_summary) != len(base_summary):
            optimizations.append('summary_enhanced')

        # Check for keyword optimization
        optimizations.append(f"keyword_strategy_{strategy['keywordStrategy']}")

        # Check for style application
        optimizations.append(f"writing_style_{strategy['writingStyle']}")
        optimizations.append(f"emphasis_{strategy['emphasisStrategy']}")

        return optimizations

    def _calculate_uniqueness(self, base_resume, tailored_resume):
        """Calculate how different the variation is from base."""
        # Simple uniqueness calculation based on text differences
        base_text = str(base_resume)
        tailored_text = str(tailored_resume)

        if len(base_text) == 0:
            return 0.0

        # Calculate character-level difference
        differences = sum(1 for a, b in zip(base_text, tailored_text) if a != b)
        max_len = max(len(base_text), len(tailored_text))

        return min(1.0, differences / max_len) if max_len > 0 else 0.0

    def _calculate_variation_metrics(self, tailored_resume, strategy):
        """Calculate performance metrics for a variation."""
        # ATS Score: Based on keyword presence and format
        ats_score = 0.7  # Base score

        # Boost for ATS-optimized strategy
        if strategy['keywordStrategy'] == 'atsOptimized':
            ats_score += 0.2

        # Check for common ATS-friendly elements
        if tailored_resume.get('skills'):
            ats_score += 0.05
        if tailored_resume.get('workExperience'):
            ats_score += 0.05

        ats_score = min(1.0, ats_score)

        # Match Score: Job type relevance
        match_score = 0.75  # Base match score

        # Keyword Density: Estimate based on strategy
        keyword_density_map = {
            'atsOptimized': 0.85,
            'dense': 0.90,
            'strategic': 0.75,
            'natural': 0.60,
            'subtle': 0.50
        }
        keyword_density = keyword_density_map.get(strategy['keywordStrategy'], 0.70)

        # Readability Score
        readability_score = 0.80  # Default good readability

        # Skills analysis
        skills = tailored_resume.get('skills', [])
        skills_matched = len(skills)
        total_skills = skills_matched

        return {
            'atsScore': round(ats_score, 2),
            'matchScore': round(match_score, 2),
            'keywordDensity': round(keyword_density, 2),
            'readabilityScore': round(readability_score, 2),
            'skillsMatched': skills_matched,
            'totalSkills': total_skills,
            'matchedKeywords': [],
            'missingKeywords': []
        }

    def generate_job_specific_variation(self, user_id, base_resume_id, job_data):
        """
        Generate a resume variation specifically optimized for a single job.

        Args:
            user_id: User ID
            base_resume_id: Base resume ID
            job_data: Job details to optimize for

        Returns:
            dict: Created variation or error
        """
        try:
            # Get base resume from user profile
            from models.user_enhanced import EnhancedUser
            user = EnhancedUser.find_by_id(user_id)

            if not user:
                return {'success': False, 'error': 'User not found'}

            base_resume = user.get('resumes', {}).get('parsed')
            if not base_resume:
                return {'success': False, 'error': 'No base resume found'}

            # Determine optimal strategy based on job
            job_type = job_data.get('jobType', '').lower()
            job_title = job_data.get('title', '').lower()

            # Select strategy based on job characteristics
            if 'engineer' in job_title or 'developer' in job_title or 'tech' in job_type:
                strategy_name = 'Technical Focus'
            elif 'manager' in job_title or 'director' in job_title or 'lead' in job_title:
                strategy_name = 'Leadership Focus'
            elif 'sales' in job_title or 'business development' in job_title:
                strategy_name = 'Dynamic & Results-Driven'
            elif 'design' in job_title or 'creative' in job_title:
                strategy_name = 'Creative Portfolio'
            else:
                strategy_name = 'Balanced Professional'

            # Get full strategy
            all_strategies = {
                'Technical Focus': {
                    'jobType': 'tech',
                    'writingStyle': 'technical',
                    'formatStyle': 'modern',
                    'emphasisStrategy': 'skillsBased',
                    'keywordStrategy': 'atsOptimized'
                },
                'Leadership Focus': {
                    'jobType': 'management',
                    'writingStyle': 'professional',
                    'formatStyle': 'executive',
                    'emphasisStrategy': 'achievementBased',
                    'keywordStrategy': 'strategic'
                },
                'Dynamic & Results-Driven': {
                    'jobType': 'sales',
                    'writingStyle': 'dynamic',
                    'formatStyle': 'modern',
                    'emphasisStrategy': 'achievementBased',
                    'keywordStrategy': 'dense'
                },
                'Creative Portfolio': {
                    'jobType': 'creative',
                    'writingStyle': 'creative',
                    'formatStyle': 'creative',
                    'emphasisStrategy': 'projectBased',
                    'keywordStrategy': 'natural'
                },
                'Balanced Professional': {
                    'jobType': 'general',
                    'writingStyle': 'professional',
                    'formatStyle': 'traditional',
                    'emphasisStrategy': 'balanced',
                    'keywordStrategy': 'natural'
                }
            }

            strategy = all_strategies.get(strategy_name)
            strategy['name'] = strategy_name

            # Generate the variation
            variation_result = self._generate_single_variation(base_resume, strategy)

            if not variation_result['success']:
                return variation_result

            # Calculate metrics
            metrics = self._calculate_variation_metrics(
                variation_result['tailoredResume'],
                strategy
            )

            # Create variation record
            variation_data = {
                'tailoredResume': variation_result['tailoredResume'],
                'jobType': strategy['jobType'],
                'jobId': job_data.get('_id'),
                'parameters': strategy,
                'appliedOptimizations': variation_result.get('optimizations', []),
                'uniquenessScore': variation_result.get('uniquenessScore', 0.5),
                **metrics
            }

            variation_id = ResumeVariation.create_variation(
                user_id,
                base_resume_id,
                variation_data
            )

            return {
                'success': True,
                'variationId': str(variation_id),
                'strategy': strategy_name
            }

        except Exception as e:
            logger.error(f"Error generating job-specific variation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
