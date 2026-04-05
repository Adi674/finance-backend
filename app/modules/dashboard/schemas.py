from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float


class CategoryBreakdown(BaseModel):
    category: str
    type: str
    total: float


class MonthlyTrend(BaseModel):
    month: str       # "YYYY-MM"
    income: float
    expense: float