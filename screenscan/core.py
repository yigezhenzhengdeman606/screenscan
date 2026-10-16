"""Local decoding and conservative URL handling. No network requests."""
from urllib.parse import urlsplit

import zxingcpp
from PIL import ImageOps


def decode(image):
    return list(dict.fromkeys(
        result.text for candidate in (image, ImageOps.invert(image.convert('RGB')))
        for result in zxingcpp.read_barcodes(
            candidate, formats=zxingcpp.BarcodeFormat.QRCode,
            try_rotate=True, try_downscale=True,
        ) if result.valid and result.text
    ))


def web_url(text):
    if any(ord(char) < 32 or char.isspace() for char in text):
        return None
    try:
        parsed = urlsplit(text)
        if (parsed.scheme.lower() in {"http", "https"} and parsed.hostname
                and not parsed.username and not parsed.password):
            _ = parsed.port
            return text
    except ValueError:
        pass
    return None
