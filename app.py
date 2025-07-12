#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv

from services.resume_analyzer import ResumeAnalyzer
from services.file_processor import FileProcessor
from services.data_storage import DataStorage

# Load environment variables
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeScreenerApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
        self.app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
        self.app.config['UPLOAD_FOLDER'] = 'uploads'
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)

        CORS(self.app, origins=['*'])

        self.resume_analyzer = ResumeAnalyzer()
        self.file_processor = FileProcessor()
        self.data_storage = DataStorage()

        self.register_routes()
        self.init_sample_data()

    def init_sample_data(self):
        try:
            sample_jobs = [
                {'title': 'Software Engineer', 'department': 'Tech', 'description': 'Build APIs', 'requirements': ['Python', 'Flask'], 'is_active': True, 'created_at': datetime.now()},
                {'title': 'Data Scientist', 'department': 'Data', 'description': 'Analyze datasets', 'requirements': ['ML', 'Python'], 'is_active': True, 'created_at': datetime.now()},
            ]
            for job in sample_jobs:
                self.data_storage.add_job_position(job)
        except Exception as e:
            logger.error(f"Sample data initialization failed: {e}", exc_info=True)

    def register_routes(self):
        @self.app.route('/')
        def index():
            try:
                stats = self.get_dashboard_stats()
                activities = self.data_storage.get_recent_activities(10)
                return render_template('dashboard.html', stats=stats, activities=activities)
            except Exception as e:
                logger.error(e, exc_info=True)
                return render_template('dashboard.html', stats={}, activities=[])

        @self.app.route('/upload', methods=['GET', 'POST'])
        def upload_resume():
            if request.method == 'GET':
                jobs = self.data_storage.get_job_positions()
                return render_template('upload.html', job_positions=jobs)

            try:
                file = request.files.get('resume_file')
                if not file or file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400

                if not self.file_processor.allowed_file(file.filename):
                    return jsonify({'error': 'Unsupported file type'}), 400

                filename = secure_filename(file.filename)
                uid_filename = f"{uuid.uuid4()}_{filename}"
                path = os.path.join(self.app.config['UPLOAD_FOLDER'], uid_filename)
                file.save(path)

                logger.info(f"Uploaded file saved to: {path}")
                job_id = request.form.get('job_position_id')

                result = self.process_resume(path, filename, job_id)
                logger.info(f"Analysis result: {result}")
                return jsonify(result)

            except RequestEntityTooLarge:
                logger.warning("Upload failed: file too large")
                return jsonify({'error': 'File exceeds 100MB'}), 413
            except Exception as e:
                logger.error(f"Upload error: {e}", exc_info=True)
                return jsonify({'error': 'Processing failed'}), 500

        @self.app.route('/candidate/<int:cid>')
        def candidate_detail(cid):
            try:
                cand = self.data_storage.get_candidate(cid)
                analysis = self.data_storage.get_candidate_analysis(cid)
                job = self.data_storage.get_job_position(analysis.get('job_position_id')) if analysis else None
                return render_template('candidate_detail.html', candidate=cand, analysis=analysis, job_position=job)
            except Exception as e:
                logger.error(e, exc_info=True)
                return redirect(url_for('index'))

        @self.app.route('/candidates')
        def candidates():
            try:
                candidates = self.data_storage.get_candidates_with_analysis()
                current_filters = {
                    'score': request.args.get('score', ''),
                    'job': request.args.get('job', '')
                }
                return render_template('candidates.html', candidates=candidates, current_filters=current_filters)
            except Exception as e:
                logger.error(e, exc_info=True)
                return render_template('candidates.html', candidates=[], current_filters={'score': '', 'job': ''})

        @self.app.route('/jobs', methods=['GET'])
        def jobs():
            try:
                jobs = self.data_storage.get_job_positions()
                return render_template('jobs.html', job_positions=jobs)
            except Exception as e:
                logger.error(e, exc_info=True)
                return render_template('jobs.html', job_positions=[])

        @self.app.route('/add_job', methods=['POST'])
        def add_job():
            try:
                job_data = {
                    'title': request.form.get('title'),
                    'department': request.form.get('department'),
                    'description': request.form.get('description'),
                    'requirements': [r.strip() for r in request.form.get('requirements', '').split(',') if r.strip()],
                    'is_active': True,
                    'created_at': datetime.now()
                }
                self.data_storage.add_job_position(job_data)
                logger.info(f"Job added: {job_data['title']}")
                return redirect(url_for('jobs'))
            except Exception as e:
                logger.error(f"Error adding job: {e}", exc_info=True)
                return redirect(url_for('jobs'))

        @self.app.route('/analytics')
        def analytics():
            try:
                data = self.get_dashboard_stats()
                return render_template('analytics.html', analytics=data)
            except Exception as e:
                logger.error(e, exc_info=True)
                return render_template('analytics.html', analytics={})

        @self.app.route('/api/candidates')
        def api_candidates():
            try:
                return jsonify(self.data_storage.get_candidates_with_analysis())
            except Exception as e:
                logger.error(e, exc_info=True)
                return jsonify({'error': 'Server error'}), 500

        @self.app.route('/config')
        def config_debug():
            return jsonify({
                "MAX_CONTENT_LENGTH": self.app.config['MAX_CONTENT_LENGTH'],
                "MAX_MB": self.app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
            })

    def process_resume(self, path, original, job_id):
        try:
            logger.info(f"Processing resume: {original} at {path}")
            text = self.file_processor.extract_text(path)
            logger.info(f"Extracted text length: {len(text)}")

            if not text.strip():
                raise ValueError("Resume text is empty")

            candidate = {
                'name': 'Unknown',
                'email': '',
                'phone': '',
                'resume_text': text,
                'filename': original,
                'created_at': datetime.now()
            }
            cid = self.data_storage.add_candidate(candidate)
            logger.info(f"Candidate ID: {cid}")

            job = self.data_storage.get_job_position(int(job_id)) if job_id else None
            result = self.resume_analyzer.analyze_resume(text, job)

            info = result.get('contact_info', {})
            self.data_storage.update_candidate(cid, {
                'name': info.get('name', 'Unknown'),
                'email': info.get('email'),
                'phone': info.get('phone')
            })

            analysis = {
                'candidate_id': cid,
                'job_position_id': int(job_id) if job_id else None,
                'overall_score': result.get('overall_score', 0),
                'skills_score': result.get('skills_score', 0),
                'experience_score': result.get('experience_score', 0),
                'education_score': result.get('education_score', 0),
                'extracted_skills': result.get('extracted_skills', []),
                'key_points': result.get('key_points', []),
                'recommendations': result.get('recommendations', ''),
                'ai_analysis': result,
                'status': 'completed'
            }
            self.data_storage.add_analysis(analysis)

            file_size = os.path.getsize(path)
            os.remove(path)
            result['file_size'] = file_size

            logger.info(f"Resume file removed: {path}")

            return {
                'success': True,
                'candidate_id': cid,
                'analysis': result
            }

        except Exception as e:
            logger.error(f"Resume processing failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def get_dashboard_stats(self):
        try:
            candidates = self.data_storage.get_candidates_with_analysis()
            jobs = self.data_storage.get_job_positions()
            total = len(candidates)
            qualified = len([c for c in candidates if c.get('overall_score', 0) >= 70])
            avg_score = round(sum([c.get('overall_score', 0) for c in candidates]) / total, 2) if total > 0 else 0

            score_buckets = [0, 0, 0, 0]
            for c in candidates:
                score = c.get('overall_score', 0)
                if score >= 80:
                    score_buckets[0] += 1
                elif score >= 60:
                    score_buckets[1] += 1
                elif score >= 40:
                    score_buckets[2] += 1
                else:
                    score_buckets[3] += 1

            timeline = {}
            for c in candidates:
                dt = c.get('created_at') or datetime.now()
                label = dt.strftime('%Y-%m-%d')
                timeline[label] = timeline.get(label, 0) + 1

            return {
                'total_applications': total,
                'qualified_rate': round((qualified / total) * 100, 1) if total > 0 else 0,
                'avg_score': avg_score,
                'avg_processing_time': '2.5 min',
                'score_distribution': score_buckets,
                'timeline_labels': list(timeline.keys()),
                'timeline_data': list(timeline.values()),
                'quality_trends': ["More Python applicants"],
                'recommendations': ["Open roles in ML/AI"]
            }
        except Exception as e:
            logger.error(f"Dashboard stats failed: {e}", exc_info=True)
            return {}

    def run(self, host='0.0.0.0', port=5000, debug=False):
        self.app.run(host=host, port=port, debug=debug)

# App entry
app_instance = ResumeScreenerApp()
app = app_instance.app

if __name__ == '__main__':
    if not os.getenv('OPENAI_API_KEY'):
        print("\u26a0\ufe0f Warning: Missing OPENAI_API_KEY for AI analysis.")
    app_instance.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
