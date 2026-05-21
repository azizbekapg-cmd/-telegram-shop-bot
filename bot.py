import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
 Application,
 CommandHandler,
 MessageHandler,
 filters,
 ContextTypes,
 ConversationHandler,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CARD_NUMBER = os.getenv("CARD_NUMBER")
CARD_OWNER = os.getenv("CARD_OWNER")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCT_CODE, QUANTITY, SIZE, NAME, PHONE, ADDRESS = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
 context.user_data.clear()
 await update.message.reply_text(
 "👔 *Do'konimizga xush kelibsiz!*\n\n"
 "Zakaz berish uchun *mahsulot kodini* yuboring:\n"
 "_(Masalan: KD‐001, SH‐025)_\n\n"
 "Bekor qilish: /cancel",
 parse_mode="Markdown",
 )
 return PRODUCT_CODE

async def get_product_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
 code = update.message.text.strip().upper()
 context.user_data["product_code"] = code
 await update.message.reply_text(
 f"✅ Mahsulot kodi: *{code}*\n\nNechta buyurtma qilmoqchisiz?",
 parse_mode="Markdown",
 )
 return QUANTITY

async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
 text = update.message.text.strip()
 if not text.isdigit() or int(text) < 1:
 await update.message.reply_text("❌ Iltimos, faqat musbat raqam kiriting (1, 2, 3...)")
 return QUANTITY
 context.user_data["quantity"] = text
 sizes = [["S", "M", "L"], ["XL", "XXL", "XXXL"]]
 await update.message.reply_text(
 "📐 *O'lchamni tanlang:*",
 parse_mode="Markdown",
 reply_markup=ReplyKeyboardMarkup(sizes, one_time_keyboard=True, resize_keyboard=True),
 )
 return SIZE

async def get_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
 context.user_data["size"] = update.message.text.strip()
 await update.message.reply_text(
 "👤 *Ismingizni* kiriting:",
 parse_mode="Markdown",
 reply_markup=ReplyKeyboardRemove(),
 )
 return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
 context.user_data["name"] = update.message.text.strip()
 await update.message.reply_text(
 "📱 *Telefon raqamingizni* kiriting:\n_(Masalan: +998901234567)_",
 parse_mode="Markdown",
 )
 return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
 context.user_data["phone"] = update.message.text.strip()
 await update.message.reply_text(
 "🏠 *Yetkazib berish manzilini* kiriting:",
 parse_mode="Markdown",
 )
 return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
 context.user_data["address"] = update.message.text.strip()
 d = context.user_data
 user = update.message.from_user
 
 await update.message.reply_text(
 "📋 *Zakaz qabul qilindi!*\n\n"
 f"🏷 Mahsulot kodi : `{d['product_code']}`\n"
 f"📦 Miqdor : {d['quantity']} ta\n"
 f"📐 O'lcham : {d['size']}\n"
 f"👤 Ism : {d['name']}\n"
 f"📱 Telefon : {d['phone']}\n"
 f"🏠 Manzil : {d['address']}\n\n"
 "━━━━━━━━━━━━━━━━━━━\n"
 "💳 *To'lov uchun karta:*\n"
 f"`{CARD_NUMBER}`\n"
 f"👤 {CARD_OWNER}\n\n"
 "✅ To'lovni amalga oshirgach biz siz bilan bog'lanamiz!",
 parse_mode="Markdown",
 )
 
 order_msg = (
 "🛒 *YANGI ZAKAZ!*\n\n"
 f"🏷 Mahsulot kodi : `{d['product_code']}`\n"
 f"📦 Miqdor : {d['quantity']} ta\n"
 f"📐 O'lcham : {d['size']}\n"
 f"👤 Ism : {d['name']}\n"
 f"📱 Telefon : {d['phone']}\n"
 f"🏠 Manzil : {d['address']}\n"
 f"💳 To'lov : Karta o'tkazma\n"
 f"🔗 Telegram : @{user.username or '—'} (ID: {user.id})"
 )
 await context.bot.send_message(chat_id=ADMIN_ID, text=order_msg, parse_mode="Markdown")
 return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
 await update.message.reply_text(
 "❌ Zakaz bekor qilindi.\nQaytadan boshlash: /start",
 reply_markup=ReplyKeyboardRemove(),
 )
 return ConversationHandler.END

def main():
 app = Application.builder().token(BOT_TOKEN).build()
 conv = ConversationHandler(
 entry_points=[CommandHandler("start", start)],
 states={
 PRODUCT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_code)],
 QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
 SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_size)],
 NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
 PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
 ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
 },
 fallbacks=[CommandHandler("cancel", cancel)],
 )
 app.add_handler(conv)
 print("✅ Bot ishga tushdi!")
 app.run_polling()

if __name__ == "__main__":
 main()
