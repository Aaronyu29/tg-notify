#!/usr/bin/env python3
"""
获取 Telegram Channel 的 Chat ID
使用方法：
1. 将你的 Bot 添加为 Channel 管理员
2. 在 Channel 中发送任意消息（或使用 Bot 命令）
3. 运行此脚本查看 Chat ID
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Bot
import asyncio

# 加载 .env (尝试多个位置)
env_paths = [
    Path(__file__).parent / ".env",
    Path(__file__).parent / "monitor" / ".env"
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")

async def get_updates():
    """获取最近的更新，包含 Channel 信息"""
    bot = Bot(token=BOT_TOKEN)

    print("=" * 60)
    print("  获取 Telegram 更新...")
    print("=" * 60)

    try:
        # 获取最近的更新
        updates = await bot.get_updates(limit=100)

        if not updates:
            print("\n⚠️  没有找到任何更新")
            print("\n请按照以下步骤操作：")
            print("1. 将 Bot 添加为 Channel 管理员")
            print("2. 在 Channel 中发送一条消息（任意内容）")
            print("3. 重新运行此脚本")
            return

        print(f"\n找到 {len(updates)} 条更新\n")

        # 用于去重
        seen_chats = set()

        for update in updates:
            # 检查 channel_post（Channel 消息）
            if update.channel_post:
                chat = update.channel_post.chat
                chat_id = chat.id

                if chat_id not in seen_chats:
                    seen_chats.add(chat_id)
                    print("=" * 60)
                    print(f"📢 Channel 信息:")
                    print(f"   名称: {chat.title}")
                    print(f"   Chat ID: {chat_id}")
                    print(f"   用户名: @{chat.username}" if chat.username else "   用户名: (未设置)")
                    print(f"   类型: {chat.type}")
                    print("=" * 60)

            # 检查 message（可能是群组或私聊）
            elif update.message:
                chat = update.message.chat
                chat_id = chat.id

                if chat_id not in seen_chats:
                    seen_chats.add(chat_id)

                    if chat.type == "channel":
                        print("=" * 60)
                        print(f"📢 Channel 信息:")
                        print(f"   名称: {chat.title}")
                        print(f"   Chat ID: {chat_id}")
                        print(f"   用户名: @{chat.username}" if chat.username else "   用户名: (未设置)")
                        print("=" * 60)
                    elif chat.type in ["group", "supergroup"]:
                        print(f"\n👥 群组: {chat.title} (ID: {chat_id})")
                    elif chat.type == "private":
                        print(f"\n👤 私聊: {chat.first_name} (ID: {chat_id})")

        if not seen_chats:
            print("\n⚠️  没有找到 Channel 信息")
            print("\n请确保：")
            print("1. Bot 已被添加为 Channel 管理员")
            print("2. 在 Channel 中发送了至少一条消息")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("\n请检查：")
        print("1. TG_BOT_TOKEN 是否正确配置在 .env 文件中")
        print("2. Bot Token 是否有效")

async def test_send_message(chat_id: str):
    """测试发送消息到指定 Chat ID"""
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.send_message(
            chat_id=chat_id,
            text="🧪 <b>测试消息</b>\n\nBot 已成功连接到此 Channel！",
            parse_mode="HTML"
        )
        print(f"\n✅ 成功发送测试消息到 Chat ID: {chat_id}")
        return True
    except Exception as e:
        print(f"\n❌ 发送失败: {e}")
        return False

if __name__ == "__main__":
    # 设置 UTF-8 编码
    import sys
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    print("\nTelegram Channel ID 获取工具\n")

    if not BOT_TOKEN:
        print("错误: 未找到 TG_BOT_TOKEN")
        print("请在 .env 文件中配置 TG_BOT_TOKEN")
        exit(1)

    # 获取更新
    asyncio.run(get_updates())

    # 询问是否测试发送
    print("\n" + "=" * 60)
    test_chat_id = input("\n是否要测试发送消息？请输入 Chat ID (直接回车跳过): ").strip()

    if test_chat_id:
        asyncio.run(test_send_message(test_chat_id))

    print("\n完成！\n")
