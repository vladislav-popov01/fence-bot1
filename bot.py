#!/usr/bin/env python3
"""
🎨 Единый Telegram-бот:
  — Магазин декоративных заборов ПО-2
  — Управление каналом @smr_gsk

Автор: Arena.ai
"""

import logging, json, os, asyncio, random
from datetime import datetime, time

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove, ChatMemberUpdated,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ChatMemberHandler,
    filters, ContextTypes,
)

from config import *
from keep_alive import keep_alive

# ─── Логирование ─────────────────────────────────────
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ─── Состояния ────────────────────────────────────────
(S_ITEM, S_STYLE, S_WISH, S_PHOTO, S_NAME, S_PHONE,
 S_CITY, S_CONFIRM, S_EXAMPLE, S_CHANNEL_TEXT, S_CHANNEL_PHOTO) = range(11)

# ─── Файлы данных ─────────────────────────────────────
def _load(f):
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as fh: return json.load(fh)
    return [] if f != "stats.json" else {}
def _save(f, d):
    with open(f, "w", encoding="utf-8") as fh: json.dump(d, fh, ensure_ascii=False, indent=2)

def load_orders():   return _load("orders.json")
def load_examples(): return _load("examples.json")
def load_queue():    return _load("queue.json")
def load_stats():    return _load("stats.json")
def save_orders(d):  _save("orders.json", d)
def save_examples(d):_save("examples.json", d)
def save_queue(d):   _save("queue.json", d)
def save_stats(d):   _save("stats.json", d)

def save_order(o):
    orders = load_orders(); orders.append(o); save_orders(orders)

def fmt(t):
    return t.format(bot=SHOP_BOT_USERNAME, master=MASTER_USERNAME)

SHOP_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🛍 Заказать", url=SHOP_BOT_LINK)],
    [InlineKeyboardButton("💬 Написать мастеру", url=f"https://t.me/{MASTER_USERNAME}")],
])

# ══════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    is_admin = u.id == ADMIN_ID

    welcome = (
        f"Добро пожаловать, {u.first_name}! 👋\n\n"
        f"<b>{SHOP_NAME}</b>\n{SHOP_DESCRIPTION}\n\n"
        "Каждый забор — произведение искусства, "
        "созданное вручную специально для вас.\n\n"
        "Выберите действие:"
    )
    buttons = [
        [InlineKeyboardButton("🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("📝 Оформить заказ", callback_data="new_order")],
        [InlineKeyboardButton("🎨 Примеры работ", callback_data="examples")],
        [InlineKeyboardButton("💬 Написать мастеру", url=f"https://t.me/{MASTER_USERNAME}")],
        [InlineKeyboardButton("ℹ️ О нас", callback_data="about")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("📢 ═ ПАНЕЛЬ КАНАЛА ═", callback_data="channel_panel")])

    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════
#  КАТАЛОГ
# ══════════════════════════════════════════════════════
async def show_catalog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    for item in CATALOG:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"📝 Заказать", callback_data=f"order_{item['id']}")]])
        await q.message.reply_text(f"<b>{item['name']}</b>\n\n{item['description']}\n\n💰 <b>{item['price_text']}</b>", reply_markup=kb, parse_mode="HTML")
    await q.message.reply_text("👆 Выберите товар или вернитесь в меню.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Меню", callback_data="main_menu")]]))

# ══════════════════════════════════════════════════════
#  ПРИМЕРЫ РАБОТ
# ══════════════════════════════════════════════════════
async def show_examples(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    examples = load_examples()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Оформить заказ", callback_data="new_order")],
        [InlineKeyboardButton("◀️ Меню", callback_data="main_menu")],
    ])
    if not examples:
        await q.message.reply_text("🎨 <b>Примеры работ</b>\n\nСкоро здесь появятся фото! ✨", reply_markup=kb, parse_mode="HTML")
        return
    await q.message.reply_text(f"🎨 <b>Примеры работ</b> ({len(examples)} шт.):", parse_mode="HTML")
    for ex in examples:
        try: await q.message.reply_photo(photo=ex["photo_id"], caption=f"🎨 {ex.get('caption','')}" if ex.get("caption") else None)
        except: pass
    await q.message.reply_text("👆 Понравилось? Закажите свой!", reply_markup=kb)

# ══════════════════════════════════════════════════════
#  О НАС
# ══════════════════════════════════════════════════════
async def show_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text(
        f"ℹ️ <b>{SHOP_NAME}</b>\n\n"
        "✅ Каждый забор — индивидуальный проект\n"
        "✅ Роспись по вашим пожеланиям и эскизам\n"
        "✅ Качественные материалы и краски\n"
        "✅ Защитное покрытие от непогоды\n"
        "✅ Доставка обсуждается индивидуально\n\n"
        "Превратите обычный забор в искусство! 🎨",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Оформить заказ", callback_data="new_order")],
            [InlineKeyboardButton("◀️ Меню", callback_data="main_menu")],
        ]), parse_mode="HTML")

# ══════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ══════════════════════════════════════════════════════
async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    is_admin = q.from_user.id == ADMIN_ID
    buttons = [
        [InlineKeyboardButton("🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("📝 Оформить заказ", callback_data="new_order")],
        [InlineKeyboardButton("🎨 Примеры работ", callback_data="examples")],
        [InlineKeyboardButton("💬 Написать мастеру", url=f"https://t.me/{MASTER_USERNAME}")],
        [InlineKeyboardButton("ℹ️ О нас", callback_data="about")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("📢 ═ ПАНЕЛЬ КАНАЛА ═", callback_data="channel_panel")])
    await q.message.reply_text(f"<b>{SHOP_NAME}</b>\n\nВыберите действие:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

# ══════════════════════════════════════════════════════
#  ОФОРМЛЕНИЕ ЗАКАЗА (шаги 1–6)
# ══════════════════════════════════════════════════════
async def order_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data.startswith("order_"):
        iid = q.data.replace("order_","")
        item = next((i for i in CATALOG if i["id"]==iid), None)
        if item:
            ctx.user_data["order"] = {"item": item["name"], "item_id": iid}
            return await _ask_style(q, ctx)
    buttons = [[InlineKeyboardButton(i["name"], callback_data=f"sel_{i['id']}")] for i in CATALOG]
    buttons.append([InlineKeyboardButton("◀️ Отмена", callback_data="main_menu")])
    await q.message.reply_text("📝 <b>Шаг 1/6:</b> Выберите забор:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return S_ITEM

async def sel_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    iid = q.data.replace("sel_","")
    item = next((i for i in CATALOG if i["id"]==iid), None)
    if not item: return S_ITEM
    ctx.user_data["order"] = {"item": item["name"], "item_id": iid}
    return await _ask_style(q, ctx)

async def _ask_style(q, ctx):
    buttons = [[InlineKeyboardButton(s, callback_data=f"sty_{i}")] for i,s in enumerate(PAINTING_STYLES)]
    await q.message.reply_text("🎨 <b>Шаг 2/6:</b> Стиль росписи:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return S_STYLE

async def sel_style(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    idx = int(q.data.replace("sty_",""))
    if 0 <= idx < len(PAINTING_STYLES): ctx.user_data["order"]["style"] = PAINTING_STYLES[idx]
    await q.message.reply_text("✏️ <b>Шаг 3/6:</b> Опишите пожелания:\n— Цвета, сюжет, размеры, количество секций", parse_mode="HTML")
    return S_WISH

async def recv_wish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["wish"] = update.message.text
    await update.message.reply_text("📸 <b>Шаг 4/6:</b> Отправьте фото-референс или нажмите «Пропустить».",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Пропустить", callback_data="skip_ph")]]), parse_mode="HTML")
    return S_PHOTO

async def recv_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["photo_id"] = update.message.photo[-1].file_id
    await update.message.reply_text("👤 <b>Шаг 5/6:</b> Введите ваше <b>имя</b>:", parse_mode="HTML")
    return S_NAME

async def skip_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data["order"]["photo_id"] = None
    await q.message.reply_text("👤 <b>Шаг 5/6:</b> Введите ваше <b>имя</b>:", parse_mode="HTML")
    return S_NAME

async def recv_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["name"] = update.message.text
    await update.message.reply_text("📱 Введите <b>номер телефона</b>:", parse_mode="HTML")
    return S_PHONE

async def recv_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["phone"] = update.message.text
    await update.message.reply_text("🏙 Введите <b>город</b> (для доставки):", parse_mode="HTML")
    return S_CITY

async def recv_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"]["city"] = update.message.text
    o = ctx.user_data["order"]
    txt = (f"📋 <b>Шаг 6/6: Проверьте заказ</b>\n\n"
           f"🏷 {o['item']}\n🎨 {o.get('style','—')}\n✏️ {o.get('wish','—')}\n"
           f"📸 {'Есть ✅' if o.get('photo_id') else 'Нет'}\n"
           f"👤 {o['name']}\n📱 {o['phone']}\n🏙 {o['city']}\n\n💰 <b>Цена — после согласования</b>\n\nВсё верно?")
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да", callback_data="confirm"), InlineKeyboardButton("❌ Нет", callback_data="cancel_ord")]
    ]), parse_mode="HTML")
    return S_CONFIRM

async def confirm_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    o = ctx.user_data.get("order",{}); u = q.from_user
    oid = f"ORD-{datetime.now():%Y%m%d%H%M%S}-{u.id}"
    o.update(order_id=oid, user_id=u.id, username=u.username or "—", date=f"{datetime.now():%d.%m.%Y %H:%M}", status="⏳")
    save_order(o)
    await q.message.reply_text(
        f"✅ <b>Заказ #{oid} оформлен!</b>\n\n"
        f"1️⃣ Мастер рассмотрит заказ\n2️⃣ Свяжется для обсуждения цены\n3️⃣ Пришлёт сумму для оплаты\n\n"
        f"💳 <b>{PAYMENT_METHOD} на {PAYMENT_BANK}</b>\n📱 <b>{PAYMENT_PHONE}</b>\n\n"
        "⚠️ <i>Не переводите до согласования цены!</i>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Я оплатил(а)", callback_data=f"paid_{oid}")],
            [InlineKeyboardButton("◀️ Меню", callback_data="main_menu")],
        ]), parse_mode="HTML")
    admin_txt = (f"🔔 <b>НОВЫЙ ЗАКАЗ #{oid}</b>\n📅 {o['date']}\n\n"
                 f"🏷 {o['item']}\n🎨 {o.get('style','—')}\n✏️ {o.get('wish','—')}\n\n"
                 f"👤 {o['name']}\n📱 {o['phone']}\n🏙 {o['city']}\n💬 @{o['username']} (ID:{o['user_id']})")
    try:
        await ctx.bot.send_message(ADMIN_ID, admin_txt, parse_mode="HTML")
        if o.get("photo_id"): await ctx.bot.send_photo(ADMIN_ID, o["photo_id"], caption=f"📸 Референс #{oid}")
    except Exception as e: log.error(f"Admin notify: {e}")
    return ConversationHandler.END

async def cancel_ord(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); ctx.user_data.pop("order",None)
    await q.message.reply_text("❌ Заказ отменён.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Меню", callback_data="main_menu")]]))
    return ConversationHandler.END

# ══════════════════════════════════════════════════════
#  ОПЛАТА
# ══════════════════════════════════════════════════════
async def client_paid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); oid = q.data.replace("paid_",""); u = q.from_user
    await q.message.reply_text(f"✅ Спасибо! Мастер проверит оплату заказа <b>#{oid}</b>.", parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Меню", callback_data="main_menu")]]))
    try:
        await ctx.bot.send_message(ADMIN_ID,
            f"💰 <b>ОПЛАТА!</b> #{oid}\n👤 @{u.username or '—'} ({u.first_name}, ID:{u.id})",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Подтвердить", callback_data=f"aok_{u.id}_{oid}"),
                 InlineKeyboardButton("❌ Не найдена", callback_data=f"ano_{u.id}_{oid}")]]))
    except: pass

async def admin_ok(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID: await q.answer("⛔"); return
    await q.answer("✅"); p = q.data.split("_"); cid=int(p[1]); oid="_".join(p[2:])
    try: await ctx.bot.send_message(cid, f"✅ <b>Оплата подтверждена!</b> Заказ #{oid} в работе. 🎨", parse_mode="HTML")
    except: pass
    await q.message.edit_text(q.message.text + "\n\n✅ <b>ПОДТВЕРЖДЕНО</b>", parse_mode="HTML")

async def admin_no(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID: await q.answer("⛔"); return
    await q.answer("❌"); p = q.data.split("_"); cid=int(p[1]); oid="_".join(p[2:])
    try: await ctx.bot.send_message(cid, f"⚠️ Оплата #{oid} не найдена. Проверьте перевод: {PAYMENT_PHONE} ({PAYMENT_BANK})", parse_mode="HTML")
    except: pass
    await q.message.edit_text(q.message.text + "\n\n❌ <b>НЕ НАЙДЕНА</b>", parse_mode="HTML")

# ══════════════════════════════════════════════════════
#  ПРИМЕРЫ РАБОТ — УПРАВЛЕНИЕ
# ══════════════════════════════════════════════════════
async def add_example_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return ConversationHandler.END
    await update.message.reply_text("📸 Отправьте фото работы (можно с подписью). /cancel для отмены.")
    return S_EXAMPLE

async def recv_example(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return ConversationHandler.END
    ex = load_examples()
    ex.append({"photo_id": update.message.photo[-1].file_id, "caption": update.message.caption or "", "date": f"{datetime.now():%d.%m.%Y %H:%M}"})
    save_examples(ex)
    await update.message.reply_text(f"✅ Фото добавлено! Всего: {len(ex)}", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("📸 Ещё", callback_data="add_more_ex")], [InlineKeyboardButton("✅ Готово", callback_data="main_menu")]]))
    return ConversationHandler.END

async def add_more_ex(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id != ADMIN_ID: return
    await q.message.reply_text("📸 Отправьте следующее фото. /cancel для отмены.")
    return S_EXAMPLE

async def del_examples(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    n = len(load_examples()); save_examples([])
    await update.message.reply_text(f"🗑 Удалено {n} примеров.")

# ══════════════════════════════════════════════════════
#  ПАНЕЛЬ КАНАЛА (только для админа)
# ══════════════════════════════════════════════════════
async def channel_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id != ADMIN_ID: return
    st = load_stats(); qu = load_queue()
    await q.message.reply_text(
        f"📢 <b>Панель канала @{CHANNEL_USERNAME}</b>\n\n"
        f"📝 Постов: {st.get('posts',0)} | 👥 Подписчиков: {st.get('members',0)}\n"
        f"📋 В очереди: {len(qu)} | ⏰ Автопостинг: {', '.join(f'{h}:00' for h in POSTING_HOURS)}\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Текстовый пост", callback_data="ch_text")],
            [InlineKeyboardButton("📸 Фото-пост", callback_data="ch_photo")],
            [InlineKeyboardButton("🔄 Автопост сейчас", callback_data="ch_auto")],
            [InlineKeyboardButton("📋 Шаблоны", callback_data="ch_templates")],
            [InlineKeyboardButton("◀️ Меню магазина", callback_data="main_menu")],
        ]), parse_mode="HTML")

async def ch_text_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id != ADMIN_ID: return
    await q.message.reply_text("📝 Напишите текст поста для канала. /cancel для отмены.")
    return S_CHANNEL_TEXT

async def ch_text_recv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return ConversationHandler.END
    try:
        await ctx.bot.send_message(f"@{CHANNEL_USERNAME}", update.message.text, parse_mode="HTML", reply_markup=SHOP_KB)
        st = load_stats(); st["posts"] = st.get("posts",0)+1; save_stats(st)
        await update.message.reply_text("✅ Опубликовано!")
    except Exception as e: await update.message.reply_text(f"❌ Ошибка: {e}")
    return ConversationHandler.END

async def ch_photo_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id != ADMIN_ID: return
    await q.message.reply_text("📸 Отправьте фото для канала (можно с подписью). /cancel для отмены.")
    return S_CHANNEL_PHOTO

async def ch_photo_recv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return ConversationHandler.END
    cap = update.message.caption or f"🎨 @{SHOP_BOT_USERNAME} | @{MASTER_USERNAME}"
    try:
        await ctx.bot.send_photo(f"@{CHANNEL_USERNAME}", update.message.photo[-1].file_id, caption=cap, parse_mode="HTML", reply_markup=SHOP_KB)
        st = load_stats(); st["posts"] = st.get("posts",0)+1; save_stats(st)
        await update.message.reply_text("✅ Фото опубликовано!")
    except Exception as e: await update.message.reply_text(f"❌ Ошибка: {e}")
    return ConversationHandler.END

async def ch_auto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id != ADMIN_ID: return
    await _send_auto(ctx)
    await q.message.reply_text("✅ Автопост отправлен!")

async def ch_templates(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id != ADMIN_ID: return
    buttons = [[InlineKeyboardButton(f"📝 Шаблон {i+1}", callback_data=f"tpl_{i}")] for i in range(len(POST_TEMPLATES))]
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="channel_panel")])
    await q.message.reply_text("📋 Выберите шаблон для публикации:", reply_markup=InlineKeyboardMarkup(buttons))

async def ch_tpl_send(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.from_user.id != ADMIN_ID: return
    idx = int(q.data.replace("tpl_",""))
    if 0 <= idx < len(POST_TEMPLATES):
        try:
            await ctx.bot.send_message(f"@{CHANNEL_USERNAME}", fmt(POST_TEMPLATES[idx]), parse_mode="HTML", reply_markup=SHOP_KB)
            st = load_stats(); st["posts"] = st.get("posts",0)+1; save_stats(st)
            await q.message.reply_text("✅ Шаблон опубликован!")
        except Exception as e: await q.message.reply_text(f"❌ {e}")

# ── Автопостинг ──
async def _send_auto(ctx: ContextTypes.DEFAULT_TYPE):
    qu = load_queue()
    if qu: txt = qu.pop(0).get("text",""); save_queue(qu)
    else: txt = fmt(random.choice(POST_TEMPLATES))
    try:
        await ctx.bot.send_message(f"@{CHANNEL_USERNAME}", txt, parse_mode="HTML", reply_markup=SHOP_KB)
        st = load_stats(); st["posts"] = st.get("posts",0)+1; st["last_auto"] = f"{datetime.now():%d.%m.%Y %H:%M}"; save_stats(st)
    except Exception as e: log.error(f"Autopost: {e}")

async def auto_job(ctx: ContextTypes.DEFAULT_TYPE): await _send_auto(ctx)

# ══════════════════════════════════════════════════════
#  ПРИВЕТСТВИЕ НОВЫХ ПОДПИСЧИКОВ КАНАЛА
# ══════════════════════════════════════════════════════
async def welcome_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    r = update.chat_member
    if r.new_chat_member.status in ("member","administrator") and r.old_chat_member.status in ("left","kicked","banned"):
        st = load_stats(); st["members"] = st.get("members",0)+1; save_stats(st)
        try:
            await ctx.bot.send_message(r.new_chat_member.user.id,
                f"Привет! 👋 Спасибо за подписку на <b>{SHOP_NAME}</b>! 🎨\n\nХотите заказать свой забор?",
                reply_markup=SHOP_KB, parse_mode="HTML")
        except: pass

# ══════════════════════════════════════════════════════
#  АДМИН-КОМАНДЫ
# ══════════════════════════════════════════════════════
async def cmd_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    orders = load_orders()
    if not orders: await update.message.reply_text("📭 Заказов нет."); return
    txt = "📋 <b>Последние заказы:</b>\n\n"
    for o in orders[-10:][::-1]:
        txt += f"<b>#{o.get('order_id','?')}</b> {o.get('date','')} — {o.get('name','')} ({o.get('city','')})\n"
    await update.message.reply_text(txt, parse_mode="HTML")

async def cmd_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    args = update.message.text.split(maxsplit=2)
    if len(args)<3: await update.message.reply_text("/msg <id> <текст>"); return
    try:
        await ctx.bot.send_message(int(args[1]), f"💬 <b>Сообщение от мастера:</b>\n\n{args[2]}", parse_mode="HTML")
        await update.message.reply_text("✅ Отправлено!")
    except Exception as e: await update.message.reply_text(f"❌ {e}")

async def cmd_queue(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = update.message.text.replace("/add_to_queue","",1).strip()
    if not txt: await update.message.reply_text("/add_to_queue <текст поста>"); return
    qu = load_queue(); qu.append({"text":txt}); save_queue(qu)
    await update.message.reply_text(f"✅ В очереди: {len(qu)}")

# ── Пересылка сообщений от клиентов ──
async def forward_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID: return
    u = update.effective_user
    try:
        await ctx.bot.send_message(ADMIN_ID, f"💬 @{u.username or '—'} ({u.first_name}, ID:{u.id})\nОтветить: /msg {u.id} <текст>", parse_mode="HTML")
        await update.message.forward(ADMIN_ID)
    except: pass
    await update.message.reply_text("✉️ Передано мастеру!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Меню", callback_data="main_menu")]]))

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("order",None)
    await update.message.reply_text("❌ Отменено. /start — меню.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ══════════════════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════════════════
def main():
    if BOT_TOKEN.startswith("ВСТАВЬТЕ"): print("❌ Укажите токен в config.py!"); return
    if ADMIN_ID == 123456789: print("⚠️ Укажите ADMIN_ID в config.py!")

    # Запускаем веб-сервер для пингов (чтобы Render не усыпил)
    keep_alive()

    app = Application.builder().token(BOT_TOKEN).build()

    # Заказ
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(order_start, pattern=r"^(new_order|order_)")],
        states={
            S_ITEM:    [CallbackQueryHandler(sel_item, pattern=r"^sel_")],
            S_STYLE:   [CallbackQueryHandler(sel_style, pattern=r"^sty_")],
            S_WISH:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_wish)],
            S_PHOTO:   [MessageHandler(filters.PHOTO, recv_photo), CallbackQueryHandler(skip_photo, pattern=r"^skip_ph$")],
            S_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_name)],
            S_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_phone)],
            S_CITY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_city)],
            S_CONFIRM: [CallbackQueryHandler(confirm_order, pattern=r"^confirm$"), CallbackQueryHandler(cancel_ord, pattern=r"^cancel_ord$")],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(main_menu, pattern=r"^main_menu$")],
        per_user=True, per_chat=True))

    # Примеры
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_example", add_example_cmd), CallbackQueryHandler(add_more_ex, pattern=r"^add_more_ex$")],
        states={S_EXAMPLE: [MessageHandler(filters.PHOTO, recv_example)]},
        fallbacks=[CommandHandler("cancel", cancel)], per_user=True, per_chat=True))

    # Канал — текст
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ch_text_start, pattern=r"^ch_text$")],
        states={S_CHANNEL_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ch_text_recv)]},
        fallbacks=[CommandHandler("cancel", cancel)], per_user=True, per_chat=True))

    # Канал — фото
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ch_photo_start, pattern=r"^ch_photo$")],
        states={S_CHANNEL_PHOTO: [MessageHandler(filters.PHOTO, ch_photo_recv)]},
        fallbacks=[CommandHandler("cancel", cancel)], per_user=True, per_chat=True))

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", cmd_orders))
    app.add_handler(CommandHandler("msg", cmd_msg))
    app.add_handler(CommandHandler("add_to_queue", cmd_queue))
    app.add_handler(CommandHandler("delete_examples", del_examples))

    # Кнопки
    app.add_handler(CallbackQueryHandler(show_catalog, pattern=r"^catalog$"))
    app.add_handler(CallbackQueryHandler(show_examples, pattern=r"^examples$"))
    app.add_handler(CallbackQueryHandler(show_about, pattern=r"^about$"))
    app.add_handler(CallbackQueryHandler(main_menu, pattern=r"^main_menu$"))
    app.add_handler(CallbackQueryHandler(client_paid, pattern=r"^paid_"))
    app.add_handler(CallbackQueryHandler(admin_ok, pattern=r"^aok_"))
    app.add_handler(CallbackQueryHandler(admin_no, pattern=r"^ano_"))
    app.add_handler(CallbackQueryHandler(channel_panel, pattern=r"^channel_panel$"))
    app.add_handler(CallbackQueryHandler(ch_auto, pattern=r"^ch_auto$"))
    app.add_handler(CallbackQueryHandler(ch_templates, pattern=r"^ch_templates$"))
    app.add_handler(CallbackQueryHandler(ch_tpl_send, pattern=r"^tpl_"))

    # Новые подписчики
    app.add_handler(ChatMemberHandler(welcome_member, ChatMemberHandler.CHAT_MEMBER))

    # Свободные сообщения
    app.add_handler(MessageHandler((filters.TEXT|filters.PHOTO) & ~filters.COMMAND, forward_msg))

    # Автопостинг
    jq = app.job_queue
    if jq:
        for h in POSTING_HOURS:
            jq.run_daily(auto_job, time=time(hour=h, minute=0), name=f"auto_{h}")

    print(f"🤖 Единый бот запущен! Магазин + Канал @{CHANNEL_USERNAME}")
    print(f"   Админ: {ADMIN_ID} | Мастер: @{MASTER_USERNAME}")
    try: app.run_polling(drop_pending_updates=True, allowed_updates=["message","callback_query","chat_member"])
    except RuntimeError:
        async def _run():
            async with app:
                await app.initialize(); await app.start()
                await app.updater.start_polling(drop_pending_updates=True, allowed_updates=["message","callback_query","chat_member"])
                print("✅ Работает!")
                try:
                    while True: await asyncio.sleep(3600)
                except: pass
                finally: await app.updater.stop(); await app.stop(); await app.shutdown()
        asyncio.run(_run())

if __name__ == "__main__":
    main()
