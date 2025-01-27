import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urlparse

def is_valid_subdomain(subdomain, main_domain):
    # Remove any trailing dots and convert to lowercase
    subdomain = subdomain.rstrip('.').lower()
    main_domain = main_domain.rstrip('.').lower()
    
    # Skip if subdomain is the same as main domain
    if subdomain == main_domain:
        return False
        
    # Skip common SSL/CDN domains
    skip_domains = ['cloudflaressl.com', 'automattic.com', 'amazonaws.com']
    if any(skip in subdomain for skip in skip_domains):
        return False
    
    # Check if it's actually a subdomain of our main domain
    return subdomain.endswith('.' + main_domain) or subdomain == main_domain

# Function to check if the subdomain is alive using both HTTP and HTTPS
def is_subdomain_alive(subdomain):
    protocols = ['http://', 'https://']
    for protocol in protocols:
        try:
            # Send a HEAD request to check if the subdomain is alive
            response = requests.head(f"{protocol}{subdomain}", timeout=5)
            # If the response status code is 200-399, the subdomain is alive
            if 200 <= response.status_code < 400:
                return True
        except requests.exceptions.RequestException:
            # Ignore the exception and try the next protocol
            continue
    return False

def get_main_domain(url):
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(':')[0]  # Remove port if present
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    except Exception:
        return url

# Set up the argument parser
parser = argparse.ArgumentParser(description="Crawl subdomains from crt.sh and check if they are alive")
parser.add_argument('-u', '--url', type=str, required=True, help='The website URL to crawl')
args = parser.parse_args()

# Get the main domain
main_domain = get_main_domain(args.url)

# Process the input URL to be used in crt.sh
target_url = f"https://crt.sh/?q=%.{main_domain}"

print("\n[SUBDOMAINS]")

# Send a GET request to crt.sh with the formatted URL
response = requests.get(target_url)

# Check if the request was successful
if response.status_code != 200:
    print(f"Failed to retrieve data from crt.sh. Status code: {response.status_code}")
    exit(1)

# Parse the HTML response using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Set to store unique subdomains
subdomains = set()

# Iterate over each <tr> (table row) in the HTML
for row in soup.find_all('tr'):
    # Get all the <td> (table data) elements in the row
    cells = row.find_all('td')
    
    if len(cells) > 4:
        # The fifth <td> contains the subdomain information
        subdomain = cells[4].text.strip()
        
        # Remove wildcards and split on newlines
        for domain in subdomain.replace('*.', '').split('\n'):
            domain = domain.strip().lower()
            if domain and is_valid_subdomain(domain, main_domain):
                subdomains.add(domain)

# List to store only alive subdomains
alive_subdomains = []

# Check each subdomain for liveness via both HTTP and HTTPS
for subdomain in sorted(subdomains):
    if is_subdomain_alive(subdomain):
        print(subdomain)
        alive_subdomains.append(subdomain)

# Save the alive subdomains into a .txt file
output_file = f"{main_domain}_alive_subdomains.txt"
with open(output_file, 'w') as file:
    for subdomain in alive_subdomains:
        file.write(f"{subdomain}\n")

print(f"Alive subdomains saved to {output_file}")