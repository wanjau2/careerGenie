"""
Advanced Course Web Scrapers
- Class Central (MOOC Aggregator - 50,000+ courses)
- Udacity (Web Scraping for dynamic courses)
- Skillshare Free Classes
- LinkedIn Learning Free Month
"""

import requests
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ClassCentralScraper:
    """
    Class Central - The largest MOOC aggregator
    50,000+ courses from 900+ universities
    https://www.classcentral.com/
    """

    def __init__(self):
        self.base_url = "https://www.classcentral.com"

    def search_courses(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 15
    ) -> List[Dict]:
        """
        Scrape Class Central for courses

        Args:
            query: Search query
            category: Category filter
            limit: Number of results

        Returns:
            List of course dictionaries
        """
        courses = []

        try:
            # Class Central search URL
            search_url = f"{self.base_url}/search"
            params = {'q': query}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(search_url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Class Central returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Class Central course cards
            course_cards = soup.find_all('div', class_='course-listing-card', limit=limit)

            if not course_cards:
                # Try alternative selector
                course_cards = soup.select('.course-list-item', limit=limit)

            for card in course_cards:
                try:
                    # Extract course details
                    title_elem = card.find('h2', class_='course-name') or card.find('a', class_='course-name')
                    link_elem = card.find('a', href=True)
                    desc_elem = card.find('div', class_='course-description') or card.find('p')
                    provider_elem = card.find('span', class_='provider-name')
                    rating_elem = card.find('span', class_='rating-text')

                    if title_elem and link_elem:
                        href = link_elem.get('href', '')
                        full_url = f'{self.base_url}{href}' if href.startswith('/') else href

                        # Extract rating
                        rating = None
                        if rating_elem:
                            rating_text = rating_elem.get_text(strip=True)
                            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                            if rating_match:
                                rating = float(rating_match.group(1))

                        # Check if free
                        is_free = 'free' in card.get_text().lower()

                        course = {
                            'id': f'classcentral_{href.split("/")[-1] if "/" in href else "unknown"}',
                            'title': title_elem.get_text(strip=True),
                            'description': desc_elem.get_text(strip=True)[:200] if desc_elem else f'Online course on {query}',
                            'provider': provider_elem.get_text(strip=True) if provider_elem else 'Various Universities',
                            'url': full_url,
                            'thumbnail': self._extract_thumbnail(card),
                            'instructor': 'University Professors',
                            'duration': 'Varies',
                            'level': 'All Levels',
                            'isFree': is_free,
                            'price': 0 if is_free else None,
                            'rating': rating,
                            'enrollments': None,
                            'category': category or 'General',
                            'skills': [query],
                            'source': 'class_central'
                        }
                        courses.append(course)
                except Exception as e:
                    logger.warning(f"Failed to parse Class Central course: {str(e)}")
                    continue

            logger.info(f"✅ Class Central: Scraped {len(courses)} courses for '{query}'")
            return courses

        except Exception as e:
            logger.error(f"Class Central scraping error: {str(e)}")
            return []

    def _extract_thumbnail(self, card_element) -> str:
        """Extract course thumbnail from card"""
        img_elem = card_element.find('img')
        if img_elem:
            return img_elem.get('src', '') or img_elem.get('data-src', '')
        return 'https://www.classcentral.com/images/logo.png'


class UdacityScraper:
    """
    Udacity Free Courses (Web Scraping)
    https://www.udacity.com/courses/all?price=Free
    """

    def __init__(self):
        self.base_url = "https://www.udacity.com"

    def search_courses(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Scrape Udacity for free courses

        Args:
            query: Search query
            limit: Number of results

        Returns:
            List of course dictionaries
        """
        courses = []

        try:
            # Udacity free courses page
            url = f"{self.base_url}/courses/all?price=Free"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Udacity returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Udacity course cards
            course_cards = soup.find_all('div', class_='course-card', limit=limit * 2)

            for card in course_cards:
                try:
                    title_elem = card.find('h3') or card.find('h2')
                    link_elem = card.find('a', href=True)
                    desc_elem = card.find('p')

                    if title_elem and link_elem:
                        # Filter by query
                        title_text = title_elem.get_text(strip=True).lower()
                        if query.lower() not in title_text and query.lower() not in card.get_text().lower():
                            continue

                        href = link_elem.get('href', '')
                        full_url = f'{self.base_url}{href}' if href.startswith('/') else href

                        course = {
                            'id': f'udacity_{href.split("/")[-1]}',
                            'title': title_elem.get_text(strip=True),
                            'description': desc_elem.get_text(strip=True) if desc_elem else '',
                            'provider': 'Udacity',
                            'url': full_url,
                            'thumbnail': self._extract_thumbnail(card),
                            'instructor': 'Udacity',
                            'duration': '2-4 weeks',
                            'level': 'Beginner to Intermediate',
                            'isFree': True,
                            'price': 0,
                            'rating': 4.5,
                            'enrollments': None,
                            'category': 'Technology',
                            'skills': [query],
                            'source': 'udacity'
                        }
                        courses.append(course)

                        if len(courses) >= limit:
                            break

                except Exception as e:
                    logger.warning(f"Failed to parse Udacity course: {str(e)}")
                    continue

            logger.info(f"✅ Udacity: Scraped {len(courses)} courses for '{query}'")
            return courses

        except Exception as e:
            logger.error(f"Udacity scraping error: {str(e)}")
            return []

    def _extract_thumbnail(self, card_element) -> str:
        """Extract course thumbnail"""
        img_elem = card_element.find('img')
        if img_elem:
            return img_elem.get('src', '') or img_elem.get('data-src', '')
        return 'https://www.udacity.com/favicon.ico'


class SkillshareScraper:
    """
    Skillshare Free Classes
    https://www.skillshare.com/browse/free
    """

    def __init__(self):
        self.base_url = "https://www.skillshare.com"

    def search_courses(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Scrape Skillshare for free classes

        Args:
            query: Search query
            limit: Number of results

        Returns:
            List of course dictionaries
        """
        courses = []

        try:
            # Skillshare search URL
            search_url = f"{self.base_url}/search"
            params = {'query': query, 'filter': 'free'}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(search_url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Skillshare returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Skillshare class cards
            class_cards = soup.find_all('div', class_='class-card', limit=limit)

            if not class_cards:
                class_cards = soup.select('[data-testid="class-card"]', limit=limit)

            for card in class_cards:
                try:
                    title_elem = card.find('h3') or card.find('h2')
                    link_elem = card.find('a', href=True)
                    teacher_elem = card.find('span', class_='teacher-name')
                    duration_elem = card.find('span', class_='duration')

                    if title_elem and link_elem:
                        href = link_elem.get('href', '')
                        full_url = f'{self.base_url}{href}' if href.startswith('/') else href

                        course = {
                            'id': f'skillshare_{href.split("/")[-1]}',
                            'title': title_elem.get_text(strip=True),
                            'description': f'Learn {query} with this Skillshare class',
                            'provider': 'Skillshare',
                            'url': full_url,
                            'thumbnail': self._extract_thumbnail(card),
                            'instructor': teacher_elem.get_text(strip=True) if teacher_elem else 'Skillshare Teacher',
                            'duration': duration_elem.get_text(strip=True) if duration_elem else '1-2 hours',
                            'level': 'All Levels',
                            'isFree': True,
                            'price': 0,
                            'rating': 4.5,
                            'enrollments': None,
                            'category': 'Creative',
                            'skills': [query],
                            'source': 'skillshare'
                        }
                        courses.append(course)

                except Exception as e:
                    logger.warning(f"Failed to parse Skillshare class: {str(e)}")
                    continue

            logger.info(f"✅ Skillshare: Scraped {len(courses)} courses for '{query}'")
            return courses

        except Exception as e:
            logger.error(f"Skillshare scraping error: {str(e)}")
            return []

    def _extract_thumbnail(self, card_element) -> str:
        """Extract class thumbnail"""
        img_elem = card_element.find('img')
        if img_elem:
            return img_elem.get('src', '') or img_elem.get('data-src', '')
        return 'https://static.skillshare.com/assets/images/favicon.ico'
