from pathlib import Path

from core._config import _const
from core._config._exception import ModuleNotFoundException

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError as e:
    raise ModuleNotFoundException(
        _const.EXCEPTION.Module_Not_Found_Exception % ('pillow', 'pip install pillow==11.2.1', str(e),))


def split_text(text, font, max_width):
    lines = []
    current_line = []
    current_width = 0
    for char in text:
        char_width = font.getlength(char)
        if current_width + char_width <= max_width:
            current_line.append(char)
            current_width += char_width
        else:
            lines.append(''.join(current_line))
            current_line = [char]
            current_width = char_width
    if current_line:
        lines.append(''.join(current_line))
    return lines


def generator_icon_picture(
        image_path: Path,
        text: str,
        output_path: Path = None,
        font_path: Path = None,
        scale: float = 0.1,
        padding: int = 20,
        max_text_width: int = 400
) -> Path:
    img = Image.open(image_path).convert("RGBA")
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    img_width, img_height = img.size

    max_font_size = 60
    min_font_size = 2
    font_size = max_font_size

    best_font_size = min_font_size
    best_lines = []

    while font_size >= min_font_size:
        font = ImageFont.truetype(font_path, font_size)
        lines = split_text(text, font, max_text_width)
        if all(font.getlength(line) <= max_text_width for line in lines):
            best_font_size = font_size
            best_lines = lines
            break
        font_size -= 1

    font = ImageFont.truetype(font_path, best_font_size)
    lines = best_lines

    ascent, descent = font.getmetrics()
    line_height = ascent + descent + 2
    text_height = line_height * len(lines)
    text_width = max(font.getlength(line) for line in lines) if lines else 0
    new_width = img_width + padding + int(text_width)
    new_height = max(img_height, text_height)
    new_img = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 0))

    new_img.paste(img, (0, (new_height - img_height) // 2), mask=img)

    draw = ImageDraw.Draw(new_img)
    text_x = img_width + padding
    text_y = (new_height - text_height) // 2
    for i, line in enumerate(lines):
        draw.text((text_x, text_y + i * line_height), line, fill=(0, 0, 0, 255), font=font)

    new_img.save(output_path)
    return Path(output_path)
