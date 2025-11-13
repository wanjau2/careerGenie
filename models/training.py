"""Training corpus and job management models."""
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Optional
from config.database import (
    get_database,
    get_training_corpora_collection,
    get_training_resumes_collection,
    get_training_jobs_collection
)


class TrainingCorpus:
    """Model for training corpus (collection of resumes)."""

    @staticmethod
    def create(corpus_data: Dict) -> ObjectId:
        """
        Create a new training corpus.

        Args:
            corpus_data: Corpus information

        Returns:
            ObjectId of created corpus
        """
        collection = get_training_corpora_collection()
        result = collection.insert_one(corpus_data)
        return result.inserted_id

    @staticmethod
    def find_by_id(corpus_id: str) -> Optional[Dict]:
        """Find corpus by ID."""
        collection = get_training_corpora_collection()

        if isinstance(corpus_id, str):
            corpus_id = ObjectId(corpus_id)

        return collection.find_one({'_id': corpus_id})

    @staticmethod
    def get_all(category: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[Dict]:
        """
        Get all training corpora.

        Args:
            category: Filter by category
            skip: Number to skip
            limit: Number to return

        Returns:
            List of corpora
        """
        collection = get_training_corpora_collection()

        query = {}
        if category:
            query['category'] = category

        cursor = collection.find(query).sort('createdAt', -1).skip(skip).limit(limit)
        return list(cursor)

    @staticmethod
    def get_count(category: Optional[str] = None) -> int:
        """Get total corpus count."""
        collection = get_training_corpora_collection()

        query = {}
        if category:
            query['category'] = category

        return collection.count_documents(query)

    @staticmethod
    def get_category_breakdown() -> List[Dict]:
        """Get corpus breakdown by category."""
        collection = get_training_corpora_collection()

        pipeline = [
            {
                '$group': {
                    '_id': '$category',
                    'count': {'$sum': 1},
                    'totalResumes': {'$sum': '$totalResumes'},
                    'avgQuality': {'$avg': '$averageQualityScore'}
                }
            },
            {'$sort': {'count': -1}}
        ]

        return list(collection.aggregate(pipeline))

    @staticmethod
    def delete(corpus_id: str) -> bool:
        """Delete a corpus."""
        collection = get_training_corpora_collection()

        if isinstance(corpus_id, str):
            corpus_id = ObjectId(corpus_id)

        result = collection.delete_one({'_id': corpus_id})
        return result.deleted_count > 0


class TrainingResume:
    """Model for individual training resumes."""

    @staticmethod
    def create(resume_data: Dict) -> ObjectId:
        """
        Create a training resume record.

        Args:
            resume_data: Resume information

        Returns:
            ObjectId of created resume
        """
        collection = get_training_resumes_collection()
        result = collection.insert_one(resume_data)
        return result.inserted_id

    @staticmethod
    def find_by_id(resume_id: str) -> Optional[Dict]:
        """Find resume by ID."""
        collection = get_training_resumes_collection()

        if isinstance(resume_id, str):
            resume_id = ObjectId(resume_id)

        return collection.find_one({'_id': resume_id})

    @staticmethod
    def get_by_corpora(corpus_ids: List[str]) -> List[Dict]:
        """
        Get all resumes from specified corpora.

        Args:
            corpus_ids: List of corpus IDs

        Returns:
            List of resumes
        """
        collection = get_training_resumes_collection()

        query = {'corpusId': {'$in': corpus_ids}}
        return list(collection.find(query))

    @staticmethod
    def get_all(skip: int = 0, limit: int = 1000) -> List[Dict]:
        """Get all training resumes."""
        collection = get_training_resumes_collection()
        cursor = collection.find().skip(skip).limit(limit)
        return list(cursor)

    @staticmethod
    def get_count() -> int:
        """Get total resume count."""
        collection = get_training_resumes_collection()
        return collection.count_documents({})

    @staticmethod
    def delete_by_corpus(corpus_id: str) -> int:
        """
        Delete all resumes in a corpus.

        Args:
            corpus_id: Corpus ID

        Returns:
            Number of resumes deleted
        """
        collection = get_training_resumes_collection()
        result = collection.delete_many({'corpusId': corpus_id})
        return result.deleted_count

    @staticmethod
    def get_average_quality_score() -> float:
        """Get average quality score across all resumes."""
        collection = get_training_resumes_collection()

        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'avgScore': {'$avg': '$qualityScore'}
                }
            }
        ]

        result = list(collection.aggregate(pipeline))
        return result[0]['avgScore'] if result else 0.0

    @staticmethod
    def count_since(date: datetime) -> int:
        """Count resumes added since a specific date."""
        collection = get_training_resumes_collection()
        return collection.count_documents({'uploadedAt': {'$gte': date}})

    @staticmethod
    def search(
        query: str = '',
        category: Optional[str] = None,
        min_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search training resumes.

        Args:
            query: Search query
            category: Filter by category
            min_score: Minimum quality score
            skip: Number to skip
            limit: Number to return

        Returns:
            List of matching resumes
        """
        collection = get_training_resumes_collection()

        filters = {}

        if query:
            filters['$or'] = [
                {'filename': {'$regex': query, '$options': 'i'}},
                {'parsedData.raw_text': {'$regex': query, '$options': 'i'}}
            ]

        if min_score:
            filters['qualityScore'] = {'$gte': min_score}

        cursor = collection.find(filters).sort('qualityScore', -1).skip(skip).limit(limit)
        return list(cursor)

    @staticmethod
    def count_search(
        query: str = '',
        category: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> int:
        """Count search results."""
        collection = get_training_resumes_collection()

        filters = {}

        if query:
            filters['$or'] = [
                {'filename': {'$regex': query, '$options': 'i'}},
                {'parsedData.raw_text': {'$regex': query, '$options': 'i'}}
            ]

        if min_score:
            filters['qualityScore'] = {'$gte': min_score}

        return collection.count_documents(filters)

    @staticmethod
    def get_common_skills(min_frequency: int = 5) -> List[Dict]:
        """Get most common skills from training resumes."""
        collection = get_training_resumes_collection()

        pipeline = [
            {'$unwind': '$parsedData.skills'},
            {
                '$group': {
                    '_id': {'$toLower': '$parsedData.skills'},
                    'count': {'$sum': 1}
                }
            },
            {'$match': {'count': {'$gte': min_frequency}}},
            {'$sort': {'count': -1}},
            {'$limit': 100}
        ]

        return list(collection.aggregate(pipeline))

    @staticmethod
    def get_common_phrases(min_frequency: int = 3) -> List[Dict]:
        """Get common phrases from successful resumes."""
        collection = get_training_resumes_collection()

        # This is a simplified version - actual implementation would use NLP
        pipeline = [
            {'$match': {'qualityScore': {'$gte': 0.7}}},
            {'$limit': 100}
        ]

        resumes = list(collection.aggregate(pipeline))

        # Extract common phrases (simplified)
        phrases = {}
        for resume in resumes:
            text = resume.get('parsedData', {}).get('raw_text', '')
            # Simple phrase extraction logic
            # In production, use proper NLP

        return []

    @staticmethod
    def get_format_patterns() -> List[Dict]:
        """Get common format patterns."""
        collection = get_training_resumes_collection()

        pipeline = [
            {'$match': {'qualityScore': {'$gte': 0.7}}},
            {
                '$group': {
                    '_id': '$parsedData.format',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]

        return list(collection.aggregate(pipeline))

    @staticmethod
    def get_structure_patterns() -> List[Dict]:
        """Get common structure patterns."""
        collection = get_training_resumes_collection()

        # Analyze section ordering and structure
        pipeline = [
            {'$match': {'qualityScore': {'$gte': 0.7}}},
            {'$limit': 100}
        ]

        return list(collection.aggregate(pipeline))


class TrainingJob:
    """Model for training job tracking."""

    @staticmethod
    def create(job_data: Dict) -> ObjectId:
        """
        Create a new training job.

        Args:
            job_data: Job information

        Returns:
            ObjectId of created job
        """
        collection = get_training_jobs_collection()
        result = collection.insert_one(job_data)
        return result.inserted_id

    @staticmethod
    def find_by_id(job_id: str) -> Optional[Dict]:
        """Find job by ID."""
        collection = get_training_jobs_collection()

        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        return collection.find_one({'_id': job_id})

    @staticmethod
    def update_status(job_id: str, status: str, progress: int = 0, error: str = None):
        """
        Update job status.

        Args:
            job_id: Job ID
            status: New status (pending, running, completed, failed)
            progress: Progress percentage (0-100)
            error: Error message if failed
        """
        collection = get_training_jobs_collection()

        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        update_data = {
            'status': status,
            'progress': progress,
            'updatedAt': datetime.utcnow()
        }

        if error:
            update_data['error'] = error

        collection.update_one(
            {'_id': job_id},
            {'$set': update_data}
        )

    @staticmethod
    def complete(job_id: str, metrics: Dict):
        """
        Mark job as completed with metrics.

        Args:
            job_id: Job ID
            metrics: Training metrics
        """
        collection = get_training_jobs_collection()

        if isinstance(job_id, str):
            job_id = ObjectId(job_id)

        collection.update_one(
            {'_id': job_id},
            {
                '$set': {
                    'status': 'completed',
                    'progress': 100,
                    'metrics': metrics,
                    'completedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }
            }
        )

    @staticmethod
    def get_recent(limit: int = 10) -> List[Dict]:
        """Get recent training jobs."""
        collection = get_training_jobs_collection()
        cursor = collection.find().sort('startedAt', -1).limit(limit)
        return list(cursor)

    @staticmethod
    def get_latest_completed() -> Optional[Dict]:
        """Get the latest completed training job."""
        collection = get_training_jobs_collection()
        return collection.find_one(
            {'status': 'completed'},
            sort=[('completedAt', -1)]
        )

    @staticmethod
    def get_count(status: Optional[str] = None) -> int:
        """Get job count."""
        collection = get_training_jobs_collection()

        query = {}
        if status:
            query['status'] = status

        return collection.count_documents(query)
