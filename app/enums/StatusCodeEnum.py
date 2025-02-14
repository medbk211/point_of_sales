from enum import Enum


class StatusCodeEnum(Enum):
    Pending = "Pending"
    Completed = "Completed"
    Canceled = "Canceled"