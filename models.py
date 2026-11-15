from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Assignment:
    assign_id: str
    title: str
    subject: Optional[str] = None
    completed: bool = False
    status: int = 0
    start_time: int = 0
    score: Optional[float] = None

@dataclass
class Question:
    id: str
    index: int
    content: str
    qtype: str = "choice"
    options: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[str]] = None
    answer: Optional[Any] = None
