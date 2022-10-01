import datetime

import cv2
import pytesseract
from aiogram.types import ContentType
from pytesseract import Output
from PIL import ImageDraw
from textblob import TextBlob
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from aiogram import Bot, Dispatcher, executor, types
import logging
from io import BytesIO
import os


API_TOKEN = 'Your Telegram API key goes here'  # Translator_projbot

logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands='start')
async def start_cmd_handler(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    text_and_data = (
        ('نص', 'text'),
        ('صورة', 'image'),
    )
    # in real life for the callback_data the callback data factory should be used
    # here the raw string is used for the simplicity
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)

    keyboard_markup.row(*row_btns)

    await message.reply("مرحبا\nماذا تود ترجمته؟", reply_markup=keyboard_markup)


# Use multiple registrators. Handler will execute when one of the filters is OK
@dp.callback_query_handler(text='image')  # if cb.data == 'no'
@dp.callback_query_handler(text='text')  # if cb.data == 'yes'
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    answer_data = query.data
    # always answer callback queries, even if you have nothing to say
    await query.answer(f'You answered with {answer_data!r}')

    if answer_data == 'text':
        text = 'قم بكتابة او تحويل النص من محادثة اخرى لترجمته'
    elif answer_data == 'image':
        text = 'قم بالتقاط او ارسال صورة تحتوي كلمات لترجمتها'
    else:
        text = f'Unexpected callback data {answer_data!r}!'

    await bot.send_message(query.from_user.id, text)


# if the text starts with any string from the list
@dp.message_handler(content_types=ContentType.TEXT)
async def text_startswith_handler(message: types.Message):
    logging.info('text task')
    reply = TextBlob(message.text)
    translated = reply.translate(to='ar')
    today = datetime.datetime.now()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")
    # output = "/opt/output/" + year + "/" + month + "/" + day
    data_path = "user_data/" + str(message.from_user.username) + "/" + year + "/" + month + "/" + day
    # Check whether the specified path exists or not
    isExist = os.path.exists(data_path)

    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(data_path)
        print("The new directory is created!")
    open(data_path + "/ " + 'messages.txt', 'a').write(
        message.chat.id + ' | ' + message.text + '||' + "\n translation: " + translated + "\n")
    await message.answer(translated)


# @dp.message_handler(commands=['image'])
# def start(message):
#     message.answer("قم بالتقاط أو ارسال صورة تحتوي كلمات لترجمتها")


def get_image(update, context):
    photo = update.message.photo[-1].get_file()
    # photo.download('img.jpg')
    # img = cv2.imread('img.jpg')
    img = cv2.imdecode(np.fromstring(BytesIO(photo.download_as_bytearray()).getvalue(), np.uint8), 1)


def image_ocr(test, message):
    logging.info('ocr func')
    img = test
    # img = cv2.imread(file)
    # d1 = ImageDraw.Draw(img)
    # roi = img[50:500, 200:600]
    # print(tes.image_to_string(roi))
    custom_config = r'--psm 11'
    d = pytesseract.image_to_data(img, config=custom_config, output_type=Output.DICT)
    # print(d.keys())
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(d['conf'][i]) > 60:
            # print(d['text'][i])
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            blob = TextBlob(d['text'][i])
            string = ''
            try:
                string = blob.translate(to='ar')
                # reshaped_text = arabic_reshaper.reshape(string)    # correct its shape
                # bidi_text = get_display(string)
                # string = bidi_text
                # print(string)
            except Exception as e:
                print(str(e))
                string = d['text'][i]
                print(string)

            # if(string is str and string is not None):
            # translated = string
            # else:
            # translated = d['text'][i]
            # reshaped_text = arabic_reshaper.reshape(str(string))    # correct its shape
            # bidi_text = get_display(reshaped_text)
            # translated = bidi_text
            translated = str(string)
            print(translated)
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), -1)
            # cv2.putText(img, 'Text', (int(x+(w/2)-(int(len(d['text'][i])/1.25))),int(y+(h/1.5))), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (36,255,12), 1)
            # cv2.putText(img, u""+translated, (x,y+h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
            # d1.text((x,y),"This is a Text",fill(255,0,0))
            text = translated
            fontpath = "./arial.ttf"  # <== 这里是宋体路径
            # textsize = cv2.getTextSize(text, fontpath, 1, 2)[0]
            font2 = cv2.FONT_HERSHEY_SIMPLEX
            textsize = cv2.getTextSize(text, font2, 1, 2)[0]
            textX = (img.shape[1] - textsize[0]) / 2
            textY = (img.shape[0] + textsize[1]) / 2
            font = ImageFont.truetype(fontpath, 16)
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            draw.text((x + w // 2, y + h // 2), translated, font=font, fill=(0, 0, 0, 0))
            img = np.array(img_pil)
    # bio = BytesIO()
    # # bio.name = 'image.jpeg'
    # bio.name = str(message.message_id) +"_ans"+".jpg"
    # img.save(bio, 'JPEG')
    filename = str(message.message_id) + "_ans" + ".jpg"
    cv2.imwrite(filename, img)
    return filename
    # bio.seek(0)
    # bot.send_photo(message.chat.id, photo=open(str(message.message_id) +"_ans"+".jpg", 'rb'))
    # bot.send_photo(chat_id, photo=bio)
    # while (1):
    #     cv2.imshow('img', img)
    #     k = cv2.waitKey(33)
    #     if k == 27:  # Esc key to stop
    #         break
    #     elif k == -1:  # normally -1 returned,so don't print it
    #         continue
    #     else:
    #         print(k)  # else print its value


@dp.message_handler(content_types=ContentType.PHOTO)
async def echo(message: types.Message):
    logging.info('ocr task')
    # file_id = message.document.file_id
    # file_info = await bot.get_file(photo[len(photo) - 1].file_id)
    # new_photo = (await bot.download_file(file_info.file_path)).read()
    photo = message.photo.pop()
    today = datetime.datetime.now()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")
    # output = "/opt/output/" + year + "/" + month + "/" + day
    data_path = "user_data/" + str(message.from_user.username) + "/" + year + "/" + month + "/" + day
    # Check whether the specified path exists or not
    isExist = os.path.exists(data_path)

    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(data_path)
        print("The new directory is created!")
    await photo.download(data_path + "/ " + str(message.message_id) + ".jpg")
    # logging.info(file.file_path)
    # await message.photo[-1].download(message.message_id)
    # file = await bot.get_file(file_id)
    # file_path = file.file_path
    # myobj = BytesIO(file.download_as_bytearray())
    # # get_image()
    # # file_id = message.document.file_id
    # # file = await bot.get_file(file_id)
    # downloaded = await bot.download_file_by_id(message.photo[-1].file_id)
    # photo = downloaded
    # img = cv2.imdecode(np.fromstring(myobj.getvalue(), np.uint8), 1)
    img = cv2.imread(str(message.message_id) + ".jpg")
    filename = image_ocr(img, message)

    # await message.copy_to(message.chat.id)
    await bot.send_photo(message.chat.id, photo=open(str(message.message_id) + "_ans" + ".jpg", 'rb'))
    os.remove(str(filename))
    os.remove(str(message.message_id) + ".jpg")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


def get_optimal_font_scale(text, width):
    for scale in reversed(range(0, 60, 1)):
        textSize = cv2.getTextSize(text, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=scale / 10, thickness=1)
        new_width = textSize[0][0]
        print(new_width)
        if (new_width <= width):
            return int(scale / 10)
    return 1

# font = ImageFont.truetype("arial.ttf", 18)
# cv2.imshow('img', img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
