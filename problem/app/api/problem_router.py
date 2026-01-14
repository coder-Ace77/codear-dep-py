from fastapi import APIRouter, Depends, Query, Header
from typing import List, Optional
from app.database import get_db
from app.core import security
from app.services.problem_service import ProblemService
from sqlalchemy.orm import Session
from app.services.submission_service import SubmissionService
from app.schemas.problem_schema import ProblemSendDTO, ProblemsMetaData, ProblemSummaryDTO, CodeRequest
import uuid # For generating submissionId
from app.schemas.problem_schema import TestDTO
from app.core.sqs import send_to_queue, TEST_QUEUE_URL
from app.services.cache_service import CacheService
router = APIRouter(prefix="/api/v1/problem")

@router.get("/search")
async def search(
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    page: int = 0,
    size: int = 10,
    db=Depends(get_db)
):
    service = ProblemService(db)
    content = service.search_problems(search, difficulty, tags, page, size)
    total = service.count_filtered_problems(search, difficulty, tags)
    return {
        "content": content,
        "totalCount": total,
        "totalPages": (total + size - 1) // size
    }

@router.post("/test")
async def run_test_case(test_data: TestDTO):
    """
    Equivalent to TestCaseRun.processSubmittedCode in Java.
    Initiates a test run without creating a permanent DB submission record.
    """
    # 1. Generate a unique submission ID for this test
    submission_id = str(uuid.uuid4())
    
    # 2. Update the DTO with the generated ID and set status
    test_data.submissionId = submission_id
    test_data.status = "IN_PROGRESS"
    
    # 3. Send to SQS Test Queue (matching your Java SQS_TEST_QUEUE)
    # We convert the Pydantic model to a dict for SQS serialization
    send_to_queue(test_data.model_dump(), queue_url=TEST_QUEUE_URL)
    
    # 4. Cache the test request in Redis for long polling
    # This allows the frontend to poll for the result
    CacheService.set_object(submission_id, test_data.model_dump(), expire_seconds=600)
    
    return {
        "message": "Test in queue",
        "submissionId": submission_id
    }

@router.post("/submit")
async def submit(
    data: CodeRequest, 
    authorization: str = Header(...), 
    db=Depends(get_db)
):
    user_id = security.extract_user_id(authorization.split(" ")[1])
    service = SubmissionService(db)
    res = await service.submit_code(data, int(user_id))
    return {"message": "Code submitted successfully", "submissionId": res}

@router.get("/submissions/{submissionId}")
async def get_status(submissionId: str, db=Depends(get_db)):
    service = SubmissionService(db)
    return await service.long_poll_submission(submissionId)

# 1. GET /api/v1/problem/problem/{id}
@router.get("/problem/{id}", response_model=ProblemSendDTO)
def get_problem_by_id(id: int, db: Session = Depends(get_db)):
    service = ProblemService(db)
    problem = service.get_problem_by_id(id)
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem with id {id} not found")
    return problem

# 2. GET /api/v1/problem/problemCntAndTags
@router.get("/problemCntAndTags", response_model=ProblemsMetaData)
def get_problem_cnt_and_tags(db: Session = Depends(get_db)):
    service = ProblemService(db)
    return {
        "count": service.get_problem_cnt(),
        "tags": service.get_tags_for_problem()
    }

# 3. GET /api/v1/problem/recent
@router.get("/recent", response_model=List[ProblemSummaryDTO])
def get_recent_problems(
    authorization: str = Header(...), 
    db: Session = Depends(get_db)
):
    token = authorization.split(" ")[1]
    user_id = security.extract_user_id(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    service = ProblemService(db)
    return service.get_problem_summary_recent(user_id)

# 4. GET /api/v1/problem/problems (Added to match Java getAllProblems)
@router.get("/problems", response_model=List[ProblemSummaryDTO])
def get_all_problems(db: Session = Depends(get_db)):
    service = ProblemService(db)
    return service.get_all_problems()