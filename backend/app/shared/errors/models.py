from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from app.shared.errors.codes import ErrorCode


@dataclass(frozen=True)
class ApiError:
    code: ErrorCode
    message: str
    request_id: str
    timestamp: datetime
    details: Any | None = None

    @classmethod
    def create(
        cls,
        *,
        code: ErrorCode,
        message: str,
        request_id: str,
        details: Any | None = None,
    ) -> "ApiError":
        return cls(
            code=code,
            message=message,
            request_id=request_id,
            timestamp=datetime.now(UTC),
            details=details,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        data["code"] = self.code.value
        data["timestamp"] = self.timestamp.isoformat()

        return {
            "error": data,
        }
