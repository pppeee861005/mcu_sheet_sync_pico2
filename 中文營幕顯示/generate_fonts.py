import os
from PIL import Image, ImageDraw, ImageFont

font_path = 'C:\\Windows\\Fonts\\msjh.ttc'
font = ImageFont.truetype(font_path, 14)

chars = ['中', '文', '螢', '幕', '顯', '示', '極', '客', '掌', '機', '上', '課', '簽', '到', '成', '功', '股', '市', '大', '盤']

output_dict = {}

for ch in chars:
    img = Image.new('1', (16, 16), 0)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), ch, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    ox = max(0, (16 - w) // 2) - bbox[0]
    oy = max(0, (16 - h) // 2) - bbox[1]
    draw.text((ox, oy), ch, font=font, fill=1)
    
    # 採用 Row-Major 16x16: 16 行，每行 2 bytes (16 bits)
    data = []
    for y in range(16):
        b1 = 0
        b2 = 0
        for x in range(8):
            if img.getpixel((x, y)):
                b1 |= (1 << (7 - x))
        for x in range(8, 16):
            if img.getpixel((x, y)):
                b2 |= (1 << (15 - x))
        data.extend([b1, b2])
    output_dict[ch] = data

file_content = '''# fonts_cn.py - 繁體中文 16x16 標準點陣字型庫 (微軟正黑體向量光柵化精確產生)
# 格式：Row-major (每行 2 bytes，共 16 行 = 32 bytes)
# bit 7 到 bit 0 由左至右映射像素

FONT_16x16 = {
'''

for ch, d in output_dict.items():
    hex_str = ','.join(f'0x{b:02X}' for b in d)
    file_content += f'    "{ch}": bytes([{hex_str}]),\n'

file_content += '''}\n
def draw_char_16x16(oled, char, x, y, color=1):
    glyph = FONT_16x16.get(char)
    if not glyph:
        oled.rect(x, y, 16, 16, color)
        return
    # row-major 繪製
    for row in range(16):
        b1 = glyph[row * 2]
        b2 = glyph[row * 2 + 1]
        for col in range(8):
            if (b1 >> (7 - col)) & 1:
                oled.pixel(x + col, y + row, color)
        for col in range(8):
            if (b2 >> (7 - col)) & 1:
                oled.pixel(x + 8 + col, y + row, color)

def draw_string_cn(oled, text, start_x, start_y, color=1):
    cur_x = start_x
    cur_y = start_y
    for ch in text:
        if ch in FONT_16x16:
            if cur_x + 16 > 128:
                cur_x = start_x
                cur_y += 18
            draw_char_16x16(oled, ch, cur_x, cur_y, color)
            cur_x += 16
        elif ch == '\\n':
            cur_x = start_x
            cur_y += 18
        else:
            if cur_x + 8 > 128:
                cur_x = start_x
                cur_y += 18
            oled.text(ch, cur_x, cur_y + 4, color)
            cur_x += 8
'''

with open(r'd:\練習操作區\創客\中文營幕顯示\fonts_cn.py', 'w', encoding='utf-8') as f:
    f.write(file_content)

print('Successfully generated fonts_cn.py with genuine MSJH 16x16 glyphs!')
