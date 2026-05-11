import requests
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}


def fetch_jina_content(url: str, timeout: int = 15) -> str:
    """用 Jina Reader 获取网页纯文本，失败返回空字符串"""
    try:
        r = requests.get(
            f'https://r.jina.ai/{url}',
            headers={'Accept': 'text/plain', 'X-Return-Format': 'text'},
            timeout=timeout,
        )
        if r.status_code == 200 and len(r.text.strip()) > 100:
            return r.text.strip()[:3000]
    except Exception:
        pass
    return ''


def fetch_trafilatura_content(url: str, timeout: int = 15) -> str:
    """用 trafilatura 抓取并提取正文，失败返回空字符串"""
    if not HAS_TRAFILATURA:
        return ''
    try:
        html = requests.get(url, headers=HEADERS, timeout=timeout).text
        text = trafilatura.extract(html, include_comments=False, include_tables=False)
        if text and len(text) > 100:
            return text[:3000]
    except Exception:
        pass
    return ''


def fetch_article_content(url: str) -> str:
    """
    抓取文章原文：先试 Jina，失败则降级到 trafilatura。
    两者都失败返回空字符串。
    """
    content = fetch_jina_content(url)
    if content:
        return content
    return fetch_trafilatura_content(url)
