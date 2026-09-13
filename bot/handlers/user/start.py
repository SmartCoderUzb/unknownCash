import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.database.models import User
from bot.states.user_states import UserStates
from bot.keyboards.reply import (
    get_main_menu,
    get_contact_keyboard
)
from bot.keyboards.inline import get_continue_keyboard
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
    Foydalanuvchi telefon raqami va majburiy kanallarini tekshiradi.
    Agar barchasi to'g'ri bo'lsa True qaytaradi.
    """
    user_id = db_user.id
    target_msg = message_or_query if isinstance(message_or_query, Message) else message_or_query.message

    # 1. Telefon raqami tekshiruvi
    if not db_user.phone:
        await state.set_state(UserStates.request_contact)
        phone_btn = await TextService.get_button(session, "getPhone")
        text_phone = await TextService.get_text(
            session=session,
            key="textPhone",
            first=db_user.first_name,
            last=db_user.last_name,
            user_id=user_id
        )
        await target_msg.answer(
            text=text_phone,
            reply_markup=get_contact_keyboard(phone_btn)
        )
        return False

    # 2. Majburiy kanallar tekshiruvi
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
    db_user: User
):
    await state.clear()
    user_id = message.from_user.id
    bot_info = await bot.get_me()

    # Referal parametrini tekshirish
    args = command.args
    if args and args.isdigit():
        ref_id = int(args)
        if ref_id != user_id and not db_user.referrer_id:
            # Referrerni saqlaymiz
            referrer = await crud.get_user(session, ref_id)
            if referrer:
                db_user.referrer_id = ref_id
                await session.commit()
                # Taklif qilinganligi haqida referrerga xabar
                all_settings = await crud.get_all_settings(session)
                new_ref_text = await TextService.get_text(
                    session=session,
                    key="newRef",
                    refid=user_id,
                    currency=all_settings.get("valyuta", "uc"),
                    refpay=all_settings.get("taklif", "5")
                )
                try:
                    await bot.send_message(chat_id=ref_id, text=new_ref_text)
                except Exception:
                    pass

    # Kirish ruxsati tekshiruvi
    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    # Asosiy menyu
    is_admin = settings.is_admin(user_id)
    all_settings = await crud.get_all_settings(session)
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


@start_router.message(UserStates.request_contact, F.contact)
async def process_contact(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    contact = message.contact
    user_id = message.from_user.id
    bot_info = await bot.get_me()

    # Kontakt tekshiruvi: faqat o'z raqamini yuborishi kerak
    if contact.user_id != user_id:
        phone_btn = await TextService.get_button(session, "getPhone")
        text_phone = await TextService.get_text(
            session=session,
            key="textPhone",
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            user_id=user_id
        )
        await message.answer(
            text=f"⚠️ Faqat o'zingizning kontakt raqamingizni yuboring!\n\n{text_phone}",
            reply_markup=get_contact_keyboard(phone_btn)
        )
        return

    phone = contact.phone_number.replace("+", "").strip()

    # O'zbekiston raqami tekshiruvi: uzunligi 12 va 998 bilan boshlanishi
    if len(phone) == 12 and "998" in phone:
        await crud.update_user_phone(session, user_id, phone)
        await state.clear()

        continue_btn = await TextService.get_button(session, "contiune")
        con_phone_text = await TextService.get_text(
            session=session,
            key="conPhone",
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            user_id=user_id,
            phone=phone
        )
        await message.answer(
            text=con_phone_text,
            reply_markup=get_continue_keyboard(continue_btn)
        )
    else:
        # O'zbekiston raqami bo'lmasa bloklanadi (UcBot.php asl mantig'i)
        no_phone_text = await TextService.get_text(session, "noPhone")
        await crud.set_user_ban(session, user_id, True)
        await state.clear()
        await message.answer(text=no_phone_text, reply_markup=ReplyKeyboardRemove())


@start_router.callback_query(F.data == "davom")
async def on_davom_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await callback.message.delete()
    user_id = callback.from_user.id
    bot_info = await bot.get_me()

    can_proceed = await check_user_access(callback, session, state, bot, db_user)
    if not can_proceed:
        return

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
        await callback.answer("⚠️ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        check_btn = await TextService.get_button(session, "check")
        markup = SubscriptionService.build_subscription_keyboard(status_list, check_btn)
        try:
            await callback.message.edit_reply_markup(reply_markup=markup)
        except Exception:
            pass
        return

    await callback.message.delete()

    # Referal mukofotini berish (agar obuna bo'lib birinchi marta kelsa)
    if db_user.referrer_id:
        all_settings = await crud.get_all_settings(session)
        reward = float(all_settings.get("taklif", "5"))
        currency = all_settings.get("valyuta", "uc")

        await crud.increment_referral(session, db_user.referrer_id, reward)
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
