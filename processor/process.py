import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
)
MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-v4-pro')

SYSTEM_PROMPT = """你是一个 AI 技术资讯编辑助手，专注于以下领域：
1. 大语言模型（LLM）相关技术、研究、产品
2. AI 开发工具、框架、基础设施（如 vLLM、LangChain、推理优化等）
3. AI 芯片与硬件（NVIDIA、AMD、自研芯片、数据中心等）
4. 大模型训练、微调、部署相关技术

你的任务是评估文章的相关性并生成中文摘要。"""


def analyze_article(title: str, content: str, source: str) -> dict:
    """返回 {'score': 0-100, 'summary': str, 'relevant': bool}"""
    prompt = f"""请分析以下文章，判断是否与 AI 技术领域（大模型/AI工具/AI芯片）相关。

来源: {source}
标题: {title}
内容摘要: {content[:800]}

请以 JSON 格式回复（不要加 markdown 代码块）：
{{
  "score": <0-100的整数，表示与AI技术领域的相关度>,
  "summary": "<如果相关(score>=60)，用2-3句中文概括核心内容；否则留空>",
  "reason": "<判断依据，一句话>"
}}"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=500,
        temperature=0.1,
    )

    text = resp.choices[0].message.content.strip()

    import json
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        import re
        m = re.search(r'\{.*\}', text, re.DOTALL)
        result = json.loads(m.group()) if m else {}

    score = int(result.get('score', 0))
    return {
        'score': score,
        'summary': result.get('summary', ''),
        'relevant': score >= 60,
    }
