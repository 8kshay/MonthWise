"""Draw the Monthwise icon (assets/monthwise.ico and .png). Run once: python tools/make_icon.py"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SIZE = 512


def draw() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Rounded square with a two-tone blue gradient.
    top, bottom = (0, 95, 184), (59, 125, 216)
    for y in range(SIZE):
        t = y / SIZE
        colour = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
        d.line([(0, y), (SIZE, y)], fill=colour)
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([16, 16, SIZE - 16, SIZE - 16], radius=110, fill=255)
    img.putalpha(mask)
    # Three faint rising bars (months) behind the rupee sign, blended on their own layer.
    bars = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    b = ImageDraw.Draw(bars)
    for i, h in enumerate((130, 200, 280)):
        x = 108 + i * 104
        b.rounded_rectangle([x, 440 - h, x + 84, 440], radius=16, fill=(255, 255, 255, 46))
    bars.putalpha(Image.composite(bars.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), mask))
    img = Image.alpha_composite(img, bars)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/seguisb.ttf", 290)
    except OSError:
        font = ImageFont.load_default()
    sign = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(sign).text((SIZE / 2, SIZE / 2 - 6), "\u20b9", font=font,
                              fill=(255, 255, 255, 255), anchor="mm")
    return Image.alpha_composite(img, sign)


def main():
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    img = draw()
    img.resize((256, 256), Image.LANCZOS).save(out / "monthwise.png")
    img.save(out / "monthwise.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                                           (128, 128), (256, 256)])
    print("Wrote", out / "monthwise.ico", "and", out / "monthwise.png")


if __name__ == "__main__":
    main()
