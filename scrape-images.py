#
# Downloads all the images of a website following internal links recursively
#

import re
import requests
from bs4 import BeautifulSoup
import os
import sys

out_dir = sys.argv[2]

def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path

visited_pages = []
downloaded_urls = []

def scrape_images_rec(root_site, page=None):
  if page is None:
    page = root_site 

  if page in visited_pages:
    return

  print('Scraping page:', page)
  response = requests.get(page)

  soup = BeautifulSoup(response.text, 'html.parser')

  # NOTE: This approach is not exhaustive. There are other ways to show an image in HTML that we ignore
  img_tags = soup.find_all('img')
  sources = [img['src'] for img in img_tags]

  href_tags = soup.find_all(href=True)
  links = [link['href'] for link in href_tags]

  if not os.path.exists(out_dir):
      os.makedirs(out_dir)

  for source in sources:
    filename = re.search(r'/([\w_-]+.(jpg|gif|png))$', source)
    if not filename:
      print('Detected image with unexpected source:', source)
      continue

    path = os.path.join(out_dir, filename.group(1))
    if os.path.exists(path):
      path = uniquify(path)

    # If url is relative
    if 'http' not in source:
        source = '{}{}'.format(page, source)
    if source in downloaded_urls:
      print('Skipping already downloaded:', source)
    else:
      downloaded_urls.append(source)
      print('Downloading:', source)
      response = requests.get(source)
      with open(path, 'wb') as f:
        f.write(response.content)

  visited_pages.append(page) 

  for link in links:
    # Visit page if part of the root site and an html file
    extension = re.search(r'\.\w\w\w(\?.*)?$', link)
    if not extension and link.startswith(root_site):
      scrape_images_rec(root_site, link)

scrape_images_rec(sys.argv[1])
print('Downloaded', len(downloaded_urls), 'images.')
