from fastapi import APIRouter

from app.api.v1.endpoints import auth, tickets, ai, approvals, documents, analytics, public

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(documents.router, prefix="/documents", tags=["Knowledge Base"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Processing"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Human Approval"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# Public customer-facing endpoints (no auth)
api_router.include_router(public.router, prefix="/public", tags=["Public - Customer"])
