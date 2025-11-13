"""Skill recommendation service for diverse career paths."""
from services.skill_taxonomy import (
    SkillTaxonomyService,
    SKILL_TAXONOMY,
    UNIVERSAL_SOFT_SKILLS,
    COMMON_TECHNICAL_SKILLS
)
from models.user_enhanced import EnhancedUser


class SkillRecommendationService:
    """Service for recommending skills based on user profile and career goals."""

    def __init__(self):
        self.taxonomy = SkillTaxonomyService()

    def get_onboarding_skill_recommendations(self, user_data):
        """
        Get diverse skill recommendations during onboarding.
        Ensures recommendations span multiple industries if user hasn't specified preferences.

        Args:
            user_data: User profile data from onboarding

        Returns:
            dict: Organized skill recommendations with diversity
        """
        target_industries = user_data.get('jobPreferences', {}).get('industries', [])
        target_roles = user_data.get('jobPreferences', {}).get('targetRoles', [])
        career_level = user_data.get('professional', {}).get('careerLevel', 'entry')
        current_skills = [skill.get('name', '') for skill in user_data.get('skills', [])]

        recommendations = {
            'recommended_skills': [],
            'by_category': {},
            'priority_skills': [],
            'diverse_options': [],
            'metadata': {
                'total_recommendations': 0,
                'industries_covered': [],
                'includes_soft_skills': True,
                'career_level_appropriate': True
            }
        }

        # 1. Industry-specific skills
        if target_industries:
            # User has specified industries - focus on those
            industry_skills = self._get_industry_specific_skills(
                target_industries,
                current_skills,
                career_level
            )
            recommendations['recommended_skills'].extend(industry_skills)
            recommendations['metadata']['industries_covered'] = target_industries
        else:
            # No industries specified - provide diverse sampling
            diverse_skills = self._get_diverse_industry_sampling(
                current_skills,
                career_level
            )
            recommendations['recommended_skills'].extend(diverse_skills)
            recommendations['diverse_options'] = diverse_skills
            recommendations['metadata']['industries_covered'] = [
                'Technology', 'Healthcare', 'Finance', 'Marketing & Sales',
                'Education', 'Retail', 'Manufacturing', 'Hospitality'
            ]

        # 2. Universal soft skills (essential for all careers)
        soft_skills = self._get_career_level_soft_skills(
            career_level,
            current_skills
        )
        recommendations['recommended_skills'].extend(soft_skills)

        # 3. Common technical skills (Office, productivity)
        common_skills = self._get_common_technical_skills(current_skills)
        recommendations['recommended_skills'].extend(common_skills)

        # 4. Identify priority skills based on job market demand
        recommendations['priority_skills'] = self._identify_priority_skills(
            recommendations['recommended_skills'],
            target_roles,
            target_industries
        )

        # 5. Organize by category for better UX
        recommendations['by_category'] = self._organize_by_category(
            recommendations['recommended_skills']
        )

        # Update metadata
        recommendations['metadata']['total_recommendations'] = len(
            recommendations['recommended_skills']
        )

        return recommendations

    def _get_industry_specific_skills(self, target_industries, current_skills, career_level):
        """Get skills specific to user's target industries."""
        industry_skills = []

        for industry_name in target_industries:
            # Find matching industry in taxonomy
            industry_key = self._find_industry_key(industry_name)

            if industry_key and industry_key in SKILL_TAXONOMY:
                industry_data = SKILL_TAXONOMY[industry_key]

                # Get skills from all categories in this industry
                for category_key, category_data in industry_data['categories'].items():
                    category_skills = category_data['skills']

                    # Filter out skills user already has
                    new_skills = [
                        skill for skill in category_skills
                        if skill not in current_skills
                    ]

                    # Prioritize based on career level
                    skills_to_recommend = self._filter_by_career_level(
                        new_skills,
                        career_level
                    )

                    # Add to recommendations
                    for skill in skills_to_recommend[:15]:  # Top 15 per category
                        industry_skills.append({
                            'skill': skill,
                            'industry': industry_data['display_name'],
                            'category': category_data['display_name'],
                            'source': 'industry_match',
                            'priority': self._calculate_skill_priority(skill, career_level)
                        })

        return industry_skills

    def _get_diverse_industry_sampling(self, current_skills, career_level):
        """
        Provide diverse skill sampling across multiple industries.
        Used when user hasn't specified target industries.
        """
        diverse_skills = []

        # Sample from all major industries
        sample_count_per_industry = 8

        for industry_key, industry_data in SKILL_TAXONOMY.items():
            # Get first category from each industry for diversity
            first_category = list(industry_data['categories'].values())[0]
            category_skills = first_category['skills']

            # Filter out existing skills
            new_skills = [
                skill for skill in category_skills
                if skill not in current_skills
            ]

            # Get appropriate skills for career level
            filtered_skills = self._filter_by_career_level(new_skills, career_level)

            # Add top skills from this industry
            for skill in filtered_skills[:sample_count_per_industry]:
                diverse_skills.append({
                    'skill': skill,
                    'industry': industry_data['display_name'],
                    'category': first_category['display_name'],
                    'source': 'diverse_sampling',
                    'priority': 'medium'
                })

        return diverse_skills

    def _get_career_level_soft_skills(self, career_level, current_skills):
        """Get soft skills appropriate for career level."""
        soft_skills = []

        # Determine which soft skill categories are most important by level
        priority_categories = {
            'entry': ['communication', 'collaboration', 'adaptability', 'organization'],
            'junior': ['communication', 'problem_solving', 'collaboration', 'organization'],
            'mid': ['leadership', 'problem_solving', 'communication', 'collaboration'],
            'senior': ['leadership', 'problem_solving', 'collaboration', 'organization'],
            'executive': ['leadership', 'problem_solving', 'collaboration', 'adaptability'],
            'c-level': ['leadership', 'problem_solving', 'collaboration', 'adaptability']
        }

        relevant_categories = priority_categories.get(career_level, priority_categories['mid'])

        for category_key in relevant_categories:
            if category_key in UNIVERSAL_SOFT_SKILLS:
                category_data = UNIVERSAL_SOFT_SKILLS[category_key]
                category_skills = category_data['skills']

                # Filter out existing skills
                new_skills = [
                    skill for skill in category_skills
                    if skill not in current_skills
                ]

                # Add top skills
                for skill in new_skills[:6]:  # Top 6 per category
                    soft_skills.append({
                        'skill': skill,
                        'industry': 'Universal',
                        'category': category_data['display_name'],
                        'source': 'soft_skills',
                        'priority': 'high' if category_key in relevant_categories[:2] else 'medium'
                    })

        return soft_skills

    def _get_common_technical_skills(self, current_skills):
        """Get common technical skills (Office, productivity tools)."""
        common_skills = []

        for category_data in COMMON_TECHNICAL_SKILLS.values():
            category_skills = category_data['skills']

            # Filter out existing skills
            new_skills = [
                skill for skill in category_skills
                if skill not in current_skills
            ]

            # Add top skills
            for skill in new_skills[:10]:  # Top 10
                common_skills.append({
                    'skill': skill,
                    'industry': 'Universal',
                    'category': category_data['display_name'],
                    'source': 'common_technical',
                    'priority': 'medium'
                })

        return common_skills

    def _filter_by_career_level(self, skills, career_level):
        """
        Filter skills appropriate for career level.
        Entry-level: Focus on foundational skills
        Senior+: Focus on advanced/specialized skills
        """
        # For now, return all skills
        # In future, could add skill-level mapping to taxonomy
        return skills

    def _calculate_skill_priority(self, skill, career_level):
        """Calculate priority level for a skill."""
        # Leadership skills are high priority for senior+ roles
        leadership_keywords = ['management', 'leadership', 'strategic', 'director', 'executive']
        if career_level in ['senior', 'executive', 'c-level']:
            if any(keyword in skill.lower() for keyword in leadership_keywords):
                return 'high'

        # Technical skills are high priority for entry/mid roles
        technical_keywords = ['programming', 'software', 'technical', 'system', 'tool']
        if career_level in ['entry', 'junior', 'mid']:
            if any(keyword in skill.lower() for keyword in technical_keywords):
                return 'high'

        return 'medium'

    def _identify_priority_skills(self, all_skills, target_roles, target_industries):
        """Identify priority skills based on market demand and user goals."""
        priority_skills = []

        # Skills with high priority
        high_priority = [skill for skill in all_skills if skill.get('priority') == 'high']

        # Add top 20 high-priority skills
        priority_skills.extend(high_priority[:20])

        # If less than 20, add some medium priority skills
        if len(priority_skills) < 20:
            medium_priority = [skill for skill in all_skills if skill.get('priority') == 'medium']
            priority_skills.extend(medium_priority[:20 - len(priority_skills)])

        return priority_skills

    def _organize_by_category(self, skills):
        """Organize skills by category for better presentation."""
        by_category = {}

        for skill_data in skills:
            category = skill_data.get('category', 'Other')

            if category not in by_category:
                by_category[category] = []

            by_category[category].append(skill_data)

        return by_category

    def _find_industry_key(self, industry_name):
        """Find industry key from display name."""
        industry_name_lower = industry_name.lower()

        for key, data in SKILL_TAXONOMY.items():
            if data['display_name'].lower() == industry_name_lower:
                return key

        return None

    def recommend_skills_for_job(self, job_data, user_profile):
        """
        Recommend skills user should develop for a specific job.

        Args:
            job_data: Job posting data
            user_profile: User's profile with current skills

        Returns:
            dict: Skill gap analysis and recommendations
        """
        job_required_skills = self._extract_job_skills(job_data)
        user_skills = [skill.get('name', '') for skill in user_profile.get('skills', [])]

        # Identify missing skills
        missing_skills = []
        for job_skill in job_required_skills:
            if job_skill not in user_skills:
                missing_skills.append(job_skill)

        # Find related/alternative skills user could learn
        alternative_skills = []
        for missing_skill in missing_skills:
            related = self.taxonomy.get_related_skills(missing_skill)
            alternative_skills.extend(related[:3])  # Top 3 related skills

        return {
            'required_skills': job_required_skills,
            'missing_skills': missing_skills,
            'alternative_skills': list(set(alternative_skills)),
            'match_percentage': (
                (len(job_required_skills) - len(missing_skills)) / len(job_required_skills) * 100
                if job_required_skills else 0
            )
        }

    def _extract_job_skills(self, job_data):
        """Extract skills from job posting."""
        # Simple extraction - could be enhanced with NLP
        skills = []

        # Get from requirements field
        requirements = job_data.get('requirements', '')
        if isinstance(requirements, str):
            # Search for known skills in requirements text
            all_known_skills = self.taxonomy.get_all_skills_flat()

            for skill in all_known_skills:
                if skill.lower() in requirements.lower():
                    skills.append(skill)

        # Get from explicit skills field if available
        if 'skills' in job_data:
            skills.extend(job_data['skills'])

        return list(set(skills))

    def get_skill_development_path(self, user_id):
        """
        Create a skill development path for user based on their goals and gaps.

        Args:
            user_id: User ID

        Returns:
            dict: Structured learning path
        """
        # This would integrate with course recommendation system
        # For now, just return identified skill gaps
        skill_gaps = EnhancedUser.get_skill_gaps(user_id)

        learning_path = {
            'immediate_priority': [],
            'short_term': [],
            'long_term': []
        }

        for gap in skill_gaps:
            priority = gap.get('priority', 'medium')
            frequency = gap.get('frequency', 1)

            if priority == 'high' or frequency >= 5:
                learning_path['immediate_priority'].append(gap)
            elif frequency >= 3:
                learning_path['short_term'].append(gap)
            else:
                learning_path['long_term'].append(gap)

        return learning_path
