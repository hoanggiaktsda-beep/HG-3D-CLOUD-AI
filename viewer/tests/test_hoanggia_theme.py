"""Regression tests: HG 3D CLOUD AI adopts HOANGGIA STUDIO navigation without breaking tools."""
import shutil
import unittest
import os
from playwright.sync_api import sync_playwright
URL=os.environ.get("HG_VIEWER_URL","http://127.0.0.1:8765")
class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=sync_playwright().start()
        cls.browser=cls.p.chromium.launch(executable_path=shutil.which("chromium"),headless=True,
           args=["--no-sandbox","--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()
    def test_desktop_navigation_and_brand(self):
        context=self.browser.new_context(viewport={"width":1440,"height":900})
        self.addCleanup(context.close)
        page=context.new_page()
        page.goto(URL+"#chatgpt-studio")
        page.wait_for_function("() => !!window.hgViewer?.ready")
        self.assertTrue(page.locator(".hg-side").is_visible())
        self.assertTrue(page.locator(".hg-topbar").is_visible())
        self.assertEqual(page.locator("#hg-crumb").inner_text(),"XƯỞNG CHATGPT")
        self.assertEqual(page.locator('.hg-side-nav [data-hg-route="chatgpt-studio"]').get_attribute("aria-current"),"page")
        self.assertTrue(page.locator('#cgpt-copy').is_visible())
        self.assertEqual(page.locator(".hg-brand img").get_attribute("src"),"assets/hoanggia-icon.svg")
        self.assertEqual(page.locator('.hg-side-home').get_attribute('href'),"https://hoanggiaktsda-beep.github.io/hoanggia-studio/#home")
        page.locator('.hg-side-nav a[href="#create-model"]').click()
        page.wait_for_function('() => document.querySelector("#hg-crumb").textContent === "TẠO MÔ HÌNH 3D"')

    def test_phone_bottom_navigation_and_no_overflow(self):
        for width,height in [(390,844),(375,812),(320,640),(820,1180)]:
            with self.subTest(width=width):
                context=self.browser.new_context(viewport={"width":width,"height":height},is_mobile=True,has_touch=True)
                self.addCleanup(context.close)
                page=context.new_page()
                page.goto(URL+"#create-model")
                page.wait_for_function("() => !!window.hgViewer?.ready")
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),width+1)
                if width<=390:
                    self.assertTrue(page.locator(".hg-mobile-nav").is_visible())
                    self.assertFalse(page.locator(".hg-side").is_visible())
                    page.locator('.hg-mobile-nav [href="#chatgpt-studio"]').click()
                    page.wait_for_function('() => document.querySelector("#hg-crumb").textContent === "XƯỞNG CHATGPT"')
                else:
                    self.assertTrue(page.locator(".hg-side").is_visible())

if __name__=="__main__":
    unittest.main()
