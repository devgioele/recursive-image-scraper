#
# Downloads all the images of a website following internal links recursively
#

import re
import requests
from bs4 import BeautifulSoup
import os
import sys

out_dir = sys.argv[2]

def uniquify_path(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path

def make_url_absolute(page_url, relative_url):
  # If url is absolute
  if 'http' in relative_url:
    return relative_url
  # Take page url without ending file, if any
  # The first two slashes are due to '://'
  # A file contains a dot in the name
  page_url_segments = page_url.split('/')
  if len(page_url_segments) > 3 and '.' in page_url_segments[-1]:
    root_page_url = '/'.join(page_url_segments[:-1])
  else:
    root_page_url = page_url
  # Join and leading slash to relative url if missing
  if root_page_url.endswith('/') and relative_url.startswith('/'):
    relative_url = relative_url[1:]
  return '{}{}{}'.format(root_page_url, '' if root_page_url.endswith('/') or relative_url.startswith('/')else '/', relative_url)

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
      path = uniquify_path(path)

    source = make_url_absolute(page, source)
    if source in downloaded_urls:
      print('Skipping already downloaded:', source)
    else:
      downloaded_urls.append(source)
      print('Downloading:', source)
      # TODO: Try failed connections more than once
      try:
        response = requests.get(source)
      except requests.exceptions.ConnectionError as e:
        print('Could not download source', source)
        continue
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
