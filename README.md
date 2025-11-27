# Books Scraper

Скрипт для збору даних про книги з сайту [Books to Scrape](https://books.toscrape.com/) за допомогою **Playwright** та **мультипроцесності**.

---

## Можливості

- Збір даних про книги:
  - Назва (`title`)
  - Категорія (`category`)
  - Ціна (`price`)
  - Наявність на складі (`stock`)
  - Рейтинг (`rating`)
  - URL зображення (`image_url`)
  - Опис (`description`)
  - Інформація з таблиці продукту (`product_info`)
  - Посилання на сторінку книги (`url`)
- Підтримка **кількох процесів** для швидшого збору даних
- Конфігурація через `.env` (кількість процесів, headless режим, ім’я файлу для збереження)
- Збереження результатів у **JSON файл** (`books.json`)

---

## Вимоги

- Python 3.10+
- Playwright
- python-dotenv

---

## Установка


```bash
git clone https://github.com/TsapenkoA/books-scraper.git
cd books-scraper
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
pip install -r requirements.txt
playwright install
python main.py
```
