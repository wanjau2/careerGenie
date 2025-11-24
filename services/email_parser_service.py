"""Email parsing service to detect job application statuses from email content."""
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailParserService:
    """Service for parsing job application emails and detecting status updates."""

    # Keyword patterns for different application statuses
    STATUS_PATTERNS = {
        'rejected': [
            # Direct rejection phrases
            r'(?i)(we\s+(regret|are\s+sorry|apologize)\s+to\s+(inform|tell)\s+you)',
            r'(?i)(unfortunately|regrettably)[\s,]+we\s+(will\s+not|cannot|are\s+unable)',
            r'(?i)(not\s+be\s+moving\s+forward|will\s+not\s+be\s+proceeding)',
            r'(?i)(other\s+candidates?\s+whose|selected\s+another\s+candidate)',
            r'(?i)(better\s+match|better\s+fit\s+for\s+this\s+position)',
            r'(?i)(chosen\s+to\s+pursue\s+other|application\s+has\s+been\s+unsuccessful)',
            r'(?i)(decided\s+not\s+to\s+move\s+forward|no\s+longer\s+considering)',
            r'(?i)thanks?\s+for\s+(your\s+)?(interest|applying)(?!.*interview)',
            r'(?i)(position\s+has\s+been\s+filled|role\s+has\s+been\s+filled)',
        ],
        'interview_scheduled': [
            # Interview invitation phrases
            r'(?i)(schedule\s+an?\s+interview|interview\s+scheduling)',
            r'(?i)(would\s+like\s+to\s+(schedule|arrange|set\s+up)\s+an?\s+(call|meeting|interview))',
            r'(?i)(invite\s+you\s+to\s+(an?\s+)?(interview|phone\s+call|video\s+call))',
            r'(?i)(interview\s+(on|at|for)\s+\d{1,2})',
            r'(?i)(next\s+step.*interview|move\s+forward.*interview)',
            r'(?i)(meet\s+with\s+(our\s+)?team|speak\s+with\s+(our\s+)?team)',
            r'(?i)(phone\s+screen|initial\s+call|screening\s+call)',
            r'(?i)(available\s+for\s+(an?\s+)?(call|interview|meeting))',
            r'(?i)(interview\s+details|interview\s+confirmation)',
        ],
        'under_review': [
            # Application being reviewed
            r'(?i)(reviewing\s+your\s+application|application\s+(is\s+)?under\s+review)',
            r'(?i)(received\s+your\s+application|thank\s+you\s+for\s+(your\s+)?application)',
            r'(?i)(application\s+has\s+been\s+received|successfully\s+received)',
            r'(?i)(evaluating\s+your|assessing\s+your\s+qualifications)',
            r'(?i)(reviewing\s+(all\s+)?applications|review\s+process)',
            r'(?i)(currently\s+reviewing|in\s+the\s+review\s+process)',
        ],
        'offer_received': [
            # Job offer phrases
            r'(?i)(pleased\s+to\s+(extend|offer)|happy\s+to\s+offer)',
            r'(?i)(offer\s+of\s+employment|formal\s+offer)',
            r'(?i)(would\s+like\s+to\s+offer\s+you\s+the\s+position)',
            r'(?i)(congratulations.*selected|you\s+have\s+been\s+selected)',
            r'(?i)(offer\s+letter|employment\s+contract)',
            r'(?i)(join\s+(our\s+)?team|welcome\s+to\s+(the\s+)?team)',
            r'(?i)(accept\s+(the\s+)?offer|offer\s+acceptance)',
            r'(?i)(compensation\s+package|salary\s+offer)',
        ],
        'interviewed': [
            # Post-interview communication
            r'(?i)(thank\s+you\s+for.*interview|thanks?\s+for\s+(coming\s+in|speaking\s+with))',
            r'(?i)(enjoyed\s+(meeting|speaking\s+with)\s+you)',
            r'(?i)(following\s+up\s+(on|from)\s+(our\s+)?interview)',
            r'(?i)(next\s+steps\s+after.*interview)',
            r'(?i)(interview\s+follow[\s-]?up)',
        ],
    }

    # Company-related patterns to help match emails to applications
    COMPANY_PATTERNS = [
        r'(?i)(from|at)\s+([A-Z][A-Za-z0-9\s&,\.]+(?:Inc|LLC|Corp|Ltd|Co\.)?)',
        r'(?i)(working\s+(at|with|for))\s+([A-Z][A-Za-z0-9\s&,\.]+)',
    ]

    # Job title patterns
    JOB_TITLE_PATTERNS = [
        r'(?i)(position|role|job)\s+(of|as|for)\s+([A-Za-z\s]+)',
        r'(?i)(software|data|marketing|sales|product|design|engineer|developer|manager|analyst|specialist)',
    ]

    def parse_email(self, email: Dict) -> Dict:
        """
        Parse email and extract job application information.

        Args:
            email: Email data with subject, body, from, etc.

        Returns:
            Dict: Parsed information including status, company, job title
        """
        subject = email.get('subject', '')
        body = email.get('body', '')
        snippet = email.get('snippet', '')
        from_email = email.get('from', '')

        # Combine text for analysis
        full_text = f"{subject}\n{snippet}\n{body}"

        # Detect status
        detected_status = self._detect_status(full_text)

        # Extract company name
        company = self._extract_company(from_email, full_text)

        # Extract job title
        job_title = self._extract_job_title(subject, full_text)

        # Determine if this is job-related
        is_job_related = self._is_job_related(full_text, from_email)

        return {
            'emailId': email.get('id'),
            'subject': subject,
            'from': from_email,
            'receivedAt': email.get('receivedAt'),
            'status': detected_status,
            'company': company,
            'jobTitle': job_title,
            'isJobRelated': is_job_related,
            'confidence': self._calculate_confidence(full_text, detected_status)
        }

    def _detect_status(self, text: str) -> Optional[str]:
        """
        Detect application status from email text.

        Args:
            text: Email text to analyze

        Returns:
            Optional[str]: Detected status or None
        """
        # Check each status pattern
        status_scores = {}

        for status, patterns in self.STATUS_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1

            if score > 0:
                status_scores[status] = score

        # Return status with highest score
        if status_scores:
            return max(status_scores, key=status_scores.get)

        return None

    def _extract_company(self, from_email: str, text: str) -> Optional[str]:
        """
        Extract company name from email.

        Args:
            from_email: Sender email address
            text: Email text

        Returns:
            Optional[str]: Company name
        """
        # Try to extract from email domain
        email_match = re.search(r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', from_email)
        if email_match:
            domain = email_match.group(1)
            # Remove common email domains
            if domain not in ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'live.com']:
                # Extract company name from domain
                company = domain.split('.')[0]
                # Capitalize first letter of each word
                return company.replace('-', ' ').title()

        # Try to extract from email text
        for pattern in self.COMPANY_PATTERNS:
            match = re.search(pattern, text)
            if match:
                # Return the captured company name
                return match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()

        return None

    def _extract_job_title(self, subject: str, text: str) -> Optional[str]:
        """
        Extract job title from email.

        Args:
            subject: Email subject
            text: Email text

        Returns:
            Optional[str]: Job title
        """
        # Check subject first (often contains job title)
        for pattern in self.JOB_TITLE_PATTERNS:
            match = re.search(pattern, subject)
            if match:
                return match.group(0).strip()

        # Check body
        for pattern in self.JOB_TITLE_PATTERNS:
            match = re.search(pattern, text[:500])  # Check first 500 chars
            if match:
                return match.group(0).strip()

        return None

    def _is_job_related(self, text: str, from_email: str) -> bool:
        """
        Determine if email is job/recruitment related.

        Args:
            text: Email text
            from_email: Sender email

        Returns:
            bool: True if job-related
        """
        # Check for job-related keywords
        job_keywords = [
            'application', 'interview', 'position', 'role', 'candidate',
            'recruitment', 'hiring', 'talent', 'hr', 'human resources',
            'job', 'career', 'employment', 'offer', 'resume', 'cv'
        ]

        text_lower = text.lower()
        keyword_count = sum(1 for keyword in job_keywords if keyword in text_lower)

        # Check sender
        job_domains = ['noreply', 'jobs', 'talent', 'recruiting', 'hr', 'careers']
        from_job_domain = any(domain in from_email.lower() for domain in job_domains)

        # Consider job-related if multiple keywords or from job domain
        return keyword_count >= 2 or from_job_domain

    def _calculate_confidence(self, text: str, status: Optional[str]) -> float:
        """
        Calculate confidence score for detected status.

        Args:
            text: Email text
            status: Detected status

        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        if not status:
            return 0.0

        # Count matching patterns
        patterns = self.STATUS_PATTERNS.get(status, [])
        matches = sum(1 for pattern in patterns if re.search(pattern, text))

        # Calculate confidence based on number of matches
        if matches >= 3:
            return 0.9
        elif matches == 2:
            return 0.75
        elif matches == 1:
            return 0.6
        else:
            return 0.3

    def match_email_to_application(
        self,
        parsed_email: Dict,
        user_applications: List[Dict]
    ) -> Optional[str]:
        """
        Match parsed email to existing application.

        Args:
            parsed_email: Parsed email data
            user_applications: List of user's applications

        Returns:
            Optional[str]: Matched application ID or None
        """
        email_company = parsed_email.get('company', '').lower()
        email_job_title = parsed_email.get('jobTitle', '').lower()

        best_match = None
        best_score = 0

        for app in user_applications:
            score = 0

            # Get job data from application
            job_data = app.get('jobData', {})
            app_company = job_data.get('company', '').lower()
            app_title = job_data.get('title', '').lower()

            # Match company
            if email_company and app_company:
                if email_company in app_company or app_company in email_company:
                    score += 3

            # Match job title
            if email_job_title and app_title:
                # Check for word overlap
                email_words = set(email_job_title.split())
                app_words = set(app_title.split())
                overlap = len(email_words & app_words)
                score += overlap

            # Consider timing (recent applications more likely to match)
            app_date = app.get('appliedAt')
            if app_date:
                try:
                    from datetime import datetime, timedelta
                    if isinstance(app_date, str):
                        app_date = datetime.fromisoformat(app_date.replace('Z', '+00:00'))

                    days_since = (datetime.utcnow() - app_date.replace(tzinfo=None)).days
                    if days_since <= 30:
                        score += 1
                except:
                    pass

            if score > best_score:
                best_score = score
                best_match = app.get('_id')

        # Only return match if score is high enough
        return str(best_match) if best_score >= 3 else None

    def scan_and_update_applications(
        self,
        emails: List[Dict],
        applications: List[Dict]
    ) -> Dict:
        """
        Scan emails and update application statuses.

        Args:
            emails: List of fetched emails
            applications: List of user's applications

        Returns:
            Dict: Scan results with statistics
        """
        results = {
            'emailsScanned': len(emails),
            'jobEmailsFound': 0,
            'applicationsMatched': 0,
            'statusesUpdated': 0,
            'updates': []
        }

        for email in emails:
            # Parse email
            parsed = self.parse_email(email)

            if not parsed['isJobRelated']:
                continue

            results['jobEmailsFound'] += 1

            # Try to match to application
            matched_app_id = self.match_email_to_application(parsed, applications)

            if matched_app_id:
                results['applicationsMatched'] += 1

                # Check if status update is needed
                if parsed['status'] and parsed['confidence'] >= 0.6:
                    results['updates'].append({
                        'applicationId': matched_app_id,
                        'newStatus': parsed['status'],
                        'emailSubject': parsed['subject'],
                        'confidence': parsed['confidence']
                    })
                    results['statusesUpdated'] += 1

        return results
