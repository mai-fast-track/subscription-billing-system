"""
Transaction endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import Error
from app.schemas.transaction import Transaction

router = APIRouter()


@router.get("", response_model=list[Transaction])
async def list_transactions(
    type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user)  # TODO: Add auth dependency
):
    """
    List user transactions

    Returns transaction history for current user, optionally filtered by type
    """
    # TODO: Implement list transactions logic
    # 1. Get current user
    # 2. Query transactions for user
    # 3. Filter by type if provided
    # 4. Apply limit
    # 5. Return list of transactions
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{transaction_id}", response_model=Transaction, responses={404: {"model": Error}})
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user)  # TODO: Add auth dependency
):
    """
    Get transaction

    Returns transaction details by ID
    """
    # TODO: Implement get transaction logic
    # 1. Get current user
    # 2. Check ownership
    # 3. Get transaction from database
    # 4. Return transaction or 404
    raise HTTPException(status_code=501, detail="Not implemented")
