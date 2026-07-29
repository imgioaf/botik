import io
import qrcode

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import get_all_wallets, get_wallet, set_deposit_address
from bot.keyboards.main_kb import wallet_keyboard, back_keyboard
from blockchain.ton_wallet import TONWalletGenerator
from config import settings

router = Router()

# Инициализируется один раз при импорте модуля
_ton_generator = TONWalletGenerator(settings.ton_mnemonic_list)

CURRENCY_EMOJI = {"TON": "💎", "USDT": "💵", "ETH": "⟠", "BTC": "₿"}


@router.callback_query(F.data == "wallet")
async def show_wallet(callback: CallbackQuery, session: AsyncSession):
    wallets = await get_all_wallets(session, callback.from_user.id)

    lines = ["💼 <b>Твой кошелёк</b>\n"]
    for w in wallets:
        emoji = CURRENCY_EMOJI.get(w.currency, "🪙")
        lines.append(f"{emoji} <b>{w.currency}:</b> {w.balance:.6f}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=wallet_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "deposit_TON")
async def show_ton_deposit(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    wallet = await get_wallet(session, user_id, "TON")

    # Генерируем адрес если ещё нет
    if not wallet or not wallet.deposit_address:
        address = _ton_generator.get_deposit_address(user_id)
        await set_deposit_address(session, user_id, "TON", address)
    else:
        address = wallet.deposit_address

    # QR-код
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(f"ton://transfer/{address}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    await callback.message.answer_photo(
        photo=BufferedInputFile(buf.read(), filename="qr.png"),
        caption=(
            f"📥 <b>Пополнение TON</b>\n\n"
            f"Адрес:\n<code>{address}</code>\n\n"
            f"⚡ Средства зачисляются автоматически (~30 сек после подтверждения)\n"
            f"⚠️ Отправляй только <b>TON</b> на этот адрес\n"
            f"Минимум: <b>0.01 TON</b>"
        ),
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.in_({"deposit_USDT", "deposit_ETH", "deposit_BTC"}))
async def show_other_deposit(callback: CallbackQuery):
    currency = callback.data.split("_")[1]
    await callback.message.edit_text(
        f"📥 <b>Пополнение {currency}</b>\n\n"
        f"⏳ Поддержка {currency} будет добавлена в следующем обновлении.",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    from bot.keyboards.main_kb import main_keyboard
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery, session: AsyncSession):
    from database.crud import get_transaction_history
    txs = await get_transaction_history(session, callback.from_user.id, limit=10)

    if not txs:
        await callback.message.edit_text(
            "📊 <b>История транзакций</b>\n\nПока нет транзакций.",
            reply_markup=back_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    type_labels = {
        "deposit": "📥 Депозит",
        "withdraw": "📤 Вывод",
        "transfer_out": "➡️ Перевод",
        "transfer_in": "⬅️ Получение",
        "check_received": "🧾 Чек получен",
        "fee": "💸 Комиссия",
    }

    lines = ["📊 <b>История (последние 10)</b>\n"]
    for tx in txs:
        label = type_labels.get(tx.type, tx.type)
        sign = "+" if tx.type in ("deposit", "transfer_in", "check_received") else "-"
        lines.append(
            f"{label}: <b>{sign}{tx.amount:.4f} {tx.currency}</b>\n"
            f"   {tx.created_at.strftime('%d.%m %H:%M')} • {tx.status}"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "deposit_menu")
async def show_deposit_menu(callback: CallbackQuery):
    from bot.keyboards.main_kb import deposit_menu_keyboard
    await callback.message.edit_text(
        "📥 <b>Пополнение</b>\n\nВыбери валюту:",
        reply_markup=deposit_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()