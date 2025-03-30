from math import trunc
from typing import List
from PIL import Image, ImageFont, ImageDraw
import textwrap

# На замену font.getsize
def get_size_font(font, word):
    # Получение bounding box для текста
    bbox = font.getbbox(word)

    # Распаковка bbox: (left, top, right, bottom)
    left, top, right, bottom = bbox

    # Вычисление ширины и высоты текста
    font_width = right - left
    font_height = bottom - top
    return font_width, font_height

White = (255, 255, 255)
Black = (0, 0, 0)
Red = (255, 0, 0)
Green = (0, 255, 0)
Blue = (0, 0, 255)
font_path = '.\JetBrainsMono-Medium-Italic.ttf'
fontsize = 40
font = ImageFont.truetype(font_path, fontsize)
label_image = Image.open(".\logo.jpg")
#label_image = label_image.resize((98, 40))

font_width, font_height =  get_size_font(font, "a")
min_width, min_height = 1200, 944
max_width, max_height = 2480, 1968

def change_font(filename):
    global font
    font = ImageFont.truetype(filename, fontsize)


def change_fontsize(size):
    global fontsize
    fontsize = size


def draw_multiple_line_text(image, lines, font, text_color, text_start_height):
    draw = ImageDraw.Draw(image)
    image_width, _ = image.size
    y_text = text_start_height
    for line in lines:
        line_width, line_height = get_size_font(font, line)
        draw.text(((image_width - line_width) / 2, y_text),
                  line, font=font, fill=text_color)
        y_text += line_height


def create_border_img(img, width, height, dwidth, dheight):
    # Уменьшаем или увеличиваем изображение до нужных размеров
    img = img.resize((width, height))
    # Изменяем высоту и ширину так чтобы создать картину с границами
    height += dheight
    width += dwidth
    # Создание картины с нужной шириной и высотой
    image = Image.new("RGB", (width, height), Red)
    # Устанавливаем картину в этот квадрат
    image.paste(img, (dwidth // 2, dheight // 2))
    return image


def create_logo_img(img, x, y, dwidth, dheight):
    dr = ImageDraw.Draw(img)
    dr.rectangle([x - dwidth // 2, y - dwidth // 2, x +
                 label_image.size[0] + dwidth // 2, y + label_image.size[1] + dheight // 2], Green)
    img.paste(label_image, (x, y))


def get_image_with_border(width, height, img, with_label=True):
    dwidth, dheight = 40, 40
    image = create_border_img(img, width, height, dwidth, dheight)
    # Нужно ли вставить логотип?
    if with_label:
        create_logo_img(image, width - label_image.size[0],
                        height - label_image.size[1], dwidth, dheight)
    return image


def get_meme(text_lines_for_print, img):
    # Расчет допустимого размера ширины картинки
    current_width: int = min(max(img.size[0], min_width), max_width)
    # Расчет допустимого размера высоты картинки
    current_height: int = min(max(img.size[1], min_height), max_height)
    img = img.resize((current_width, current_height))
    # Переменная которая будет хранить List[str] строки которые будут в печать
    lines: List[str] = []
    # Делим строки которые начинаются с новой строки и каждую эту строку делим на определенное количество символов
    lines_texts: List[List[str]] = [textwrap.wrap(
        text_for_print, current_width // font_width) for text_for_print in text_lines_for_print.split("\n")]
    # Собираем теперь отдельные части в него
    for line_text in lines_texts:
        # Вносим эту строку
        lines.extend(line_text)
        # Делаем отступ
        lines.append("")
    # Лишний отступ удаляем
    lines.pop()
    # Расчет высоты текста
    text_height: int = sum([get_size_font(font, lines[i])[1]
                           for i in range(len(lines))])
    # Создание временной картины для хранения текущей картины с рамкой и логотипом
    image_with_border = get_image_with_border(
        current_width, current_height, img)
    # Создание временной картины для хранения текста
    image_with_text = Image.new(
        "RGB", (current_width + 40, text_height + 40), Red)
    dr = ImageDraw.Draw(image_with_text)
    dr.rectangle([0, 0, image_with_text.size[0] - 40, image_with_text.size[1] - 20], Blue)
    # Печать текста
    draw_multiple_line_text(image_with_text, lines, font, White, 0)
    # Создание главной картины
    image_main = Image.new(
        "RGB", (image_with_text.size[0], image_with_text.size[1] + image_with_border.size[1]), Red)
    # Вставляем картину с логотипом и рамкой
    image_main.paste(image_with_border, (0, 0))
    # Вставляем картину с текстом
    image_main.paste(image_with_text, (20, image_with_border.size[1]))
    # возврат готовой картинки
    return image_main
    #return get_image_with_border(image_main.size[0], image_main.size[1], image_main, False)


if __name__ == "__main__":
    get_meme("Hello world", Image.open("JvFZuvTsYPo.jpg")).save("tmp.png")
