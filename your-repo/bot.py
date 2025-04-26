import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import json
import os
from datetime import datetime

# تنظیمات پایه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن ربات و آیدی ادمین
TOKEN = '7924870342:AAHq4DCOs2JuuPyxLmf8osQoVsjdZKX50_Y'
ADMIN_ID = 7058515436

# حالت‌های گفتگو
(
    MENU, SUPPORT, PRODUCTS, 
    ORDER, PAYMENT, SEND_MESSAGE,
    BROADCAST, MANAGE_PRODUCTS, ADD_PRODUCT,
    EDIT_PRODUCT, DELETE_PRODUCT, VIEW_STATS,
    COOPERATION
) = range(13)

# دیتابیس ساده
DB_FILE = 'database.json'

# اطلاعات پیش‌فرض
DEFAULT_DATA = {
    'products': {
        '1': {
            'name': 'Prime PC',
            'description': 'سرویس پرمیوم مخصوص کامپیوتر\n- تک کاربره\n- سرعت بالا\n-ضد بن و کاملا امن\n- پشتیبانی 24/7',
            'price': '299,000 تومان',
            'image': None
        },
        '2': {
            'name': 'Lite PC',
            'description': 'سرویس لایت مخصوص کامپیوتر\n- تک کاربره\n- سرعت متوسط\n-ضد بن و کاملا امن\n- پشتیبانی 24/7',
            'price': '199,000 تومان',
            'image': None
        },
        '3': {
            'name': 'Android Visual',
            'description': 'سرویس مخصوص اندروید\n-تک کاربره\n- درانواع رنگ ها\n-ضد بن و کاملا امن\n- پشتیبانی 24/7',
            'price': '299,000 تومان',
            'image': None
        }
    },
    'bank_info': {
        'card_number': '6104-3386-4447-6687',
        'card_holder': 'سبحان پرهیزکار',
        'bank_name': 'ملت'
    },
    'orders': {},
    'user_messages': {},
    'stats': {
        'total_users': 0,
        'total_orders': 0,
        'total_sales': 0
    }
}

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=4)
    return DEFAULT_DATA

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_keyboard(buttons, columns=2):
    keyboard = []
    row = []
    for i, button in enumerate(buttons, 1):
        row.append(button)
        if i % columns == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID:
        buttons = [
            InlineKeyboardButton("📦 مدیریت محصولات", callback_data='manage_products'),
            InlineKeyboardButton("📊 آمار و گزارشات", callback_data='view_stats'),
            InlineKeyboardButton("📩 ارسال پیام به کاربر", callback_data='send_message'),
            InlineKeyboardButton("📢 ارسال همگانی", callback_data='broadcast')
        ]
    else:
        buttons = [
            InlineKeyboardButton("🛒 محصولات", callback_data='products'),
            InlineKeyboardButton("💬 پشتیبانی", callback_data='support'),
            InlineKeyboardButton("🤝 همکاری با ما", callback_data='cooperation'),
            InlineKeyboardButton("ℹ️ راهنما", callback_data='help')
        ]
    
    reply_markup = create_keyboard(buttons)
    welcome_text = "به ربات فروشگاه Dream خوش آمدید!\n \nمحصولات با کیفیت ✅\nضدبن و کاملا امن 🔐\nپشتیبانی 24/7 ⚡\n \nلطفا یک گزینه را انتخاب کنید:"
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
    
    return MENU

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = load_db()
    products = db['products']
    
    buttons = []
    for product_id, product in products.items():
        buttons.append(
            InlineKeyboardButton(
                f"{product['name']} - {product['price']}",
                callback_data=f'product_{product_id}'
            )
        )
    
    buttons.append(InlineKeyboardButton("🔙 بازگشت", callback_data='back'))
    
    reply_markup = InlineKeyboardMarkup([buttons[i:i+1] for i in range(0, len(buttons))])
    await update.callback_query.edit_message_text(
        "محصولات ما:\nلطفا یک محصول را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return PRODUCTS

async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = update.callback_query.data.split('_')[1]
    db = load_db()
    product = db['products'][product_id]
    
    text = f"""
📌 محصول: {product['name']}
💰 قیمت: {product['price']}
📝 توضیحات:
{product['description']}
"""
    
    buttons = [
        InlineKeyboardButton("🛒 سفارش محصول", callback_data=f'order_{product_id}'),
        InlineKeyboardButton("🔙 بازگشت", callback_data='products')
    ]
    
    reply_markup = InlineKeyboardMarkup([buttons])
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    return ORDER

async def order_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = update.callback_query.data.split('_')[1]
    db = load_db()
    product = db['products'][product_id]
    
    context.user_data['current_order'] = {
        'product_id': product_id,
        'product_name': product['name'],
        'price': product['price']
    }
    
    text = f"""
📌 سفارش: {product['name']}
💰 مبلغ قابل پرداخت: {product['price']}

💳 اطلاعات پرداخت:
شماره کارت: {db['bank_info']['card_number']}
به نام: {db['bank_info']['card_holder']}
بانک: {db['bank_info']['bank_name']}

✅ پس از پرداخت، لطفا رسید پرداخت را (عکس یا متن) ارسال کنید.
"""
    
    buttons = [
        InlineKeyboardButton("🔙 بازگشت", callback_data=f'product_{product_id}'),
        InlineKeyboardButton("🏠 صفحه اصلی", callback_data='back')
    ]
    
    reply_markup = InlineKeyboardMarkup([buttons])
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    return PAYMENT

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.username or "بدون یوزرنیم"
    first_name = update.effective_user.first_name or "بدون نام"
    last_name = update.effective_user.last_name or "بدون نام خانوادگی"
    db = load_db()
    order = context.user_data['current_order']
    order_id = str(len(db['orders']) + 1)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payment_proof = ""
    if update.message.photo:
        payment_proof = "عکس رسید پرداخت"
        photo_file_id = update.message.photo[-1].file_id
    elif update.message.text:
        payment_proof = update.message.text
    
    # ذخیره اطلاعات سفارش در دیتابیس
    db['orders'][order_id] = {
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'product_id': order['product_id'],
        'product_name': order['product_name'],
        'price': order['price'],
        'status': 'pending',
        'payment_proof': payment_proof,
        'date': now
    }
    save_db(db)
    
    # آماده کردن پیام برای ادمین
    admin_message = f"""
🛒 سفارش جدید دریافت شد!

📌 اطلاعات سفارش:
🔹 شماره سفارش: {order_id}
🔹 محصول: {order['product_name']}
🔹 قیمت: {order['price']}
🔹 تاریخ سفارش: {now}

👤 اطلاعات خریدار:
🔹 آیدی کاربر: {user_id}
🔹 یوزرنیم: @{username}
🔹 نام: {first_name} {last_name}
"""

    # ارسال پیام به ادمین
    try:
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_file_id,
                caption=admin_message
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"{admin_message}\n📝 رسید پرداخت:\n{payment_proof}"
            )
    except Exception as e:
        logger.error(f"Error sending order notification to admin: {e}")
    
    await update.message.reply_text(
        "✅ رسید پرداخت شما دریافت شد. سفارش شما در حال پردازش است.\n"
        "ادمین به زودی به شما اطلاع خواهد داد."
    )
    return await start(update, context)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text(
        "لطفا پیام خود را ارسال کنید. ادمین در اسرع وقت پاسخ خواهد داد."
    )
    return SUPPORT

async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.username or "بدون یوزرنیم"
    message = update.message.text
    
    db = load_db()
    db['user_messages'][str(user_id)] = {
        'username': username,
        'message': message
    }
    save_db(db)
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"پیام جدید از کاربر @{username}:\n{message}"
    )
    return await start(update, context)

async def show_cooperation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cooperation_text = """
🤝 *همکاری با Dream*

ما به دنبال شرکای تجاری و همکاران متعهدیم ! اگر علاقه‌مند به همکاری در زمینه‌های زیر هستید، با ما در ارتباط باشید:

🔹 *فروش محصولات*: کسب درآمد از طریق فروش محصولات ما
🔹 *همکاری در بازاریابی*: معرفی محصولات به دیگران و دریافت پورسانت

📌 *مزایای همکاری با ما*:
- درآمد ثابت و پورسانت بالا
- پشتیبانی کامل از همکاران
- تخفیف محصولات برای همکاران

📩 برای شروع همکاری، پیام خود را از طریق بخش پشتیبانی ارسال کنید یا با آیدی زیر ارتباط بگیرید:
@Dream_admins
"""

    buttons = [
        InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data='support'),
        InlineKeyboardButton("🏠 صفحه اصلی", callback_data='back')
    ]
    
    reply_markup = InlineKeyboardMarkup([buttons])
    
    try:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=cooperation_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in show_cooperation: {e}")
        await update.callback_query.edit_message_text(
            text=cooperation_text.replace('*', '').replace('_', ''),
            reply_markup=reply_markup
        )
    
    return COOPERATION

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    help_text = """
📚 راهنمای استفاده از ربات:

🛒 بخش فروش:
- برای مشاهده محصولات از منوی اصلی گزینه "محصولات" را انتخاب کنید
- پس از انتخاب محصول می‌توانید آن را سفارش دهید
- پس از پرداخت، رسید پرداخت را برای ما ارسال کنید

💬 بخش پشتیبانی:
- برای ارتباط با پشتیبانی از منوی اصلی گزینه "پشتیبانی" را انتخاب کنید
- پیام خود را ارسال کنید
- پشتیبان‌ها در اسرع وقت پاسخ خواهند داد

🤝 بخش همکاری:
- برای اطلاعات درباره همکاری با ما گزینه "همکاری" را انتخاب کنید

ℹ️ اطلاعات پشتیبانی:
- پشتیبانی تلگرام: @Dream_admins
- ساعات کاری: 9 صبح تا 12 شب
"""
    
    buttons = [
        InlineKeyboardButton("🛒 محصولات", callback_data='products'),
        InlineKeyboardButton("💬 پشتیبانی", callback_data='support'),
        InlineKeyboardButton("🤝 همکاری با ما", callback_data='cooperation'),
        InlineKeyboardButton("ℹ️ راهنما", callback_data='help')
    ]
    
    reply_markup = InlineKeyboardMarkup([buttons])
    await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)
    return MENU

async def manage_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.callback_query.answer("شما دسترسی ندارید!", show_alert=True)
        return MENU
    
    buttons = [
        InlineKeyboardButton("➕ افزودن محصول", callback_data='add_product'),
        InlineKeyboardButton("✏️ ویرایش محصول", callback_data='edit_product'),
        InlineKeyboardButton("🗑️ حذف محصول", callback_data='delete_product'),
        InlineKeyboardButton("🔙 بازگشت", callback_data='back')
    ]
    
    reply_markup = InlineKeyboardMarkup([buttons[i:i+2] for i in range(0, len(buttons), 2)])
    await update.callback_query.edit_message_text("مدیریت محصولات:", reply_markup=reply_markup)
    return MANAGE_PRODUCTS

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text(
        "لطفا اطلاعات محصول را به این فرمت ارسال کنید:\n\n"
        "نام محصول|توضیحات|قیمت\n\n"
        "مثال:\n"
        "محصول تست|این یک محصول تستی است|100,000 تومان"
    )
    return ADD_PRODUCT

async def handle_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        name, description, price = update.message.text.split('|', 2)
        db = load_db()
        product_id = str(max([int(k) for k in db['products'].keys()]) + 1) if db['products'] else '1'
        
        db['products'][product_id] = {
            'name': name.strip(),
            'description': description.strip(),
            'price': price.strip(),
            'image': None
        }
        save_db(db)
        
        await update.message.reply_text(f"محصول با موفقیت اضافه شد. 🎉\nکد محصول: {product_id}")
        return await start(update, context)
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}\nلطفا فرمت را رعایت کنید.")
        return ADD_PRODUCT

async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = load_db()
    if not db['products']:
        await update.callback_query.edit_message_text("هیچ محصولی برای ویرایش وجود ندارد.")
        return await start(update, context)
    
    buttons = []
    for product_id, product in db['products'].items():
        buttons.append(InlineKeyboardButton(
            f"{product['name']} - {product['price']}",
            callback_data=f'edit_{product_id}'
        ))
    
    buttons.append(InlineKeyboardButton("🔙 بازگشت", callback_data='back'))
    reply_markup = InlineKeyboardMarkup([buttons[i:i+1] for i in range(0, len(buttons))])
    await update.callback_query.edit_message_text(
        "لطفا محصول مورد نظر برای ویرایش را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return EDIT_PRODUCT

async def handle_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = update.callback_query.data.split('_')[1]
    context.user_data['editing_product'] = product_id
    await update.callback_query.edit_message_text(
        f"لطفا اطلاعات جدید محصول را به این فرمت ارسال کنید:\n\n"
        f"نام محصول|توضیحات|قیمت\n\n"
        f"مثال:\n"
        f"محصول ویرایش شده|توضیحات جدید|200,000 تومان"
    )
    return EDIT_PRODUCT

async def save_edited_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        name, description, price = update.message.text.split('|', 2)
        product_id = context.user_data['editing_product']
        db = load_db()
        
        db['products'][product_id] = {
            'name': name.strip(),
            'description': description.strip(),
            'price': price.strip(),
            'image': db['products'][product_id].get('image')
        }
        save_db(db)
        
        await update.message.reply_text("محصول با موفقیت ویرایش شد. ✅")
        return await start(update, context)
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}\nلطفا فرمت را رعایت کنید.")
        return EDIT_PRODUCT

async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = load_db()
    if not db['products']:
        await update.callback_query.edit_message_text("هیچ محصولی برای حذف وجود ندارد.")
        return await start(update, context)
    
    buttons = []
    for product_id, product in db['products'].items():
        buttons.append(InlineKeyboardButton(
            f"{product['name']} - {product['price']}",
            callback_data=f'delete_{product_id}'
        ))
    
    buttons.append(InlineKeyboardButton("🔙 بازگشت", callback_data='back'))
    reply_markup = InlineKeyboardMarkup([buttons[i:i+1] for i in range(0, len(buttons))])
    await update.callback_query.edit_message_text(
        "لطفا محصول مورد نظر برای حذف را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return DELETE_PRODUCT

async def handle_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = update.callback_query.data.split('_')[1]
    db = load_db()
    product_name = db['products'][product_id]['name']
    del db['products'][product_id]
    save_db(db)
    
    await update.callback_query.edit_message_text(f"محصول '{product_name}' با موفقیت حذف شد. ✅")
    return await start(update, context)

async def view_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.callback_query.answer("شما دسترسی ندارید!", show_alert=True)
        return MENU
    
    db = load_db()
    stats = db.get('stats', {})
    
    text = f"""
📊 آمار فروشگاه:
👥 تعداد کاربران: {stats.get('total_users', 0)}
🛒 تعداد سفارشات: {stats.get('total_orders', 0)}
💰 مجموع فروش: {stats.get('total_sales', 0)} تومان
"""
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back')]
        ])
    )
    return VIEW_STATS

async def send_message_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.callback_query.answer("شما دسترسی ندارید!", show_alert=True)
        return MENU
    
    await update.callback_query.edit_message_text(
        "لطفا آیدی عددی کاربر و پیام را به این فرمت ارسال کنید:\n"
        "user_id|پیام شما\n\n"
        "مثال:\n"
        "123456789|سلام، پیام شما دریافت شد."
    )
    return SEND_MESSAGE

async def handle_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی ندارید!")
        return MENU
    
    try:
        parts = update.message.text.split('|', 1)
        if len(parts) != 2:
            raise ValueError("فرمت پیام نادرست است")
        
        user_identifier = parts[0].strip()
        message = parts[1].strip()
        
        try:
            if user_identifier.startswith('@'):
                user = await context.bot.get_chat(user_identifier)
                user_id = user.id
                username = user_identifier
            else:
                user_id = int(user_identifier)
                username = f"کاربر {user_id}"
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📩 پیام از مدیریت:\n\n{message}"
                )
                await update.message.reply_text(f"پیام با موفقیت به {username} ارسال شد.")
            except Exception as e:
                await update.message.reply_text(f"خطا در ارسال پیام به {username}: {str(e)}")
        
        except Exception as e:
            await update.message.reply_text(f"خطا در یافتن کاربر: {str(e)}")
    
    except ValueError as e:
        await update.message.reply_text(f"خطا: {str(e)}\nلطفا فرمت را رعایت کنید.")
    except Exception as e:
        await update.message.reply_text(f"خطای ناشناخته: {str(e)}")
    
    return await start(update, context)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.callback_query.answer("شما دسترسی ندارید!", show_alert=True)
        return MENU
    
    await update.callback_query.edit_message_text("لطفا پیام همگانی را ارسال کنید (متن، عکس یا هر دو):")
    return BROADCAST

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی ندارید!")
        return MENU
    
    db = load_db()
    users = set()
    
    for order in db['orders'].values():
        users.add((order['user_id'], order.get('username', 'بدون یوزرنیم')))
    
    for user_id, data in db['user_messages'].items():
        if isinstance(data, dict):
            users.add((int(user_id), data.get('username', 'بدون یوزرنیم')))
        else:
            users.add((int(user_id), 'بدون یوزرنیم'))
    
    success = 0
    failed = 0
    
    for user_id, username in users:
        try:
            if update.message.text:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"\n\n{update.message.text}"
                )
            elif update.message.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=update.message.photo[-1].file_id,
                    caption=f"\n\n{update.message.caption or ''}"
                )
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send message to @{username} ({user_id}): {e}")
    
    await update.message.reply_text(
        f"✅ ارسال همگانی انجام شد:\n"
        f"تعداد موفق: {success}\n"
        f"تعداد ناموفق: {failed}"
    )
    return await start(update, context)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("عملیات لغو شد.")
    return await start(update, context)

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [
                CallbackQueryHandler(show_cooperation, pattern='^cooperation$'),
                CallbackQueryHandler(manage_products, pattern='^manage_products$'),
                CallbackQueryHandler(view_stats, pattern='^view_stats$'),
                CallbackQueryHandler(send_message_to_user, pattern='^send_message$'),
                CallbackQueryHandler(broadcast, pattern='^broadcast$'),
                CallbackQueryHandler(show_products, pattern='^products$'),
                CallbackQueryHandler(support, pattern='^support$'),
                CallbackQueryHandler(show_cooperation, pattern='^cooperation$'),
                CallbackQueryHandler(show_help, pattern='^help$'),
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ],
            PRODUCTS: [
                CallbackQueryHandler(product_detail, pattern='^product_'),
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ],
            ORDER: [
                CallbackQueryHandler(order_product, pattern='^order_'),
                CallbackQueryHandler(show_products, pattern='^products$')
            ],
            PAYMENT: [
                MessageHandler(filters.TEXT | filters.PHOTO, handle_payment),
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ],
            SUPPORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message),
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ],
            COOPERATION: [
                CallbackQueryHandler(support, pattern='^support$'),
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ],
            MANAGE_PRODUCTS: [
                CallbackQueryHandler(add_product, pattern='^add_product$'),
                CallbackQueryHandler(edit_product, pattern='^edit_product$'),
                CallbackQueryHandler(delete_product, pattern='^delete_product$'),
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ],
            ADD_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_product)
            ],
            EDIT_PRODUCT: [
                CallbackQueryHandler(handle_edit_product, pattern='^edit_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_product)
            ],
            DELETE_PRODUCT: [
                CallbackQueryHandler(handle_delete_product, pattern='^delete_'),
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ],
            SEND_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_send_message)
            ],
            BROADCAST: [
                MessageHandler(filters.TEXT | filters.PHOTO, handle_broadcast)
            ],
            VIEW_STATS: [
                CallbackQueryHandler(back_to_menu, pattern='^back$')
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        save_db(DEFAULT_DATA)
    main()