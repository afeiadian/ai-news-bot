"""配置 X/Twitter 账号，运行一次即可"""
import asyncio
import sys
sys.path.insert(0, '.')

from twscrape import API

DB_PATH = "../data/twitter_accounts.db"

# ============================================================
# 使用浏览器 Cookie 登录（适用于 Google/Apple 第三方登录账号）
#
# 获取步骤：
#   1. 在浏览器中登录 https://x.com
#   2. 打开开发者工具（F12）→ Application → Cookies → https://x.com
#   3. 找到 auth_token 和 ct0 两个值，填入下方
# ============================================================

USERNAME = "afeiadian"        # 你的 X 用户名（不含 @）
AUTH_TOKEN = "7b1e948ec67766c0d9a63eb1ac30d180de617fd4"      # 浏览器 Cookie 中的 auth_token 值
CT0 = "abcceb797e50fcb029095696900cce992c0957e965fa59a9d6220b7c953fe84ead15e99083a548131e6b1d7349bbdca1a0717b1b87587b45f9fbae02fb16560eabb0002778c6fcbdffae6d9a3f1a6625"             # 浏览器 Cookie 中的 ct0 值


async def main():
    if not USERNAME or not AUTH_TOKEN or not CT0:
        print("❌ 请先填写 USERNAME、AUTH_TOKEN 和 CT0")
        return

    api = API(DB_PATH)

    cookies = f"auth_token={AUTH_TOKEN}; ct0={CT0}"
    await api.pool.add_account(
        username="afeiadian",
        password="",          # Cookie 登录不需要密码
        email="afeiadian@gmail.com",
        email_password="",
        cookies=cookies,
    )
    print(f"已添加账号：{USERNAME}")

    # 验证：搜索一条测试推文
    print("\n验证搜索功能...")
    async for tweet in api.search("LLM", limit=1):
        print(f"  测试成功：@{tweet.user.username}: {tweet.rawContent[:60]}")
        break
    else:
        print("  ⚠️  搜索无结果，请检查 Cookie 是否有效")

    print("✅ 账号配置完成")


if __name__ == '__main__':
    asyncio.run(main())
