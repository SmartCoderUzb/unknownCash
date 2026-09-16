import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.database.models import User
from bot.keyboards.reply import get_main_menu
from bot.services.text_manager import TextService
from bot.services.subscription import SubscriptionService

logger = logging.getLogger("UserStart")
start_router = Router()


async def check_user_access(
    message_or_query: Message | CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
) -> bool:
    """
    Foydalanuvchining majburiy kanallarga obunasini tekshiradi.
    Bot adminlari uchun doimiy ochiq.
    """
    user_id = db_user.id
    if settings.is_admin(user_id):
        return True

    target_msg = message_or_query if isinstance(message_or_query, Message) else message_or_query.message

    # Majburiy kanallar tekshiruvi
    is_subscribed, status_list = await SubscriptionService.check_user_subscriptions(bot, session, user_id)
    if not is_subscribed:
        sub_text = await TextService.get_text(
            session=session,
            key="subChannels",
            first=db_user.first_name,
            last=db_user.last_name,
            user_id=user_id
        )
        check_btn = await TextService.get_button(session, "check")
        markup = SubscriptionService.build_subscription_keyboard(status_list, check_btn)
        await target_msg.answer(text=sub_text, reply_markup=markup, disable_web_page_preview=True)
        return False

    return True


@start_router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User,
    is_new_user: bool = False
):
    await state.clear()
    user_id = message.from_user.id
    bot_info = await bot.get_me()

    # Yangi foydalanuvchi bo'lsa va referal orqali kirgan bo'lsa
    args = command.args
    if is_new_user and args and args.isdigit():
        ref_id = int(args)
        if ref_id != user_id and not db_user.referrer_id:
            referrer = await crud.get_user(session, ref_id)
            if referrer:
                db_user.referrer_id = ref_id
                await session.commit()
                # Referrerga yangi taklif xabari
                all_settings = await crud.get_all_settings(session)
                new_ref_text = await TextService.get_text(
                    session=session,
                    key="newRef",
                    refid=user_id,
                    currency=all_settings.get("valyuta", "UC"),
                    refpay=all_settings.get("taklif", "5")
                )
                try:
                    await bot.send_message(chat_id=ref_id, text=new_ref_text)
                except Exception:
                    pass

    # Majburiy obunani tekshirish
    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    # Agar obunani o'tgan bo'lsa va referal mukofoti hali berilmagan bo'lsa
    if db_user.referrer_id and not getattr(db_user, "is_referrer_rewarded", False):
        all_settings = await crud.get_all_settings(session)
        reward = float(all_settings.get("taklif", "5"))
        currency = all_settings.get("valyuta", "UC")

        await crud.increment_referral(session, db_user.referrer_id, reward)
        db_user.is_referrer_rewarded = True
        await session.commit()

        check_ref_text = await TextService.get_text(
            session=session,
            key="checkRef",
            refpay=reward,
            currency=currency,
            refid=user_id
        )
        try:
            await bot.send_message(chat_id=db_user.referrer_id, text=check_ref_text)
        except Exception:
            pass

    # Asosiy menyu
    is_admin = settings.is_admin(user_id)
    welcome_text = await TextService.get_text(
        session=session,
        key="welcome",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=user_id,
        username=message.from_user.username,
        botname=bot_info.username
    )
    menu_kb = await get_main_menu(session, is_admin=is_admin)
    await message.answer(text=welcome_text, reply_markup=menu_kb)


@start_router.callback_query(F.data == "check_subscription")
async def on_check_subscription(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()

    is_subscribed, status_list = await SubscriptionService.check_user_subscriptions(bot, session, user_id)
    if not is_subscribed:
        await callback.answer("⚠️ Hali barcha homiy kanallarga a'zo bo'lmadingiz!", show_alert=True)
        check_btn = await TextService.get_button(session, "check")
        markup = SubscriptionService.build_subscription_keyboard(status_list, check_btn)
        try:
            await callback.message.edit_reply_markup(reply_markup=markup)
        except Exception:
            pass
        return

    await callback.message.delete()

    # Referal mukofotini bir marotaba berish
    if db_user.referrer_id and not getattr(db_user, "is_referrer_rewarded", False):
        all_settings = await crud.get_all_settings(session)
        reward = float(all_settings.get("taklif", "5"))
        currency = all_settings.get("valyuta", "UC")

        await crud.increment_referral(session, db_user.referrer_id, reward)
        db_user.is_referrer_rewarded = True
        await session.commit()

        check_ref_text = await TextService.get_text(
            session=session,
            key="checkRef",
            refpay=reward,
            currency=currency,
            refid=user_id
        )
        try:
            await bot.send_message(chat_id=db_user.referrer_id, text=check_ref_text)
        except Exception:
            pass

    is_admin = settings.is_admin(user_id)
    welcome_text = await TextService.get_text(
        session=session,
        key="welcome",
        first=callback.from_user.first_name,
        last=callback.from_user.last_name,
        user_id=user_id,
        username=callback.from_user.username,
        botname=bot_info.username
    )
    menu_kb = await get_main_menu(session, is_admin=is_admin)
    await callback.message.answer(text=welcome_text, reply_markup=menu_kb)


@start_router.message(F.text.in_(["◀️ Orqaga", "Orqaga"]))
async def back_to_menu(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await state.clear()
    user_id = message.from_user.id
    bot_info = await bot.get_me()

    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    is_admin = settings.is_admin(user_id)
    back_home_text = await TextService.get_text(
        session=session,
        key="backHome",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=user_id,
        botname=bot_info.username
    )
    menu_kb = await get_main_menu(session, is_admin=is_admin)
    await message.answer(text=back_home_text, reply_markup=menu_kb)
