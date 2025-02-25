import telebot
import os
import qrcode
from datetime import datetime
from fpdf import FPDF
from telebot import types

TOKEN = '6928284331:AAF7BI7UJqkfN7BZ2lIsIbwRpuh1gsE_cbI'
bot = telebot.TeleBot(TOKEN)

user_data = {}

class InvoicePDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', font_family='Arial', font_size=12):
        super().__init__(orientation, unit, format)
        self.font_family = font_family
        self.font_size = font_size
        self.set_auto_page_break(auto=True, margin=15)
        
    def create_invoice(self, invoice_data):
        self.add_page()
        self.set_margins(10, 10, 10)
        self.set_font(self.font_family, 'B', 16)
        rtl = invoice_data.get('language') == 'Arabic'
        
        if invoice_data.get('logo_path'):
            self.image(invoice_data['logo_path'], x=10, y=10, w=30)
            self.ln(5)
        else:
            self.set_font(self.font_family, 'B', 14)
            self.cell(0, 10, "Invoice Generator Bot", ln=True)
        
        self.set_font(self.font_family, 'B', 18)
        self.cell(0, 15, "INVOICE" if not rtl else "فاتورة", ln=True, align='C')
        self.set_font(self.font_family, '', self.font_size)
        
        seller_label = "Seller:" if not rtl else "البائع:"
        address_label = "Address:" if not rtl else "العنوان:"
        date_label = "Date:" if not rtl else "التاريخ:"
        invoice_label = "Invoice #:" if not rtl else "رقم الفاتورة:"
        
        self.cell(0, 10, f"{seller_label} {invoice_data.get('seller_name', 'N/A')}", ln=True)
        self.cell(0, 10, f"{address_label} {invoice_data.get('seller_address', 'N/A')}", ln=True)
        self.cell(0, 10, f"{date_label} {invoice_data.get('date', 'N/A')}", ln=True)
        self.cell(0, 10, f"{invoice_label} {invoice_data.get('invoice_number', 'N/A')}", ln=True)
        self.ln(10)
        
        bill_to = "Bill To:" if not rtl else "فاتورة إلى:"
        client_label = "Client:" if not rtl else "العميل:"
        
        self.set_font(self.font_family, 'B', self.font_size)
        self.cell(0, 10, bill_to, ln=True)
        self.set_font(self.font_family, '', self.font_size)
        self.cell(0, 10, f"{client_label} {invoice_data.get('buyer_name', 'N/A')}", ln=True)
        self.cell(0, 10, f"{address_label} {invoice_data.get('buyer_address', 'N/A')}", ln=True)
        self.ln(15)
        
        desc_label = "Description" if not rtl else "الوصف"
        qty_label = "Quantity" if not rtl else "الكمية"
        price_label = "Unit Price" if not rtl else "سعر الوحدة"
        amount_label = "Amount" if not rtl else "المبلغ"
        total_label = "Total:" if not rtl else "المجموع:"
        
        self.set_font(self.font_family, 'B', self.font_size)
        col_w = [80, 30, 40, 40]
        self.cell(col_w[0], 10, desc_label, 1, 0, 'C')
        self.cell(col_w[1], 10, qty_label, 1, 0, 'C')
        self.cell(col_w[2], 10, price_label, 1, 0, 'C')
        self.cell(col_w[3], 10, amount_label, 1, 1, 'C')
        self.set_font(self.font_family, '', self.font_size)
        
        total = 0
        for item in invoice_data.get('items', []):
            amount = item.get('quantity', 0) * item.get('price', 0)
            total += amount
            self.cell(col_w[0], 10, item.get('name', ''), 1, 0)
            self.cell(col_w[1], 10, str(item.get('quantity', '')), 1, 0, 'C')
            self.cell(col_w[2], 10, str(item.get('price', '')), 1, 0, 'C')
            self.cell(col_w[3], 10, str(amount), 1, 1, 'C')
        
        self.set_font(self.font_family, 'B', self.font_size)
        self.cell(col_w[0] + col_w[1] + col_w[2], 10, total_label, 1, 0, 'R')
        self.cell(col_w[3], 10, str(total), 1, 1, 'C')
        
        if invoice_data.get('qr_path'):
            self.ln(10)
            self.image(invoice_data['qr_path'], x=10, y=self.get_y(), w=30)
        
        if invoice_data.get('signature_path'):
            self.image(invoice_data['signature_path'], x=150, y=self.get_y() - 30, w=30)
        
        self.ln(40)
        self.set_font(self.font_family, '', 10)
        thank_you = "Thank you for your business!" if not rtl else "شكراً لتعاملكم معنا!"
        self.cell(0, 10, thank_you, 0, 1, 'C')
        
        pdf_path = f"invoice_{invoice_data.get('invoice_number', 'temp')}.pdf"
        self.output(pdf_path)
        return pdf_path


def generate_qr_code(data, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'step': 'language'}
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('English')
    btn2 = types.KeyboardButton('Arabic')
    markup.add(btn1, btn2)
    bot.reply_to(message, "Welcome to the Invoice Generator Bot!\nPlease select your preferred language:\n\nمرحباً بك في روبوت إنشاء الفواتير!\nيرجى اختيار اللغة المفضلة لديك:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['English', 'Arabic'] and message.chat.id in user_data and user_data[message.chat.id].get('step') == 'language')
def select_font(message):
    chat_id = message.chat.id
    language = message.text
    user_data[chat_id]['language'] = language
    user_data[chat_id]['step'] = 'font'
    if language == 'English':
        fonts = ["Arial", "Helvetica", "Times", "Courier"]
        bot.send_message(chat_id, "Please select a font:", reply_markup=create_font_keyboard(fonts))
    else:
        fonts = ["Arial", "Times", "Courier"]
        bot.send_message(chat_id, "يرجى اختيار الخط:", reply_markup=create_font_keyboard(fonts))


def create_font_keyboard(fonts):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(font) for font in fonts]
    markup.add(*buttons)
    return markup


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get('step') == 'font')
def select_font_size(message):
    chat_id = message.chat.id
    font = message.text
    user_data[chat_id]['font'] = font
    user_data[chat_id]['step'] = 'font_size'
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    sizes = ["10", "12", "14"]
    buttons = [types.KeyboardButton(size) for size in sizes]
    markup.add(*buttons)
    if user_data[chat_id]['language'] == 'English':
        bot.send_message(chat_id, "Please select font size:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "يرجى اختيار حجم الخط:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get('step') == 'font_size')
def show_main_menu(message):
    chat_id = message.chat.id
    try:
        font_size = int(message.text)
        user_data[chat_id]['font_size'] = font_size
    except:
        user_data[chat_id]['font_size'] = 12
    
    user_data[chat_id]['step'] = None
    
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if user_data[chat_id]['language'] == 'English':
        btn = types.KeyboardButton('Create Invoice')
        markup.add(btn)
        bot.send_message(chat_id, "Thank you for your preferences. Press 'Create Invoice' to start.", reply_markup=markup)
    else:
        btn = types.KeyboardButton('إنشاء فاتورة')
        markup.add(btn)
        bot.send_message(chat_id, "شكراً لاختيارك. اضغط على 'إنشاء فاتورة' للبدء.", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Create Invoice', 'إنشاء فاتورة'])
def invoice_type_selection(message):
    chat_id = message.chat.id
    
    if chat_id not in user_data:
        send_welcome(message)
        return
    
    if 'language' not in user_data[chat_id]:
        send_welcome(message)
        return
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if user_data[chat_id]['language'] == 'English':
        btn1 = types.KeyboardButton('Custom Invoice')
        btn2 = types.KeyboardButton('Advanced Invoice')
        markup.add(btn1, btn2)
        bot.send_message(chat_id, "Please select the type of invoice you want to create:", reply_markup=markup)
    else:
        btn1 = types.KeyboardButton('فاتورة عادية')
        btn2 = types.KeyboardButton('فاتورة متقدمة')
        markup.add(btn1, btn2)
        bot.send_message(chat_id, "يرجى اختيار نوع الفاتورة التي تريد إنشاءها:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Custom Invoice', 'Advanced Invoice', 'فاتورة عادية', 'فاتورة متقدمة'])
def invoice_details_request(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'language' not in user_data[chat_id]:
        send_welcome(message)
        return
    
    invoice_type = message.text
    language = user_data[chat_id]['language']
    user_data[chat_id].update({
        'type': invoice_type,
        'step': 'seller_name',
        'items': [],
        'invoice_number': str(int(datetime.now().timestamp()))
    })
    
    if language == 'English':
        bot.send_message(chat_id, "Please enter the seller's name:")
    else:
        bot.send_message(chat_id, "يرجى إدخال اسم البائع:")


@bot.message_handler(content_types=['text', 'photo'])
def handle_invoice_steps(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        send_welcome(message)
        return
    
    current_step = user_data[chat_id].get('step')
    
    if current_step is None:
        if message.text in ['Create Invoice', 'إنشاء فاتورة']:
            invoice_type_selection(message)
        return
    
    language = user_data[chat_id].get('language', 'English')
    is_english = language == 'English'
    
    def get_text(en_text, ar_text):
        return en_text if is_english else ar_text
    
    if current_step == 'seller_name':
        user_data[chat_id]['seller_name'] = message.text
        user_data[chat_id]['step'] = 'seller_address'
        bot.send_message(chat_id, get_text("Please enter the seller's address:", "يرجى إدخال عنوان البائع:"))
    
    elif current_step == 'seller_address':
        user_data[chat_id]['seller_address'] = message.text
        user_data[chat_id]['step'] = 'buyer_name'
        bot.send_message(chat_id, get_text("Please enter the buyer's name:", "يرجى إدخال اسم المشتري:"))
    
    elif current_step == 'buyer_name':
        user_data[chat_id]['buyer_name'] = message.text
        user_data[chat_id]['step'] = 'buyer_address'
        bot.send_message(chat_id, get_text("Please enter the buyer's address:", "يرجى إدخال عنوان المشتري:"))
    
    elif current_step == 'buyer_address':
        user_data[chat_id]['buyer_address'] = message.text
        user_data[chat_id]['step'] = 'date'
        bot.send_message(chat_id, get_text("Please enter the invoice date:", "يرجى إدخال تاريخ الفاتورة:"))
    
    elif current_step == 'date':
        user_data[chat_id]['date'] = message.text
        user_data[chat_id]['step'] = 'logo'
        bot.send_message(chat_id, get_text("Please send your logo image (or type 'skip' to use text):", "يرجى إرسال صورة الشعار (أو اكتب 'تخطي' لاستخدام النص):"))
    
    elif current_step == 'logo':
        skip_text = 'skip' if is_english else 'تخطي'
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            logo_path = f"logo_{chat_id}.jpg"
            with open(logo_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            user_data[chat_id]['logo_path'] = logo_path
            user_data[chat_id]['step'] = 'signature'
            bot.send_message(chat_id, get_text("Please send your signature image (or type 'skip' to proceed without):", "يرجى إرسال صورة التوقيع (أو اكتب 'تخطي' للمتابعة بدونها):"))
        elif message.text.lower() == skip_text.lower():
            user_data[chat_id]['logo_path'] = None
            user_data[chat_id]['step'] = 'signature'
            bot.send_message(chat_id, get_text("Please send your signature image (or type 'skip' to proceed without):", "يرجى إرسال صورة التوقيع (أو اكتب 'تخطي' للمتابعة بدونها):"))
        else:
            bot.send_message(chat_id, get_text("Please send an image or type 'skip'.", "يرجى إرسال صورة أو كتابة 'تخطي'."))
    
    elif current_step == 'signature':
        skip_text = 'skip' if is_english else 'تخطي'
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            signature_path = f"signature_{chat_id}.jpg"
            with open(signature_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            user_data[chat_id]['signature_path'] = signature_path
            user_data[chat_id]['step'] = 'qr_data'
            bot.send_message(chat_id, get_text("Please enter data for QR code (or type 'skip'):", "يرجى إدخال البيانات لرمز QR (أو اكتب 'تخطي'):"))
        elif message.text.lower() == skip_text.lower():
            user_data[chat_id]['signature_path'] = None
            user_data[chat_id]['step'] = 'qr_data'
            bot.send_message(chat_id, get_text("Please enter data for QR code (or type 'skip'):", "يرجى إدخال البيانات لرمز QR (أو اكتب 'تخطي'):"))
        else:
            bot.send_message(chat_id, get_text("Please send an image or type 'skip'.", "يرجى إرسال صورة أو كتابة 'تخطي'."))
    
    elif current_step == 'qr_data':
        skip_text = 'skip' if is_english else 'تخطي'
        if message.text.lower() == skip_text.lower():
            user_data[chat_id]['qr_path'] = None
        else:
            qr_path = f"qrcode_{chat_id}.png"
            generate_qr_code(message.text, qr_path)
            user_data[chat_id]['qr_path'] = qr_path
        user_data[chat_id]['step'] = 'add_items'
        user_data[chat_id]['current_item'] = {}
        bot.send_message(chat_id, get_text("Let's add items to the invoice. Please enter item name:", "لنضف عناصر إلى الفاتورة. يرجى إدخال اسم العنصر:"))
    
    elif current_step == 'add_items':
        done_text = 'done' if is_english else 'تم'
        add_another_text = 'Add Another Item' if is_english else 'إضافة عنصر آخر'
        
        if message.text.lower() == done_text.lower():
            try:
                pdf = InvoicePDF(
                    font_family=user_data[chat_id].get('font', 'Arial'),
                    font_size=user_data[chat_id].get('font_size', 12)
                )
                pdf_path = pdf.create_invoice(user_data[chat_id])
                with open(pdf_path, 'rb') as f:
                    bot.send_document(
                        chat_id, 
                        f, 
                        caption=get_text("Here is your invoice!", "إليك فاتورتك!")
                    )
                
                for file_key in ['logo_path', 'signature_path', 'qr_path']:
                    if user_data[chat_id].get(file_key):
                        try:
                            os.remove(user_data[chat_id][file_key])
                        except:
                            pass
                try:
                    os.remove(pdf_path)
                except:
                    pass
                
                language = user_data[chat_id].get('language')
                font = user_data[chat_id].get('font')
                font_size = user_data[chat_id].get('font_size')
                user_data[chat_id] = {
                    'language': language,
                    'font': font,
                    'font_size': font_size,
                    'step': None
                }
                
                markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                btn = types.KeyboardButton(get_text('Create Invoice', 'إنشاء فاتورة'))
                markup.add(btn)
                bot.send_message(
                    chat_id, 
                    get_text("Invoice created successfully! Press 'Create Invoice' to create another one.", 
                            "تم إنشاء الفاتورة بنجاح! اضغط على 'إنشاء فاتورة' لإنشاء فاتورة أخرى."),
                    reply_markup=markup
                )
            except Exception as e:
                error_msg = str(e)
                bot.send_message(
                    chat_id, 
                    get_text(f"Error creating invoice: {error_msg}. Please try again.", 
                            f"خطأ في إنشاء الفاتورة: {error_msg}. يرجى المحاولة مرة أخرى.")
                )
        elif message.text == add_another_text:
            user_data[chat_id]['current_item'] = {}
            
            if 'item_step' in user_data[chat_id]:  # التحقق قبل الحذف
                del user_data[chat_id]['item_step']
            
            bot.send_message(chat_id, get_text("Please enter item name:", "يرجى إدخال اسم العنصر:"))
        elif 'item_step' not in user_data[chat_id]:
            user_data[chat_id]['current_item'] = {'name': message.text}
            user_data[chat_id]['item_step'] = 'quantity'
            bot.send_message(chat_id, get_text("Enter quantity:", "أدخل الكمية:"))
        elif user_data[chat_id]['item_step'] == 'quantity':
            try:
                user_data[chat_id]['current_item']['quantity'] = int(message.text)
                user_data[chat_id]['item_step'] = 'price'
                bot.send_message(chat_id, get_text("Enter unit price:", "أدخل سعر الوحدة:"))
            except ValueError:
                bot.send_message(chat_id, get_text("Please enter a valid number for quantity.", "يرجى إدخال رقم صحيح للكمية."))
        elif user_data[chat_id]['item_step'] == 'price':
            try:
                user_data[chat_id]['current_item']['price'] = float(message.text)
                user_data[chat_id]['items'].append(user_data[chat_id]['current_item'])
                markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
                markup.add(types.KeyboardButton(add_another_text), types.KeyboardButton(done_text))
                bot.send_message(
                    chat_id, 
                    get_text("Item added! Add another or finish?", "تمت إضافة العنصر! إضافة آخر أو الانتهاء؟"), 
                    reply_markup=markup
                )
                del user_data[chat_id]['item_step']
            except ValueError:
                bot.send_message(chat_id, get_text("Please enter a valid number for price.", "يرجى إدخال رقم صحيح للسعر."))


if __name__ == '__main__':
    print("Invoice Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)