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

# Menu items
MENU = {
    "Pizza": 10.99,
    "Burger": 7.99,
    "Pasta": 8.99,
    "Salad": 5.99
}

# States
SELECT_ITEM, SPECIFY_QUANTITY, GET_ADDRESS, UPLOAD_RECEIPT = range(4)

# Dictionary to store orders
orders = {}  # Format: {user_id: {order_details}}

# Persistent Keyboard Buttons
PERSISTENT_KEYBOARD = ReplyKeyboardMarkup(
    [['Start', 'Menu', 'Cancel']],
    resize_keyboard=True, one_time_keyboard=False
)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use the buttons below or /menu to place an order.",
        reply_markup=PERSISTENT_KEYBOARD
    )

# Menu Command
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(item, callback_data=item)] for item in MENU.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an item from the menu:", reply_markup=reply_markup)
    return SELECT_ITEM

# Item Selection
async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item = query.data
    context.user_data['item'] = item
    context.user_data['time_ordered'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Store timestamp
    await query.answer()
    await query.edit_message_text(f"Selected *{item}*. Enter the quantity:", parse_mode="Markdown")
    return SPECIFY_QUANTITY

# Quantity Input
async def specify_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError
        context.user_data['quantity'] = quantity
        await update.message.reply_text("Enter your delivery address:", reply_markup=ReplyKeyboardRemove())
        return GET_ADDRESS
    except ValueError:
        await update.message.reply_text("Please enter a valid positive number for the quantity:")
        return SPECIFY_QUANTITY

# Address Input
async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text
    context.user_data['address'] = address
    total_price = MENU[context.user_data['item']] * context.user_data['quantity']
    context.user_data['total_price'] = total_price

    await update.message.reply_text(
        f"Your order:\n*{context.user_data['item']}* x {context.user_data['quantity']}\n"
        f"Total Price: ${total_price:.2f}\n\nPlease upload your payment receipt.",
        parse_mode="Markdown"
    )
    return UPLOAD_RECEIPT

# Upload Receipt
async def upload_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
    context.user_data['receipt_file_id'] = file_id
    user_id = update.message.from_user.id

    # Save order
    orders[user_id] = context.user_data

    # Notify user
    await update.message.reply_text("Your order has been sent to the admin for confirmation! 🎉", reply_markup=PERSISTENT_KEYBOARD)

    # Notify Admin
    admin_message = (
        f"🚨 *New Order Received* 🚨\n\n"
        f"User ID: {user_id}\n"
        f"Item: {context.user_data['item']}\n"
        f"Quantity: {context.user_data['quantity']}\n"
        f"Address: {context.user_data['address']}\n"
        f"Total Price: ${context.user_data['total_price']:.2f}\n"
        f"Time Ordered: {context.user_data['time_ordered']}\n\n"
        "Please confirm or reject this order."
    )
    await context.bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
    await context.bot.send_photo(ADMIN_ID, file_id)

    return ConversationHandler.END

# Confirm Order (Admin Only)
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure the admin is running the command
    if update.message.chat_id == ADMIN_ID:
        try:
            command_parts = update.message.text.split()
            if len(command_parts) < 2:
                await update.message.reply_text("⚠️ Please use the format: `/confirm <user_id>`", parse_mode="Markdown")
                return
            
            user_id = int(command_parts[1])  # Extract user_id
            
            if user_id in orders:
                user_order = orders[user_id]
                orders[user_id]['time_confirmed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Notify the user
                await context.bot.send_message(
                    user_id,
                    f"🎉 Your order for *{user_order['item']}* x {user_order['quantity']} has been confirmed! 🎉\n"
                    f"Delivery is on the way! 🚚",
                    parse_mode="Markdown"
                )
                await update.message.reply_text(f"✅ Order for user {user_id} has been confirmed successfully.")
            else:
                await update.message.reply_text("⚠️ No order found for the provided user ID.")
        except ValueError:
            await update.message.reply_text("⚠️ Invalid user ID. Please enter a valid numeric user ID.")
    else:
        await update.message.reply_text("❌ Only the admin can confirm orders.")

# Cancel Command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Order process cancelled. Use /menu to start again.", reply_markup=PERSISTENT_KEYBOARD)
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for ordering
    order_handler = ConversationHandler(
        entry_points=[
            CommandHandler("menu", show_menu),  # Command /menu
            MessageHandler(filters.Regex("^(Menu)$"), show_menu),  # "Menu" button handler
        ],
        states={
            SELECT_ITEM: [CallbackQueryHandler(select_item)],
            SPECIFY_QUANTITY: [MessageHandler(filters.TEXT, specify_quantity)],
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
    app.add_handler(MessageHandler(filters.Regex("^(Start)$"), start))
    app.add_handler(MessageHandler(filters.Regex("^(Cancel)$"), cancel))

    # Start polling
    print("Bot is running...")
    app.run_polling()



if __name__ == "__main__":
    main()
