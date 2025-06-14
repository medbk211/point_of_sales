from enum import Enum

class Comparer(Enum):
    gt = "gt"  # Greater than
    gte = "gte"  # Greater than or equal
    lt = "lt"  # Less than
    lte = "lte"  # Less than or equal
    e = "e"  # Equal
    in_ = "in"  # In list or range  