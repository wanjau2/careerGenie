#!/usr/bin/env python3
"""
Fetch Comprehensive Courses Across All Fields
==============================================

This script fetches courses from all sources across multiple categories and skills.
It demonstrates how to retrieve maximum course coverage.

Usage:
    python fetch_comprehensive_courses.py
"""

import os
import sys
import time
import json
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.course_aggregation import CourseAggregationService


class ComprehensiveCourseFetcher:
    """Fetch courses across all major fields and skills."""

    def __init__(self):
        """Initialize the course fetcher."""
        self.service = CourseAggregationService()
        self.all_courses = []
        self.errors = []

    # Define comprehensive skill/topic coverage
    COMPREHENSIVE_TOPICS = {
        "Programming & Development": [
            "Python",
            "JavaScript",
            "Java",
            "C++",
            "C#",
            "Go",
            "Rust",
            "TypeScript",
            "PHP",
            "Ruby",
            "Swift",
            "Kotlin",
            "React",
            "Angular",
            "Vue.js",
            "Node.js",
            "Django",
            "Flask",
            "Spring Boot",
            "ASP.NET",
            "Laravel",
            "Ruby on Rails",
        ],
        "Data Science & AI": [
            "Machine Learning",
            "Deep Learning",
            "Data Science",
            "Data Analysis",
            "Artificial Intelligence",
            "Neural Networks",
            "Natural Language Processing",
            "Computer Vision",
            "TensorFlow",
            "PyTorch",
            "Scikit-learn",
            "Pandas",
            "NumPy",
            "Statistics",
            "R Programming",
        ],
        "Cloud & DevOps": [
            "AWS",
            "Azure",
            "Google Cloud",
            "Docker",
            "Kubernetes",
            "CI/CD",
            "DevOps",
            "Terraform",
            "Jenkins",
            "GitHub Actions",
            "Cloud Architecture",
            "Microservices",
            "Serverless",
        ],
        "Databases": [
            "SQL",
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Redis",
            "Elasticsearch",
            "Database Design",
            "NoSQL",
            "GraphQL",
            "Firebase",
        ],
        "Mobile Development": [
            "iOS Development",
            "Android Development",
            "React Native",
            "Flutter",
            "Mobile App Development",
            "Xcode",
            "Android Studio",
        ],
        "Web Development": [
            "HTML",
            "CSS",
            "Responsive Design",
            "Web Design",
            "Frontend Development",
            "Backend Development",
            "Full Stack Development",
            "Web3",
            "Blockchain Development",
        ],
        "Design & UX": [
            "UI/UX Design",
            "Figma",
            "Adobe XD",
            "Photoshop",
            "Illustrator",
            "Graphic Design",
            "User Experience",
            "Prototyping",
            "Design Thinking",
        ],
        "Business & Management": [
            "Project Management",
            "Agile",
            "Scrum",
            "Product Management",
            "Business Analysis",
            "Leadership",
            "Management",
            "Entrepreneurship",
            "Strategy",
        ],
        "Digital Marketing": [
            "Digital Marketing",
            "SEO",
            "Social Media Marketing",
            "Content Marketing",
            "Email Marketing",
            "Google Analytics",
            "Facebook Ads",
            "Google Ads",
            "Marketing Strategy",
        ],
        "Finance & Accounting": [
            "Accounting",
            "Finance",
            "Financial Analysis",
            "Investment",
            "Stock Market",
            "Cryptocurrency",
            "Excel",
            "Financial Modeling",
        ],
        "IT & Security": [
            "Cybersecurity",
            "Ethical Hacking",
            "Network Security",
            "Penetration Testing",
            "CompTIA",
            "CISSP",
            "IT Support",
            "Network Administration",
        ],
        "Soft Skills": [
            "Communication",
            "Public Speaking",
            "Leadership",
            "Time Management",
            "Productivity",
            "Negotiation",
            "Critical Thinking",
            "Problem Solving",
        ],
        "Creative": [
            "Video Editing",
            "Music Production",
            "Photography",
            "Writing",
            "Content Creation",
            "Animation",
            "Game Development",
            "Unity",
            "Unreal Engine",
        ],
    }

    def fetch_by_topics(self, max_per_topic: int = 20) -> List[Dict]:
        """
        Fetch courses by topics across all categories.

        Args:
            max_per_topic: Maximum courses to fetch per topic

        Returns:
            List of unique courses
        """
        print("=" * 80)
        print("COMPREHENSIVE COURSE FETCHING")
        print("=" * 80)
        print(f"\nFetching courses across {len(self.COMPREHENSIVE_TOPICS)} major categories...")
        print(f"Target: {max_per_topic} courses per topic\n")

        all_courses_dict = {}  # Use dict to deduplicate by ID
        category_stats = {}

        for category, topics in self.COMPREHENSIVE_TOPICS.items():
            print(f"\n{'─' * 80}")
            print(f"Category: {category}")
            print(f"{'─' * 80}")

            category_courses = 0

            for topic in topics:
                try:
                    print(f"  Fetching: {topic}...", end=" ")

                    result = self.service.search_courses(
                        query=topic,
                        page=1,
                        page_size=max_per_topic
                    )

                    courses = result.get('courses', [])
                    new_courses = 0

                    for course in courses:
                        course_id = course.get('id')
                        if course_id and course_id not in all_courses_dict:
                            # Add category tag
                            course['category_tag'] = category
                            course['topic_tag'] = topic
                            all_courses_dict[course_id] = course
                            new_courses += 1

                    category_courses += new_courses
                    print(f"✓ {new_courses} new courses")

                    # Rate limiting - be nice to APIs
                    time.sleep(0.5)

                except Exception as e:
                    print(f"✗ Error: {str(e)}")
                    self.errors.append({
                        'category': category,
                        'topic': topic,
                        'error': str(e)
                    })

            category_stats[category] = category_courses
            print(f"\n  Total new courses in {category}: {category_courses}")

        self.all_courses = list(all_courses_dict.values())

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"\nTotal unique courses fetched: {len(self.all_courses)}")
        print("\nBreakdown by category:")
        for category, count in category_stats.items():
            print(f"  {category:30} {count:5} courses")

        if self.errors:
            print(f"\n⚠ Errors encountered: {len(self.errors)}")

        return self.all_courses

    def fetch_featured_and_popular(self) -> List[Dict]:
        """
        Fetch featured and popular courses.

        Returns:
            List of featured courses
        """
        print("\n" + "=" * 80)
        print("Fetching Featured & Popular Courses")
        print("=" * 80)

        try:
            result = self.service.get_featured_courses(limit=100)
            featured = result.get('courses', [])

            for course in featured:
                course_id = course.get('id')
                if course_id and course_id not in [c['id'] for c in self.all_courses]:
                    course['category_tag'] = 'Featured'
                    self.all_courses.append(course)

            print(f"✓ Added {len(featured)} featured courses")

        except Exception as e:
            print(f"✗ Error fetching featured: {str(e)}")
            self.errors.append({
                'category': 'Featured',
                'error': str(e)
            })

        return self.all_courses

    def fetch_free_courses(self, limit: int = 100) -> List[Dict]:
        """
        Fetch free courses specifically.

        Args:
            limit: Maximum free courses to fetch

        Returns:
            List of free courses
        """
        print("\n" + "=" * 80)
        print("Fetching Free Courses")
        print("=" * 80)

        try:
            result = self.service.search_courses(
                is_free=True,
                page_size=limit
            )

            free_courses = result.get('courses', [])
            new_free = 0

            for course in free_courses:
                course_id = course.get('id')
                if course_id and course_id not in [c['id'] for c in self.all_courses]:
                    course['category_tag'] = 'Free'
                    self.all_courses.append(course)
                    new_free += 1

            print(f"✓ Added {new_free} new free courses")

        except Exception as e:
            print(f"✗ Error fetching free courses: {str(e)}")
            self.errors.append({
                'category': 'Free Courses',
                'error': str(e)
            })

        return self.all_courses

    def save_to_json(self, filename: str = "comprehensive_courses.json"):
        """
        Save all fetched courses to JSON file.

        Args:
            filename: Output filename
        """
        output_path = os.path.join(os.path.dirname(__file__), filename)

        data = {
            'total_courses': len(self.all_courses),
            'fetch_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'categories': list(self.COMPREHENSIVE_TOPICS.keys()),
            'errors': self.errors,
            'courses': self.all_courses
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Saved {len(self.all_courses)} courses to {output_path}")

    def print_statistics(self):
        """Print detailed statistics about fetched courses."""
        print("\n" + "=" * 80)
        print("DETAILED STATISTICS")
        print("=" * 80)

        # Provider breakdown
        providers = {}
        for course in self.all_courses:
            provider = course.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1

        print("\nCourses by Provider:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
            print(f"  {provider:20} {count:5} courses")

        # Price breakdown
        free_count = sum(1 for c in self.all_courses if c.get('isFree', False))
        paid_count = len(self.all_courses) - free_count

        print("\nPricing:")
        print(f"  Free:  {free_count:5} courses ({free_count/len(self.all_courses)*100:.1f}%)")
        print(f"  Paid:  {paid_count:5} courses ({paid_count/len(self.all_courses)*100:.1f}%)")

        # Level breakdown
        levels = {}
        for course in self.all_courses:
            level = course.get('level', 'Unknown')
            levels[level] = levels.get(level, 0) + 1

        print("\nCourses by Level:")
        for level, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
            print(f"  {level:20} {count:5} courses")

        # Top rated courses
        print("\nTop 10 Highest Rated Courses:")
        sorted_by_rating = sorted(
            self.all_courses,
            key=lambda x: (x.get('rating', 0), x.get('reviewCount', 0)),
            reverse=True
        )[:10]

        for i, course in enumerate(sorted_by_rating, 1):
            print(f"  {i:2}. {course.get('title', 'Unknown')[:60]}")
            print(f"      ⭐ {course.get('rating', 0):.1f} | {course.get('provider', 'Unknown')} | "
                  f"{course.get('reviewCount', 0):,} reviews")

    def fetch_all(self, max_per_topic: int = 20):
        """
        Run comprehensive fetch of all courses.

        Args:
            max_per_topic: Maximum courses per topic
        """
        print(f"\nStarting comprehensive course fetch...")
        print(f"This will take a few minutes. Please wait...\n")

        start_time = time.time()

        # Fetch by topics
        self.fetch_by_topics(max_per_topic=max_per_topic)

        # Fetch featured
        self.fetch_featured_and_popular()

        # Fetch free
        self.fetch_free_courses(limit=100)

        # Print statistics
        self.print_statistics()

        # Save to JSON
        self.save_to_json()

        elapsed_time = time.time() - start_time
        print(f"\n✓ Completed in {elapsed_time:.1f} seconds")
        print(f"\nTotal courses fetched: {len(self.all_courses)}")

        if self.errors:
            print(f"\n⚠ Total errors: {len(self.errors)}")
            print("\nFirst 5 errors:")
            for error in self.errors[:5]:
                print(f"  - {error}")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("CAREER GENIE - COMPREHENSIVE COURSE FETCHER")
    print("=" * 80)

    # Check for API key
    api_key = os.getenv('RAPIDAPI_KEY')
    if not api_key:
        print("\n⚠ WARNING: RAPIDAPI_KEY not found in environment!")
        print("  Some course sources may not work.")
        print("  Set RAPIDAPI_KEY in your .env file for full course access.\n")

    fetcher = ComprehensiveCourseFetcher()

    # Fetch all courses
    # Adjust max_per_topic to control total courses fetched
    # 20 topics × 13 categories × 20 courses = ~5,200 courses max
    fetcher.fetch_all(max_per_topic=20)

    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)
    print("\nResults saved to: comprehensive_courses.json")
    print("You can now analyze or import these courses.\n")


if __name__ == '__main__':
    main()
