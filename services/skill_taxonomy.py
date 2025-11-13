"""Comprehensive skill taxonomy covering all major industries."""

# Skill categories and industries
SKILL_TAXONOMY = {
    # Technology & IT
    'technology': {
        'display_name': 'Technology & IT',
        'categories': {
            'programming': {
                'display_name': 'Programming & Development',
                'skills': [
                    'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin',
                    'Go', 'Rust', 'TypeScript', 'R', 'MATLAB', 'SQL', 'HTML/CSS', 'React', 'Angular',
                    'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring Boot', 'ASP.NET'
                ]
            },
            'data_analytics': {
                'display_name': 'Data & Analytics',
                'skills': [
                    'Data Analysis', 'SQL', 'Python', 'R', 'Excel', 'Tableau', 'Power BI',
                    'Data Visualization', 'Statistical Analysis', 'Machine Learning', 'Deep Learning',
                    'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Big Data', 'Hadoop', 'Spark'
                ]
            },
            'cloud_devops': {
                'display_name': 'Cloud & DevOps',
                'skills': [
                    'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins',
                    'Git', 'Linux', 'Bash', 'Terraform', 'Ansible', 'DevOps', 'Microservices'
                ]
            },
            'cybersecurity': {
                'display_name': 'Cybersecurity',
                'skills': [
                    'Network Security', 'Penetration Testing', 'Vulnerability Assessment',
                    'Security Auditing', 'SIEM', 'Firewall Management', 'Incident Response',
                    'Cryptography', 'Ethical Hacking', 'ISO 27001', 'CISSP', 'CEH'
                ]
            }
        }
    },

    # Healthcare & Medical
    'healthcare': {
        'display_name': 'Healthcare & Medical',
        'categories': {
            'clinical': {
                'display_name': 'Clinical Skills',
                'skills': [
                    'Patient Care', 'Clinical Documentation', 'EMR/EHR', 'HIPAA Compliance',
                    'Vital Signs Monitoring', 'IV Therapy', 'Wound Care', 'CPR/BLS', 'ACLS',
                    'Medication Administration', 'Patient Assessment', 'Medical Terminology'
                ]
            },
            'medical_specialties': {
                'display_name': 'Medical Specialties',
                'skills': [
                    'Radiology', 'Cardiology', 'Oncology', 'Pediatrics', 'Surgery', 'Anesthesiology',
                    'Emergency Medicine', 'Family Medicine', 'Internal Medicine', 'Psychiatry',
                    'Orthopedics', 'Neurology', 'Dermatology', 'Obstetrics', 'Gynecology'
                ]
            },
            'healthcare_admin': {
                'display_name': 'Healthcare Administration',
                'skills': [
                    'Healthcare Management', 'Medical Billing', 'Medical Coding', 'ICD-10',
                    'CPT Coding', 'Revenue Cycle Management', 'Healthcare Analytics',
                    'Quality Assurance', 'Regulatory Compliance', 'Risk Management'
                ]
            },
            'laboratory': {
                'display_name': 'Laboratory & Diagnostics',
                'skills': [
                    'Laboratory Testing', 'Phlebotomy', 'Clinical Chemistry', 'Hematology',
                    'Microbiology', 'Immunology', 'Pathology', 'Quality Control', 'Lab Safety'
                ]
            }
        }
    },

    # Finance & Banking
    'finance': {
        'display_name': 'Finance & Banking',
        'categories': {
            'accounting': {
                'display_name': 'Accounting & Bookkeeping',
                'skills': [
                    'Financial Accounting', 'Bookkeeping', 'QuickBooks', 'Accounts Payable',
                    'Accounts Receivable', 'General Ledger', 'Bank Reconciliation', 'GAAP',
                    'Tax Preparation', 'Payroll Processing', 'Cost Accounting', 'Auditing'
                ]
            },
            'financial_analysis': {
                'display_name': 'Financial Analysis',
                'skills': [
                    'Financial Modeling', 'Investment Analysis', 'Valuation', 'DCF Analysis',
                    'Risk Management', 'Portfolio Management', 'Budgeting', 'Forecasting',
                    'Financial Reporting', 'Bloomberg Terminal', 'Excel VBA', 'SQL'
                ]
            },
            'banking': {
                'display_name': 'Banking & Lending',
                'skills': [
                    'Loan Processing', 'Credit Analysis', 'Underwriting', 'Mortgage Lending',
                    'Commercial Banking', 'Wealth Management', 'Treasury Management',
                    'Anti-Money Laundering (AML)', 'KYC', 'Compliance', 'Risk Assessment'
                ]
            }
        }
    },

    # Education & Training
    'education': {
        'display_name': 'Education & Training',
        'categories': {
            'teaching': {
                'display_name': 'Teaching & Instruction',
                'skills': [
                    'Curriculum Development', 'Lesson Planning', 'Classroom Management',
                    'Student Assessment', 'Differentiated Instruction', 'Educational Technology',
                    'Special Education', 'ESL/ELL', 'Online Teaching', 'Learning Management Systems',
                    'Google Classroom', 'Canvas LMS', 'Blackboard', 'Student Engagement'
                ]
            },
            'training_development': {
                'display_name': 'Training & Development',
                'skills': [
                    'Corporate Training', 'Employee Development', 'Instructional Design',
                    'E-Learning Development', 'Training Needs Analysis', 'Adult Learning Theory',
                    'Performance Management', 'Coaching', 'Mentoring', 'Workshop Facilitation'
                ]
            },
            'administration': {
                'display_name': 'Educational Administration',
                'skills': [
                    'Educational Leadership', 'School Administration', 'Budget Management',
                    'Policy Development', 'Student Services', 'Academic Advising',
                    'Enrollment Management', 'Accreditation', 'Program Evaluation'
                ]
            }
        }
    },

    # Marketing & Sales
    'marketing_sales': {
        'display_name': 'Marketing & Sales',
        'categories': {
            'digital_marketing': {
                'display_name': 'Digital Marketing',
                'skills': [
                    'SEO', 'SEM', 'Google Analytics', 'Google Ads', 'Facebook Ads', 'Social Media Marketing',
                    'Content Marketing', 'Email Marketing', 'Marketing Automation', 'HubSpot',
                    'Salesforce Marketing Cloud', 'A/B Testing', 'Conversion Optimization', 'PPC'
                ]
            },
            'sales': {
                'display_name': 'Sales & Business Development',
                'skills': [
                    'B2B Sales', 'B2C Sales', 'Lead Generation', 'Cold Calling', 'Prospecting',
                    'Sales Presentations', 'Negotiation', 'Account Management', 'CRM', 'Salesforce',
                    'Pipeline Management', 'Sales Forecasting', 'Closing Deals', 'Customer Retention'
                ]
            },
            'brand_creative': {
                'display_name': 'Brand & Creative',
                'skills': [
                    'Brand Strategy', 'Brand Management', 'Copywriting', 'Creative Writing',
                    'Graphic Design', 'Adobe Creative Suite', 'Photoshop', 'Illustrator',
                    'Video Production', 'Photography', 'UI/UX Design', 'Figma', 'Sketch'
                ]
            }
        }
    },

    # Manufacturing & Operations
    'manufacturing': {
        'display_name': 'Manufacturing & Operations',
        'categories': {
            'production': {
                'display_name': 'Production & Assembly',
                'skills': [
                    'Manufacturing Processes', 'Assembly Line Operations', 'Quality Control',
                    'Lean Manufacturing', 'Six Sigma', 'Kaizen', '5S', 'Production Planning',
                    'Inventory Management', 'Machine Operation', 'CNC Programming', 'Welding'
                ]
            },
            'supply_chain': {
                'display_name': 'Supply Chain & Logistics',
                'skills': [
                    'Supply Chain Management', 'Logistics', 'Procurement', 'Vendor Management',
                    'Warehouse Management', 'Distribution', 'SAP', 'Oracle SCM', 'Demand Planning',
                    'Inventory Optimization', 'Transportation Management', 'Import/Export'
                ]
            },
            'maintenance': {
                'display_name': 'Maintenance & Engineering',
                'skills': [
                    'Preventive Maintenance', 'Equipment Repair', 'Troubleshooting', 'PLC Programming',
                    'HVAC', 'Electrical Systems', 'Mechanical Systems', 'Hydraulics', 'Pneumatics',
                    'Blueprint Reading', 'CAD', 'AutoCAD', 'SolidWorks'
                ]
            }
        }
    },

    # Hospitality & Food Services
    'hospitality': {
        'display_name': 'Hospitality & Food Services',
        'categories': {
            'hotel_management': {
                'display_name': 'Hotel & Resort Management',
                'skills': [
                    'Hotel Management', 'Front Desk Operations', 'Guest Services', 'Reservations',
                    'Revenue Management', 'Hospitality Management', 'Property Management Systems',
                    'Opera PMS', 'Customer Service', 'Housekeeping Management', 'Event Planning'
                ]
            },
            'food_beverage': {
                'display_name': 'Food & Beverage',
                'skills': [
                    'Food Preparation', 'Culinary Arts', 'Menu Planning', 'Kitchen Management',
                    'Food Safety', 'ServSafe', 'Bartending', 'Wine Knowledge', 'Restaurant Management',
                    'Inventory Management', 'Cost Control', 'Health Code Compliance', 'Catering'
                ]
            },
            'travel_tourism': {
                'display_name': 'Travel & Tourism',
                'skills': [
                    'Travel Planning', 'Tour Operations', 'Customer Service', 'Destination Knowledge',
                    'Travel Booking Systems', 'Amadeus', 'Sabre', 'Tourism Marketing',
                    'Event Coordination', 'Cruise Operations', 'Travel Documentation'
                ]
            }
        }
    },

    # Retail & Customer Service
    'retail': {
        'display_name': 'Retail & Customer Service',
        'categories': {
            'retail_operations': {
                'display_name': 'Retail Operations',
                'skills': [
                    'Retail Management', 'Store Operations', 'Visual Merchandising', 'Inventory Management',
                    'POS Systems', 'Loss Prevention', 'Cash Handling', 'Stock Management',
                    'Product Knowledge', 'Sales Associates Training', 'Store Opening/Closing'
                ]
            },
            'customer_service': {
                'display_name': 'Customer Service',
                'skills': [
                    'Customer Support', 'Problem Resolution', 'Active Listening', 'Empathy',
                    'Communication', 'Zendesk', 'Freshdesk', 'Live Chat Support', 'Phone Support',
                    'Email Support', 'Complaint Handling', 'Customer Satisfaction', 'CRM'
                ]
            },
            'ecommerce': {
                'display_name': 'E-commerce',
                'skills': [
                    'E-commerce Management', 'Shopify', 'WooCommerce', 'Amazon FBA', 'Product Listings',
                    'Marketplace Management', 'Online Customer Service', 'Order Fulfillment',
                    'Returns Management', 'E-commerce Analytics', 'Conversion Optimization'
                ]
            }
        }
    },

    # Construction & Real Estate
    'construction': {
        'display_name': 'Construction & Real Estate',
        'categories': {
            'construction_trades': {
                'display_name': 'Construction Trades',
                'skills': [
                    'Carpentry', 'Plumbing', 'Electrical Work', 'HVAC Installation', 'Masonry',
                    'Roofing', 'Drywall', 'Painting', 'Flooring', 'Concrete Work', 'Framing',
                    'Blueprint Reading', 'Building Codes', 'OSHA Safety', 'Power Tools'
                ]
            },
            'project_management': {
                'display_name': 'Construction Management',
                'skills': [
                    'Construction Management', 'Project Planning', 'Cost Estimation', 'Scheduling',
                    'Contract Management', 'Site Supervision', 'Quality Control', 'Safety Management',
                    'Microsoft Project', 'Primavera', 'Procore', 'BIM', 'AutoCAD', 'Permitting'
                ]
            },
            'real_estate': {
                'display_name': 'Real Estate',
                'skills': [
                    'Real Estate Sales', 'Property Management', 'Leasing', 'Real Estate Marketing',
                    'Market Analysis', 'Property Valuation', 'Contract Negotiation', 'MLS',
                    'Real Estate Law', 'Tenant Relations', 'Property Inspections', 'Investment Analysis'
                ]
            }
        }
    },

    # Legal & Compliance
    'legal': {
        'display_name': 'Legal & Compliance',
        'categories': {
            'legal_practice': {
                'display_name': 'Legal Practice',
                'skills': [
                    'Legal Research', 'Legal Writing', 'Contract Law', 'Litigation', 'Discovery',
                    'Legal Analysis', 'Case Management', 'Client Counseling', 'Negotiation',
                    'Court Procedures', 'LexisNexis', 'Westlaw', 'e-Discovery', 'Mediation'
                ]
            },
            'paralegal': {
                'display_name': 'Paralegal & Legal Support',
                'skills': [
                    'Document Preparation', 'Legal Filing', 'Case Research', 'Trial Preparation',
                    'Client Interviews', 'Legal Documentation', 'Case Management Software',
                    'Notary Public', 'Court Filing', 'Record Management', 'Legal Transcription'
                ]
            },
            'compliance': {
                'display_name': 'Compliance & Regulatory',
                'skills': [
                    'Regulatory Compliance', 'Risk Assessment', 'Policy Development', 'Auditing',
                    'GDPR', 'HIPAA', 'SOX Compliance', 'Anti-Money Laundering', 'Corporate Governance',
                    'Compliance Training', 'Internal Controls', 'Ethics Programs'
                ]
            }
        }
    },

    # Human Resources
    'human_resources': {
        'display_name': 'Human Resources',
        'categories': {
            'recruitment': {
                'display_name': 'Recruitment & Talent Acquisition',
                'skills': [
                    'Recruiting', 'Talent Acquisition', 'Candidate Screening', 'Interviewing',
                    'Applicant Tracking Systems', 'LinkedIn Recruiter', 'Boolean Search',
                    'Job Posting', 'Offer Negotiation', 'Employer Branding', 'Onboarding'
                ]
            },
            'hr_operations': {
                'display_name': 'HR Operations',
                'skills': [
                    'HRIS', 'Workday', 'ADP', 'Benefits Administration', 'Payroll', 'FMLA',
                    'Workers Compensation', 'Employee Relations', 'Performance Management',
                    'HR Analytics', 'Employee Engagement', 'HR Compliance', 'Labor Law'
                ]
            },
            'learning_development': {
                'display_name': 'Learning & Development',
                'skills': [
                    'Training & Development', 'Organizational Development', 'Change Management',
                    'Leadership Development', 'Succession Planning', 'Talent Management',
                    'Performance Coaching', 'Career Development', 'Learning Management Systems'
                ]
            }
        }
    },

    # Media & Communications
    'media': {
        'display_name': 'Media & Communications',
        'categories': {
            'journalism': {
                'display_name': 'Journalism & Writing',
                'skills': [
                    'Journalism', 'News Writing', 'Investigative Reporting', 'Copyediting',
                    'Fact-Checking', 'Interviewing', 'AP Style', 'Content Writing', 'Blogging',
                    'Technical Writing', 'Grant Writing', 'Proofreading', 'WordPress'
                ]
            },
            'broadcasting': {
                'display_name': 'Broadcasting & Production',
                'skills': [
                    'Video Production', 'Video Editing', 'Audio Production', 'Broadcasting',
                    'Camera Operation', 'Final Cut Pro', 'Adobe Premiere', 'After Effects',
                    'Lighting', 'Sound Design', 'Live Production', 'Streaming'
                ]
            },
            'public_relations': {
                'display_name': 'Public Relations',
                'skills': [
                    'Public Relations', 'Media Relations', 'Press Releases', 'Crisis Communication',
                    'Internal Communications', 'Corporate Communications', 'Event Management',
                    'Spokesperson Training', 'Media Monitoring', 'Reputation Management'
                ]
            }
        }
    },

    # Government & Public Service
    'government': {
        'display_name': 'Government & Public Service',
        'categories': {
            'public_administration': {
                'display_name': 'Public Administration',
                'skills': [
                    'Public Policy', 'Government Relations', 'Public Administration',
                    'Budget Management', 'Grant Management', 'Public Speaking', 'Community Engagement',
                    'Policy Analysis', 'Program Management', 'Legislative Process', 'Advocacy'
                ]
            },
            'law_enforcement': {
                'display_name': 'Law Enforcement & Security',
                'skills': [
                    'Law Enforcement', 'Criminal Investigation', 'Crime Prevention', 'Report Writing',
                    'Evidence Collection', 'Firearms Training', 'Defensive Tactics', 'Emergency Response',
                    'Community Policing', 'Security Operations', 'Surveillance', 'Crisis Intervention'
                ]
            },
            'social_services': {
                'display_name': 'Social Services',
                'skills': [
                    'Case Management', 'Social Work', 'Counseling', 'Crisis Intervention',
                    'Client Assessment', 'Resource Coordination', 'Program Development',
                    'Community Outreach', 'Mental Health Support', 'Child Welfare', 'Elder Care'
                ]
            }
        }
    }
}


# Soft skills that apply to ALL industries
UNIVERSAL_SOFT_SKILLS = {
    'communication': {
        'display_name': 'Communication',
        'skills': [
            'Verbal Communication', 'Written Communication', 'Active Listening', 'Presentation Skills',
            'Public Speaking', 'Interpersonal Communication', 'Cross-Cultural Communication',
            'Persuasion', 'Storytelling', 'Business Writing', 'Email Etiquette'
        ]
    },
    'leadership': {
        'display_name': 'Leadership & Management',
        'skills': [
            'Leadership', 'Team Management', 'Project Management', 'Decision Making',
            'Strategic Planning', 'Conflict Resolution', 'Delegation', 'Motivation',
            'Change Management', 'Performance Management', 'Coaching', 'Mentoring'
        ]
    },
    'problem_solving': {
        'display_name': 'Problem Solving & Critical Thinking',
        'skills': [
            'Problem Solving', 'Critical Thinking', 'Analytical Skills', 'Research',
            'Creativity', 'Innovation', 'Strategic Thinking', 'Troubleshooting',
            'Root Cause Analysis', 'Continuous Improvement', 'Process Optimization'
        ]
    },
    'collaboration': {
        'display_name': 'Collaboration & Teamwork',
        'skills': [
            'Teamwork', 'Collaboration', 'Cross-Functional Collaboration', 'Networking',
            'Relationship Building', 'Stakeholder Management', 'Facilitation',
            'Consensus Building', 'Remote Collaboration', 'Virtual Teams'
        ]
    },
    'organization': {
        'display_name': 'Organization & Time Management',
        'skills': [
            'Time Management', 'Organization', 'Prioritization', 'Task Management',
            'Attention to Detail', 'Multitasking', 'Planning', 'Scheduling',
            'Meeting Deadlines', 'Workflow Management', 'Resource Management'
        ]
    },
    'adaptability': {
        'display_name': 'Adaptability & Learning',
        'skills': [
            'Adaptability', 'Flexibility', 'Quick Learning', 'Resilience',
            'Growth Mindset', 'Self-Learning', 'Continuous Learning', 'Open-Mindedness',
            'Change Management', 'Stress Management', 'Emotional Intelligence'
        ]
    }
}


# Microsoft Office & Common Tools (applies to most industries)
COMMON_TECHNICAL_SKILLS = {
    'office_productivity': {
        'display_name': 'Office & Productivity Tools',
        'skills': [
            'Microsoft Office', 'Microsoft Word', 'Microsoft Excel', 'Microsoft PowerPoint',
            'Microsoft Outlook', 'Google Workspace', 'Google Docs', 'Google Sheets',
            'Google Slides', 'Slack', 'Microsoft Teams', 'Zoom', 'Asana', 'Trello',
            'Monday.com', 'Notion', 'Data Entry', 'Typing', 'File Management'
        ]
    }
}


class SkillTaxonomyService:
    """Service for managing and querying the skill taxonomy."""

    @staticmethod
    def get_all_industries():
        """Get list of all industries with display names."""
        return {
            industry_key: data['display_name']
            for industry_key, data in SKILL_TAXONOMY.items()
        }

    @staticmethod
    def get_skills_by_industry(industry_key):
        """
        Get all skills for a specific industry.

        Args:
            industry_key: Industry key (e.g., 'technology', 'healthcare')

        Returns:
            dict: Skills organized by category
        """
        if industry_key not in SKILL_TAXONOMY:
            return {}

        return SKILL_TAXONOMY[industry_key]['categories']

    @staticmethod
    def get_skills_by_category(industry_key, category_key):
        """
        Get skills for a specific category within an industry.

        Args:
            industry_key: Industry key
            category_key: Category key within industry

        Returns:
            list: List of skills
        """
        if industry_key not in SKILL_TAXONOMY:
            return []

        categories = SKILL_TAXONOMY[industry_key]['categories']
        if category_key not in categories:
            return []

        return categories[category_key]['skills']

    @staticmethod
    def get_all_skills_flat(industry_key=None):
        """
        Get flat list of all skills, optionally filtered by industry.

        Args:
            industry_key: Optional industry filter

        Returns:
            list: Flat list of all skills
        """
        all_skills = []

        if industry_key:
            # Get skills for specific industry
            if industry_key in SKILL_TAXONOMY:
                for category_data in SKILL_TAXONOMY[industry_key]['categories'].values():
                    all_skills.extend(category_data['skills'])
        else:
            # Get all skills across all industries
            for industry_data in SKILL_TAXONOMY.values():
                for category_data in industry_data['categories'].values():
                    all_skills.extend(category_data['skills'])

        # Add soft skills
        for category_data in UNIVERSAL_SOFT_SKILLS.values():
            all_skills.extend(category_data['skills'])

        # Add common technical skills
        for category_data in COMMON_TECHNICAL_SKILLS.values():
            all_skills.extend(category_data['skills'])

        # Remove duplicates and sort
        return sorted(list(set(all_skills)))

    @staticmethod
    def get_soft_skills():
        """Get all soft skills that apply universally."""
        return UNIVERSAL_SOFT_SKILLS

    @staticmethod
    def get_common_technical_skills():
        """Get common technical skills (Office, productivity tools)."""
        return COMMON_TECHNICAL_SKILLS

    @staticmethod
    def search_skills(query, industry_key=None):
        """
        Search for skills matching a query.

        Args:
            query: Search query string
            industry_key: Optional industry filter

        Returns:
            list: Matching skills with industry/category context
        """
        query_lower = query.lower()
        results = []

        # Search industry-specific skills
        industries_to_search = [industry_key] if industry_key else SKILL_TAXONOMY.keys()

        for ind_key in industries_to_search:
            if ind_key not in SKILL_TAXONOMY:
                continue

            industry_data = SKILL_TAXONOMY[ind_key]
            for cat_key, cat_data in industry_data['categories'].items():
                for skill in cat_data['skills']:
                    if query_lower in skill.lower():
                        results.append({
                            'skill': skill,
                            'industry': industry_data['display_name'],
                            'category': cat_data['display_name'],
                            'industry_key': ind_key,
                            'category_key': cat_key
                        })

        # Search soft skills
        for cat_key, cat_data in UNIVERSAL_SOFT_SKILLS.items():
            for skill in cat_data['skills']:
                if query_lower in skill.lower():
                    results.append({
                        'skill': skill,
                        'industry': 'Universal',
                        'category': cat_data['display_name'],
                        'industry_key': 'universal',
                        'category_key': cat_key
                    })

        return results

    @staticmethod
    def get_related_skills(skill_name, industry_key=None):
        """
        Get skills related to a given skill (same category).

        Args:
            skill_name: Skill to find related skills for
            industry_key: Optional industry filter

        Returns:
            list: Related skills
        """
        # Find the skill's category
        skill_context = None

        industries_to_search = [industry_key] if industry_key else SKILL_TAXONOMY.keys()

        for ind_key in industries_to_search:
            if ind_key not in SKILL_TAXONOMY:
                continue

            for cat_key, cat_data in SKILL_TAXONOMY[ind_key]['categories'].items():
                if skill_name in cat_data['skills']:
                    skill_context = (ind_key, cat_key)
                    break

            if skill_context:
                break

        if not skill_context:
            return []

        # Return all skills in the same category (excluding the original skill)
        ind_key, cat_key = skill_context
        all_skills = SKILL_TAXONOMY[ind_key]['categories'][cat_key]['skills']

        return [s for s in all_skills if s != skill_name]

    @staticmethod
    def recommend_skills_for_onboarding(user_data):
        """
        Recommend diverse skills for user during onboarding based on their profile.

        Args:
            user_data: User profile data including industry preferences, target roles, etc.

        Returns:
            dict: Organized skill recommendations
        """
        recommendations = {
            'industry_specific': [],
            'soft_skills': [],
            'common_technical': [],
            'total_count': 0
        }

        # Get user's target industries
        target_industries = user_data.get('jobPreferences', {}).get('industries', [])
        target_roles = user_data.get('jobPreferences', {}).get('targetRoles', [])

        # If no industries specified, recommend from multiple industries
        if not target_industries:
            # Provide sampler from diverse industries
            sample_industries = ['technology', 'healthcare', 'finance', 'marketing_sales',
                               'education', 'manufacturing', 'retail', 'hospitality']

            for ind_key in sample_industries:
                if ind_key in SKILL_TAXONOMY:
                    # Get first category from each industry
                    first_category = list(SKILL_TAXONOMY[ind_key]['categories'].values())[0]
                    recommendations['industry_specific'].extend([
                        {
                            'skill': skill,
                            'industry': SKILL_TAXONOMY[ind_key]['display_name'],
                            'category': first_category['display_name']
                        }
                        for skill in first_category['skills'][:5]  # Top 5 from each
                    ])
        else:
            # Provide skills from user's target industries
            for industry_name in target_industries:
                # Find matching industry key
                ind_key = None
                for key, data in SKILL_TAXONOMY.items():
                    if data['display_name'].lower() == industry_name.lower():
                        ind_key = key
                        break

                if ind_key and ind_key in SKILL_TAXONOMY:
                    # Get all categories for this industry
                    for cat_data in SKILL_TAXONOMY[ind_key]['categories'].values():
                        recommendations['industry_specific'].extend([
                            {
                                'skill': skill,
                                'industry': SKILL_TAXONOMY[ind_key]['display_name'],
                                'category': cat_data['display_name']
                            }
                            for skill in cat_data['skills'][:10]  # Top 10 per category
                        ])

        # Always include soft skills (essential for all jobs)
        for cat_data in UNIVERSAL_SOFT_SKILLS.values():
            recommendations['soft_skills'].extend([
                {
                    'skill': skill,
                    'category': cat_data['display_name']
                }
                for skill in cat_data['skills'][:8]  # Top 8 per category
            ])

        # Include common technical skills
        for cat_data in COMMON_TECHNICAL_SKILLS.values():
            recommendations['common_technical'].extend([
                {
                    'skill': skill,
                    'category': cat_data['display_name']
                }
                for skill in cat_data['skills'][:10]
            ])

        # Calculate total
        recommendations['total_count'] = (
            len(recommendations['industry_specific']) +
            len(recommendations['soft_skills']) +
            len(recommendations['common_technical'])
        )

        return recommendations
