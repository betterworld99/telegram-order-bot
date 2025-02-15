import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from datetime import datetime

# Bot Constants
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Reads from system environment
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Reads bot token from environment

# Menu items (Persian translations)
MENU = {
    "پیتزا": 10.99,
    "برگر": 7.99,
    "پاستا": 8.99,
    "سالاد": 5.99
}

# States
# SELECT_ITEM, SPECIFY_QUANTITY, GET_ADDRESS, UPLOAD_RECEIPT = range(4)
SELECT_ITEM, SPECIFY_QUANTITY, ADD_MORE_ITEMS, GET_ADDRESS, UPLOAD_RECEIPT = range(5)


# Dictionary to store orders
orders = {}  # Format: {user_id: {order_details}}

# Persistent Keyboard Buttons (Translated into Persian)
PERSISTENT_KEYBOARD = ReplyKeyboardMarkup(
    [['شروع', 'منو', 'لغو']],  # Start, Menu, Cancel
    resize_keyboard=True, one_time_keyboard=False
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Prepare the price list
    price_list = "\n".join([f"🍽 {item}: {price} تومان" for item, price in MENU.items()])

    # Send the welcome message with the price list
    await update.message.reply_text(
        f"خوش آمدید! از دکمه‌های زیر یا دستور /menu برای ثبت سفارش استفاده کنید.\n\n"
        f"📋 *لیست قیمت‌ها*:\n{price_list}",
        parse_mode="Markdown",
        reply_markup=PERSISTENT_KEYBOARD
    )


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    keyboard = [[InlineKeyboardButton(item, callback_data=item)] for item in MENU.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        # If called from a callback query
        await query.message.reply_text("لطفاً یکی از موارد منو را انتخاب کنید:", reply_markup=reply_markup)
    else:
        # If called from a normal update message
        await update.message.reply_text("لطفاً یکی از موارد منو را انتخاب کنید:", reply_markup=reply_markup)
        return SELECT_ITEM


async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item = query.data
    context.user_data.setdefault('order', []).append({'item': item})
    context.user_data['time_ordered'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Store timestamp
    await query.answer()
    await query.edit_message_text(f"شما *{item}* را انتخاب کردید. لطفاً تعداد را وارد کنید:", parse_mode="Markdown")
    return SPECIFY_QUANTITY


async def specify_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError
        context.user_data['order'][-1]['quantity'] = quantity

        keyboard = [
            [InlineKeyboardButton("بله", callback_data='yes')],
            [InlineKeyboardButton("خیر", callback_data='no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("آیا می‌خواهید آیتم دیگری اضافه کنید؟", reply_markup=reply_markup)
        return ADD_MORE_ITEMS
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد مثبت معتبر برای تعداد وارد کنید:")
        return SPECIFY_QUANTITY
    

async def add_more_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == 'yes':
        await show_menu(update, context, query=query)
        return SELECT_ITEM
    else:
        await query.answer()
        await query.edit_message_text("لطفاً آدرس تحویل خود را وارد کنید:")
        return GET_ADDRESS




async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text
    context.user_data['address'] = address
    total_price = sum(MENU[item['item']] * item['quantity'] for item in context.user_data['order'])
    context.user_data['total_price'] = total_price

    order_details = "\n".join([f" {item['item']} {item['quantity']} عدد " for item in context.user_data['order']])
    await update.message.reply_text(
        f"سفارش شما:\n{order_details}\n"
        f"قیمت کل: {total_price:.2f}تومان\n\nلطفاً رسید پرداخت خود را آپلود کنید.",
        parse_mode="Markdown"
    )
    return UPLOAD_RECEIPT


async def upload_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
    context.user_data['receipt_file_id'] = file_id
    user_id = update.message.from_user.id

    # Save order
    orders[user_id] = context.user_data

    # Notify user
    await update.message.reply_text("سفارش شما برای تأیید به ادمین ارسال شد! 🎉", reply_markup=PERSISTENT_KEYBOARD)

    # Notify Admin
    order_details = "\n".join([f"{item['item']} {item['quantity']} عدد " for item in context.user_data['order']])
    admin_message = (
        f"🚨 *سفارش جدید دریافت شد* 🚨\n\n"
        f"شناسه کاربر: {user_id}\n"
        f"آیتم‌ها: \n{order_details}\n"
        f"آدرس: {context.user_data['address']}\n"
        f"قیمت کل: {context.user_data['total_price']:.2f}تومان\n"
        f"زمان ثبت سفارش: {context.user_data['time_ordered']}\n\n"
        "لطفاً این سفارش را تأیید یا رد کنید."
    )
    await context.bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
    await context.bot.send_photo(ADMIN_ID, file_id)

    return ConversationHandler.END


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == ADMIN_ID:
        try:
            command_parts = update.message.text.split()
            if len(command_parts) < 2:
                await update.message.reply_text("⚠️ لطفاً از فرمت زیر استفاده کنید: `/confirm <user_id>`", parse_mode="Markdown")
                return
            
            user_id = int(command_parts[1])  # Extract user_id
            
            if user_id in orders:
                user_order = orders[user_id]
                orders[user_id]['time_confirmed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Generate order details message
                order_details = "\n".join([f"{item['quantity']} عدد {item['item']}" for item in user_order['order']])
                
                # Notify the user
                await context.bot.send_message(
                    user_id,
                    f"🎉 سفارش شما تأیید شد!  🎉\n"
                    f"جزئیات سفارش:\n{order_details}\n"
                    f"تحویل در راه است! 🚚",
                    parse_mode="Markdown"
                )
                await update.message.reply_text(f"✅ سفارش کاربر {user_id} با موفقیت تأیید شد.")
            else:
                await update.message.reply_text("⚠️ هیچ سفارشی برای شناسه کاربر وارد شده یافت نشد.")
        except ValueError:
            await update.message.reply_text("⚠️ شناسه کاربر نامعتبر است. لطفاً یک عدد معتبر وارد کنید.")
    else:
        await update.message.reply_text("❌ فقط ادمین می‌تواند سفارشات را تأیید کند.")

# Cancel Command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرآیند سفارش لغو شد. برای شروع دوباره از دستور /menu استفاده کنید.", reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    

    order_handler = ConversationHandler(
    entry_points=[
        CommandHandler("menu", show_menu),  # Command /menu
        MessageHandler(filters.Regex("^(منو)$"), show_menu),  # Persian "Menu" button handler
    ],
    states={
        SELECT_ITEM: [CallbackQueryHandler(select_item)],
        SPECIFY_QUANTITY: [MessageHandler(filters.TEXT, specify_quantity)],
        ADD_MORE_ITEMS: [CallbackQueryHandler(add_more_items)],
        GET_ADDRESS: [MessageHandler(filters.TEXT, get_address)],
        UPLOAD_RECEIPT: [MessageHandler(filters.PHOTO | filters.Document.PDF, upload_receipt)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(order_handler)
    app.add_handler(CommandHandler("confirm", confirm_order))  # Admin confirmation

    # Add persistent buttons handlers
    app.add_handler(MessageHandler(filters.Regex("^(شروع)$"), start))  # Persian "Start"
    app.add_handler(MessageHandler(filters.Regex("^(لغو)$"), cancel))  # Persian "Cancel"

    # Start polling
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()




    