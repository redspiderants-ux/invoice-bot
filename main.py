from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

# States
ORDER_NUM, CLIENT_NAME, PRODUCTS, PAYMENT_METHOD, ADDRESS = range(5)

# Storage (can be replaced with DB)
orders = []

# Start command
def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return update.message.reply_text("Welcome to Master Invoicer Bot. Type /newinvoice to begin.")

# Start invoice creation
def new_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Enter Order Number:")
    return ORDER_NUM

def order_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_num'] = update.message.text
    update.message.reply_text("Enter Client Name (must end with - M):")
    return CLIENT_NAME

def client_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['client_name'] = update.message.text
    update.message.reply_text("Enter Products (e.g., 1P #CODE Name $Price):")
    return PRODUCTS

def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['products'] = update.message.text
    reply_keyboard = [["Cash App", "Zelle", "Chime"]]
    update.message.reply_text(
        "Select Payment Method:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return PAYMENT_METHOD

def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = update.message.text.lower()
    context.user_data['payment_method'] = method
    update.message.reply_text("Enter Address:")
    return ADDRESS

def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    data = context.user_data

    # Basic shipping logic
    shipping = 20

    # Calculate total
    import re, math
    product_lines = data['products'].split('\n')
    total = 0
    for line in product_lines:
        match = re.search(r'\$(\d+)', line)
        if match:
            total += int(match.group(1))

    total += shipping

    # Fee
    fee_rate = {"cash app": 0.05, "zelle": 0.04, "chime": 0.03}
    fee_percent = fee_rate.get(data['payment_method'], 0)
    fee = math.ceil(total * fee_percent)

    # Format invoice
    invoice = f"""
8/6
#{data['order_num']}
{data['client_name']}
{data['products']}

SHIPPING $20
{data['payment_method'].capitalize()} {int(fee_percent*100)}% fee : ${fee}

Total: ${total + fee}

Addy
{data['address']}
"""
    orders.append(invoice)
    update.message.reply_text(invoice)
    return ConversationHandler.END

def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Invoice canceled.")
    return ConversationHandler.END

import os
app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('newinvoice', new_invoice)],
    states={
        ORDER_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_num)],
        CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
        PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, products)],
        PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_method)],
        ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

app.add_handler(CommandHandler('start', start))
app.add_handler(conv_handler)

app.run_polling()
