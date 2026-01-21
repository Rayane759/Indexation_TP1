import urllib.request
import urllib.parse
import urllib.error
from bs4 import BeautifulSoup
import re
import time
import json
from queue import Queue

headers = {
    'User-Agent': 'ENSAI-Indexation-TP1/1.0 (rayane.djidjelli@eleve.ensai.fr)'
}

start_url = "https://web-scraping.dev/products"

product_queue = Queue()
general_queue = Queue()
general_queue.put(start_url)

# Track visited URLs
visited_urls = set()
max_crawl = 50

# Regex for product pages
product_url_pattern = re.compile(r"https://web-scraping\.dev/product/(\d+)")

# List to collect scraped data
scraped_data = []


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


def extract_page_data(current_url, soup):
    """
    Extract title, description, product features, and links from page
    """
    
    # Extract title (h3 with class product-title)
    title = ""
    title_element = soup.find("h3", class_="product-title")
    if title_element:
        title = title_element.get_text(strip=True)
    
    # Extract description (p with class product-description)
    description = ""
    para_element = soup.find("p", class_="product-description")
    if para_element:
        description = para_element.get_text(strip=True)
    
    # Extract product features from the product-features div with table
    product_features = {}
    features_div = soup.find("div", class_="product-features")
    if features_div:
        table = features_div.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    # First cell is the feature name, second is the value
                    feature_name = cells[0].get_text(strip=True).lower()
                    feature_value = cells[1].get_text(strip=True)
                    product_features[feature_name] = feature_value
    
    # Extract all links from the page body
    links = []
    link_elements = soup.find_all("a", href=True)
    
    for link_element in link_elements:
        url = link_element["href"]
        absolute_url = urllib.parse.urljoin(start_url, url)
        if absolute_url.startswith("https://web-scraping.dev/"):
            links.append(absolute_url)
    
    # Remove duplicates
    links = list(dict.fromkeys(links))
    
    return {
        "title": title,
        "description": description,
        "product_features": product_features,
        "links": links
    }


def crawler():
    crawl_count = 0

    while crawl_count < max_crawl:
        # Prioritize product links
        current_url = None
        if not product_queue.empty():
            current_url = product_queue.get()
        elif not general_queue.empty():
            current_url = general_queue.get()
        else:
            break

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        print(f"Crawling ({crawl_count+1}/{max_crawl}): {current_url}")

        try:
            # Fetch page content
            html_content = fetch_url(current_url)
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract page data
            page_data = extract_page_data(current_url, soup)
            
            # Build output JSON
            data = {
                "url": current_url,
                "title": page_data["title"],
                "description": page_data["description"],
                "product_features": page_data["product_features"],
                "links": page_data["links"]
            }
            
            # Extract all links from the page and add to queues
            for link in page_data["links"]:
                if link not in visited_urls and link not in general_queue.queue and link not in product_queue.queue:
                    if product_url_pattern.match(link):
                        product_queue.put(link)
                    else:
                        general_queue.put(link)
            
            scraped_data.append(data)
            crawl_count += 1
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing {current_url}: {e}")
            crawl_count += 1


crawler()

# Save to JSONL file
output_file = "products.jsonl"
with open(output_file, "w", encoding="utf-8") as f:
    for item in scraped_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
