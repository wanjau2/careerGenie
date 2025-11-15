"""
Free Course Aggregator for ALL Fields
Supports: Tech, Healthcare, Business, Marketing, Design, Teaching, etc.

Free Sources Used:
1. YouTube Data API - 10,000 requests/day (FREE)
2. edX API - Public courses (FREE)
3. Khan Academy - K-12 to College (FREE)
4. Alison - Career courses (FREE)
5. MIT OpenCourseWare - 2,500+ courses (FREE)
6. Harvard CS50 - Computer Science (FREE)
7. FreeCodeCamp - Web Development (FREE)
8. Udacity Free Courses (FREE)
"""

import os
import requests
from typing import List, Dict, Optional
import logging
from datetime import datetime
import json

from services.additional_course_sources import (
    MITOpenCourseWare,
    HarvardCS50,
    FreeCodeCampCourses,
    UdacityFreeCourses
)
from services.course_scrapers import (
    ClassCentralScraper,
    UdacityScraper,
    SkillshareScraper
)

logger = logging.getLogger(__name__)


class FreeCourseAggregator:
    """Aggregate FREE courses from multiple platforms covering ALL fields"""

    def __init__(self):
        # YouTube Data API (10,000 requests/day - FREE!)
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')

        # Other free APIs
        self.use_edx = True
        self.use_khan_academy = True
        self.use_alison = True

        # Initialize additional course sources
        self.mit_ocw = MITOpenCourseWare()
        self.harvard_cs50 = HarvardCS50()
        self.freecodecamp = FreeCodeCampCourses()
        self.udacity = UdacityFreeCourses()

        # Initialize web scrapers (MASSIVE course increase!)
        self.class_central = ClassCentralScraper()  # 50,000+ courses!
        self.udacity_scraper = UdacityScraper()  # Dynamic Udacity courses
        self.skillshare = SkillshareScraper()  # Creative courses

    def search_courses(
        self,
        query: str,
        category: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search for courses across all free platforms

        Args:
            query: Search query (e.g., "nursing", "marketing", "python")
            category: Category filter (healthcare, business, tech, design, etc)
            level: Difficulty level (beginner, intermediate, advanced)
            limit: Number of results

        Returns:
            List of normalized course dictionaries
        """
        all_courses = []

        # 1. YouTube Educational Content (BEST - covers ALL fields)
        youtube_courses = self._search_youtube(query, category, limit=limit//2)
        all_courses.extend(youtube_courses)

        # 2. edX Courses (Academic - all fields)
        edx_courses = self._search_edx(query, limit=5)
        all_courses.extend(edx_courses)

        # 3. Alison (Career skills - all fields)
        alison_courses = self._search_alison(query, category, limit=5)
        all_courses.extend(alison_courses)

        # 4. Khan Academy (K-12 to college - all subjects)
        if self._is_academic_subject(query, category):
            khan_courses = self._search_khan_academy(query, limit=3)
            all_courses.extend(khan_courses)

        # 5. Harvard CS50 (Computer Science - if tech/programming query)
        if self._is_tech_subject(query, category):
            cs50_courses = self.harvard_cs50.get_courses(limit=3)
            all_courses.extend(cs50_courses)

        # 6. FreeCodeCamp (Web Development - if tech query)
        if self._is_tech_subject(query, category):
            fcc_courses = self.freecodecamp.get_courses(limit=3)
            all_courses.extend(fcc_courses)

        # 7. MIT OpenCourseWare (STEM subjects)
        if self._is_academic_subject(query, category) or self._is_tech_subject(query, category):
            mit_courses = self.mit_ocw.search_courses(query, category, limit=3)
            all_courses.extend(mit_courses)

        # 8. Udacity Free (Tech skills)
        if self._is_tech_subject(query, category):
            udacity_courses = self.udacity.get_courses(limit=2)
            all_courses.extend(udacity_courses)

        # 9. Class Central (MASSIVE - 50,000+ courses via web scraping!)
        class_central_courses = self.class_central.search_courses(query, category, limit=10)
        all_courses.extend(class_central_courses)

        # 10. Udacity Scraper (Dynamic courses - more results!)
        if self._is_tech_subject(query, category):
            udacity_scraped = self.udacity_scraper.search_courses(query, limit=5)
            all_courses.extend(udacity_scraped)

        # 11. Skillshare (Creative courses via web scraping)
        if self._is_creative_subject(query, category):
            skillshare_courses = self.skillshare.search_courses(query, limit=5)
            all_courses.extend(skillshare_courses)

        # Remove duplicates and limit
        unique_courses = self._deduplicate_courses(all_courses)

        logger.info(f"🎯 Total unique courses found: {len(unique_courses)} for '{query}'")
        return unique_courses[:limit]

    def _search_youtube(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search YouTube for educational content (FREE - 10,000 requests/day)

        YouTube covers EVERYTHING:
        - Tech: Programming, Data Science
        - Healthcare: Nursing, Medical, First Aid
        - Business: Marketing, Sales, Management
        - Creative: Design, Photography, Music
        - Education: Teaching, Tutoring
        - Trades: Plumbing, Electrician, Carpentry
        - And more!
        """
        if not self.youtube_api_key:
            logger.warning("YouTube API key not found - skipping YouTube courses")
            return []

        try:
            # Enhance query for educational content
            enhanced_query = self._enhance_query_for_education(query, category)

            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': enhanced_query,
                'type': 'video',
                'videoDuration': 'medium',  # 4-20 min videos
                'videoDefinition': 'high',
                'relevanceLanguage': 'en',
                'maxResults': limit,
                'key': self.youtube_api_key,
                'order': 'relevance'
            }

            # Add category-specific filters
            if category:
                params['videoCategoryId'] = self._get_youtube_category_id(category)

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 403:
                logger.error("YouTube API quota exceeded or invalid key")
                return []

            response.raise_for_status()
            data = response.json()

            courses = []
            for item in data.get('items', []):
                snippet = item.get('snippet', {})
                video_id = item.get('id', {}).get('videoId', '')

                course = {
                    'id': f'youtube_{video_id}',
                    'title': snippet.get('title', 'No Title'),
                    'description': snippet.get('description', ''),
                    'provider': 'YouTube',
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'instructor': snippet.get('channelTitle', 'Unknown'),
                    'duration': 'Video',
                    'level': 'All Levels',
                    'isFree': True,
                    'price': 0,
                    'rating': None,
                    'enrollments': None,
                    'category': category or 'General',
                    'skills': [query],
                    'source': 'youtube'
                }
                courses.append(course)

            logger.info(f"✅ YouTube: Found {len(courses)} courses for '{query}'")
            return courses

        except Exception as e:
            logger.error(f"YouTube API error: {str(e)}")
            return []

    def _search_edx(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search edX courses (FREE - Public API)

        Covers: Computer Science, Business, Engineering, Humanities,
               Science, Math, Data Analysis, Language, etc.
        """
        try:
            url = "https://www.edx.org/api/v1/catalog/search"
            params = {
                'q': query,
                'page_size': limit
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return []

            data = response.json()
            courses = []

            for item in data.get('results', []):
                course = {
                    'id': f"edx_{item.get('key', '')}",
                    'title': item.get('title', 'No Title'),
                    'description': item.get('short_description', ''),
                    'provider': 'edX',
                    'url': f"https://www.edx.org{item.get('marketing_url', '')}",
                    'thumbnail': item.get('image_url', ''),
                    'instructor': ', '.join([owner.get('name', '') for owner in item.get('owners', [])]),
                    'duration': f"{item.get('weeks_to_complete', 'N/A')} weeks",
                    'level': item.get('level_type', 'All Levels'),
                    'isFree': item.get('has_enrollable_paid_seats', True) == False,
                    'price': 0 if item.get('has_enrollable_paid_seats') == False else None,
                    'rating': None,
                    'enrollments': None,
                    'category': item.get('subjects', [{}])[0].get('name', 'General'),
                    'skills': item.get('skill_names', []),
                    'source': 'edx'
                }
                courses.append(course)

            logger.info(f"✅ edX: Found {len(courses)} courses for '{query}'")
            return courses

        except Exception as e:
            logger.error(f"edX API error: {str(e)}")
            return []

    def _search_alison(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search Alison courses (FREE - Career & Life Skills)

        Covers: IT, Business, Health, Language, Marketing, Sales,
               Management, Personal Development, Teaching, etc.
        """
        try:
            # Alison has a public search page we can parse
            # For now, return synthetic courses based on common Alison offerings

            alison_categories = {
                'healthcare': ['Nursing', 'First Aid', 'Mental Health', 'Nutrition'],
                'business': ['Marketing', 'Sales', 'Management', 'Accounting'],
                'tech': ['Programming', 'Web Development', 'Data Science', 'IT Support'],
                'education': ['Teaching', 'Classroom Management', 'Early Childhood'],
                'marketing': ['Digital Marketing', 'SEO', 'Social Media', 'Content Marketing'],
                'design': ['Graphic Design', 'UI/UX', 'Photography'],
                'personal': ['Communication', 'Leadership', 'Time Management'],
                'language': ['English', 'Spanish', 'French', 'Business English']
            }

            courses = []
            relevant_skills = []

            # Map query to relevant skills
            for cat, skills in alison_categories.items():
                if category and cat in category.lower():
                    relevant_skills.extend(skills)
                elif any(skill.lower() in query.lower() for skill in skills):
                    relevant_skills.extend(skills)

            if not relevant_skills:
                relevant_skills = alison_categories.get('business', [])

            for skill in relevant_skills[:limit]:
                course = {
                    'id': f'alison_{skill.lower().replace(" ", "_")}',
                    'title': f'Diploma in {skill}',
                    'description': f'Free online diploma course in {skill}. Learn essential skills and get certified.',
                    'provider': 'Alison',
                    'url': f'https://alison.com/courses/{skill.lower().replace(" ", "-")}',
                    'thumbnail': 'https://alison.com/images/default-course.jpg',
                    'instructor': 'Alison',
                    'duration': '3-6 hours',
                    'level': 'Beginner to Intermediate',
                    'isFree': True,
                    'price': 0,
                    'rating': 4.5,
                    'enrollments': None,
                    'category': category or 'Career Skills',
                    'skills': [skill],
                    'source': 'alison'
                }
                courses.append(course)

            logger.info(f"✅ Alison: Created {len(courses)} course suggestions for '{query}'")
            return courses

        except Exception as e:
            logger.error(f"Alison courses error: {str(e)}")
            return []

    def _search_khan_academy(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search Khan Academy (FREE - K-12 to College)

        Covers: Math, Science, Economics, Arts, Humanities,
               Computing, Test Prep, etc.
        """
        try:
            # Khan Academy subjects
            khan_subjects = {
                'math': ['Algebra', 'Geometry', 'Calculus', 'Statistics'],
                'science': ['Biology', 'Chemistry', 'Physics', 'Astronomy'],
                'economics': ['Microeconomics', 'Macroeconomics', 'Finance'],
                'computing': ['Computer Programming', 'Computer Science'],
                'arts': ['Art History', 'Music'],
                'humanities': ['World History', 'US History', 'Civics']
            }

            courses = []
            for subject_cat, subjects in khan_subjects.items():
                if subject_cat in query.lower() or any(subj.lower() in query.lower() for subj in subjects):
                    for subject in subjects[:limit]:
                        course = {
                            'id': f'khan_{subject.lower().replace(" ", "_")}',
                            'title': subject,
                            'description': f'Free {subject} course from Khan Academy. Learn at your own pace.',
                            'provider': 'Khan Academy',
                            'url': f'https://www.khanacademy.org/{subject.lower().replace(" ", "-")}',
                            'thumbnail': 'https://cdn.kastatic.org/images/khan-logo-dark-background.png',
                            'instructor': 'Khan Academy',
                            'duration': 'Self-paced',
                            'level': 'Beginner to Advanced',
                            'isFree': True,
                            'price': 0,
                            'rating': 5.0,
                            'enrollments': None,
                            'category': subject_cat.title(),
                            'skills': [subject],
                            'source': 'khan_academy'
                        }
                        courses.append(course)
                    break

            return courses[:limit]

        except Exception as e:
            logger.error(f"Khan Academy error: {str(e)}")
            return []

    def _enhance_query_for_education(self, query: str, category: Optional[str]) -> str:
        """Enhance search query to find educational content"""
        educational_keywords = [
            'tutorial', 'course', 'learn', 'training', 'guide',
            'beginner', 'fundamentals', 'basics', 'introduction'
        ]

        # Add educational context
        enhanced = f"{query} tutorial course"

        # Add category context
        if category:
            category_contexts = {
                'healthcare': 'medical training certification',
                'business': 'professional course',
                'tech': 'programming tutorial',
                'marketing': 'digital marketing course',
                'design': 'creative tutorial',
                'education': 'teaching course',
                'trades': 'vocational training'
            }
            context = category_contexts.get(category.lower(), 'professional course')
            enhanced = f"{query} {context}"

        return enhanced

    def _get_youtube_category_id(self, category: str) -> str:
        """Map category to YouTube category ID"""
        category_map = {
            'tech': '28',  # Science & Technology
            'education': '27',  # Education
            'business': '27',  # Education
            'howto': '26',  # Howto & Style
            'healthcare': '27',  # Education
            'design': '26',  # Howto & Style
            'music': '10',  # Music
            'sports': '17',  # Sports
        }
        return category_map.get(category.lower(), '27')  # Default: Education

    def _is_academic_subject(self, query: str, category: Optional[str]) -> bool:
        """Check if query is an academic subject suitable for Khan Academy/MIT OCW"""
        academic_keywords = [
            'math', 'science', 'biology', 'chemistry', 'physics',
            'algebra', 'geometry', 'calculus', 'statistics',
            'history', 'economics', 'finance', 'computing'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in academic_keywords)

    def _is_tech_subject(self, query: str, category: Optional[str]) -> bool:
        """Check if query is a tech/programming subject"""
        tech_keywords = [
            'programming', 'python', 'javascript', 'java', 'web', 'app',
            'software', 'developer', 'code', 'coding', 'html', 'css',
            'react', 'node', 'django', 'flask', 'sql', 'database',
            'frontend', 'backend', 'fullstack', 'devops', 'git',
            'api', 'computer science', 'data science', 'machine learning',
            'ai', 'artificial intelligence', 'algorithm'
        ]
        query_lower = query.lower()
        category_lower = category.lower() if category else ''

        return (
            any(keyword in query_lower for keyword in tech_keywords) or
            category_lower in ['tech', 'technology', 'programming', 'computer science']
        )

    def _is_creative_subject(self, query: str, category: Optional[str]) -> bool:
        """Check if query is a creative/design subject"""
        creative_keywords = [
            'design', 'graphic', 'photography', 'photo', 'video', 'editing',
            'art', 'drawing', 'painting', 'illustration', 'creative',
            'photoshop', 'illustrator', 'adobe', 'ui', 'ux', 'figma',
            'animation', 'music', 'sound', 'audio', 'film', 'cinema'
        ]
        query_lower = query.lower()
        category_lower = category.lower() if category else ''

        return (
            any(keyword in query_lower for keyword in creative_keywords) or
            category_lower in ['design', 'creative', 'art', 'photography', 'video']
        )

    def _deduplicate_courses(self, courses: List[Dict]) -> List[Dict]:
        """Remove duplicate courses based on title similarity"""
        unique_courses = []
        seen_titles = set()

        for course in courses:
            title_normalized = course['title'].lower().strip()

            # Simple deduplication by title
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_courses.append(course)

        return unique_courses

    def get_recommended_courses(
        self,
        skills: List[str],
        limit: int = 20
    ) -> Dict:
        """
        Get recommended courses for a list of skills

        Args:
            skills: List of skills to find courses for
            limit: Total number of courses to return

        Returns:
            Dict with courses and metadata
        """
        all_courses = []

        for skill in skills[:5]:  # Limit to top 5 skills to avoid API overuse
            courses = self.search_courses(
                query=skill,
                limit=limit // len(skills[:5]) + 2
            )
            all_courses.extend(courses)

        # Remove duplicates
        unique_courses = self._deduplicate_courses(all_courses)

        return {
            'success': True,
            'courses': unique_courses[:limit],
            'total': len(unique_courses),
            'skills_searched': skills[:5],
            'providers': list(set(c['provider'] for c in unique_courses))
        }
