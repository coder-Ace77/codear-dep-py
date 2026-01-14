from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from app.models.problem import Problem, Submission
from app.schemas.problem_schema import ProblemSendDTO, ProblemSummaryDTO
from app.services.cache_service import CacheService
from typing import List, Optional
import json

class ProblemService:
    def __init__(self, db: Session):
        self.db = db
        # Cache Keys matching your Java service constants
        self.PROBLEM_KEY_PREFIX = "problem:id:"
        self.ALL_TAGS_KEY = "all_tags"
        self.PROBLEM_COUNT_KEY = "problem_count"
        self.PROBLEM_SEARCH_KEY = "Search_problem"

    def add_problem(self, problem_data: Problem) -> Problem:
        """Equivalent to Java addProblem: saves problem and clears general caches."""
        if problem_data.test_cases:
            for ts in problem_data.test_cases:
                ts.problem = problem_data
        
        self.db.add(problem_data)
        self.db.commit()
        self.db.refresh(problem_data)
        
        # Invalidate list/count caches
        CacheService.delete("all_problems_summary")
        CacheService.delete(self.PROBLEM_COUNT_KEY)
        CacheService.delete(self.ALL_TAGS_KEY)
        return problem_data

    def get_problem_by_id(self, problem_id: int):
        key = f"{self.PROBLEM_KEY_PREFIX}{problem_id}"
        
        # 1. Try Cache
        cached_problem = CacheService.get_object(key)
        if cached_problem:
            return cached_problem
            
        # 2. Query DB
        db_problem = self.db.query(Problem).filter(Problem.id == problem_id).first()
        if not db_problem:
            return None
            
        # 3. Map to DTO format
        problem_data = {
            "id": db_problem.id,
            "title": db_problem.title,
            "description": db_problem.description,
            "inputDescription": db_problem.input_description,
            "outputDescription": db_problem.output_description,
            "constraints": db_problem.constraints,
            "difficulty": db_problem.difficulty,
            "tags": db_problem.tags or [],
            "timeLimitMs": db_problem.time_limit_ms,
            "memoryLimitMb": db_problem.memory_limit_mb
        }
        
        # 4. Set Cache
        CacheService.set_object(key, problem_data, expire_seconds=3600)
        return problem_data

    def get_all_problems(self) -> List[dict]:
        """Equivalent to Java findAllSummaries."""
        db_list = self.db.query(Problem.id, Problem.title, Problem.tags, Problem.difficulty).all()
        return [
            {"id": p.id, "title": p.title, "tags": p.tags or [], "difficulty": p.difficulty} 
            for p in db_list
        ]

    def get_problem_cnt(self) -> int:
        cached_count = CacheService.get_value(self.PROBLEM_COUNT_KEY)
        if cached_count:
            return int(cached_count)
            
        count = self.db.query(Problem).count()
        CacheService.set_object(self.PROBLEM_COUNT_KEY, count, expire_seconds=1800)
        return count

    def get_tags_for_problem(self) -> List[str]:
        cached_tags = CacheService.get_object(self.ALL_TAGS_KEY)
        if cached_tags:
            return cached_tags
            
        query = text("SELECT DISTINCT UNNEST(tags) as tag FROM problems WHERE tags IS NOT NULL")
        result = self.db.execute(query).fetchall()
        tags = sorted([r.tag for r in result if r.tag])
        
        CacheService.set_object(self.ALL_TAGS_KEY, tags, expire_seconds=86400)
        return tags

    def search_problems(self, search: Optional[str], difficulty: Optional[str], tags: Optional[List[str]], page: int, size: int):
        offset = page * size
        tag_str = ",".join(tags) if tags else None
        
        # PostgreSQL Full Text Search + Array Overlap query
        query = text("""
            SELECT id, title, tags, difficulty FROM problems p
            WHERE (:search IS NULL OR :search = '' OR to_tsvector('english', p.title || ' ' || p.description) @@ plainto_tsquery(:search))
            AND (:difficulty IS NULL OR :difficulty = '' OR LOWER(p.difficulty) = LOWER(:difficulty))
            AND (:tags IS NULL OR :tags = '' OR p.tags && string_to_array(:tags, ','))
            ORDER BY p.id LIMIT :limit OFFSET :offset
        """)
        
        result = self.db.execute(query, {
            "search": search, "difficulty": difficulty, 
            "tags": tag_str, "limit": size, "offset": offset
        }).fetchall()
        
        return [{"id": r.id, "title": r.title, "tags": r.tags or [], "difficulty": r.difficulty} for r in result]

    def count_filtered_problems(self, search: Optional[str], difficulty: Optional[str], tags: Optional[List[str]]):
        tag_str = ",".join(tags) if tags else None
        query = text("""
            SELECT COUNT(*) FROM problems p
            WHERE (:search IS NULL OR :search = '' OR to_tsvector('english', p.title || ' ' || p.description) @@ plainto_tsquery(:search))
            AND (:difficulty IS NULL OR :difficulty = '' OR LOWER(p.difficulty) = LOWER(:difficulty))
            AND (:tags IS NULL OR :tags = '' OR p.tags && string_to_array(:tags, ','))
        """)
        return self.db.execute(query, {"search": search, "difficulty": difficulty, "tags": tag_str}).scalar()

    def get_problem_summary_recent(self, user_id: int):
        results = (
            self.db.query(
                Problem.id, 
                Problem.title, 
                Problem.tags, 
                Problem.difficulty
            )
            .join(Submission, Problem.id == Submission.problem_id)
            .filter(Submission.user_id == user_id)
            .group_by(Problem.id, Problem.title, Problem.tags, Problem.difficulty)
            .order_by(desc(func.max(Submission.submitted_at)))
            .limit(5)
            .all()
        )
        return [
            {"id": r.id, "title": r.title, "tags": r.tags or [], "difficulty": r.difficulty}
            for r in results
        ]