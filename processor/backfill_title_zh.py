"""给数据库中已有文章补填中文标题翻译"""
import sys
import time
sys.path.insert(0, '.')

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from storage import init_db, get_articles_without_title_zh, update_title_zh

client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
)
MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-v4-pro')


def translate_title(title: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{
            'role': 'user',
            'content': f'将以下标题翻译成中文，只输出翻译结果，不加任何解释：\n{title}'
        }],
        max_tokens=2000,
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip()


def main():
    init_db()
    articles = get_articles_without_title_zh(limit=500)
    print(f'需要补填中文标题：{len(articles)} 篇')

    for i, a in enumerate(articles, 1):
        print(f'[{i}/{len(articles)}] {a["title"][:60]}')
        try:
            title_zh = translate_title(a['title'])
            update_title_zh(a['url'], title_zh)
            print(f'  → {title_zh}')
        except Exception as e:
            print(f'  ⚠️  失败: {e}')
        time.sleep(0.3)

    print('\n✅ 补填完成')


if __name__ == '__main__':
    main()
