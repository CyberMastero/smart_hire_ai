"""
Data Storage Service
In-memory data storage for the resume screening application
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# --- Data Classes ---
@dataclass
class JobPosition:
    id: int
    title: str
    department: str
    description: str
    requirements: List[str]
    is_active: bool
    created_at: datetime


@dataclass
class Candidate:
    id: int
    name: str
    email: str
    phone: str
    resume_text: str
    filename: str
    file_size: int
    uploaded_at: datetime


@dataclass
class ResumeAnalysis:
    id: int
    candidate_id: int
    job_position_id: Optional[int]
    overall_score: int
    skills_score: int
    experience_score: int
    education_score: int
    extracted_skills: List[str]
    key_points: List[str]
    recommendations: str
    ai_analysis: Dict[str, Any]
    status: str
    created_at: datetime


@dataclass
class ProcessingItem:
    id: int
    candidate_id: int
    status: str
    progress: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class Activity:
    id: int
    type: str
    description: str
    candidate_id: Optional[int]
    job_position_id: Optional[int]
    created_at: datetime


# --- In-Memory Data Storage ---
class DataStorage:
    def __init__(self):
        self.job_positions: Dict[int, JobPosition] = {}
        self.candidates: Dict[int, Candidate] = {}
        self.analyses: Dict[int, ResumeAnalysis] = {}
        self.processing_items: Dict[int, ProcessingItem] = {}
        self.activities: Dict[int, Activity] = {}

        self.next_job_id = 1
        self.next_candidate_id = 1
        self.next_analysis_id = 1
        self.next_processing_id = 1
        self.next_activity_id = 1

        logger.info("🗃️ Data storage initialized")

    # --- Job Positions ---
    def add_job_position(self, job_data: Dict) -> int:
        try:
            job = JobPosition(
                id=self.next_job_id,
                title=job_data['title'],
                department=job_data['department'],
                description=job_data['description'],
                requirements=job_data.get('requirements', []),
                is_active=job_data.get('is_active', True),
                created_at=datetime.now()
            )
            self.job_positions[job.id] = job
            self.next_job_id += 1
            logger.info(f"📌 Added job position: {job.title}")
            return job.id
        except Exception as e:
            logger.error(f"❌ Error adding job position: {e}")
            raise

    def get_job_positions(self) -> List[Dict]:
        return [asdict(job) for job in self.job_positions.values()]

    def get_job_position(self, job_id: int) -> Optional[Dict]:
        job = self.job_positions.get(job_id)
        return asdict(job) if job else None

    def update_job_position(self, job_id: int, updates: Dict) -> bool:
        job = self.job_positions.get(job_id)
        if not job:
            return False
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        logger.info(f"✏️ Updated job position {job_id}")
        return True

    # --- Candidates ---
    def add_candidate(self, data: Dict) -> int:
        try:
            candidate = Candidate(
                id=self.next_candidate_id,
                name=data.get('name', 'Unknown'),
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                resume_text=data['resume_text'],
                filename=data['filename'],
                file_size=data.get('file_size', 0),
                uploaded_at=datetime.now()
            )
            self.candidates[candidate.id] = candidate
            self.next_candidate_id += 1
            logger.info(f"👤 Added candidate: {candidate.name}")
            return candidate.id
        except Exception as e:
            logger.error(f"❌ Error adding candidate: {e}")
            raise

    def get_candidates(self) -> List[Dict]:
        return [asdict(c) for c in self.candidates.values()]

    def get_candidate(self, candidate_id: int) -> Optional[Dict]:
        c = self.candidates.get(candidate_id)
        return asdict(c) if c else None

    def update_candidate(self, candidate_id: int, updates: Dict) -> bool:
        c = self.candidates.get(candidate_id)
        if not c:
            return False
        for key, value in updates.items():
            if hasattr(c, key):
                setattr(c, key, value)
        logger.info(f"✏️ Updated candidate {candidate_id}")
        return True

    def get_candidates_with_analysis(self) -> List[Dict]:
        result = []
        for c in self.candidates.values():
            c_dict = asdict(c)
            analysis = next((a for a in self.analyses.values() if a.candidate_id == c.id), None)
            if analysis:
                a_dict = asdict(analysis)
                c_dict.update({
                    'overall_score': a_dict['overall_score'],
                    'skills_score': a_dict['skills_score'],
                    'experience_score': a_dict['experience_score'],
                    'education_score': a_dict['education_score'],
                    'extracted_skills': a_dict['extracted_skills'],
                    'job_position_id': a_dict['job_position_id'],
                    'analysis': a_dict
                })
            else:
                c_dict.update({
                    'overall_score': 0,
                    'skills_score': 0,
                    'experience_score': 0,
                    'education_score': 0,
                    'extracted_skills': [],
                    'job_position_id': None,
                    'analysis': None
                })
            result.append(c_dict)
        return result

    # --- Resume Analysis ---
    def add_analysis(self, data: Dict) -> int:
        try:
            analysis = ResumeAnalysis(
                id=self.next_analysis_id,
                candidate_id=data['candidate_id'],
                job_position_id=data.get('job_position_id'),
                overall_score=data['overall_score'],
                skills_score=data['skills_score'],
                experience_score=data['experience_score'],
                education_score=data['education_score'],
                extracted_skills=data.get('extracted_skills', []),
                key_points=data.get('key_points', []),
                recommendations=data.get('recommendations', ''),
                ai_analysis=data.get('ai_analysis', {}),
                status=data.get('status', 'completed'),
                created_at=datetime.now()
            )
            self.analyses[analysis.id] = analysis
            self.next_analysis_id += 1
            logger.info(f"🧠 Added analysis for candidate {analysis.candidate_id}")
            return analysis.id
        except Exception as e:
            logger.error(f"❌ Error adding analysis: {e}")
            raise

    def get_candidate_analysis(self, candidate_id: int) -> Optional[Dict]:
        for a in self.analyses.values():
            if a.candidate_id == candidate_id:
                return asdict(a)
        return None

    def update_analysis(self, analysis_id: int, updates: Dict) -> bool:
        a = self.analyses.get(analysis_id)
        if not a:
            return False
        for key, value in updates.items():
            if hasattr(a, key):
                setattr(a, key, value)
        logger.info(f"✏️ Updated analysis {analysis_id}")
        return True

    # --- Processing Items ---
    def add_processing_item(self, data: Dict) -> int:
        item = ProcessingItem(
            id=self.next_processing_id,
            candidate_id=data['candidate_id'],
            status=data.get('status', 'pending'),
            progress=data.get('progress', 0),
            error_message=data.get('error_message'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.processing_items[item.id] = item
        self.next_processing_id += 1
        logger.info(f"📦 Added processing item for candidate {item.candidate_id}")
        return item.id

    def get_processing_queue(self) -> List[Dict]:
        return [asdict(i) for i in self.processing_items.values()]

    def update_processing_item(self, candidate_id: int, updates: Dict) -> bool:
        item = next((i for i in self.processing_items.values() if i.candidate_id == candidate_id), None)
        if not item:
            return False
        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)
        item.updated_at = datetime.now()
        logger.info(f"✏️ Updated processing item for candidate {candidate_id}")
        return True

    # --- Activities ---
    def add_activity(self, data: Dict) -> int:
        activity = Activity(
            id=self.next_activity_id,
            type=data['type'],
            description=data['description'],
            candidate_id=data.get('candidate_id'),
            job_position_id=data.get('job_position_id'),
            created_at=datetime.now()
        )
        self.activities[activity.id] = activity
        self.next_activity_id += 1
        logger.info(f"📍 Activity logged: {activity.type}")
        return activity.id

    def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        activities = sorted(self.activities.values(), key=lambda x: x.created_at, reverse=True)
        return [asdict(a) for a in activities[:limit]]

    # --- Utility Methods ---
    def get_statistics(self) -> Dict[str, int]:
        return {
            'job_positions': len(self.job_positions),
            'candidates': len(self.candidates),
            'analyses': len(self.analyses),
            'processing_items': len(self.processing_items),
            'activities': len(self.activities)
        }

    def clear_all_data(self) -> bool:
        self.__init__()
        logger.info("🧹 All in-memory data cleared")
        return True

    def export_data(self) -> Dict[str, Any]:
        return {
            'job_positions': [asdict(j) for j in self.job_positions.values()],
            'candidates': [asdict(c) for c in self.candidates.values()],
            'analyses': [asdict(a) for a in self.analyses.values()],
            'processing_items': [asdict(p) for p in self.processing_items.values()],
            'activities': [asdict(a) for a in self.activities.values()],
            'export_timestamp': datetime.now().isoformat()
        }

    def import_data(self, data: Dict[str, Any]) -> bool:
        try:
            self.clear_all_data()
            for j in data.get('job_positions', []):
                j['created_at'] = datetime.fromisoformat(j['created_at'])
                self.job_positions[j['id']] = JobPosition(**j)
                self.next_job_id = max(self.next_job_id, j['id'] + 1)

            for c in data.get('candidates', []):
                c['uploaded_at'] = datetime.fromisoformat(c['uploaded_at'])
                self.candidates[c['id']] = Candidate(**c)
                self.next_candidate_id = max(self.next_candidate_id, c['id'] + 1)

            for a in data.get('analyses', []):
                a['created_at'] = datetime.fromisoformat(a['created_at'])
                self.analyses[a['id']] = ResumeAnalysis(**a)
                self.next_analysis_id = max(self.next_analysis_id, a['id'] + 1)

            for p in data.get('processing_items', []):
                p['created_at'] = datetime.fromisoformat(p['created_at'])
                p['updated_at'] = datetime.fromisoformat(p['updated_at'])
                self.processing_items[p['id']] = ProcessingItem(**p)
                self.next_processing_id = max(self.next_processing_id, p['id'] + 1)

            for a in data.get('activities', []):
                a['created_at'] = datetime.fromisoformat(a['created_at'])
                self.activities[a['id']] = Activity(**a)
                self.next_activity_id = max(self.next_activity_id, a['id'] + 1)

            logger.info("✅ Data imported successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error importing data: {e}")
            return False
