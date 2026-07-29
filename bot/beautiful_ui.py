"""
Beautiful UI Keyboards for Switzerbot (Cryptobot style)
Inline buttons with emojis and HTML formatting
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from decimal import Decimal


class CryptobotUI:
    """Create beautiful Cryptobot-style keyboards"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu with wallet operations"""
        kb = ReplyKeyboardBuilder()
        
        kb.button(text="💰 Кошелек")
        kb.button(text="📤 Вывести")
        kb.adjust(2)
        
        kb.button(text="🔗 Перевод")
        kb.button(text="📊 Истрия")
        kb.adjust(2)
        
        kb.button(text="💎 Рефер")
        kb.button(text="⚙️ Настройки")
        kb.adjust(2)
        
        return kb.as_markup(resize_keyboard=True)
    
    @staticmethod
    def wallet_menu() -> InlineKeyboardMarkup:
        """Wallet operations inline menu"""
        kb = InlineKeyboardBuilder()
        
        kb.button(text="💵 Пополнить", callback_data="wallet_deposit")
        kb.button(text="📤 Вывести", callback_data="wallet_withdraw")
        kb.adjust(2)
        
        kb.button(text="🔄 Обновить", callback_data="wallet_refresh")
        kb.button(text="↩️ Назад", callback_data="back_main")
        kb.adjust(2)
        
        return kb.as_markup()
    
    @staticmethod
    def currency_selector(action: str = "select") -> InlineKeyboardMarkup:
        """Select cryptocurrency"""
        kb = InlineKeyboardBuilder()
        
        kb.button(text="🪙 TON", callback_data=f"{action}_TON")
        kb.button(text="🔹 USDT", callback_data=f"{action}_USDT")
        kb.adjust(2)
        
        kb.button(text="↩️ Назад", callback_data="back")
        
        return kb.as_markup()
    
    @staticmethod
    def confirm_transaction(
        amount: Decimal,
        currency: str,
        fee: Decimal,
        recipient: str = ""
    ) -> InlineKeyboardMarkup:
        """Confirm transaction"""
        kb = InlineKeyboardBuilder()
        
        kb.button(text="✅ Подтвердить", callback_data="confirm_send")
        kb.button(text="❌ Отменить", callback_data="cancel_send")
        kb.adjust(2)
        
        return kb.as_markup()
    
    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Settings menu"""
        kb = InlineKeyboardBuilder()
        
        kb.button(text="🔐 Безопасность", callback_data="settings_security")
        kb.button(text="📱 Двухфакторная", callback_data="settings_2fa")
        kb.adjust(2)
        
        kb.button(text="🖥️ Устройства", callback_data="settings_devices")
        kb.button(text="⚪ IP Whitelist", callback_data="settings_ip")
        kb.adjust(2)
        
        kb.button(text="↩️ Назад", callback_data="back_main")
        
        return kb.as_markup()
    
    @staticmethod
    def qr_payment_menu() -> InlineKeyboardMarkup:
        """QR payment options"""
        kb = InlineKeyboardBuilder()
        
        kb.button(text="📱 Отправить QR", callback_data="send_qr_code")
        kb.button(text="💳 Реквизиты", callback_data="show_details")
        kb.adjust(2)
        
        kb.button(text="📋 Скопировать", callback_data="copy_address")
        kb.button(text="↩️ Назад", callback_data="back")
        kb.adjust(2)
        
        return kb.as_markup()


class FormattedMessages:
    """Beautiful formatted messages"""
    
    @staticmethod
    def wallet_balance(
        ton_balance: Decimal,
        usdt_balance: Decimal,
        ton_usd: Decimal = Decimal("7.5"),
        total_usd: Decimal = Decimal("0")
    ) -> str:
        """Format wallet balance message"""
        total = ton_balance * ton_usd + usdt_balance
        
        msg = "💰 <b>Ваш Кошелек</b>\n\n"
        msg += "┌─────────────────────┐\n"
        msg += f"│ 🪙 TON\n"
        msg += f"│ <code>{ton_balance:.4f}</code>\n"
        msg += f"│ ≈ ${ton_balance * ton_usd:.2f}\n"
        msg += "├─────────────────────┤\n"
        msg += f"│ 🔹 USDT\n"
        msg += f"│ <code>{usdt_balance:.2f}</code>\n"
        msg += f"│ ≈ ${usdt_balance:.2f}\n"
        msg += "├─────────────────────┤\n"
        msg += f"│ 💵 Итого\n"
        msg += f"│ ≈ <b>${total:.2f}</b>\n"
        msg += "└─────────────────────┘\n"
        
        return msg
    
    @staticmethod
    def deposit_address(
        address: str,
        currency: str = "TON",
        min_amount: Decimal = Decimal("0.01")
    ) -> str:
        """Format deposit address with QR"""
        emoji = "🪙" if currency == "TON" else "🔹"
        
        msg = f"📥 <b>Пополнение {emoji} {currency}</b>\n\n"
        msg += f"<b>Адрес:</b>\n<code>{address}</code>\n\n"
        msg += f"<b>Реквизиты:</b>\n"
        msg += f"• <b>Сеть:</b> TON Blockchain\n"
        msg += f"• <b>Тип:</b> {currency}\n"
        msg += f"• <b>Минимум:</b> {min_amount} {currency}\n"
        msg += f"• <b>Комисия:</b> Бесплатно ✅\n\n"
        msg += f"⏱️ <i>Зачисление: 10-30 сек</i>\n"
        
        return msg
    
    @staticmethod
    def transaction_confirm(
        to_username: str,
        amount: Decimal,
        currency: str,
        fee: Decimal,
        total: Decimal
    ) -> str:
        """Format transaction confirmation"""
        emoji = "🪙" if currency == "TON" else "🔹"
        
        msg = "✋ <b>Проверьте перевод</b>\n\n"
        msg += f"👤 <b>Кому:</b> @{to_username}\n"
        msg += f"{emoji} <b>Сумма:</b> {amount} {currency}\n"
        msg += f"💳 <b>Комиссия:</b> {fee} {currency}\n"
        msg += "─────────────────────\n"
        msg += f"📊 <b>Итого:</b> {total} {currency}\n\n"
        msg += "✅ Нажмите кнопку ниже для подтверждения"
        
        return msg
    
    @staticmethod
    def transaction_success(
        tx_id: str,
        to_username: str,
        amount: Decimal,
        currency: str
    ) -> str:
        """Format successful transaction message"""
        emoji = "🪙" if currency == "TON" else "🔹"
        
        msg = "✅ <b>Успешно!</b>\n\n"
        msg += f"📤 Перевод отправлен\n"
        msg += f"👤 <b>Адресату:</b> @{to_username}\n"
        msg += f"{emoji} <b>Сумма:</b> {amount} {currency}\n"
        msg += f"🆔 <b>ID:</b> <code>{tx_id}</code>\n\n"
        msg += f"⏱️ <i>Обработано за 1-2 сек</i>\n"
        
        return msg
    
    @staticmethod
    def referral_program(
        referral_link: str,
        ref_count: int,
        earned: Decimal
    ) -> str:
        """Format referral program info"""
        msg = "🔗 <b>Реферальная Программа</b>\n\n"
        msg += f"👥 <b>Приглашено:</b> {ref_count} пользователей\n"
        msg += f"💰 <b>Заработано:</b> {earned:.4f} TON\n\n"
        msg += "📊 <b>Структура комиссий:</b>\n"
        msg += "• Вы получаете 20% от комиссии реферала\n"
        msg += "• Комиссия при переводе: 0.5%\n"
        msg += "• Ваша комиссия: 0.1%\n\n"
        msg += "<b>🔗 Ваша ссылка:</b>\n"
        msg += f"<code>{referral_link}</code>\n\n"
        msg += "💡 <i>Делитесь ссылкой с друзьями!</i>"
        
        return msg
    
    @staticmethod
    def security_status(
        two_fa_enabled: bool,
        trusted_devices: int,
        whitelisted_ips: int,
        last_login: str = "Только что"
    ) -> str:
        """Format security status"""
        two_fa_status = "✅ Включена" if two_fa_enabled else "❌ Отключена"
        
        msg = "🔐 <b>Статус Безопасности</b>\n\n"
        msg += f"🔑 <b>Двухфакторная:</b> {two_fa_status}\n"
        msg += f"🖥️ <b>Устройства:</b> {trusted_devices}\n"
        msg += f"⚪ <b>IP Адреса:</b> {whitelisted_ips}\n"
        msg += f"🕐 <b>Последний вход:</b> {last_login}\n\n"
        msg += "💡 <i>Рекомендуем включить 2FA для защиты</i>"
        
        return msg
    
    @staticmethod
    def withdrawal_pending(
        amount: Decimal,
        currency: str,
        address: str,
        fee: Decimal,
        risk_score: float
    ) -> str:
        """Format pending withdrawal"""
        emoji = "🪙" if currency == "TON" else "🔹"
        
        msg = "⏳ <b>Вывод на Проверке</b>\n\n"
        msg += f"{emoji} <b>Сумма:</b> {amount} {currency}\n"
        msg += f"📍 <b>Адрес:</b> <code>{address[:20]}...</code>\n"
        msg += f"💳 <b>Комиссия:</b> {fee} {currency}\n"
        msg += f"⚠️ <b>Уровень Риска:</b> {risk_score:.1f}/10\n\n"
        
        if risk_score > 7.0:
            msg += "🔍 <b>Требуется Верификация</b>\n"
            msg += "Для вывода крупной суммы нужно подтвердить действие.\n"
            msg += "Мы отправим код проверки на email.\n"
        
        return msg


class QRCodeGenerator:
    """Generate QR codes for payments"""
    
    @staticmethod
    async def generate_deposit_qr(address: str) -> bytes:
        """Generate QR code for deposit address"""
        import qrcode
        import io
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(address)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
    
    @staticmethod
    async def generate_payment_qr(
        address: str,
        amount: str = "",
        currency: str = "TON"
    ) -> bytes:
        """Generate QR code for payment (with amount)"""
        import qrcode
        import io
        
        if amount:
            data = f"ton://transfer/{address}?amount={amount}"
        else:
            data = f"ton://transfer/{address}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
