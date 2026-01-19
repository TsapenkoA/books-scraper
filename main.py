import multiprocessing
import time
import json
from queue import Empty
from dotenv import load_dotenv
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


load_dotenv()
NUM_PROCESSES = int(os.getenv("NUM_PROCESSES", 3))
HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "books.json")

BASE_URL = "https://books.toscrape.com/catalogue/category/books_1/page-{}.html"

class ScraperProcess(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, headless=True, test_mode=False):
        super().__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.headless = headless
        self.test_mode = test_mode

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            while True:
                try:
                    url = self.task_queue.get(timeout=3)
                except Empty:
                    break
                try:
                    page.goto(url, timeout=30000)
                    # Збираємо всі URL книг спочатку
                    book_links = [
                        urljoin(page.url, b.get_attribute("href"))
                        for b in page.query_selector_all("article.product_pod h3 a")
                    ]
                    for book_url in book_links:
                        self.scrape_book(page, book_url)
                except Exception as e:
                    print(f"[{self.name}] Error on page {url}: {e}")
            browser.close()

    def scrape_book(self, page, book_url):
        try:
            page.goto(book_url, timeout=30000)
            title = page.query_selector("h1").inner_text()
            price = page.query_selector(".price_color").inner_text()
            stock = page.query_selector(".availability").inner_text().strip()
            rating_class = page.query_selector(".star-rating").get_attribute("class")
            rating = rating_class.replace("star-rating", "").strip()
            category = page.query_selector("ul.breadcrumb li:nth-child(3) a").inner_text()
            image_url = urljoin(page.url, page.query_selector("#product_gallery img").get_attribute("src"))
            desc_el = page.query_selector("#product_description ~ p")
            description = desc_el.inner_text() if desc_el else ""

            # Product information
            table_rows = page.query_selector_all("table.table-striped tr")
            product_info = {row.query_selector("th").inner_text(): row.query_selector("td").inner_text() for row in table_rows}

            data = {
                "title": title,
                "category": category,
                "price": price,
                "stock": stock,
                "rating": rating,
                "image_url": image_url,
                "description": description,
                "product_info": product_info,
                "url": book_url
            }

            if self.test_mode:
                print(data)
            else:
                self.result_queue.put(data)
        except Exception as e:
            print(f"[{self.name}] Error scraping book {book_url}: {e}")

class ProcessManager:
    def __init__(self, num_processes=3, test_mode=False):
        self.num_processes = num_processes
        self.test_mode = test_mode
        self.manager = multiprocessing.Manager()
        self.task_queue = self.manager.Queue()
        self.result_queue = self.manager.Queue()
        self.processes = []

    def populate_tasks(self, num_pages=3):
        for i in range(1, num_pages + 1):
            self.task_queue.put(BASE_URL.format(i))

    def start_processes(self):
        for _ in range(self.num_processes):
            p = ScraperProcess(self.task_queue, self.result_queue, headless=HEADLESS, test_mode=self.test_mode)
            p.start()
            self.processes.append(p)

    def monitor_processes(self):
        while any(p.is_alive() for p in self.processes):
            for i, p in enumerate(self.processes):
                if not p.is_alive():
                    print(f"[ProcessManager] Restarting process {p.name}")
                    new_p = ScraperProcess(self.task_queue, self.result_queue, headless=HEADLESS, test_mode=self.test_mode)
                    new_p.start()
                    self.processes[i] = new_p
            time.sleep(2)

        for p in self.processes:
            p.join()

    def collect_results(self):
        results = []
        while not self.result_queue.empty():
            try:
                results.append(self.result_queue.get_nowait())
            except Empty:
                break
        return results
        
def main():
    manager = ProcessManager(num_processes=NUM_PROCESSES, test_mode=False)
    manager.populate_tasks(num_pages=3)
    manager.start_processes()
    manager.monitor_processes()

    results = manager.collect_results()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"[Main] Saved {len(results)} books to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

