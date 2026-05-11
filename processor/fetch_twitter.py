import json
import os
import time
import urllib.parse
import requests
import yaml
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.yaml')

BEARER = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
GQL = 'https://x.com/i/api/graphql'

GQL_FEATURES = {
    'articles_preview_enabled': False,
    'c9s_tweet_anatomy_moderator_badge_enabled': True,
    'communities_web_enable_tweet_community_results_fetch': True,
    'creator_subscriptions_quote_tweet_preview_enabled': False,
    'creator_subscriptions_tweet_preview_api_enabled': True,
    'freedom_of_speech_not_reach_fetch_enabled': True,
    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
    'longform_notetweets_consumption_enabled': True,
    'longform_notetweets_inline_media_enabled': True,
    'longform_notetweets_rich_text_read_enabled': True,
    'responsive_web_edit_tweet_api_enabled': True,
    'responsive_web_enhance_cards_enabled': False,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'responsive_web_graphql_timeline_navigation_enabled': True,
    'responsive_web_media_download_video_enabled': False,
    'responsive_web_twitter_article_tweet_consumption_enabled': True,
    'rweb_tipjar_consumption_enabled': True,
    'rweb_video_timestamps_enabled': True,
    'standardized_nudges_misinfo': True,
}


def _headers():
    auth_token = os.getenv('TWITTER_AUTH_TOKEN', '')
    ct0 = os.getenv('TWITTER_CT0', '')
    if not auth_token or not ct0:
        raise ValueError('缺少 TWITTER_AUTH_TOKEN 或 TWITTER_CT0，请在 .env 中配置')
    return {
        'authorization': f'Bearer {BEARER}',
        'x-csrf-token': ct0,
        'cookie': f'auth_token={auth_token}; ct0={ct0}',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en',
    }


def _get_user_id(handle):
    variables = {'screen_name': handle, 'withSafetyModeUserFields': True}
    r = requests.get(
        f'{GQL}/1VOOyvKkiI3FMmkeDNxM9A/UserByScreenName',
        headers=_headers(),
        params={'variables': json.dumps(variables), 'features': json.dumps(GQL_FEATURES)},
        timeout=10,
    )
    data = r.json()
    return data['data']['user']['result']['rest_id']


def _parse_tweets(data):
    try:
        # 兼容 timeline 和 timeline_v2 两种响应格式
        result = data['data']['user']['result']
        tl = result.get('timeline_v2') or result.get('timeline')
        instructions = tl['timeline']['instructions']
    except (KeyError, TypeError):
        return []

    tweets = []
    for inst in instructions:
        if inst.get('type') != 'TimelineAddEntries':
            continue
        for entry in inst.get('entries', []):
            try:
                tweet_result = entry['content']['itemContent']['tweet_results']['result']
                # 跳过转推
                if 'retweeted_status_result' in tweet_result.get('legacy', {}):
                    continue
                legacy = tweet_result['legacy']
                user_legacy = tweet_result['core']['user_results']['result']['legacy']
                screen_name = user_legacy['screen_name']
                tweet_id = legacy['id_str']
                text = legacy['full_text']
                created_at = legacy['created_at']
                dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=timezone.utc)
                tweets.append({
                    'id': tweet_id,
                    'text': text,
                    'screen_name': screen_name,
                    'url': f'https://x.com/{screen_name}/status/{tweet_id}',
                    'date': dt,
                })
            except (KeyError, TypeError, ValueError):
                continue
    return tweets


def _get_user_tweets(user_id, limit=20):
    variables = {
        'userId': user_id,
        'count': min(limit, 40),
        'includePromotedContent': True,
        'withQuickPromoteEligibilityTweetFields': True,
        'withVoice': True,
        'withV2Timeline': True,
    }
    r = requests.get(
        f'{GQL}/HeWHY26ItCfUmm1e6ITjeA/UserTweets',
        headers=_headers(),
        params={'variables': json.dumps(variables), 'features': json.dumps(GQL_FEATURES)},
        timeout=10,
    )
    return _parse_tweets(r.json())


def fetch_twitter_entries(days_back=2, limit_per_account=20):
    try:
        _headers()  # 提前校验凭证
    except ValueError as e:
        print(f'⚠️  {e}')
        return []

    with open(SOURCES_PATH, encoding='utf-8') as f:
        config = yaml.safe_load(f)

    accounts = config.get('twitter_accounts', [])
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    all_articles = []
    for account in accounts:
        handle = account['handle']
        try:
            user_id = _get_user_id(handle)
            tweets = _get_user_tweets(user_id, limit=limit_per_account)
            recent = [t for t in tweets if t['date'] >= cutoff]
            print(f'  @{handle}: {len(recent)} 条')
            for t in recent:
                all_articles.append({
                    'source_id': f'twitter_{t["id"]}',
                    'title': t['text'][:280],
                    'url': t['url'],
                    'source_name': f'@{t["screen_name"]}',
                    'category': 'X',
                    'published_at': t['date'].isoformat(),
                    'content': t['text'],
                })
            time.sleep(1)  # 避免限流
        except Exception as e:
            print(f'  ⚠️  @{handle} 获取失败: {e}')

    return all_articles
