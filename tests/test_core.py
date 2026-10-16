import unittest

import qrcode
from PIL import Image, ImageOps

from screenscan.core import decode, web_url


class DecoderTests(unittest.TestCase):
    def test_unicode_and_inverted_rotated_qr(self):
        text = 'ScreenScan 屏幕扫码 https://example.com/'
        qr = qrcode.make(text).convert('RGB')
        self.assertEqual(decode(qr), [text])
        self.assertEqual(decode(ImageOps.invert(qr).rotate(90)), [text])

    def test_blank(self):
        self.assertEqual(decode(Image.new('RGB', (300, 300), 'white')), [])

    def test_multiple(self):
        first = qrcode.make('first').convert('RGB')
        second = qrcode.make('second').convert('RGB')
        image = Image.new('RGB', (first.width + second.width + 40, 400), 'white')
        image.paste(first, (0, 0))
        image.paste(second, (first.width + 40, 0))
        self.assertEqual(set(decode(image)), {'first', 'second'})

    def test_web_urls_only(self):
        self.assertEqual(web_url('https://example.com/a?q=1'), 'https://example.com/a?q=1')
        for value in ['file:///C:/test', 'javascript:alert(1)', 'weixin://test',
                      'https://user:pass@example.com', 'hello', 'https://',
                      'https://example.com\n', 'https://example.com:bad', 'https://[']:
            with self.subTest(value=value):
                self.assertIsNone(web_url(value))


if __name__ == '__main__':
    unittest.main()
