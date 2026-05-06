"""给数据库中已有文章补填话题分类"""
import sys, time, json, re, os
sys.path.insert(0, '.')

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from storage import init_db, get_articles_without_topic, update_topic, get_articles_without_title_zh, update_title_zh

client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
)
MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-v4-pro')

TOPICS = ['基础大模型', '推理部署', '训练微调', '开发工具', 'AI芯片硬件', '学术论文', '行业资讯']


def classify(title, title_zh, summary):
    text = f'标题：{title_zh or title}\n摘要：{summary or ""}'
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{'role': 'user', 'content':
            f'从以下选项中为这篇AI资讯选择1-3个最匹配的话题分类，用英文逗号分隔输出，不加其他内容：\n'
            f'选项：{"、".join(TOPICS)}\n\n{text}'}],
        max_tokens=500,
        temperature=0.1,
    )
    result = resp.choices[0].message.content.strip()
    matched = [t for t in TOPICS if t in result]
    return ','.join(matched) if matched else '行业资讯'


def translate(title):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{'role': 'user', 'content':
            f'将以下标题翻译成中文，只输出翻译结果，不加任何解释：\n{title}'}],
        max_tokens=100,
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip()


def main():
    init_db()

    # 先补填中文标题
    no_zh = get_articles_without_title_zh(limit=500)
    if no_zh:
        print(f'\n=== 补填中文标题：{len(no_zh)} 篇 ===')
        for i, a in enumerate(no_zh, 1):
            print(f'[{i}/{len(no_zh)}] {a["title"][:55]}')
            try:
                zh = translate(a['title'])
                update_title_zh(a['url'], zh)
                print(f'  → {zh}')
            except Exception as e:
                print(f'  ⚠️ {e}')
            time.sleep(0.3)

    # 再补填话题分类
    no_topic = get_articles_without_topic(limit=500)
    if no_topic:
        print(f'\n=== 补填话题分类：{len(no_topic)} 篇 ===')
        for i, a in enumerate(no_topic, 1):
            print(f'[{i}/{len(no_topic)}] {(a.get("title_zh") or a["title"])[:50]}')
            try:
                topic = classify(a['title'], a.get('title_zh', ''), a.get('summary', ''))
                update_topic(a['url'], topic)
                print(f'  → {topic}')
            except Exception as e:
                print(f'  ⚠️ {e}')
            time.sleep(0.3)

    print('\n✅ 补填完成')


if __name__ == '__main__':
    main()
