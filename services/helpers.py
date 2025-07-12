"""
Helper utilities for the resume screening application
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


def format_date(date: Union[datetime, str], format_type: str = 'default') -> str:
    """Format datetime objects for display"""
    try:
        if isinstance(date, str):
            date = datetime.fromisoformat(date)

        format_map = {
            'short': '%m/%d/%Y',
            'time': '%I:%M %p',
            'full': '%B %d, %Y at %I:%M %p',
            'relative': None,
            'default': '%Y-%m-%d %H:%M'
        }

        if format_type == 'relative':
            return format_relative_time(date)

        fmt = format_map.get(format_type, format_map['default'])
        return date.strftime(fmt)
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        return "Invalid date"


def format_relative_time(date: datetime) -> str:
    """Format datetime as relative time (e.g., '2 hours ago')"""
    try:
        now = datetime.now()
        diff = now - date

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    except Exception as e:
        logger.error(f"Error formatting relative time: {str(e)}")
        return "Unknown time"


def calculate_match_score(candidate_skills: List[str], job_requirements: List[str]) -> int:
    """Calculate how well candidate skills match job requirements"""
    try:
        if not candidate_skills or not job_requirements:
            return 0

        normalized_candidate = [skill.lower().strip() for skill in candidate_skills]
        normalized_requirements = [req.lower().strip() for req in job_requirements]

        matches = sum(
            1 for req in normalized_requirements
            if any(req in skill or skill in req for skill in normalized_candidate)
        )

        return min(100, int((matches / len(normalized_requirements)) * 100))
    except Exception as e:
        logger.error(f"Error calculating match score: {str(e)}")
        return 0


def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """Extract contact information from resume text"""
    try:
        contact_info = {'email': None, 'phone': None, 'name': None}

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'

        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)

        if emails:
            contact_info['email'] = emails[0]
        if phones:
            phone = ''.join(phones[0])
            contact_info['phone'] = phone

        lines = text.splitlines()
        for line in lines[:5]:
            line = line.strip()
            if 2 <= len(line.split()) <= 4:
                words = line.split()
                if all(word.replace('.', '').isalpha() for word in words):
                    contact_info['name'] = line
                    break

        return contact_info
    except Exception as e:
        logger.error(f"Error extracting contact info: {str(e)}")
        return {'email': None, 'phone': None, 'name': None}


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    try:
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"
    except Exception as e:
        logger.error(f"Error formatting file size: {str(e)}")
        return "Unknown size"


def generate_insights(candidates: List[Dict]) -> Dict[str, Any]:
    """Generate summarized insights from candidate data"""
    try:
        if not candidates:
            return {'total': 0, 'insights': []}

        insights = []
        total = len(candidates)

        high = sum(1 for c in candidates if c.get('overall_score', 0) >= 80)
        medium = sum(1 for c in candidates if 60 <= c.get('overall_score', 0) < 80)
        low = total - high - medium

        insights.append({
            'title': 'Score Distribution',
            'description': f'{high} high (80+), {medium} medium (60–79), {low} low (<60)',
            'type': 'score_distribution'
        })

        all_skills = []
        for c in candidates:
            all_skills.extend(c.get('extracted_skills', []))

        if all_skills:
            skill_freq = {}
            for skill in all_skills:
                skill_freq[skill] = skill_freq.get(skill, 0) + 1

            top_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:3]
            skill_desc = ', '.join([f"{s} ({c})" for s, c in top_skills])

            insights.append({
                'title': 'Most Common Skills',
                'description': skill_desc,
                'type': 'top_skills'
            })

        avg_score = sum(c.get('overall_score', 0) for c in candidates) / total
        insights.append({
            'title': 'Average Score',
            'description': f'{avg_score:.1f}/100 across all candidates',
            'type': 'average_score'
        })

        return {'total': total, 'insights': insights}
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return {'total': 0, 'insights': []}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    try:
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = re.sub(r'\.+', '.', sanitized)

        if len(sanitized) > 100:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:95] + ('.' + ext if ext else '')

        return sanitized
    except Exception as e:
        logger.error(f"Error sanitizing filename: {str(e)}")
        return "unknown_file"


def validate_score(score: Any) -> int:
    """Validate and normalize score"""
    try:
        if isinstance(score, str):
            score = float(score)
        score = int(score)
        return max(0, min(100, score))
    except (ValueError, TypeError):
        return 0


def format_skills_list(skills: List[str], max_display: int = 5) -> str:
    """Format skills list with optional truncation"""
    try:
        if not skills:
            return "No skills identified"

        unique = sorted(set(skills))

        if len(unique) <= max_display:
            return ', '.join(unique)
        else:
            return ', '.join(unique[:max_display]) + f' and {len(unique) - max_display} more'
    except Exception as e:
        logger.error(f"Error formatting skills list: {str(e)}")
        return "Error formatting skills"


def calculate_processing_eta(queue_size: int, avg_processing_time: float = 120) -> str:
    """Calculate estimated processing time for queue"""
    try:
        if queue_size == 0:
            return "No items in queue"

        total_seconds = queue_size * avg_processing_time

        if total_seconds < 60:
            return f"~{int(total_seconds)} seconds"
        elif total_seconds < 3600:
            return f"~{int(total_seconds / 60)} minute{'s' if total_seconds >= 120 else ''}"
        else:
            return f"~{int(total_seconds / 3600)} hour{'s' if total_seconds >= 7200 else ''}"
    except Exception as e:
        logger.error(f"Error calculating processing ETA: {str(e)}")
        return "Unknown"


def generate_activity_description(activity_type: str, context: Dict[str, Any]) -> str:
    """Generate activity description string based on type"""
    try:
        templates = {
            'resume_uploaded': 'Resume uploaded for {name}',
            'analysis_completed': 'Analysis completed for {name} with score {score}/100',
            'candidate_reviewed': 'Candidate {name} reviewed by HR team',
            'job_position_created': 'New job position created: {title}',
            'candidate_rejected': 'Candidate {name} marked as not suitable',
            'candidate_shortlisted': 'Candidate {name} added to shortlist',
            'bulk_upload': '{count} resumes uploaded in bulk',
            'system_update': 'System updated with new features'
        }

        template = templates.get(activity_type, 'Activity: {type}')
        return template.format(**context)
    except Exception as e:
        logger.error(f"Error generating activity description: {str(e)}")
        return f"Activity: {activity_type}"


def export_candidates_csv(candidates: List[Dict]) -> str:
    """Export candidate data to CSV string"""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            'Name', 'Email', 'Phone', 'Overall Score', 'Skills Score',
            'Experience Score', 'Education Score', 'Top Skills', 'Upload Date'
        ]
        writer.writerow(headers)

        for candidate in candidates:
            skills = candidate.get('extracted_skills', [])
            top_skills = ', '.join(skills[:3]) if skills else 'None'

            writer.writerow([
                candidate.get('name', ''),
                candidate.get('email', ''),
                candidate.get('phone', ''),
                candidate.get('overall_score', 0),
                candidate.get('skills_score', 0),
                candidate.get('experience_score', 0),
                candidate.get('education_score', 0),
                top_skills,
                format_date(candidate.get('uploaded_at', ''), 'short')
            ])

        return output.getvalue()
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return "Error generating CSV export"


def get_score_color_class(score: int) -> str:
    """Return Tailwind CSS text color based on score range"""
    if score >= 80:
        return 'text-green-600'
    elif score >= 60:
        return 'text-yellow-600'
    else:
        return 'text-red-600'


def get_score_badge_class(score: int) -> str:
    """Return Tailwind CSS badge color based on score range"""
    if score >= 80:
        return 'bg-green-100 text-green-800'
    elif score >= 60:
        return 'bg-yellow-100 text-yellow-800'
    else:
        return 'bg-red-100 text-red-800'
