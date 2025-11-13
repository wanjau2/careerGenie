"""Swipe tracking model and operations."""
from datetime import datetime
from bson import ObjectId
from config.database import get_swipes_collection, get_applications_collection


class Swipe:
    """Swipe history model with database operations."""

    @staticmethod
    def record_swipe(user_id, job_id, action, match_score=None):
        """
        Record a user's swipe action on a job.

        Args:
            user_id: User ID
            job_id: Job ID
            action: Swipe action ('like', 'dislike', 'superlike')
            match_score: Optional match score

        Returns:
            ObjectId: Created swipe record ID
        """
        swipes = get_swipes_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        swipe_data = {
            'userId': user_id,
            'jobId': job_id,
            'action': action,
            'timestamp': datetime.utcnow(),
            'matchScore': match_score
        }

        # Use upsert to avoid duplicate swipes
        result = swipes.update_one(
            {'userId': user_id, 'jobId': job_id},
            {'$set': swipe_data},
            upsert=True
        )

        return result.upserted_id if result.upserted_id else True

    @staticmethod
    def get_user_swipes(user_id, action=None, skip=0, limit=20):
        """
        Get user's swipe history.

        Args:
            user_id: User ID
            action: Optional filter by action type
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            list: List of swipe documents
        """
        swipes = get_swipes_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        query = {'userId': user_id}
        if action:
            query['action'] = action

        cursor = swipes.find(query).sort('timestamp', -1).skip(skip).limit(limit)
        return list(cursor)

    @staticmethod
    def get_swiped_job_ids(user_id):
        """
        Get all job IDs that user has swiped on.

        Args:
            user_id: User ID

        Returns:
            list: List of job IDs
        """
        swipes = get_swipes_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Get all swipes for this user
        cursor = swipes.find({'userId': user_id}, {'jobId': 1})

        return [swipe['jobId'] for swipe in cursor]

    @staticmethod
    def get_liked_jobs(user_id, skip=0, limit=20):
        """
        Get jobs that user has liked.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            list: List of job IDs
        """
        swipes = get_swipes_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        cursor = swipes.find(
            {'userId': user_id, 'action': {'$in': ['like', 'superlike']}}
        ).sort('timestamp', -1).skip(skip).limit(limit)

        return [swipe['jobId'] for swipe in cursor]

    @staticmethod
    def has_swiped(user_id, job_id):
        """
        Check if user has already swiped on a job.

        Args:
            user_id: User ID
            job_id: Job ID

        Returns:
            bool: True if already swiped
        """
        swipes = get_swipes_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        return swipes.count_documents({'userId': user_id, 'jobId': job_id}) > 0

    @staticmethod
    def get_swipe_count(user_id, action=None):
        """
        Get count of user's swipes.

        Args:
            user_id: User ID
            action: Optional filter by action type

        Returns:
            int: Swipe count
        """
        swipes = get_swipes_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        query = {'userId': user_id}
        if action:
            query['action'] = action

        return swipes.count_documents(query)

    @staticmethod
    def get_statistics(user_id):
        """
        Get user's swipe statistics.

        Args:
            user_id: User ID

        Returns:
            dict: Swipe statistics
        """
        swipes = get_swipes_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Get total swipes by action
        total_swipes = swipes.count_documents({'userId': user_id})
        likes = swipes.count_documents({'userId': user_id, 'action': 'like'})
        superlikes = swipes.count_documents({'userId': user_id, 'action': 'superlike'})
        dislikes = swipes.count_documents({'userId': user_id, 'action': 'dislike'})

        # Calculate average match score
        pipeline = [
            {'$match': {'userId': user_id, 'matchScore': {'$exists': True}}},
            {'$group': {
                '_id': None,
                'avgMatchScore': {'$avg': '$matchScore'}
            }}
        ]

        avg_result = list(swipes.aggregate(pipeline))
        avg_match_score = avg_result[0]['avgMatchScore'] if avg_result else 0

        return {
            'totalSwipes': total_swipes,
            'likes': likes,
            'superlikes': superlikes,
            'dislikes': dislikes,
            'likeRate': round((likes + superlikes) / total_swipes, 2) if total_swipes > 0 else 0,
            'averageMatchScore': round(avg_match_score, 2) if avg_match_score else 0
        }


class Application:
    """Job application model with database operations."""

    @staticmethod
    def create_application(user_id, job_id, application_data=None):
        """
        Create a job application.

        Args:
            user_id: User ID
            job_id: Job ID
            application_data: Optional application data (cover letter, etc.)

        Returns:
            ObjectId: Created application ID
        """
        applications = get_applications_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        app_data = {
            'userId': user_id,
            'jobId': job_id,
            'status': 'applied',
            'appliedAt': datetime.utcnow(),
            'applicationData': application_data or {},
            'timeline': [
                {
                    'status': 'applied',
                    'timestamp': datetime.utcnow(),
                    'note': 'Application submitted'
                }
            ]
        }

        result = applications.insert_one(app_data)
        return result.inserted_id

    @staticmethod
    def get_user_applications(user_id, status=None, skip=0, limit=20):
        """
        Get user's job applications.

        Args:
            user_id: User ID
            status: Optional filter by status
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            list: List of application documents
        """
        applications = get_applications_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        query = {'userId': user_id}
        if status:
            query['status'] = status

        cursor = applications.find(query).sort('appliedAt', -1).skip(skip).limit(limit)
        return list(cursor)

    @staticmethod
    def update_application_status(application_id, status, note=None):
        """
        Update application status.

        Args:
            application_id: Application ID
            status: New status
            note: Optional note

        Returns:
            bool: True if successful
        """
        applications = get_applications_collection()

        if isinstance(application_id, str):
            application_id = ObjectId(application_id)

        timeline_entry = {
            'status': status,
            'timestamp': datetime.utcnow(),
            'note': note or f'Status changed to {status}'
        }

        result = applications.update_one(
            {'_id': application_id},
            {
                '$set': {'status': status},
                '$push': {'timeline': timeline_entry}
            }
        )

        return result.modified_count > 0
