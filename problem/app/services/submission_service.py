import asyncio
import uuid
from datetime import datetime
from app.models.problem import Submission, SubmissionStatus
from app.core import cache, sqs

class SubmissionService:
    def __init__(self, db):
        self.db = db

    async def submit_code(self, data, user_id):
        sub_id = str(uuid.uuid4())
        
        # 1. Update Redis
        cache.set_cache(sub_id, SubmissionStatus.IN_PROGRESS.value)
        
        # 2. Save to DB
        new_sub = Submission(
            submission_id=sub_id,
            user_id=user_id,
            problem_id=data.problemId,
            code=data.code,
            language=data.language,
            status=SubmissionStatus.IN_PROGRESS
        )
        self.db.add(new_sub)
        self.db.commit()

        # 3. Send to SQS
        sqs.send_to_queue({
            "submissionId": sub_id,
            "userId": user_id,
            "code": data.code,
            "language": data.language,
            "problemId": data.problemId
        })
        return sub_id

    async def long_poll_submission(self, sub_id: str):
        max_wait = 10  # seconds
        waited = 0
        
        while waited < max_wait:
            status = cache.get_cache(sub_id)
            if status != SubmissionStatus.IN_PROGRESS.value:
                break
            await asyncio.sleep(1)
            waited += 1
            
        submission = self.db.query(Submission).filter(Submission.submission_id == sub_id).first()
        return submission
    
    def get_submissions_by_user_and_problem(self, user_id: int, problem_id: int) -> list[Submission]:
        """Equivalent to getSubmissionByIdAndProblem in Java."""
        return (
            self.db.query(Submission)
            .filter(Submission.user_id == user_id)
            .filter(Submission.problem_id == problem_id)
            .order_by(Submission.submitted_at.desc()) # Added ordering for better UX
            .all()
        )