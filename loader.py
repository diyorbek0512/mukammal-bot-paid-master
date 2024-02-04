from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.utils.executor import start_polling
from data import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

confirmation_keyboard = InlineKeyboardMarkup(row_width=1)
confirmation_keyboard.add(InlineKeyboardButton("Ishonch telefonlari ☎️", callback_data="phones"))


class Form(StatesGroup):
    name = State()
    phone_number = State()
    suggestions = State()
    media = State()
    ready_for_next = State()

@dp.message_handler(state=Form.suggestions)
async def process_suggestions(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['suggestions'] = message.text
    await Form.media.set()
    await message.reply("Ma'lumotingizga qo'shimcha rasm yoki video fayl yuboring : ")
@dp.message_handler(content_types=['photo', 'video'], state=Form.media)
async def process_media(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        choice = "Murojaat:" if data['choice'] == "contact" else "Fikr:"
        caption = f"<b>{choice}</b>\nISM: {data['name']}\nTEL: {data['phone_number']}\nTAKLIFLAR: {data['suggestions']}"

        for admin_id in config.ADMINS:
            if message.photo:
                await bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption)
            elif message.video:
                await bot.send_video(admin_id, message.video.file_id, caption=caption)

    await bot.send_message(
        message.chat.id,
        "✅ Murojaatingiz yuborildi!\nSizga tez orada javob qaytariladi",
        reply_markup=confirmation_keyboard  # Add the keyboard here
    )
    await Form.ready_for_next.set()
@dp.message_handler(content_types=types.ContentTypes.ANY, state=Form.media)
async def process_invalid_media(message: types.Message, state: FSMContext):
    await message.reply("Iltimos, rasm yoki video fayl yuboring. Boshqa turdagi fayllar qabul qilinmaydi.")




@dp.callback_query_handler(lambda c: c.data == 'phones', state='*')
async def process_phones_button(callback_query: types.CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "Telefon raqam: <u>+998 (67) 236-84-86</u>",
        parse_mode=types.ParseMode.HTML
    )
    await callback_query.answer()  # Important to give feedback that the button press was received





@dp.message_handler(state=Form.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = message.text
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("Murojaat ✔", callback_data="contact"),
                 InlineKeyboardButton("Fikr bildirish ❗", callback_data="opinion"))
    await message.reply("Quyidagi amallardan birini tanlang !", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data in ['contact', 'opinion'], state=Form.phone_number)
async def process_callback_button(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['choice'] = callback_query.data  # Storing the choice in the state
        await Form.suggestions.set()
        if callback_query.data == "contact":
            await bot.send_message(callback_query.from_user.id, "Murojaatingizni yozib qoldiring: ")
        else:
            await bot.send_message(callback_query.from_user.id, "Fikringizni yozib qoldiring:")
    await callback_query.answer()  # Important to give feedback that the button press was received




@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()  # Reset the state
    await Form.name.set()  # Set the state to the first step
    await message.reply("Assalomu alaykum! Botga hush kelibsiz! \nSiz ushbu bot orqali jamoat transporti xizmalaridan qoniqmagan taqdiringizda shikoyat va takliflaringizni qoldirishingiz mumkin\n\nIltimos, ism familiyangizni yozib, jo'nating:")



@dp.message_handler(commands=['next'], state='*')
async def command_next(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            if 'name' in data and 'phone_number' in data:
                # If name and phone number are already stored, go to suggestions
                await Form.suggestions.set()
                await message.reply("Sizda qandaydir taklif yoki shikoyatlar bormi?")
            else:
                # If name and phone number are not stored, start from the beginning
                await Form.name.set()
                await message.reply("Assalomu alaykum, iltimos, ism familiyangizni kiriting")
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await Form.name.set()
    await message.reply(f"Assalomu alaykum, iltimos, ism familiyangizni kiriting")
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()
    await message.reply(f"Rahmat, {message.text}.\nMurojaat uchun telefon raqamingizni yuboring: ")


@dp.message_handler(state=Form.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = message.text
    await Form.next()
    await message.reply("Sizda qandaydir taklif yoki shikoyatlar bormi?")




@dp.message_handler(commands=['next'], state='*')
async def command_next(message: types.Message, state: FSMContext):
    await state.finish()  # Reset the state
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("Murojaat ✔", callback_data="contact"),
                 InlineKeyboardButton("Fikr 👌", callback_data="opinion"))
    await message.reply("Choose whether you have an opinion or you want to contact", reply_markup=keyboard)
    await Form.phone_number.set()  # Set the state to expect the phone number next



if __name__ == '__main__':
    start_polling(dp, skip_updates=True)