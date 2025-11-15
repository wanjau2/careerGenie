"""
Additional Free Course Sources
- MIT OpenCourseWare (OCW)
- Harvard CS50
- FreeCodeCamp
- Udacity Free Courses
- Codecademy Free Track
"""

import requests
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MITOpenCourseWare:
    """
    MIT OpenCourseWare - 2,500+ free courses from MIT
    Web scraping from https://ocw.mit.edu/
    """

    def __init__(self):
        self.base_url = "https://ocw.mit.edu"

    def search_courses(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search MIT OCW courses via web scraping

        Args:
            query: Search query
            category: Category filter
            limit: Number of results

        Returns:
            List of course dictionaries
        """
        courses = []

        try:
            # MIT OCW search URL (updated for 2025)
            search_url = f"{self.base_url}/search/"
            params = {'q': query, 'type': 'course'}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(search_url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"MIT OCW returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Try multiple selectors for course results
            # MIT OCW frequently updates their HTML structure
            course_elements = (
                soup.find_all('li', class_='course-item', limit=limit) or
                soup.find_all('article', class_='course', limit=limit) or
                soup.find_all('div', class_='course-card', limit=limit) or
                soup.select('.search-results .course', limit=limit)
            )

            for element in course_elements:
                try:
                    # Try to find title
                    title_elem = (
                        element.find('h2') or
                        element.find('h3') or
                        element.find('a', class_='course-title') or
                        element.find('a')
                    )

                    # Try to find link
                    link_elem = element.find('a', href=True)

                    # Try to find description
                    desc_elem = (
                        element.find('p', class_='description') or
                        element.find('div', class_='description') or
                        element.find('p')
                    )

                    if title_elem and link_elem:
                        href = link_elem.get('href', '')
                        full_url = f'{self.base_url}{href}' if href.startswith('/') else href

                        # Extract course ID from URL
                        course_id = href.split('/')[-2] if '/' in href else 'unknown'

                        course = {
                            'id': f'mit_ocw_{course_id}',
                            'title': title_elem.get_text(strip=True),
                            'description': desc_elem.get_text(strip=True) if desc_elem else f'MIT OpenCourseWare course on {query}',
                            'provider': 'MIT OpenCourseWare',
                            'url': full_url,
                            'thumbnail': 'https://ocw.mit.edu/static_shared/images/favicon.ico',
                            'instructor': 'MIT Faculty',
                            'duration': 'Self-paced',
                            'level': 'College Level',
                            'isFree': True,
                            'price': 0,
                            'rating': 5.0,
                            'enrollments': None,
                            'category': category or 'STEM',
                            'skills': [query],
                            'source': 'mit_ocw'
                        }
                        courses.append(course)
                except Exception as e:
                    logger.warning(f"Failed to parse MIT OCW course element: {str(e)}")
                    continue

            if courses:
                logger.info(f"✅ MIT OCW: Scraped {len(courses)} courses for '{query}'")
            else:
                logger.warning(f"⚠️ MIT OCW: No courses found for '{query}' (check HTML structure)")

            return courses

        except Exception as e:
            logger.error(f"MIT OCW scraping error: {str(e)}")
            return []


class HarvardCS50:
    """
    Harvard CS50 - Free computer science courses
    https://cs50.harvard.edu/
    """

    def get_courses(self, limit: int = 10) -> List[Dict]:
        """
        Get Harvard CS50 courses

        Returns:
            List of course dictionaries
        """
        # Predefined CS50 courses (updated 2025)
        courses = [
            {
                'id': 'harvard_cs50x',
                'title': 'CS50x: Introduction to Computer Science',
                'description': "Harvard University's introduction to computer science and programming. Learn problem-solving, algorithms, data structures, and more.",
                'provider': 'Harvard University',
                'url': 'https://cs50.harvard.edu/x/',
                'thumbnail': 'https://cs50.harvard.edu/x/2025/favicon.ico',
                'instructor': 'David J. Malan',
                'duration': '10-12 weeks',
                'level': 'Beginner',
                'isFree': True,
                'price': 0,
                'rating': 5.0,
                'enrollments': 3000000,
                'category': 'Computer Science',
                'skills': ['Programming', 'Algorithms', 'Data Structures', 'Python', 'C'],
                'source': 'harvard_cs50'
            },
            {
                'id': 'harvard_cs50w',
                'title': 'CS50 Web: Web Programming with Python and JavaScript',
                'description': 'Learn to design and implement web applications with Python, JavaScript, and SQL.',
                'provider': 'Harvard University',
                'url': 'https://cs50.harvard.edu/web/',
                'thumbnail': 'https://cs50.harvard.edu/x/2025/favicon.ico',
                'instructor': 'Brian Yu',
                'duration': '12 weeks',
                'level': 'Intermediate',
                'isFree': True,
                'price': 0,
                'rating': 5.0,
                'enrollments': 500000,
                'category': 'Web Development',
                'skills': ['Python', 'JavaScript', 'Django', 'SQL', 'HTML/CSS'],
                'source': 'harvard_cs50'
            },
            {
                'id': 'harvard_cs50ai',
                'title': 'CS50 AI: Introduction to Artificial Intelligence with Python',
                'description': 'Explore AI concepts and algorithms using Python.',
                'provider': 'Harvard University',
                'url': 'https://cs50.harvard.edu/ai/',
                'thumbnail': 'https://cs50.harvard.edu/x/2025/favicon.ico',
                'instructor': 'Brian Yu',
                'duration': '7 weeks',
                'level': 'Intermediate',
                'isFree': True,
                'price': 0,
                'rating': 5.0,
                'enrollments': 300000,
                'category': 'Artificial Intelligence',
                'skills': ['Python', 'Machine Learning', 'AI', 'Neural Networks'],
                'source': 'harvard_cs50'
            },
            {
                'id': 'harvard_cs50p',
                'title': 'CS50 Python: Introduction to Programming with Python',
                'description': 'Learn to program in Python, one of the most popular programming languages.',
                'provider': 'Harvard University',
                'url': 'https://cs50.harvard.edu/python/',
                'thumbnail': 'https://cs50.harvard.edu/x/2025/favicon.ico',
                'instructor': 'David J. Malan',
                'duration': '9 weeks',
                'level': 'Beginner',
                'isFree': True,
                'price': 0,
                'rating': 5.0,
                'enrollments': 400000,
                'category': 'Programming',
                'skills': ['Python', 'Programming Fundamentals', 'Problem Solving'],
                'source': 'harvard_cs50'
            },
            {
                'id': 'harvard_cs50sql',
                'title': 'CS50 SQL: Introduction to Databases with SQL',
                'description': 'Learn to design, query, and manage databases using SQL.',
                'provider': 'Harvard University',
                'url': 'https://cs50.harvard.edu/sql/',
                'thumbnail': 'https://cs50.harvard.edu/x/2025/favicon.ico',
                'instructor': 'Carter Zenke',
                'duration': '7 weeks',
                'level': 'Beginner',
                'isFree': True,
                'price': 0,
                'rating': 5.0,
                'enrollments': 200000,
                'category': 'Databases',
                'skills': ['SQL', 'Database Design', 'PostgreSQL', 'MySQL'],
                'source': 'harvard_cs50'
            },
        ]

        logger.info(f"✅ Harvard CS50: Returning {min(limit, len(courses))} courses")
        return courses[:limit]


class FreeCodeCampCourses:
    """
    FreeCodeCamp - Free coding bootcamp
    https://www.freecodecamp.org/
    """

    def get_courses(self, limit: int = 10) -> List[Dict]:
        """
        Get FreeCodeCamp certifications

        Returns:
            List of course dictionaries
        """
        courses = [
            {
                'id': 'fcc_responsive_web',
                'title': 'Responsive Web Design Certification',
                'description': 'Learn HTML, CSS, Flexbox, Grid, and responsive design principles.',
                'provider': 'FreeCodeCamp',
                'url': 'https://www.freecodecamp.org/learn/2022/responsive-web-design/',
                'thumbnail': 'https://cdn.freecodecamp.org/universal/favicons/favicon.ico',
                'instructor': 'FreeCodeCamp',
                'duration': '300 hours',
                'level': 'Beginner',
                'isFree': True,
                'price': 0,
                'rating': 4.8,
                'enrollments': 2000000,
                'category': 'Web Development',
                'skills': ['HTML', 'CSS', 'Responsive Design', 'Flexbox', 'Grid'],
                'source': 'freecodecamp'
            },
            {
                'id': 'fcc_javascript',
                'title': 'JavaScript Algorithms and Data Structures',
                'description': 'Master JavaScript fundamentals, ES6, algorithms, and data structures.',
                'provider': 'FreeCodeCamp',
                'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/',
                'thumbnail': 'https://cdn.freecodecamp.org/universal/favicons/favicon.ico',
                'instructor': 'FreeCodeCamp',
                'duration': '300 hours',
                'level': 'Beginner to Intermediate',
                'isFree': True,
                'price': 0,
                'rating': 4.9,
                'enrollments': 1500000,
                'category': 'Programming',
                'skills': ['JavaScript', 'Algorithms', 'Data Structures', 'ES6'],
                'source': 'freecodecamp'
            },
            {
                'id': 'fcc_frontend',
                'title': 'Front End Development Libraries',
                'description': 'Learn React, Redux, Bootstrap, jQuery, and Sass.',
                'provider': 'FreeCodeCamp',
                'url': 'https://www.freecodecamp.org/learn/front-end-development-libraries/',
                'thumbnail': 'https://cdn.freecodecamp.org/universal/favicons/favicon.ico',
                'instructor': 'FreeCodeCamp',
                'duration': '300 hours',
                'level': 'Intermediate',
                'isFree': True,
                'price': 0,
                'rating': 4.8,
                'enrollments': 1000000,
                'category': 'Frontend Development',
                'skills': ['React', 'Redux', 'Bootstrap', 'jQuery', 'Sass'],
                'source': 'freecodecamp'
            },
            {
                'id': 'fcc_data_viz',
                'title': 'Data Visualization',
                'description': 'Learn D3.js and create interactive data visualizations.',
                'provider': 'FreeCodeCamp',
                'url': 'https://www.freecodecamp.org/learn/data-visualization/',
                'thumbnail': 'https://cdn.freecodecamp.org/universal/favicons/favicon.ico',
                'instructor': 'FreeCodeCamp',
                'duration': '300 hours',
                'level': 'Intermediate',
                'isFree': True,
                'price': 0,
                'rating': 4.7,
                'enrollments': 500000,
                'category': 'Data Visualization',
                'skills': ['D3.js', 'Data Visualization', 'JavaScript', 'JSON'],
                'source': 'freecodecamp'
            },
            {
                'id': 'fcc_backend',
                'title': 'Back End Development and APIs',
                'description': 'Learn Node.js, Express, MongoDB, and build RESTful APIs.',
                'provider': 'FreeCodeCamp',
                'url': 'https://www.freecodecamp.org/learn/back-end-development-and-apis/',
                'thumbnail': 'https://cdn.freecodecamp.org/universal/favicons/favicon.ico',
                'instructor': 'FreeCodeCamp',
                'duration': '300 hours',
                'level': 'Intermediate',
                'isFree': True,
                'price': 0,
                'rating': 4.8,
                'enrollments': 800000,
                'category': 'Backend Development',
                'skills': ['Node.js', 'Express', 'MongoDB', 'REST APIs'],
                'source': 'freecodecamp'
            },
            {
                'id': 'fcc_python',
                'title': 'Scientific Computing with Python',
                'description': 'Learn Python for scientific computing, data analysis, and automation.',
                'provider': 'FreeCodeCamp',
                'url': 'https://www.freecodecamp.org/learn/scientific-computing-with-python/',
                'thumbnail': 'https://cdn.freecodecamp.org/universal/favicons/favicon.ico',
                'instructor': 'FreeCodeCamp',
                'duration': '300 hours',
                'level': 'Beginner to Intermediate',
                'isFree': True,
                'price': 0,
                'rating': 4.9,
                'enrollments': 900000,
                'category': 'Python',
                'skills': ['Python', 'NumPy', 'Pandas', 'Data Analysis'],
                'source': 'freecodecamp'
            },
        ]

        logger.info(f"✅ FreeCodeCamp: Returning {min(limit, len(courses))} courses")
        return courses[:limit]


class UdacityFreeCourses:
    """
    Udacity Free Courses
    https://www.udacity.com/courses/all?price=Free
    """

    def get_courses(self, limit: int = 10) -> List[Dict]:
        """
        Get Udacity free courses

        Returns:
            List of course dictionaries
        """
        courses = [
            {
                'id': 'udacity_intro_html_css',
                'title': 'Intro to HTML and CSS',
                'description': 'Learn to convert digital design mockups into static web pages.',
                'provider': 'Udacity',
                'url': 'https://www.udacity.com/course/intro-to-html-and-css--ud001',
                'thumbnail': 'https://www.udacity.com/favicon.ico',
                'instructor': 'Udacity',
                'duration': '3 weeks',
                'level': 'Beginner',
                'isFree': True,
                'price': 0,
                'rating': 4.6,
                'enrollments': 300000,
                'category': 'Web Development',
                'skills': ['HTML', 'CSS', 'Web Design'],
                'source': 'udacity'
            },
            {
                'id': 'udacity_intro_programming',
                'title': 'Introduction to Programming',
                'description': 'Learn the basics of programming with HTML, CSS, and Python.',
                'provider': 'Udacity',
                'url': 'https://www.udacity.com/course/intro-to-programming-nanodegree--nd000',
                'thumbnail': 'https://www.udacity.com/favicon.ico',
                'instructor': 'Udacity',
                'duration': '4 weeks',
                'level': 'Beginner',
                'isFree': True,
                'price': 0,
                'rating': 4.5,
                'enrollments': 500000,
                'category': 'Programming',
                'skills': ['Python', 'HTML', 'CSS', 'Programming Fundamentals'],
                'source': 'udacity'
            },
            {
                'id': 'udacity_git_github',
                'title': 'Version Control with Git',
                'description': 'Learn Git and GitHub for version control and collaboration.',
                'provider': 'Udacity',
                'url': 'https://www.udacity.com/course/version-control-with-git--ud123',
                'thumbnail': 'https://www.udacity.com/favicon.ico',
                'instructor': 'Udacity',
                'duration': '4 weeks',
                'level': 'Beginner',
                'isFree': True,
                'price': 0,
                'rating': 4.7,
                'enrollments': 400000,
                'category': 'DevOps',
                'skills': ['Git', 'GitHub', 'Version Control', 'Collaboration'],
                'source': 'udacity'
            },
        ]

        logger.info(f"✅ Udacity: Returning {min(limit, len(courses))} courses")
        return courses[:limit]
