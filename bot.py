from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import os

# States
START, PRODUCT_CODE, PAYMENT_CONFIRMATION, RECEIPT_PHOTO, SIZE = range(5)

# Product database (code: price)
PRODUCTS = {
    "001": 250000,
    "002": 180000,
    "003": 130000,
    "004": 220000,
}

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
CARD_NUMBER = os.getenv("CARD_NUMBER")
CARD_OWNER = os.getenv("CARD_OWNER")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Buyurtma bermoqchiman", callback_data="order")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎉 Luxano.uz kanalining Rasmiy botiga xush kelibsiz!\n\n"
        "Buyurtma berish uchun tugmani bosing:",
        reply_markup=reply_markup
    )
    return START

async def order_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="Buyurtma bermoqchi bo'lgan tovaringizni kodini yozing:"
    )
    return PRODUCT_CODE

async def product_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    
    if code not in PRODUCTS:
        await update.message.reply_text("❌ Tovar kodi topilmadi. Qayta urinib ko'ring:")
        return PRODUCT_CODE
    
    price = PRODUCTS[code]
    prepayment = price // 2
    
    context.user_data["product_code"] = code
    context.user_data["total_price"] = price
    context.user_data["prepayment"] = prepayment
    
    message = (
        f"✅ Tovar tanlandi!\n\n"
        f"💰 Umumiy narxi: {price:,} so'm\n"
        f"💳 Oldindan to'lov (50%): {prepayment:,} so'm\n\n"
        f"📱 To'lov ma'lumotlari:\n"
        f"Karta egasi: {CARD_OWNER}\n"
        f"Karta raqami: {CARD_NUMBER}\n\n"
        f"⚠️ Cheksiz to'lov qabul qilinmaydi!\n\n"
        f"To'lovni amalga oshirgandan so'ng, chek suratini va razmerlaringizni adminga tashlang."
    )
    
    keyboard = [[InlineKeyboardButton("To'lov qildim", callback_data="payment_done")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    return PAYMENT_CONFIRMATION

async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="📸 Iltimos, to'lov chekining suratini yuboring:"
    )
    return RECEIPT_PHOTO

async def receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Iltimos, rasm yuboring:")
        return RECEIPT_PHOTO
    
    photo_file_id = update.message.photo[-1].file_id
    context.user_data["receipt_photo"] = photo_file_id
    
    await update.message.reply_text("📏 Iltimos, razmerlaringizni yozing (masalan: M, L, XL yoki santimetrda):")
    return SIZE

async def size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    size_text = update.message.text
    context.user_data["size"] = size_text
    
    # Send to admin
    user = update.effective_user
    product_code = context.user_data["product_code"]
    total_price = context.user_data["total_price"]
    prepayment = context.user_data["prepayment"]
    receipt_photo = context.user_data["receipt_photo"]
    
    admin_message = (
        f"📦 Yangi buyurtma!\n\n"
        f"👤 Foydalanuvchi: {user.first_name} {user.last_name or ''}\n"
        f"🆔 User ID: {user.id}\n"
        f"📱 Username: @{user.username or 'yo\'q'}\n\n"
        f"🛍️ Tovar kodi: {product_code}\n"
        f"💰 Umumiy narxi: {total_price:,} so'm\n"
        f"💳 To'langan: {prepayment:,} so'm\n"
        f"📏 Razmer: {size_text}\n"
    )
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=receipt_photo,
        caption=admin_message
    )
    
    await update.message.reply_text(
        f"✅ Buyurtmangiz qabul qilindi!\n\n"
        f"Admin @{ADMIN_USERNAME} bilan bog'lanadi.\n"
        f"Rahmat! 🙏"
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi. /start bosing.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [CallbackQueryHandler(order_button, pattern="order")],
            PRODUCT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_code)],
            PAYMENT_CONFIRMATION: [CallbackQueryHandler(payment_done, pattern="payment_done")],
            RECEIPT_PHOTO: [MessageHandler(filters.PHOTO, receipt_photo)],
            SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, size)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()