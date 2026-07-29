"""
🏆 TOURNAMENTS (Турниры)
Weekly leaderboard with prizes
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from database.models import User, Transaction

logger = logging.getLogger(__name__)
router = Router()


class TournamentManager:
    """Manage weekly tournaments"""
    
    # Config
    PRIZE_POOL = Decimal("10")  # 10 TON per week
    TOP_PRIZES = {
        1: Decimal("5"),    # 1st place: 5 TON
        2: Decimal("3"),    # 2nd place: 3 TON
        3: Decimal("2")     # 3rd place: 2 TON
    }
    
    @staticmethod
    def get_week_start() -> datetime:
        """Get Monday of current week"""
        today = datetime.utcnow()
        return today - timedelta(days=today.weekday())
    
    @staticmethod
    async def get_leaderboard(session: AsyncSession, limit: int = 10) -> list:
        """Get weekly leaderboard by transaction count"""
        week_start = TournamentManager.get_week_start()
        
        # Count transfers per user this week
        query = (
            select(
                User.id,
                User.username,
                User.first_name,
                func.count(Transaction.id).label("transfer_count"),
                func.sum(Transaction.amount).label("total_volume")
            )
            .join(Transaction, Transaction.user_id == User.id)
            .where(
                Transaction.created_at >= week_start,
                Transaction.type.in_(["transfer", "deposit"])
            )
            .group_by(User.id, User.username, User.first_name)
            .order_by(desc("transfer_count"))
            .limit(limit)
        )
        
        result = await session.execute(query)
        return result.fetchall()
    
    @staticmethod
    async def get_user_rank(
        session: AsyncSession,
        user_id: int
    ) -> tuple[int, int]:
        """Get user's current rank and transfer count"""
        week_start = TournamentManager.get_week_start()
        
        # Get user's transfer count
        user_result = await session.execute(
            select(func.count(Transaction.id))
            .where(
                Transaction.user_id == user_id,
                Transaction.created_at >= week_start,
                Transaction.type.in_(["transfer", "deposit"])
            )
        )
        user_count = user_result.scalar() or 0
        
        # Get rank (how many users have more transfers)
        # Use subquery to properly count transfers per user
        from sqlalchemy import and_
        subq = select(
            Transaction.user_id,
            func.count(Transaction.id).label('tx_count')
        ).where(
            and_(
                Transaction.created_at >= week_start,
                Transaction.type.in_(["transfer", "deposit"])
            )
        ).group_by(Transaction.user_id).subquery()
        
        rank_result = await session.execute(
            select(func.count(subq.c.tx_count))
            .where(subq.c.tx_count > user_count)
        )
        
        rank = (rank_result.scalar() or 0) + 1
        
        return rank, user_count


def format_leaderboard_message(leaderboard: list, user_rank: int = None) -> str:
    """Format leaderboard message"""
    msg = "🏆 <b>ТУРНИР НЕДЕЛИ</b> 🏆\n\n"
    msg += "Топ-3 получают призы!\n"
    msg += "💰 1-е место: 5 TON\n"
    msg += "🥈 2-е место: 3 TON\n"
    msg += "🥉 3-е место: 2 TON\n\n"
    
    msg += "<b>ЛИДЕРБОРД:</b>\n"
    msg += "┌─────────────────────────┐\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for idx, row in enumerate(leaderboard, 1):
        medal = medals[idx-1] if idx <= 3 else f"#{idx}"
        username = row[1] or f"User{row[0]}"
        count = row[3]
        volume = row[4] or 0
        
        msg += f"│ {medal} @{username}\n"
        msg += f"│    {count} переводов\n"
        msg += f"│    Объем: {volume:.2f} TON\n"
    
    msg += "└─────────────────────────┘\n\n"
    
    if user_rank:
        msg += f"📊 Ваш рейтинг: #{user_rank}\n"
    
    msg += "⏰ Конец недели: Воскресенье 23:59 UTC\n"
    msg += "💡 Чем больше переводов → выше рейтинг!"
    
    return msg


@router.message(F.text == "🏆 Турнир")
async def show_tournament(message: types.Message, session: AsyncSession):
    """Show current tournament"""
    leaderboard = await TournamentManager.get_leaderboard(session)
    rank, count = await TournamentManager.get_user_rank(session, message.from_user.id)
    
    msg = format_leaderboard_message(leaderboard, rank)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="tournament_refresh")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await message.answer(msg, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "tournament_refresh")
async def refresh_tournament(query: types.CallbackQuery, session: AsyncSession):
    """Refresh leaderboard"""
    leaderboard = await TournamentManager.get_leaderboard(session)
    rank, count = await TournamentManager.get_user_rank(session, query.from_user.id)
    
    msg = format_leaderboard_message(leaderboard, rank)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="tournament_refresh")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_main")]
    ])
    
    await query.message.edit_text(msg, parse_mode="HTML", reply_markup=kb)
    await query.answer()


async def distribute_prizes(session: AsyncSession):
    """Distribute weekly prizes (run every Monday 00:00 UTC)"""
    leaderboard = await TournamentManager.get_leaderboard(session, limit=3)
    
    for idx, row in enumerate(leaderboard, 1):
        if idx in TournamentManager.TOP_PRIZES:
            user_id = row[0]
            prize = TournamentManager.TOP_PRIZES[idx]
            
            # Add prize to wallet
            from database.crud import get_wallet
            wallet = await get_wallet(session, user_id, "TON")
            
            if wallet:
                wallet.balance += prize
                
                # Log prize
                from database.models import Transaction
                tx = Transaction(
                    user_id=user_id,
                    type="tournament_prize",
                    amount=prize,
                    currency="TON",
                    fee=Decimal("0"),
                    status="completed"
                )
                session.add(tx)
            
            logger.info(f"Distributed {prize} TON to user {user_id} (rank #{idx})")
    
    await session.commit()
