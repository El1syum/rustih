import asyncio
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

MAIN_URL = 'https://rustih.ru'
ENCODING = 'UTF-8'
FILE_NAME = 'output4.xml'


async def parse_page(session, page, xml_doc):
    async with session.get(urljoin(MAIN_URL, f'/page/{page}')) as r:
        soup = BeautifulSoup(await r.text(), 'lxml')
        cards = soup.find('div', class_='posts-container').find_all('div', class_='post-card-one')
        links = list(map(lambda i: i.find('a').get('href'), cards))
        for link in links:
            async with session.get(link) as r:
                soup = BeautifulSoup(await r.text(), 'lxml')
                try:
                    title = soup.find('h1', class_='entry-title').text.split(': Стих')[0].strip()
                except AttributeError:
                    print(page, link)
                    continue
                text = ''.join(list(map(str, soup.find('div', class_='poem-text').findChildren('p')))). \
                    split('<p><ins class="adsbygoogle"')[0]

                item = ET.SubElement(xml_doc, 'item')
                ET.SubElement(item, 'title').text = f'<![CDATA[{title}]]>'
                ET.SubElement(item, 'content:encoded').text = f'<![CDATA[{text}]]>'
                ET.SubElement(item, 'wp:post_type').text = '<![CDATA[post]]>'
                ET.SubElement(item, 'wp:status').text = '<![CDATA[publish]]>'
                ET.SubElement(item, 'category', domain='post_tag', nicename='stihi').text = '<![CDATA[Стихи]]>'


async def gather_data():
    xml_doc = ET.Element('channel')
    ET.SubElement(xml_doc, 'language').text = 'ru-RU'
    ET.SubElement(xml_doc, 'wp:wxr_version').text = '1.2'
    author = ET.SubElement(xml_doc, 'wp:author')
    ET.SubElement(author, 'wp:author_id').text = '0'

    async with aiohttp.ClientSession() as session:
        tasks = []
        r = await session.get(MAIN_URL)
        soup = BeautifulSoup(await r.text(), 'lxml')
        max_page = int(re.findall(r'page/\d+',
                                  soup.find('nav', class_='pagination').find_all('a', class_='page-numbers')[-1].get(
                                      'href'))[0].split('/')[1])
        for page in range(600, max_page+1):  # max_page+1
            task = asyncio.create_task(parse_page(session, page, xml_doc))
            tasks.append(task)

        await asyncio.gather(*tasks)

    tree = ET.ElementTree(xml_doc)
    tree.write(FILE_NAME, encoding=ENCODING, xml_declaration=True)
    with open(FILE_NAME, 'a', encoding=ENCODING) as file:
        file.write('</rss>')


def main():
    asyncio.run(gather_data())


if __name__ == '__main__':
    main()
