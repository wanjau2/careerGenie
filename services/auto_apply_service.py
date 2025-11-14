"""Automatic job application service for paid users."""
from datetime import datetime
from models.swipe import Application
from models.user_enhanced import EnhancedUser
from models.user import User
from services.gemini_service import GeminiService
import logging

logger = logging.getLogger(__name__)


class AutoApplyService:
    """Service for automatically applying to jobs when paid users swipe right."""

    def __init__(self):
        self.gemini_service = GeminiService()

    def apply_to_job_automatically(self, user_id, job_id, job_data, user_profile=None):
        """
        Automatically apply to a job when a paid user swipes right.

        This includes:
        1. Generating an AI-powered cover letter
        2. Customizing the resume for this specific job
        3. Creating an application record
        4. Updating user analytics

        Args:
            user_id: User ID
            job_id: Job ID
            job_data: Job details dictionary
            user_profile: Optional user profile (if already fetched)

        Returns:
            dict: Result with success status and details
        """
        try:
            # Get user profile if not provided
            if not user_profile:
                user_profile = User.find_by_id(user_id)
                if not user_profile:
                    return {
                        'success': False,
                        'error': 'User profile not found'
                    }

            # Get user's selected resume from preferences
            # The resume is set in the filter modal
            selected_resume = self._get_selected_resume(user_profile)

            if not selected_resume:
                logger.warning(f"No resume found for user {user_id}. Applying without custom resume.")

            # Step 1: Generate AI cover letter
            logger.info(f"Generating cover letter for user {user_id} and job {job_id}")
            cover_letter_result = self._generate_cover_letter(job_data, user_profile)

            if not cover_letter_result['success']:
                # Continue with application even if cover letter fails
                logger.warning(f"Cover letter generation failed: {cover_letter_result.get('error')}")
                cover_letter = None
            else:
                cover_letter = cover_letter_result.get('coverLetter')

            # Step 2: Customize resume for this job
            logger.info(f"Customizing resume for user {user_id} and job {job_id}")
            resume_result = self._customize_resume(job_data, user_profile, selected_resume)

            if not resume_result['success']:
                logger.warning(f"Resume customization failed: {resume_result.get('error')}")
                customized_resume = None
            else:
                customized_resume = resume_result.get('customizedResume')

            # Step 3: Create application data
            application_data = {
                'coverLetter': cover_letter,
                'customizedResume': customized_resume,
                'originalResume': selected_resume,
                'autoApplied': True,
                'appliedVia': 'swipe',
                'aiGenerated': {
                    'coverLetter': cover_letter is not None,
                    'resumeCustomized': customized_resume is not None
                },
                'submittedAt': datetime.utcnow()
            }

            # Step 4: Create application record
            logger.info(f"Creating application record for user {user_id} and job {job_id}")
            app_id = Application.create_application(
                user_id,
                job_id,
                application_data
            )

            # Step 5: Update user analytics
            try:
                EnhancedUser.increment_analytics(user_id, 'autoApplications')
                EnhancedUser.increment_analytics(user_id, 'totalApplications')
            except Exception as e:
                logger.error(f"Failed to update analytics for user {user_id}: {str(e)}")
                # Don't fail the entire application if analytics update fails

            # Step 6: Track skill gaps (for learning recommendations)
            self._track_skill_gaps(user_id, job_data, user_profile)

            logger.info(f"Successfully auto-applied to job {job_id} for user {user_id}")

            return {
                'success': True,
                'applicationId': str(app_id),
                'coverLetterGenerated': cover_letter is not None,
                'resumeCustomized': customized_resume is not None,
                'appliedAt': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Auto-apply failed for user {user_id} and job {job_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_selected_resume(self, user_profile):
        """
        Get the user's selected resume from their preferences.
        The resume selection is stored in user preferences (set in filter modal).

        Args:
            user_profile: User profile dictionary

        Returns:
            str or dict: Resume data or file path
        """
        # Check if user has enhanced profile with resumes
        if 'resumes' in user_profile:
            resumes = user_profile['resumes']

            # Check for default/selected version
            default_version = resumes.get('defaultVersion')
            if default_version:
                return default_version

            # Fall back to parsed resume
            if resumes.get('parsed'):
                return resumes['parsed']

            # Fall back to original uploaded resume
            if resumes.get('original'):
                return resumes['original']

        # Check basic profile for resume
        if 'profile' in user_profile:
            profile = user_profile['profile']
            if profile.get('resume'):
                return profile['resume']

        return None

    def _generate_cover_letter(self, job_data, user_profile):
        """
        Generate AI-powered cover letter using Gemini.

        Args:
            job_data: Job details
            user_profile: User profile

        Returns:
            dict: Result with cover letter or error
        """
        try:
            result = self.gemini_service.generate_cover_letter(job_data, user_profile)
            return result
        except Exception as e:
            logger.error(f"Failed to generate cover letter: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _customize_resume(self, job_data, user_profile, original_resume):
        """
        Customize resume for specific job using Gemini AI.

        Args:
            job_data: Job details
            user_profile: User profile
            original_resume: Original resume data

        Returns:
            dict: Result with customized resume or error
        """
        if not original_resume:
            return {
                'success': False,
                'error': 'No resume available to customize'
            }

        try:
            result = self.gemini_service.customize_resume_content(
                job_data,
                user_profile,
                original_resume
            )
            return result
        except Exception as e:
            logger.error(f"Failed to customize resume: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _track_skill_gaps(self, user_id, job_data, user_profile):
        """
        Track skill gaps based on job requirements vs user skills.
        This helps with course recommendations later.

        Args:
            user_id: User ID
            job_data: Job details
            user_profile: User profile
        """
        try:
            # Get job requirements/skills
            job_requirements = job_data.get('requirements', [])
            if isinstance(job_requirements, str):
                # If requirements is a string, split it
                job_requirements = [req.strip() for req in job_requirements.split(',')]

            # Get user's current skills from profile or top-level
            user_skills = []

            # Check profile.skills first (from onboarding)
            profile = user_profile.get('profile', {})
            if profile.get('skills'):
                skills_data = profile['skills']
                user_skills = [
                    skill.get('name', skill) if isinstance(skill, dict) else skill
                    for skill in skills_data
                ]
            # Fallback to top-level skills (legacy)
            elif 'skills' in user_profile:
                user_skills = [
                    skill.get('name', skill) if isinstance(skill, dict) else skill
                    for skill in user_profile.get('skills', [])
                ]

            # Find missing skills (simplified - could be enhanced with NLP)
            for requirement in job_requirements:
                requirement_lower = requirement.lower()

                # Check if user has this skill
                has_skill = any(
                    skill.lower() in requirement_lower or requirement_lower in skill.lower()
                    for skill in user_skills
                )

                if not has_skill:
                    # Add as skill gap (with medium priority by default)
                    try:
                        EnhancedUser.add_skill_gap(
                            user_id,
                            skill=requirement,
                            priority='medium',
                            frequency=1
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add skill gap: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to track skill gaps: {str(e)}")
            # Don't fail the application process if skill tracking fails

    def can_auto_apply(self, user_id):
        """
        Check if a user has auto-apply feature enabled.
        Only paid users have this feature.

        Args:
            user_id: User ID

        Returns:
            bool: True if user can auto-apply
        """
        try:
            user = User.find_by_id(user_id)
            if not user:
                return False

            subscription = user.get('subscription', {})
            plan = subscription.get('plan', 'free')

            # Only paid users can auto-apply
            return plan == 'paid'

        except Exception as e:
            logger.error(f"Error checking auto-apply eligibility: {str(e)}")
            return False

    def get_auto_apply_stats(self, user_id):
        """
        Get auto-apply statistics for a user.

        Args:
            user_id: User ID

        Returns:
            dict: Auto-apply statistics
        """
        try:
            # Get user analytics
            user = User.find_by_id(user_id)
            if not user:
                return {
                    'totalAutoApplications': 0,
                    'successRate': 0.0
                }

            analytics = user.get('analytics', {})

            return {
                'totalAutoApplications': analytics.get('autoApplications', 0),
                'totalApplications': analytics.get('totalApplications', 0),
                'responsesReceived': analytics.get('responsesReceived', 0),
                'interviewsScheduled': analytics.get('interviewsScheduled', 0),
                'offersReceived': analytics.get('offersReceived', 0),
                'rejections': analytics.get('rejections', 0),
                'successRate': analytics.get('successRate', 0.0)
            }

        except Exception as e:
            logger.error(f"Error fetching auto-apply stats: {str(e)}")
            return {
                'totalAutoApplications': 0,
                'successRate': 0.0
            }
