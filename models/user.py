"""User model and operations."""
from datetime import datetime, timedelta
from bson import ObjectId
import bcrypt
from config.database import get_users_collection
from config.settings import Config
from utils.helpers import calculate_swipe_reset_date, should_reset_swipes


class User:
    """User model with database operations."""

    @staticmethod
    def create_user(email, password, first_name=None, last_name=None):
        """
        Create a new user.

        Args:
            email: User email
            password: User password (plain text)
            first_name: User's first name
            last_name: User's last name

        Returns:
            ObjectId: Created user ID
        """
        users = get_users_collection()

        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=Config.BCRYPT_LOG_ROUNDS)
        ).decode('utf-8')

        # Create user document
        user_data = {
            'email': email.lower(),
            'password_hash': password_hash,
            'profile': {
                'firstName': first_name or '',
                'lastName': last_name or '',
                'phone': '',
                'location': {},
                'profilePicture': None,
                'resume': None,
                'skills': [],
                'experience': '',
                'expectedSalary': {
                    'min': 0,
                    'max': 0
                }
            },
            'preferences': {
                'jobTypes': [],
                'industries': [],
                'roleLevels': [],
                'remoteOnly': False
            },
            'subscription': {
                'plan': 'free',
                'swipesUsed': 0,
                'swipeLimit': Config.FREE_SWIPE_LIMIT,
                'resetDate': calculate_swipe_reset_date(),
                'subscriptionStart': datetime.utcnow(),
                'subscriptionEnd': None
            },
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'isActive': True,
            'emailVerified': False
        }

        result = users.insert_one(user_data)
        return result.inserted_id

    @staticmethod
    def find_by_email(email):
        """
        Find user by email.

        Args:
            email: User email

        Returns:
            dict: User document or None
        """
        users = get_users_collection()
        return users.find_one({'email': email.lower()})

    @staticmethod
    def find_by_id(user_id):
        """
        Find user by ID.

        Args:
            user_id: User ID (string or ObjectId)

        Returns:
            dict: User document or None
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        return users.find_one({'_id': user_id})

    @staticmethod
    def verify_password(plain_password, password_hash):
        """
        Verify password against hash.

        Args:
            plain_password: Plain text password
            password_hash: Hashed password

        Returns:
            bool: True if password matches
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            password_hash.encode('utf-8')
        )

    @staticmethod
    def update_profile(user_id, profile_data):
        """
        Update user profile.

        Args:
            user_id: User ID
            profile_data: Profile data to update

        Returns:
            bool: True if successful
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Build update document
        update_doc = {}
        allowed_fields = [
            'firstName', 'lastName', 'phone', 'location',
            'skills', 'experience', 'expectedSalary'
        ]

        for field in allowed_fields:
            if field in profile_data:
                update_doc[f'profile.{field}'] = profile_data[field]

        if update_doc:
            update_doc['updatedAt'] = datetime.utcnow()
            result = users.update_one(
                {'_id': user_id},
                {'$set': update_doc}
            )
            return result.modified_count > 0

        return False

    @staticmethod
    def update_preferences(user_id, preferences_data):
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences_data: Preferences data to update

        Returns:
            bool: True if successful
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Build update document
        update_doc = {}
        allowed_fields = ['jobTypes', 'industries', 'roleLevels', 'remoteOnly']

        for field in allowed_fields:
            if field in preferences_data:
                update_doc[f'preferences.{field}'] = preferences_data[field]

        if update_doc:
            update_doc['updatedAt'] = datetime.utcnow()
            result = users.update_one(
                {'_id': user_id},
                {'$set': update_doc}
            )
            return result.modified_count > 0

        return False

    @staticmethod
    def update_profile_picture(user_id, file_path):
        """
        Update user profile picture.

        Args:
            user_id: User ID
            file_path: Path to profile picture

        Returns:
            bool: True if successful
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'profile.profilePicture': file_path,
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    @staticmethod
    def update_resume(user_id, file_path):
        """
        Update user resume.

        Args:
            user_id: User ID
            file_path: Path to resume

        Returns:
            bool: True if successful
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'profile.resume': file_path,
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    @staticmethod
    def increment_swipes(user_id):
        """
        Increment user swipe count and reset if needed.

        Args:
            user_id: User ID

        Returns:
            tuple: (success, swipes_remaining)
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Get current user data
        user = users.find_one({'_id': user_id})
        if not user:
            return False, 0

        subscription = user.get('subscription', {})
        reset_date = subscription.get('resetDate')

        # Check if we need to reset swipes
        if should_reset_swipes(reset_date):
            users.update_one(
                {'_id': user_id},
                {
                    '$set': {
                        'subscription.swipesUsed': 1,
                        'subscription.resetDate': calculate_swipe_reset_date(),
                        'updatedAt': datetime.utcnow()
                    }
                }
            )
            swipes_remaining = subscription.get('swipeLimit', Config.FREE_SWIPE_LIMIT) - 1
        else:
            # Increment swipes
            swipes_used = subscription.get('swipesUsed', 0)
            swipe_limit = subscription.get('swipeLimit', Config.FREE_SWIPE_LIMIT)

            if swipe_limit != -1 and swipes_used >= swipe_limit:
                return False, 0

            users.update_one(
                {'_id': user_id},
                {
                    '$inc': {'subscription.swipesUsed': 1},
                    '$set': {'updatedAt': datetime.utcnow()}
                }
            )
            swipes_remaining = swipe_limit - (swipes_used + 1) if swipe_limit != -1 else -1

        return True, swipes_remaining

    @staticmethod
    def get_swipe_status(user_id):
        """
        Get user's current swipe status.

        Args:
            user_id: User ID

        Returns:
            dict: Swipe status info
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        user = users.find_one({'_id': user_id})
        if not user:
            return None

        subscription = user.get('subscription', {})

        # Check if reset is needed
        if should_reset_swipes(subscription.get('resetDate')):
            swipes_used = 0
            reset_date = calculate_swipe_reset_date()
        else:
            swipes_used = subscription.get('swipesUsed', 0)
            reset_date = subscription.get('resetDate')

        swipe_limit = subscription.get('swipeLimit', Config.FREE_SWIPE_LIMIT)
        swipes_remaining = swipe_limit - swipes_used if swipe_limit != -1 else -1

        return {
            'swipesUsed': swipes_used,
            'swipeLimit': swipe_limit,
            'swipesRemaining': swipes_remaining,
            'resetDate': reset_date,
            'plan': subscription.get('plan', 'free')
        }

    @staticmethod
    def upgrade_subscription(user_id, plan):
        """
        Upgrade user subscription plan.

        2-Tier System:
        - Free: 50 swipes/day, manual apply
        - Paid: Unlimited swipes, auto-apply ($8.99/month)

        Args:
            user_id: User ID
            plan: New plan ('free' or 'paid')

        Returns:
            bool: True if successful
        """
        users = get_users_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Determine swipe limit based on plan (2-tier system)
        swipe_limits = {
            'free': Config.FREE_SWIPE_LIMIT,
            'paid': Config.PAID_SWIPE_LIMIT  # Unlimited (-1)
        }

        swipe_limit = swipe_limits.get(plan, Config.FREE_SWIPE_LIMIT)
        subscription_end = None

        # Paid plan gets 30-day subscription
        if plan == 'paid':
            subscription_end = datetime.utcnow() + timedelta(days=30)

        result = users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'subscription.plan': plan,
                    'subscription.swipeLimit': swipe_limit,
                    'subscription.subscriptionEnd': subscription_end,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0
