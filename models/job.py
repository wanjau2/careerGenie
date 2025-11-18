"""Job model and operations."""
import re
from datetime import datetime
from bson import ObjectId
from config.database import get_jobs_collection
from utils.helpers import calculate_match_score


class Job:
    """Job model with database operations."""

    @staticmethod
    def create_job(job_data):
        """
        Create a new job posting.

        Args:
            job_data: Job data dictionary

        Returns:
            ObjectId: Created job ID
        """
        jobs = get_jobs_collection()

        # Add timestamps
        job_data['postedAt'] = datetime.utcnow()
        job_data['updatedAt'] = datetime.utcnow()
        job_data['isActive'] = job_data.get('isActive', True)

        result = jobs.insert_one(job_data)
        return result.inserted_id

    @staticmethod
    def find_by_id(job_id):
        """
        Find job by ID.

        Args:
            job_id: Job ID (string or ObjectId)

        Returns:
            dict: Job document or None
        """
        jobs = get_jobs_collection()

        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        return jobs.find_one({'_id': job_id})

    @staticmethod
    def get_active_jobs(filters=None, skip=0, limit=20, sort_by='postedAt'):
        """
        Get active jobs with optional filters.

        Args:
            filters: Dictionary of filters
            skip: Number of documents to skip
            limit: Number of documents to return
            sort_by: Field to sort by

        Returns:
            list: List of job documents
        """
        jobs = get_jobs_collection()

        # Base query for active jobs
        query = {'isActive': True}

        # Add filters
        if filters:
            # Keywords/Title Search
            if 'keywords' in filters and filters['keywords']:
                query['$or'] = [
                    {'title': {'$regex': filters['keywords'], '$options': 'i'}},
                    {'description': {'$regex': filters['keywords'], '$options': 'i'}},
                    {'requirements': {'$regex': filters['keywords'], '$options': 'i'}}
                ]

            # Location filter
            if 'city' in filters and filters['city']:
                query['location.city'] = {'$regex': filters['city'], '$options': 'i'}
            if 'state' in filters and filters['state']:
                query['location.state'] = {'$regex': f'^{re.escape(filters["state"])}$', '$options': 'i'}
            if 'country' in filters and filters['country']:
                query['location.country'] = {'$regex': f'^{re.escape(filters["country"])}$', '$options': 'i'}

            # Remote filter
            if 'remoteOnly' in filters and filters['remoteOnly']:
                query['location.remote'] = True

            # Salary filter - only include jobs with salary data and within range
            if 'minSalary' in filters and filters['minSalary']:
                # Filter jobs where salary.max exists and is >= minSalary
                query['salary.max'] = {'$gte': filters['minSalary'], '$ne': None}
            if 'maxSalary' in filters and filters['maxSalary']:
                # Filter jobs where salary.min exists and is <= maxSalary
                query['salary.min'] = {'$lte': filters['maxSalary'], '$ne': None}

            # Employment type filter (case-insensitive with format normalization)
            if 'jobTypes' in filters and filters['jobTypes']:
                # Create regex pattern that matches any of the job types (case-insensitive)
                # This matches: "full-time", "full time", "Full-time", "Full Time", etc.
                patterns = []
                for job_type in filters['jobTypes']:
                    # Normalize the pattern to handle both spaces and hyphens
                    # Replace any space or hyphen with pattern that matches either
                    pattern = re.sub(r'[ -]', '[ -]', job_type)
                    patterns.append(pattern)

                # Combine all patterns with OR (|)
                combined_pattern = '|'.join([f'^{p}$' for p in patterns])
                query['employment.type'] = {'$regex': combined_pattern, '$options': 'i'}

            # Industry filter (case-insensitive)
            if 'industries' in filters and filters['industries']:
                # Create case-insensitive regex pattern for industries
                industry_patterns = [f'^{re.escape(ind)}$' for ind in filters['industries']]
                combined_industry_pattern = '|'.join(industry_patterns)
                query['company.industry'] = {'$regex': combined_industry_pattern, '$options': 'i'}

            # Role level / Experience level filter (case-insensitive)
            if 'experienceLevels' in filters and filters['experienceLevels']:
                level_patterns = [f'^{re.escape(level)}$' for level in filters['experienceLevels']]
                combined_level_pattern = '|'.join(level_patterns)
                query['employment.level'] = {'$regex': combined_level_pattern, '$options': 'i'}
            elif 'roleLevels' in filters and filters['roleLevels']:
                level_patterns = [f'^{re.escape(level)}$' for level in filters['roleLevels']]
                combined_level_pattern = '|'.join(level_patterns)
                query['employment.level'] = {'$regex': combined_level_pattern, '$options': 'i'}

            # Company size filter (case-insensitive)
            if 'companySize' in filters and filters['companySize']:
                size_patterns = [f'^{re.escape(size)}$' for size in filters['companySize']]
                combined_size_pattern = '|'.join(size_patterns)
                query['company.size'] = {'$regex': combined_size_pattern, '$options': 'i'}

            # Date posted filter
            if 'datePosted' in filters and filters['datePosted']:
                from datetime import timedelta
                now = datetime.utcnow()
                date_ranges = {
                    '24h': now - timedelta(hours=24),
                    '3days': now - timedelta(days=3),
                    'week': now - timedelta(weeks=1),
                    'month': now - timedelta(days=30)
                }
                if filters['datePosted'] in date_ranges:
                    query['postedAt'] = {'$gte': date_ranges[filters['datePosted']]}

        # Execute query with pagination
        cursor = jobs.find(query).sort(sort_by, -1).skip(skip).limit(limit)

        return list(cursor)

    @staticmethod
    def get_total_count(filters=None):
        """
        Get total count of active jobs matching filters.

        Args:
            filters: Dictionary of filters

        Returns:
            int: Total count
        """
        jobs = get_jobs_collection()

        # Base query
        query = {'isActive': True}

        # Add same filters as get_active_jobs
        if filters:
            # Keywords
            if 'keywords' in filters and filters['keywords']:
                query['$or'] = [
                    {'title': {'$regex': filters['keywords'], '$options': 'i'}},
                    {'description': {'$regex': filters['keywords'], '$options': 'i'}},
                    {'requirements': {'$regex': filters['keywords'], '$options': 'i'}}
                ]

            # Location
            if 'city' in filters and filters['city']:
                query['location.city'] = {'$regex': filters['city'], '$options': 'i'}
            if 'state' in filters and filters['state']:
                query['location.state'] = {'$regex': f'^{re.escape(filters["state"])}$', '$options': 'i'}
            if 'country' in filters and filters['country']:
                query['location.country'] = {'$regex': f'^{re.escape(filters["country"])}$', '$options': 'i'}

            if 'remoteOnly' in filters and filters['remoteOnly']:
                query['location.remote'] = True

            # Salary - only include jobs with salary data and within range
            if 'minSalary' in filters and filters['minSalary']:
                query['salary.max'] = {'$gte': filters['minSalary'], '$ne': None}
            if 'maxSalary' in filters and filters['maxSalary']:
                query['salary.min'] = {'$lte': filters['maxSalary'], '$ne': None}

            # Job types (case-insensitive with format normalization)
            if 'jobTypes' in filters and filters['jobTypes']:
                # Create regex pattern that matches any of the job types (case-insensitive)
                patterns = []
                for job_type in filters['jobTypes']:
                    # Normalize the pattern to handle both spaces and hyphens
                    # Replace any space or hyphen with pattern that matches either
                    pattern = re.sub(r'[ -]', '[ -]', job_type)
                    patterns.append(pattern)

                # Combine all patterns with OR (|)
                combined_pattern = '|'.join([f'^{p}$' for p in patterns])
                query['employment.type'] = {'$regex': combined_pattern, '$options': 'i'}

            # Industries (case-insensitive)
            if 'industries' in filters and filters['industries']:
                industry_patterns = [f'^{re.escape(ind)}$' for ind in filters['industries']]
                combined_industry_pattern = '|'.join(industry_patterns)
                query['company.industry'] = {'$regex': combined_industry_pattern, '$options': 'i'}

            # Experience levels (case-insensitive)
            if 'experienceLevels' in filters and filters['experienceLevels']:
                level_patterns = [f'^{re.escape(level)}$' for level in filters['experienceLevels']]
                combined_level_pattern = '|'.join(level_patterns)
                query['employment.level'] = {'$regex': combined_level_pattern, '$options': 'i'}
            elif 'roleLevels' in filters and filters['roleLevels']:
                level_patterns = [f'^{re.escape(level)}$' for level in filters['roleLevels']]
                combined_level_pattern = '|'.join(level_patterns)
                query['employment.level'] = {'$regex': combined_level_pattern, '$options': 'i'}

            # Company size (case-insensitive)
            if 'companySize' in filters and filters['companySize']:
                size_patterns = [f'^{re.escape(size)}$' for size in filters['companySize']]
                combined_size_pattern = '|'.join(size_patterns)
                query['company.size'] = {'$regex': combined_size_pattern, '$options': 'i'}

            # Date posted
            if 'datePosted' in filters and filters['datePosted']:
                from datetime import timedelta
                now = datetime.utcnow()
                date_ranges = {
                    '24h': now - timedelta(hours=24),
                    '3days': now - timedelta(days=3),
                    'week': now - timedelta(weeks=1),
                    'month': now - timedelta(days=30)
                }
                if filters['datePosted'] in date_ranges:
                    query['postedAt'] = {'$gte': date_ranges[filters['datePosted']]}

        return jobs.count_documents(query)

    @staticmethod
    def get_jobs_for_user(user_preferences, exclude_job_ids=None, limit=20):
        """
        Get recommended jobs for a user based on preferences.

        Args:
            user_preferences: User preference dictionary
            exclude_job_ids: List of job IDs to exclude (already swiped)
            limit: Maximum number of jobs to return

        Returns:
            list: List of job documents with match scores
        """
        # Build filter from user preferences
        filters = {
            'jobTypes': user_preferences.get('jobTypes', []),
            'industries': user_preferences.get('industries', []),
            'roleLevels': user_preferences.get('roleLevels', []),
            'remoteOnly': user_preferences.get('remoteOnly', False)
        }

        # Add salary filter if specified
        expected_salary = user_preferences.get('expectedSalary', {})
        if expected_salary:
            filters['minSalary'] = expected_salary.get('min')
            filters['maxSalary'] = expected_salary.get('max')

        # Get more jobs than needed for filtering
        jobs = Job.get_active_jobs(filters, limit=limit * 3)

        # Exclude already swiped jobs
        if exclude_job_ids:
            exclude_ids = [ObjectId(jid) if isinstance(jid, str) else jid for jid in exclude_job_ids]
            jobs = [job for job in jobs if job['_id'] not in exclude_ids]

        # Calculate match scores
        jobs_with_scores = []
        for job in jobs:
            match_score = calculate_match_score(user_preferences, job)
            jobs_with_scores.append({
                'job': job,
                'matchScore': match_score
            })

        # Sort by match score (highest first)
        jobs_with_scores.sort(key=lambda x: x['matchScore'], reverse=True)

        # Return top matches
        return jobs_with_scores[:limit]

    @staticmethod
    def update_job(job_id, update_data):
        """
        Update job data.

        Args:
            job_id: Job ID
            update_data: Data to update

        Returns:
            bool: True if successful
        """
        jobs = get_jobs_collection()

        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        update_data['updatedAt'] = datetime.utcnow()

        result = jobs.update_one(
            {'_id': job_id},
            {'$set': update_data}
        )

        return result.modified_count > 0

    @staticmethod
    def deactivate_job(job_id):
        """
        Deactivate a job posting.

        Args:
            job_id: Job ID

        Returns:
            bool: True if successful
        """
        return Job.update_job(job_id, {'isActive': False})

    @staticmethod
    def search_jobs(search_term, limit=20):
        """
        Search jobs by title, company name, or description.

        Args:
            search_term: Search term
            limit: Maximum results

        Returns:
            list: List of matching jobs
        """
        jobs = get_jobs_collection()

        # Create text search query
        query = {
            'isActive': True,
            '$or': [
                {'title': {'$regex': search_term, '$options': 'i'}},
                {'company.name': {'$regex': search_term, '$options': 'i'}},
                {'description': {'$regex': search_term, '$options': 'i'}}
            ]
        }

        return list(jobs.find(query).limit(limit))
