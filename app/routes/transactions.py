from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import User, Wallet, Transaction
from app.schemas import TransactionCreate, TransactionResponse, TransactionHistoryResponse
from app.dep import get_db, get_current_user

router = APIRouter()


@router.post("/send", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def send_money(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send money from current user to another user"""
    
    # Validate receiver exists
    receiver = db.query(User).filter(User.id == transaction_data.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver user not found"
        )
    
    # Prevent self-transfer
    if current_user.id == transaction_data.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send money to yourself"
        )
    
    # Validate amount
    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    # Get sender wallet
    sender_wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not sender_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender wallet not found"
        )
    
    # Check sufficient balance
    if sender_wallet.balance < transaction_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Get receiver wallet
    receiver_wallet = db.query(Wallet).filter(Wallet.user_id == transaction_data.receiver_id).first()
    if not receiver_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver wallet not found"
        )
    
    # Create transaction
    transaction = Transaction(
        sender_id=current_user.id,
        receiver_id=transaction_data.receiver_id,
        amount=transaction_data.amount,
        description=transaction_data.description,
        status="completed"
    )
    
    # Update wallets
    sender_wallet.balance -= transaction_data.amount
    receiver_wallet.balance += transaction_data.amount
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse.from_orm(transaction)


@router.get("/history", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction history for current user"""
    
    # Get sent transactions
    sent_transactions = db.query(Transaction).filter(
        Transaction.sender_id == current_user.id
    ).all()
    
    # Get received transactions
    received_transactions = db.query(Transaction).filter(
        Transaction.receiver_id == current_user.id
    ).all()
    
    return TransactionHistoryResponse(
        sent=[TransactionResponse.from_orm(t) for t in sent_transactions],
        received=[TransactionResponse.from_orm(t) for t in received_transactions]
    )
