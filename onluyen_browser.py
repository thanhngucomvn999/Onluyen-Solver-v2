import time
from typing import List
from playwright.sync_api import sync_playwright
from models import Assignment, Question

class OnluyenBrowser:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.page = None
        self._playwright = None

    def start(self):
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=self.headless)
        context = self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
        )
        self.page = context.new_page()

    def login(self, username: str, password: str):
        self.page.goto("https://app.onluyen.vn/dang-nhap", wait_until="networkidle")
        self.page.fill('input[name="username"]', username)
        self.page.fill('input[name="password"]', password)
        self.page.click('button[type="submit"]')
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)

    def get_assignments(self) -> List[Assignment]:
        self.page.goto("https://app.onluyen.vn/bai-tap", wait_until="networkidle")
        time.sleep(2)
        cards = self.page.query_selector_all(".assignment-card")
        result = []
        for card in cards:
            title_el = card.query_selector(".title")
            title = title_el.inner_text() if title_el else "Khong ten"
            assign_id = card.get_attribute("data-id") or ""
            result.append(Assignment(assign_id=assign_id, title=title))
        return result

    def get_questions(self, assign_id: str) -> List[Question]:
        self.page.goto("https://app.onluyen.vn/bai-tap/" + assign_id, wait_until="networkidle")
        time.sleep(2)
        blocks = self.page.query_selector_all(".question-block")
        questions = []
        for idx, block in enumerate(blocks):
            content_el = block.query_selector(".question-content")
            content = content_el.inner_text() if content_el else ""
            option_els = block.query_selector_all(".option")
            options = [opt.inner_text() for opt in option_els] if option_els else None
            if options and len(options) == 4:
                qtype = "mcq"
            elif options and len(options) == 2:
                qtype = "true_false"
            else:
                qtype = "short_answer"
            questions.append(Question(
                id=assign_id + "-" + str(idx),
                content=content,
                options=options,
                qtype=qtype,
                source="browser",
            ))
        return questions

    def stop(self):
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()
