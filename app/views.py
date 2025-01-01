from django.shortcuts import render
from selenium import webdriver
# import chromedriver_autoinstaller
import time
from bs4 import BeautifulSoup
import random
import os
from django.http import JsonResponse


# File paths for proxies and SSL certificate
PROXIES_FILE_PATH = os.path.join(os.path.dirname(__file__), 'proxies.txt')
SSL_CERT_PATH = os.path.join(os.path.dirname(__file__), 'SSL.crt')

# Parse proxies from a file
def parse_proxies(file_path):
    proxies = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) == 4:
                    proxies.append({
                        'host': parts[0],
                        'port': parts[1],
                        'username': parts[2],
                        'password': parts[3]
                    })
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return{f"Error: {file_path} not found."}
    return proxies

# Configure Selenium WebDriver with proxy and SSL certificate
def configure_selenium_with_proxy(proxy):
    global driver_instance  # Use the global variable
    chrome_driver_path = r"C:\Program Files\chromedriver-win64\chromedriver.exe"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--ignore-certificate-errors")

    # Add SSL certificate if exists
    if os.path.exists(SSL_CERT_PATH):
        options.add_argument(f'--ssl-client-cert={SSL_CERT_PATH}')

    # Set proxy configuration
    proxy_settings = {
        'proxyType': 'MANUAL',
        'httpProxy': f"{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
        'sslProxy': f"{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
        'noProxy': ''
    }

    capabilities = webdriver.DesiredCapabilities.CHROME.copy()
    capabilities['proxy'] = proxy_settings

    # Initialize the WebDriver instance
    driver_instance = webdriver.Chrome(executable_path=chrome_driver_path, options=options, desired_capabilities=capabilities)
    return driver_instance

# Fetch and parse data from the URL
def datafetch(url):
    proxies = parse_proxies(PROXIES_FILE_PATH)
    random.shuffle(proxies)

    for proxy in proxies:
        driver = None
        result = {}
        try:
            driver = configure_selenium_with_proxy(proxy)
            driver.get(url)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            html_doc = soup.text.lower()  # Store the HTML text in lowercase for easier keyword checking

            # Check for various error keywords
            if any(keyword in html_doc for keyword in ["robot or human?", "server error", "captcha", "we just need to make sure you're not a robot", "403 forbidden", "503 service unavailable", "Enter the characters you see below"]):
                print(f"Proxy {proxy['host']} returned an error or CAPTCHA. Retrying with next proxy.")
                continue  # Skip to the next proxy

            # Extract various data points using BeautifulSoup selectors
            result = {
                "H1 Tags": [tag.text.strip() for tag in soup.find_all('h1')],
                "H2 Tags": [tag.text.strip() for tag in soup.find_all('h2')],
                "Paragraph Tags": [tag.text.strip() for tag in soup.find_all('p')],
                "Image Tags": [img['src'].strip() for img in soup.find_all('img') if img.get('src')],
                "Anchor Tags": [a['href'].strip() for a in soup.find_all('a') if a.get('href')],
                "Button Texts": [btn.text.strip() for btn in soup.find_all('button')],
                "Meta Descriptions": [meta['content'].strip() for meta in soup.find_all('meta', attrs={"name": "description"}) if meta.get('content')],
                # Additional fields can be added as required
            }

            driver.quit()
            return result

        except Exception as e:
            print(f"Error with proxy {proxy['host']}:{proxy['port']} - {e}")
            return {f"Error with proxy {proxy['host']}:{proxy['port']} - {e}"}

        finally:
            if driver:
                driver.quit()

    return {"Error": "Failed to fetch data using all proxies."}

# Django view to handle user requests
def proxy(request):
    data = None
    if request.method == 'POST':
        url = request.POST.get('url')
        if url:
            data = datafetch(url)
        else:
            data = {"Error": "No URL provided."}
    return render(request, 'proxy.html', {'data': data})


# Global variable to hold the WebDriver instance






# from django.shortcuts import render
# from selenium import webdriver
# import chromedriver_autoinstaller
# import time
# from bs4 import BeautifulSoup
# import random
# import os

# # File paths for proxies and SSL certificate
# PROXIES_FILE_PATH = os.path.join(os.path.dirname(__file__), 'proxies.txt')
# SSL_CERT_PATH = os.path.join(os.path.dirname(__file__), 'SSL.crt')

# # Parse proxies from a file
# def parse_proxies(file_path):
#     proxies = []
#     try:
#         with open(file_path, 'r') as f:
#             for line in f:
#                 parts = line.strip().split(':')
#                 if len(parts) == 4:
#                     proxies.append({
#                         'host': parts[0],
#                         'port': parts[1],
#                         'username': parts[2],
#                         'password': parts[3]
#                     })
#     except FileNotFoundError:
#         print(f"Error: {file_path} not found.")
#     return proxies

# # Configure Selenium WebDriver with proxy and SSL certificate
# def configure_selenium_with_proxy(proxy):
#     chromedriver_autoinstaller.install()

#     options = webdriver.ChromeOptions()
#     options.add_argument("--disable-gpu")
#     # options.add_argument("--headless")  # Uncomment for headless mode
#     options.add_argument("--ignore-certificate-errors")

#     # Add SSL certificate if exists
#     if os.path.exists(SSL_CERT_PATH):
#         options.add_argument(f'--ssl-client-cert={SSL_CERT_PATH}')

#     # Set proxy configuration
#     proxy_settings = {
#         'proxyType': 'MANUAL',
#         'httpProxy': f"{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
#         'sslProxy': f"{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
#         'noProxy': ''  # Add domains you don't want to go through the proxy, if any.
#     }

#     capabilities = webdriver.DesiredCapabilities.CHROME.copy()
#     capabilities['proxy'] = proxy_settings

#     return webdriver.Chrome(options=options)

# # Fetch and parse data from the URL
# def datafetch(url):
#     proxies = parse_proxies(PROXIES_FILE_PATH)
#     random.shuffle(proxies)

#     for proxy in proxies:
#         driver = None
#         result = {}
#         try:
#             driver = configure_selenium_with_proxy(proxy)
#             driver.get(url)
#             time.sleep(5)

#             soup = BeautifulSoup(driver.page_source, 'html.parser')
#             html_doc = soup.text.lower()  # Store the HTML text in lowercase for easier keyword checking

#             # Check for various error keywords
#             if any(keyword in html_doc for keyword in ["robot or human?", "server error", "captcha", "we just need to make sure you're not a robot","403 forbidden", "503 service unavailable"]):
#                 print(f"Proxy {proxy['host']} returned an error or CAPTCHA. Retrying with next proxy.")  # Debugging line
#                 continue  # Skip to the next proxy
#             # elif len(result) < 100:
#             #     print(f"Proxy {proxy['host']} returned an error low data. Retrying with next proxy.")  # Debugging line
#             #     continue  # Skip to the next proxy

#             result = {
#                 "H1 Tags": [tag.text.strip() for tag in soup.find_all('h1')],
#                 "H2 Tags": [tag.text.strip() for tag in soup.find_all('h2')],
#                 "Paragraph Tags": [tag.text.strip() for tag in soup.find_all('p')],
#                 "Image Tags": [img['src'].strip() for img in soup.find_all('img') if img.get('src')],
#                 "Anchor Tags": [a['href'].strip() for a in soup.find_all('a') if a.get('href')],
#                 "Button Texts": [btn.text.strip() for btn in soup.find_all('button')],
#                 "Meta Descriptions": [meta['content'].strip() for meta in soup.find_all('meta', attrs={"name": "description"}) if meta.get('content')],
#                 "Prices": [price.text.strip() for price in soup.find_all('span', class_=lambda c: c and 'price' in c.lower())],
#                 "Ratings": [rating.text.strip() for rating in soup.find_all('span', class_=lambda c: c and 'rating' in c.lower())],
#                 "Reviews": [review.text.strip() for review in soup.find_all('div', class_=lambda c: c and 'review' in c.lower())],
#                 "Categories": [category.text.strip() for category in soup.find_all('li', class_=lambda c: c and 'category' in c.lower())],
#             }

#             # if len(result) < 50 :
#             #     print(f"Proxy {proxy['host']} returned low data. Retrying with next proxy.")  # Debugging line
#             #     continue  # Skip to the next proxy

#             driver.quit()
#             return result

#         except Exception as e:
#             print(f"Error with proxy {proxy['host']}:{proxy['port']} - {e}")

#         finally:
#             if driver:
#                 driver.quit()

#     return {"Error": "Failed to fetch data using all proxies."}

# # Django view to handle user requests
# def proxy(request):
#     data = None
#     if request.method == 'POST':
#         url = request.POST.get('url')
#         if url:
#             data = datafetch(url)
#         else:
#             data = {"Error": "No URL provided."}
#     return render(request, 'proxy.html', {'data': data})



