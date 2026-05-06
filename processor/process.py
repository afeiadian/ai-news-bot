import os
import json
import re
import yaml
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
)
MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-v4-pro')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'scoring.yaml')


def load_scoring_config():
    with open(CONFIG_PATH, encoding='utf-8') as f:
        return yaml.safe_load(f)


def build_system_prompt(config):
    domains = config.get('domains', [])
    topics  = config.get('topics', [])

    domain_lines = '\n'.join(
        f'{i+1}. {d["name"]}：{d["description"]}'
        for i, d in enumerate(domains)
    )
    topic_lines = '\n'.join(
        f'- {t["name"]}：{t["description"]}'
        for t in topics
    )
    topic_names = '、'.join(t['name'] for t in topics)

    return f"""你是一个 AI 技术资讯编辑助手，专注于以下技术领域：
{domain_lines}

话题分类标准（topic 字段从以下选项中选择）：
{topic_lines}

你的任务是评估相关性、分类话题并生成中文摘要。""", topic_names


def analyze_article(title: str, content: str, source: str) -> dict:
    config = load_scoring_config()
    min_score = config.get('min_score', 60)
    system_prompt, topic_names = build_system_prompt(config)

    prompt = f"""请分析以下文章，判断是否与上述 AI 技术领域相关。

来源: {source}
标题: {title}
内容摘要: {content[:800]}

请以 JSON 格式回复（不要加 markdown 代码块）：
{{
  "score": <0-100的整数，表示与AI技术领域的相关度>,
  "title_zh": "<将英文标题翻译成中文，保持简洁准确；如果标题已是中文则原样返回>",
  "topics": "<从以下选项中选1-3个最匹配的话题，用英文逗号分隔，如：基础大模型,推理部署；若不相关则填空字符串>，可选值：{topic_names}",
  "summary": "<如果相关(score>={min_score})，用2-3句中文概括核心内容；否则留空>",
  "reason": "<判断依据，一句话>"
}}"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': prompt},
        ],
        max_tokens=500,
        temperature=0.1,
    )

    text = resp.choices[0].message.content.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        result = json.loads(m.group()) if m else {}

    score = int(result.get('score', 0))

    # 兼容返回单个字符串或列表
    raw_topics = result.get('topics', result.get('topic', ''))
    if isinstance(raw_topics, list):
        topics_str = ','.join(t.strip() for t in raw_topics if t.strip())
    else:
        topics_str = str(raw_topics).strip()

    # 校验只保留合法话题名
    valid = set(topic_names.split('、'))
    topics_str = ','.join(t for t in topics_str.split(',') if t.strip() in valid)

    return {
        'score':    score,
        'title_zh': result.get('title_zh', ''),
        'topic':    topics_str,
        'summary':  result.get('summary', ''),
        'relevant': score >= min_score,
    }
