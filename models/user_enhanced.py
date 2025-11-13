"""Enhanced User model with comprehensive onboarding data."""
from datetime import datetime, timedelta
from bson import ObjectId
import bcrypt
from config.database import get_users_collection
from config.settings import Config
from utils.helpers import calculate_swipe_reset_date, should_reset_swipes


class EnhancedUser:
    """Enhanced user model with full career profile support."""

    @staticmethod
    def create_user(email, password, **kwargs):
        """
        Create a new user with comprehensive profile.

        Args:
            email: User email
            password: User password
            **kwargs: Additional user data from onboarding

        Returns:
            ObjectId: Created user ID
        """
        users = get_users_collection()

        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=Config.BCRYPT_LOG_ROUNDS)
        ).decode('utf-8')

        # Create comprehensive user document
        user_data = {
            # Authentication
            'email': email.lower(),
            'password_hash': password_hash,
            'oauth_providers': {
                'linkedin': kwargs.get('linkedin_data'),
                'google': None
            },

            # Basic Information
            'profile': {
                'firstName': kwargs.get('firstName', ''),
                'lastName': kwargs.get('lastName', ''),
                'phone': kwargs.get('phone', ''),
                'location': kwargs.get('location', {
                    'city': '',
                    'state': '',
                    'country': '',
                    'coordinates': []
                }),
                'profilePicture': kwargs.get('profilePicture'),
                'preferredContact': kwargs.get('preferredContact', 'email'),  # email/phone
            },

            # Professional Profile
            'professional': {
                'headline': kwargs.get('headline', ''),
                'summary': kwargs.get('summary', ''),
                'careerLevel': kwargs.get('careerLevel', 'mid'),  # entry/junior/mid/senior/executive/c-level
                'yearsOfExperience': kwargs.get('yearsOfExperience', 0),
                'currentEmploymentStatus': kwargs.get('currentEmploymentStatus', 'employed'),  # employed/unemployed/student/freelance
                'currentCompany': kwargs.get('currentCompany', ''),
                'currentRole': kwargs.get('currentRole', ''),
                'availability': kwargs.get('availability', 'flexible'),  # immediate/2weeks/1month/3months/flexible
            },

            # Work Experience (from resume + LinkedIn)
            'workExperience': kwargs.get('workExperience', []),
            # Each entry: {company, title, startDate, endDate, description, achievements, skills}

            # Education
            'education': kwargs.get('education', []),
            # Each entry: {institution, degree, field, startDate, endDate, gpa, achievements}

            # Skills with proficiency
            'skills': kwargs.get('skills', []),
            # Each entry: {name, category, proficiency: beginner/intermediate/advanced/expert, endorsements, source: manual/linkedin/parsed}

            # Certifications & Licenses
            'certifications': kwargs.get('certifications', []),
            # Each entry: {name, issuer, issueDate, expiryDate, credentialId, credentialUrl}

            # Languages
            'languages': kwargs.get('languages', []),
            # Each entry: {language, proficiency: basic/conversational/professional/native}

            # Projects & Publications
            'projects': kwargs.get('projects', []),
            'publications': kwargs.get('publications', []),

            # Awards & Honors
            'awards': kwargs.get('awards', []),

            # Job Preferences
            'jobPreferences': {
                'targetRoles': kwargs.get('targetRoles', []),  # List of desired job titles
                'industries': kwargs.get('industries', []),  # List of target industries
                'jobTypes': kwargs.get('jobTypes', []),  # full-time/part-time/contract/freelance/intern
                'workArrangement': kwargs.get('workArrangement', 'flexible'),  # remote/hybrid/onsite/flexible
                'willingToRelocate': kwargs.get('willingToRelocate', False),
                'needsVisaSponsorship': kwargs.get('needsVisaSponsorship', False),
                'desiredSalary': {
                    'min': kwargs.get('salaryMin', 0),
                    'max': kwargs.get('salaryMax', 0),
                    'currency': kwargs.get('salaryCurrency', 'USD'),
                    'type': kwargs.get('salaryType', 'annual')  # annual/monthly/hourly
                },
                'preferredLocations': kwargs.get('preferredLocations', []),
                # Each: {city, state, country, radius}
            },

            # Resume Data
            'resumes': {
                'original': kwargs.get('originalResume'),  # File path to uploaded resume
                'parsed': kwargs.get('parsedResume'),  # Structured parsed data
                'versions': [],  # List of tailored resume versions
                'defaultVersion': None
            },

            # Subscription & Limits
            'subscription': {
                'plan': kwargs.get('plan', 'free'),  # free/premium/enterprise
                'swipesUsed': 0,
                'swipeLimit': Config.FREE_SWIPE_LIMIT,
                'resetDate': calculate_swipe_reset_date(),
                'subscriptionStart': datetime.utcnow(),
                'subscriptionEnd': None,
                'features': {
                    'autoApply': False,  # True for paid users
                    'customResumes': False,
                    'aiCoverLetters': False,
                    'unlimitedSwipes': False,
                    'advancedAnalytics': False,
                    'prioritySupport': False
                }
            },

            # User Consent & Permissions
            'permissions': {
                'gmailAccess': kwargs.get('gmailAccess', False),
                'autoApplyEnabled': kwargs.get('autoApplyEnabled', False),
                'courseNotifications': kwargs.get('courseNotifications', True),
                'marketingEmails': kwargs.get('marketingEmails', False),
                'dataForMLTraining': kwargs.get('dataForMLTraining', True),
            },

            # Application Analytics
            'analytics': {
                'totalApplications': 0,
                'autoApplications': 0,
                'manualApplications': 0,
                'responsesReceived': 0,
                'interviewsScheduled': 0,
                'offersReceived': 0,
                'rejections': 0,
                'averageResponseTime': 0,  # in days
                'successRate': 0.0,  # percentage
            },

            # Skill Development
            'skillDevelopment': {
                'identifiedGaps': [],  # Skills user needs based on applications
                'enrolledCourses': [],  # {platform, courseId, title, enrolledDate, completionDate, status}
                'completedCourses': [],
                'recommendations': []  # Current course recommendations
            },

            # Timestamps & Status
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'lastLoginAt': datetime.utcnow(),
            'isActive': True,
            'emailVerified': False,
            'onboardingCompleted': kwargs.get('onboardingCompleted', False),
            'onboardingStep': kwargs.get('onboardingStep', 0),
        }

        result = users.insert_one(user_data)
        return result.inserted_id

    @staticmethod
    def update_linkedin_data(user_id, linkedin_data):
        """
        Merge LinkedIn OAuth data with user profile.

        Args:
            user_id: User ID
            linkedin_data: Data from LinkedIn API

        Returns:
            bool: Success status
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Extract LinkedIn data
        update_doc = {
            'oauth_providers.linkedin': linkedin_data,
            'profile.profilePicture': linkedin_data.get('pictureUrl'),
            'professional.headline': linkedin_data.get('headline'),
            'professional.currentCompany': linkedin_data.get('positions', {}).get('values', [{}])[0].get('company', {}).get('name'),
            'professional.currentRole': linkedin_data.get('positions', {}).get('values', [{}])[0].get('title'),
            'updatedAt': datetime.utcnow()
        }

        # Merge work experience
        if 'positions' in linkedin_data:
            work_exp = []
            for pos in linkedin_data['positions'].get('values', []):
                work_exp.append({
                    'company': pos.get('company', {}).get('name'),
                    'title': pos.get('title'),
                    'startDate': pos.get('startDate'),
                    'endDate': pos.get('endDate'),
                    'description': pos.get('summary', ''),
                    'source': 'linkedin'
                })
            update_doc['workExperience'] = work_exp

        # Merge skills
        if 'skills' in linkedin_data:
            skills = []
            for skill in linkedin_data['skills'].get('values', []):
                skills.append({
                    'name': skill.get('skill', {}).get('name'),
                    'endorsements': skill.get('endorsement', {}).get('count', 0),
                    'source': 'linkedin'
                })
            update_doc['skills'] = skills

        result = users.update_one(
            {'_id': user_id},
            {'$set': update_doc}
        )

        return result.modified_count > 0

    @staticmethod
    def update_onboarding_progress(user_id, step, data):
        """
        Update user onboarding step and data.

        Args:
            user_id: User ID
            step: Current onboarding step number
            data: Data collected in this step

        Returns:
            bool: Success status
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'onboardingStep': step,
                    **data,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @staticmethod
    def complete_onboarding(user_id):
        """Mark onboarding as completed."""
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'onboardingCompleted': True,
                    'onboardingStep': -1,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @staticmethod
    def get_skill_gaps(user_id):
        """
        Get identified skill gaps for user.

        Args:
            user_id: User ID

        Returns:
            list: Skill gaps with priority and frequency
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        user = users.find_one({'_id': user_id})
        if not user:
            return []

        return user.get('skillDevelopment', {}).get('identifiedGaps', [])

    @staticmethod
    def add_skill_gap(user_id, skill, priority='medium', frequency=1):
        """
        Add or update a skill gap.

        Args:
            user_id: User ID
            skill: Skill name
            priority: Priority level (low/medium/high)
            frequency: How often this skill appears in target jobs

        Returns:
            bool: Success status
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Check if skill gap already exists
        user = users.find_one({'_id': user_id})
        skill_gaps = user.get('skillDevelopment', {}).get('identifiedGaps', [])

        existing_gap = None
        for gap in skill_gaps:
            if gap['skill'].lower() == skill.lower():
                existing_gap = gap
                break

        if existing_gap:
            # Update frequency and priority
            existing_gap['frequency'] += frequency
            if priority == 'high' and existing_gap['priority'] != 'high':
                existing_gap['priority'] = priority
        else:
            # Add new skill gap
            skill_gaps.append({
                'skill': skill,
                'priority': priority,
                'frequency': frequency,
                'identifiedAt': datetime.utcnow()
            })

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'skillDevelopment.identifiedGaps': skill_gaps,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @staticmethod
    def update_analytics(user_id, metric, value):
        """
        Update user analytics metrics.

        Args:
            user_id: User ID
            metric: Metric name
            value: Metric value

        Returns:
            bool: Success status
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    f'analytics.{metric}': value,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @staticmethod
    def increment_analytics(user_id, metric):
        """Increment an analytics counter."""
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = users.update_one(
            {'_id': user_id},
            {
                '$inc': {f'analytics.{metric}': 1},
                '$set': {'updatedAt': datetime.utcnow()}
            }
        )

        return result.modified_count > 0

    @staticmethod
    def enable_feature(user_id, feature_name):
        """Enable a subscription feature for user."""
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    f'subscription.features.{feature_name}': True,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @staticmethod
    def has_feature(user_id, feature_name):
        """Check if user has access to a feature."""
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        user = users.find_one({'_id': user_id})
        if not user:
            return False

        return user.get('subscription', {}).get('features', {}).get(feature_name, False)

    @staticmethod
    def upgrade_to_paid(user_id):
        """
        Upgrade user to paid plan with all features.

        2-Tier System:
        - Paid: $8.99/month with unlimited swipes and auto-apply

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Paid plan features
        paid_features = {
            'autoApply': True,
            'customResumes': True,
            'aiCoverLetters': True,
            'unlimitedSwipes': True,
            'advancedAnalytics': False,
            'prioritySupport': False
        }

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'subscription.plan': 'paid',
                    'subscription.swipeLimit': Config.PAID_SWIPE_LIMIT,  # Unlimited
                    'subscription.features': paid_features,
                    'subscription.subscriptionEnd': datetime.utcnow() + timedelta(days=30),
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0
