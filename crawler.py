import urllib.request
import urllib.parse
import urllib.error
from bs4 import BeautifulSoup
import re
import time
from queue import Queue

headers = {
    'User-Agent': 'ENSAI-Indexation-TP1/1.0 (rayane.djidjelli@eleve.ensai.fr)'
}

start_url = "https://web-scraping.dev/products"

# Queues
queue = Queue()
queue.put(start_url)

# Track visited URLs
visited_urls = set()
max_crawl = 20

# Regex for real product pages
product_url_pattern = re.compile(r"https://web-scraping\.dev/product/\d+")

# List to collect scraped data
product_data = []

# ----------------------------
# Fetch URL function with retries
# ----------------------------
def fetch_url(url, retries=5, delay=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                return response.read()
        except urllib.error.URLError as e:
            print(f"Error fetching {url}: {e}. Retry {attempt + 1}/{retries}")
            time.sleep(delay)
    raise Exception(f"Failed to fetch {url} after {retries} attempts")


def crawler():
    crawl_count = 0

    while not queue.empty() and crawl_count < max_crawl:
        current_url = queue.get()

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        print(f"Crawling ({crawl_count+1}/{max_crawl}): {current_url}")

        # Fetch page content
        html_content = fetch_url(current_url)
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract all links from the page
        for link_element in soup.find_all("a", href=True):
            url = link_element["href"]
            absolute_url = urllib.parse.urljoin(start_url, url)
            if absolute_url.startswith("https://web-scraping.dev/") and absolute_url not in visited_urls:
                # Only add product pages or the main products page
                if absolute_url == start_url or product_url_pattern.match(absolute_url):
                    queue.put(absolute_url)

        # Extract product data if it's a real product page
        if product_url_pattern.match(current_url):
            # Product name
            name_element = soup.find("h1", class_="product-title")
            # Product description / paragraph
            paragraph_element = soup.find("div", class_="woocommerce-product-details__short-description")
            # Product image
            image_element = soup.find("img", class_="attachment-woocommerce_thumbnail")
            
            if name_element and paragraph_element and image_element:
                data = {
                    "Url": current_url,
                    "Name": name_element.get_text(strip=True),
                    "Paragraph": paragraph_element.get_text(strip=True),
                    "Image": image_element["src"]
                }
                product_data.append(data)

        crawl_count += 1
        time.sleep(0.5)


crawler()

for product in product_data:
    print(product)

main_products = [p for p in product_data if "?" not in p["Url"]]

print(f"Total main products scraped: {len(main_products)}\n")

# Print the first 5 products
for product in main_products[:5]:
    print("URL:", product["Url"])
    print("Name:", product["Name"])
    print("Paragraph:", product["Paragraph"])
    print("Image:", product["Image"])
    print("-" * 50)
