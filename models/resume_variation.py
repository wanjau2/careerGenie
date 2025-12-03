"""Resume variation model for storing and managing multiple resume versions."""
from datetime import datetime
from bson import ObjectId
from config.database import get_database


class ResumeVariation:
    """Model for resume variations with AI-generated optimizations."""

    @staticmethod
    def get_variations_collection():
        """Get the resume variations collection."""
        db = get_database()
        return db.resume_variations

    @staticmethod
    def create_variation(user_id, base_resume_id, variation_data):
        """
        Create a new resume variation.

        Args:
            user_id: User ID
            base_resume_id: ID of the base/original resume
            variation_data: Variation details including:
                - tailored_resume: The customized resume content
                - job_type: Job type this variation is optimized for (optional)
                - job_id: Specific job this was created for (optional)
                - parameters: Variation parameters (writing style, format, etc.)
                - metrics: Performance metrics (ATS score, match score, etc.)

        Returns:
            ObjectId: Created variation ID
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        if isinstance(base_resume_id, str):
            base_resume_id = ObjectId(base_resume_id)

        # Calculate uniqueness score (how different from base resume)
        uniqueness_score = variation_data.get('uniquenessScore', 0.5)

        variation_doc = {
            'userId': user_id,
            'baseResumeId': base_resume_id,
            'jobType': variation_data.get('jobType'),  # e.g., 'remote', 'fulltime', 'tech'
            'jobId': ObjectId(variation_data['jobId']) if variation_data.get('jobId') else None,
            'tailoredResume': variation_data.get('tailoredResume', {}),
            'parameters': variation_data.get('parameters', {}),
            'metrics': {
                'atsScore': variation_data.get('atsScore', 0.0),
                'matchScore': variation_data.get('matchScore', 0.0),
                'keywordDensity': variation_data.get('keywordDensity', 0.0),
                'readabilityScore': variation_data.get('readabilityScore', 0.0),
                'skillsMatched': variation_data.get('skillsMatched', 0),
                'totalSkills': variation_data.get('totalSkills', 0),
                'matchedKeywords': variation_data.get('matchedKeywords', []),
                'missingKeywords': variation_data.get('missingKeywords', []),
            },
            'appliedOptimizations': variation_data.get('appliedOptimizations', []),
            'uniquenessScore': uniqueness_score,
            'status': 'generated',  # generated, applied, successful, rejected
            'timesUsed': 0,
            'successRate': 0.0,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
        }

        result = variations.insert_one(variation_doc)
        return result.inserted_id

    @staticmethod
    def get_user_variations(user_id, job_type=None, status=None):
        """
        Get all resume variations for a user.

        Args:
            user_id: User ID
            job_type: Optional filter by job type
            status: Optional filter by status

        Returns:
            list: List of variation documents
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        query = {'userId': user_id}

        if job_type:
            query['jobType'] = job_type

        if status:
            query['status'] = status

        return list(variations.find(query).sort('createdAt', -1))

    @staticmethod
    def get_variation_by_id(variation_id):
        """
        Get a specific variation by ID.

        Args:
            variation_id: Variation ID

        Returns:
            dict: Variation document or None
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(variation_id, str):
            variation_id = ObjectId(variation_id)

        return variations.find_one({'_id': variation_id})

    @staticmethod
    def find_best_variation_for_job(user_id, job_data):
        """
        Find the best matching variation for a specific job using AI scoring.

        Args:
            user_id: User ID
            job_data: Job details to match against

        Returns:
            dict: Best matching variation or None
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Get all user variations
        user_variations = list(variations.find({'userId': user_id, 'status': 'generated'}))

        if not user_variations:
            return None

        # Score each variation based on job match
        job_type = job_data.get('jobType') or job_data.get('employmentType', '').lower()
        job_title = job_data.get('title', '').lower()
        job_description = job_data.get('description', '').lower()

        best_variation = None
        best_score = 0.0

        for variation in user_variations:
            score = 0.0

            # Match job type (high weight)
            if variation.get('jobType') == job_type:
                score += 0.4

            # Metrics-based scoring
            metrics = variation.get('metrics', {})
            score += metrics.get('atsScore', 0.0) * 0.3
            score += metrics.get('matchScore', 0.0) * 0.2

            # Success rate bonus
            score += variation.get('successRate', 0.0) * 0.1

            if score > best_score:
                best_score = score
                best_variation = variation

        return best_variation

    @staticmethod
    def update_variation_metrics(variation_id, metrics_update):
        """
        Update metrics for a variation.

        Args:
            variation_id: Variation ID
            metrics_update: Dictionary of metrics to update

        Returns:
            bool: True if successful
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(variation_id, str):
            variation_id = ObjectId(variation_id)

        update_doc = {
            '$set': {
                f'metrics.{key}': value for key, value in metrics_update.items()
            }
        }
        update_doc['$set']['updatedAt'] = datetime.utcnow()

        result = variations.update_one({'_id': variation_id}, update_doc)
        return result.modified_count > 0

    @staticmethod
    def increment_usage(variation_id, successful=False):
        """
        Increment usage count and update success rate.

        Args:
            variation_id: Variation ID
            successful: Whether the application was successful

        Returns:
            bool: True if successful
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(variation_id, str):
            variation_id = ObjectId(variation_id)

        # Get current variation
        variation = variations.find_one({'_id': variation_id})
        if not variation:
            return False

        times_used = variation.get('timesUsed', 0) + 1
        successes = variation.get('successes', 0)

        if successful:
            successes += 1

        success_rate = (successes / times_used) if times_used > 0 else 0.0

        result = variations.update_one(
            {'_id': variation_id},
            {
                '$set': {
                    'timesUsed': times_used,
                    'successes': successes,
                    'successRate': success_rate,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @staticmethod
    def delete_variation(variation_id, user_id):
        """
        Delete a resume variation.

        Args:
            variation_id: Variation ID
            user_id: User ID (for authorization check)

        Returns:
            bool: True if deleted
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(variation_id, str):
            variation_id = ObjectId(variation_id)
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = variations.delete_one({
            '_id': variation_id,
            'userId': user_id  # Ensure user owns this variation
        })

        return result.deleted_count > 0

    @staticmethod
    def update_variation_status(variation_id, status):
        """
        Update variation status.

        Args:
            variation_id: Variation ID
            status: New status ('generated', 'applied', 'successful', 'rejected')

        Returns:
            bool: True if successful
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(variation_id, str):
            variation_id = ObjectId(variation_id)

        valid_statuses = ['generated', 'applied', 'successful', 'rejected']
        if status not in valid_statuses:
            return False

        result = variations.update_one(
            {'_id': variation_id},
            {
                '$set': {
                    'status': status,
                    'updatedAt': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @staticmethod
    def get_variation_stats(user_id):
        """
        Get statistics about user's resume variations.

        Args:
            user_id: User ID

        Returns:
            dict: Statistics including total variations, average scores, etc.
        """
        variations = ResumeVariation.get_variations_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        pipeline = [
            {'$match': {'userId': user_id}},
            {'$group': {
                '_id': None,
                'totalVariations': {'$sum': 1},
                'avgAtsScore': {'$avg': '$metrics.atsScore'},
                'avgMatchScore': {'$avg': '$metrics.matchScore'},
                'totalTimesUsed': {'$sum': '$timesUsed'},
                'avgSuccessRate': {'$avg': '$successRate'},
                'byJobType': {
                    '$push': {
                        'jobType': '$jobType',
                        'count': 1
                    }
                }
            }}
        ]

        result = list(variations.aggregate(pipeline))

        if result:
            return result[0]

        return {
            'totalVariations': 0,
            'avgAtsScore': 0.0,
            'avgMatchScore': 0.0,
            'totalTimesUsed': 0,
            'avgSuccessRate': 0.0,
            'byJobType': []
        }
