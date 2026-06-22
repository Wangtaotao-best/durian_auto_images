"""API 请求/响应数据模型"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    variety: str = Field(..., description="品种 ID")
    prompt: str = Field(..., min_length=1, max_length=500)
    negative_prompt: str = Field(default="blurry, low quality, distorted, deformed")
    num_images: int = Field(default=1, ge=1, le=4)
    steps: int = Field(default=6, ge=4, le=20)
    cfg_scale: float = Field(default=1.5, ge=0.5, le=10.0)
    seed: int = Field(default=-1)
    width: int = Field(default=512, ge=256, le=768)
    height: int = Field(default=512, ge=256, le=768)


class QueuedResponse(BaseModel):
    task_id: str
    status: Literal["queued"]
    queue_position: int
    estimated_seconds: int


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["queued", "running", "done", "failed"]
    queue_position: Optional[int] = None
    estimated_seconds: Optional[int] = None
    progress: Optional[float] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    image_urls: Optional[List[str]] = None
    error: Optional[str] = None


class Variety(BaseModel):
    id: str
    name_cn: str
    name_en: str
    trigger: str
    preview: Optional[str] = None
