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
        return {"Error": f"{file_path} not found."}

    except Exception as e: 
        print(f"An unexpected error occurred while parsing proxies: {e}")
        return {"Error": "An unexpected error occurred while parsing proxies."}

    return proxies     

# Configure Selenium WebDriver with proxy and SSL certificate
def configure_selenium_with_proxy(proxy):
    global driver_instance  # Use the global variable
    chrome_driver_path = "/usr/local/bin/chromedriver"  # Hostinger vps path **
    
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument(f'--proxy-server={proxy}')
    options.add_argument('--headless')  
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')

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

proxy_messages = []

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
            if any(keyword in html_doc for keyword in ["robot or human?", "server error", "captcha", "we just need to make sure you're not a robot", "403 forbidden", "503 service unavailable", "enter the characters you see below"]):
                message = f"Proxy {proxy['host']} returned an error or CAPTCHA. Retrying with next proxy."
                print(message)
                # proxy_messages.append(message)  # Append the message
                continue  # Skip to the next proxy

            if any(keyword in html_doc for keyword in ["domain is expired"]):
                driver.quit()
                return {"Error": "The domain is expired."}

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
            success_message = "Data fetched successfully."  # Corrected to a string
            proxy_messages.append(success_message)  # Append the success message
            return result

        except Exception as e:
            error_message = f"Error with proxy {proxy['host']}:{proxy['port']} - {e}"
            print(error_message)
            proxy_messages.append(error_message)  # Append the error message
            return {"Error": error_message}

        finally:
            if driver:
                driver.quit()

    return { "Failed to fetch data using all proxies because this web is conatining the Captcha."}

# Django view to handle user requests
def proxy(request):
    data = None
    error_message = None
    if request.method == 'POST':
        url = request.POST.get('url')
        
        if url and (url.startswith("http://") or url.startswith("https://")):
            result = datafetch(url)
            if isinstance(result, dict) and "Error" in result:
                error_message = result["Error"]
            else:
                data = result
        else:
            error_message = "Invalid or no URL provided."
    
    return render(request, 'proxy.html', {'data': data, "error_message": error_message})

