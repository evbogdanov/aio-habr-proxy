from aiohttp import web, ClientSession
import async_timeout
import bs4
import re


################################################################################
### Constants
################################################################################

HOST = '127.0.0.1'

PORT = 8080

WEBSITE = 'https://habrahabr.ru'

TAGS_TO_IGNORE = ['pre', 'code', 'script', 'style', 'head', 'title', 'meta']

RE_WORD_WITH_SIX_CHARS = re.compile(r'(\b\w{6}\b)')


################################################################################
### HTML modifications
################################################################################

def should_modify_tag(tag):
    if tag.parent.name in TAGS_TO_IGNORE:
        return False
    if isinstance(tag, bs4.Comment) or isinstance(tag, bs4.Doctype):
        return False
    return True

def modify_tag(tag):
    text = tag.string.strip()
    if not text:
        return
    text = RE_WORD_WITH_SIX_CHARS.sub(r'\1™', text)
    tag.string.replace_with(text)

def modify_html(html):
    soup = bs4.BeautifulSoup(html, 'lxml')
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            link['href'] = href.replace(WEBSITE, '')
    for tag in soup.find_all(text=True):
        if should_modify_tag(tag):
            modify_tag(tag)
    return soup.prettify()


################################################################################
### Client/server stuff
################################################################################

async def fetch(url):
    async with ClientSession() as session:
        with async_timeout.timeout(10):
            async with session.get(url) as response:
                if 'text/html' in response.headers['Content-Type']:
                    return True, await response.text()
                return False, await response.read()

async def handle(request):
    url = request.rel_url
    is_html, content = await fetch(f'{WEBSITE}{url}')
    if is_html:
        response = {'text': modify_html(content),
                    'content_type': 'text/html'}
    else:
        response = {'body': content}
    return web.Response(**response)


################################################################################
### Main
################################################################################

def main():
    app = web.Application()
    app.router.add_get('/{tail:.*}', handle)
    web.run_app(app, host=HOST, port=PORT)

if __name__ == '__main__':
    main()
