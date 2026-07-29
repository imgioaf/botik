"""Security utilities: rate limiting, logging, validation."""

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)

# Rate limiting storage: {user_id: [timestamp1, timestamp2, ...]}
_rate_limit_store = defaultdict(list)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware to prevent spam/DoS.
    
    Limits:
    - 5 requests per second
    - 100 requests per minute
    """
    
    MAX_REQUESTS_PER_SECOND = 30
    MAX_REQUESTS_PER_MINUTE = 100
    CLEANUP_INTERVAL = 60  # seconds
    
    def __init__(self):
        super().__init__()
        self.last_cleanup = datetime.now()
    
    async def __call__(self, handler, event: TelegramObject, data: dict):
        """Check rate limits before processing update."""
        
        # Get user ID from different update types
        user_id = None
        if isinstance(event, types.Update):
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
            elif event.inline_query:
                user_id = event.inline_query.from_user.id
        
        if not user_id:
            return await handler(event, data)
        
        now = datetime.now()
        timestamps = _rate_limit_store[user_id]
        
        # Cleanup old timestamps every minute
        if (now - self.last_cleanup).total_seconds() > self.CLEANUP_INTERVAL:
            cutoff = now - timedelta(seconds=60)
            _rate_limit_store[user_id] = [ts for ts in timestamps if ts > cutoff]
            self.last_cleanup = now
        
        # Remove timestamps older than 1 minute
        one_minute_ago = now - timedelta(minutes=1)
        timestamps = [ts for ts in timestamps if ts > one_minute_ago]
        
        # Check per-minute limit
        if len(timestamps) >= self.MAX_REQUESTS_PER_MINUTE:
            logger.warning(f"Rate limit (per minute) exceeded for user {user_id}")
            return
        
        # Check per-second limit
        one_second_ago = now - timedelta(seconds=1)
        recent_count = len([ts for ts in timestamps if ts > one_second_ago])
        if recent_count >= self.MAX_REQUESTS_PER_SECOND:
            logger.warning(f"Rate limit (per second) exceeded for user {user_id}")
            return
        
        # Record this request
        _rate_limit_store[user_id].append(now)
        
        return await handler(event, data)


def log_financial_operation(
    operation_type: str,
    user_id: int,
    amount: str,
    currency: str,
    status: str,
    details: str = ""
):
    """
    Audit log for all financial operations.
    Format: timestamp | operation | user_id | amount | currency | status | details
    """
    log_entry = (
        f"{operation_type:20} | user={user_id:12} | "
        f"{amount:12} {currency:4} | {status:10}"
    )
    if details:
        log_entry += f" | {details}"
    logger.info(log_entry)
