from datetime import datetime
import enum

from sqlalchemy import String, DateTime, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class BatchJobStatus(Base):
    __tablename__ = "batch_job_status"
    __table_args__ = {'comment': '배치 작업 실행 이력 및 상태'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment='작업 ID (Primary Key)')
    job_name: Mapped[str] = mapped_column(String(100), index=True, comment='작업명 (예: daily_pnl_calculation)')
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), comment='작업 상태 (PENDING/RUNNING/SUCCESS/FAILED)')
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='작업 시작일시')
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='작업 완료일시')
    records_processed: Mapped[int] = mapped_column(default=0, comment='처리된 레코드 수')
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment='에러 메시지 (실패 시)')
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment='작업 메타데이터 (JSON)')
