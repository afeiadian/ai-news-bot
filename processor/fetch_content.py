import requests


def fetch_jina_content(url: str, timeout: int = 15) -> str:
    """用 Jina Reader 获取网页纯文本，失败时返回空字符串"""
    try:
        r = requests.get(
            f'https://r.jina.ai/{url}',
            headers={'Accept': 'text/plain', 'X-Return-Format': 'text'},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.text.strip()[:3000]
    except Exception:
        pass
    return ''
