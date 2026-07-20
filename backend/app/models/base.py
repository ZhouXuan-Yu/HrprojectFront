from app.extensions import db
from sqlalchemy import Column, BigInteger, DateTime, Integer, func
from sqlalchemy.dialects.sqlite import INTEGER as SQLITE_INTEGER
from datetime import datetime, timezone


class BaseModel(db.Model):
    """Abstract base model with audit fields and soft-delete."""
    __abstract__ = True

    id = Column(
        BigInteger().with_variant(SQLITE_INTEGER, 'sqlite'),
        primary_key=True,
        autoincrement=True
    )

    # Audit fields — using server_default + default for proper row-level timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now(), default=datetime.now, comment='创建时间')
    created_by = Column(BigInteger, nullable=True, comment='创建人用户ID')
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=datetime.now, default=datetime.now, comment='更新时间')
    updated_by = Column(BigInteger, nullable=True, comment='更新人用户ID')

    # Soft delete
    is_deleted = Column(Integer, nullable=False, default=0, comment='逻辑删除: 0未删除 1已删除')

    def soft_delete(self, user_id=None):
        """Mark record as deleted."""
        self.is_deleted = 1
        if user_id:
            self.updated_by = user_id

    @classmethod
    def active(cls):
        """Query filter: only non-deleted records."""
        return cls.query.filter(cls.is_deleted == 0)
