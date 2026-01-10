"""
Telegram 通知机器人服务端 v2.0
支持 HTTP API 通知 + Critical 级别电话告警
"""

import os
import asyncio
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from twilio.rest import Client as TwilioClient
import uvicorn
import threading
import logging

# 加载 .env 文件
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# ========== 配置 ==========
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")
API_KEY = os.getenv("NOTIFY_API_KEY")
PORT = int(os.getenv("NOTIFY_PORT", 8000))

# Twilio 配置
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")  # 你的 Twilio 号码
PHONE_TO = os.getenv("PHONE_TO")  # 你的手机号（香港号码）

# 告警配置
CALL_DELAY_SECONDS = int(os.getenv("CALL_DELAY_SECONDS", 300))  # 默认 5 分钟

# TradingView Webhook Secret
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "tv_" + os.urandom(8).hex())

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Channel emoji 映射
CHANNEL_EMOJI = {
    "gold": "🥇",
    "wallet": "👛", 
    "price": "💰",
    "system": "⚙️",
    "alert": "🚨",
    "trade": "📈",
    "info": "ℹ️",
}

# 存储待确认的 critical 告警
# {alert_id: {"message": str, "time": float, "confirmed": bool, "call_task": Task}}
pending_alerts = {}

app = FastAPI(title="TG Notify Server v2.0")
bot = Bot(token=BOT_TOKEN)
twilio_client = None

if TWILIO_SID and TWILIO_TOKEN:
    twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
    logger.info("✓ Twilio 已配置")
else:
    logger.warning("⚠ Twilio 未配置，critical 告警将不会打电话")


class NotifyRequest(BaseModel):
    channel: str = "info"
    title: str
    message: str
    priority: str = "normal"  # normal / high / critical


def format_message(req: NotifyRequest, alert_id: str = None) -> str:
    """格式化消息"""
    emoji = CHANNEL_EMOJI.get(req.channel, "📢")
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    priority_mark = ""
    if req.priority == "high":
        priority_mark = "🔴 "
    elif req.priority == "critical":
        priority_mark = "🚨🚨🚨 CRITICAL 🚨🚨🚨\n"
    
    text = f"""{priority_mark}{emoji} <b>{req.title}</b>

{req.message}

<code>[{req.channel}] {timestamp}</code>"""
    
    if req.priority == "critical":
        delay_min = CALL_DELAY_SECONDS // 60
        text += f"\n\n⏰ <b>{delay_min} 分钟内未确认将自动拨打电话</b>"
    
    return text


def make_phone_call(message: str) -> bool:
    """拨打电话"""
    if not twilio_client or not TWILIO_FROM or not PHONE_TO:
        logger.error("Twilio 未正确配置，无法拨打电话")
        return False
    
    try:
        # TwiML: 语音播报两遍
        twiml = f'''<Response>
            <Say language="zh-CN">注意，紧急告警：{message}</Say>
            <Pause length="2"/>
            <Say language="zh-CN">重复一遍：{message}</Say>
            <Pause length="1"/>
            <Say language="zh-CN">请立即处理</Say>
        </Response>'''
        
        call = twilio_client.calls.create(
            to=PHONE_TO,
            from_=TWILIO_FROM,
            twiml=twiml
        )
        logger.info(f"📞 电话已拨出: {call.sid}")
        return True
    except Exception as e:
        logger.error(f"拨打电话失败: {e}")
        return False


async def delayed_call_check(alert_id: str, message: str):
    """延迟检查是否需要打电话"""
    await asyncio.sleep(CALL_DELAY_SECONDS)
    
    alert = pending_alerts.get(alert_id)
    if alert and not alert.get("confirmed"):
        logger.info(f"告警 {alert_id} 未确认，准备拨打电话...")
        
        # 发送即将打电话的通知
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text="📞 <b>即将拨打电话...</b>\n\n未在规定时间内确认告警",
                parse_mode="HTML"
            )
        except:
            pass
        
        # 打电话
        make_phone_call(message)
        
        # 清理
        pending_alerts.pop(alert_id, None)


async def handle_callback(update: Update, context):
    """处理 Telegram 按钮回调"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("ack_"):
        alert_id = data[4:]
        
        if alert_id in pending_alerts:
            pending_alerts[alert_id]["confirmed"] = True
            logger.info(f"✓ 告警 {alert_id} 已确认")
            
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("✅ <b>已确认收到，取消电话告警</b>", parse_mode="HTML")
            
            # 清理
            pending_alerts.pop(alert_id, None)
        else:
            await query.message.reply_text("⚠️ 该告警已过期或已处理")


@app.post("/notify")
async def notify(req: NotifyRequest, x_api_key: str = Header(None)):
    """接收通知并转发到 Telegram"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    alert_id = f"{int(time.time() * 1000)}"
    text = format_message(req, alert_id)
    
    try:
        if req.priority == "critical":
            # Critical: 带确认按钮 + 延迟打电话
            keyboard = [[InlineKeyboardButton("✅ 已收到，取消电话", callback_data=f"ack_{alert_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            msg = await bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            
            # 记录待确认告警
            pending_alerts[alert_id] = {
                "message": f"{req.title}: {req.message}",
                "time": time.time(),
                "confirmed": False
            }
            
            # 启动延迟检查任务
            asyncio.create_task(delayed_call_check(alert_id, f"{req.title}: {req.message}"))
            
            logger.info(f"🚨 Critical 告警已发送: {alert_id}")
            return {"status": "ok", "alert_id": alert_id, "message": "Critical notification sent, phone call scheduled"}
        
        else:
            # Normal/High: 普通发送
            await bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="HTML"
            )
            return {"status": "ok", "message": "Notification sent"}
            
    except Exception as e:
        logger.error(f"发送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/call")
async def direct_call(x_api_key: str = Header(None), message: str = "紧急告警，请查看"):
    """直接拨打电话（跳过 TG 确认）"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    success = make_phone_call(message)
    if success:
        return {"status": "ok", "message": "Phone call initiated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to make call")


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "twilio_configured": twilio_client is not None,
        "pending_alerts": len(pending_alerts)
    }


@app.get("/test")
async def test_notification():
    """测试接口（无需认证）- 仅用于快速测试"""
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🧪 <b>测试消息</b>\n\n服务运行正常！",
            parse_mode="HTML"
        )
        return {"status": "ok", "message": "Test notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== TradingView Webhook ==========
import json

@app.post("/webhook/{secret}")
async def tradingview_webhook(secret: str, request: Request):
    """
    TradingView Webhook 端点
    兼容 JSON 和纯文本格式
    """
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    # 读取原始 body
    body = await request.body()
    body_str = body.decode('utf-8').strip()
    
    # 尝试解析 JSON，失败则当纯文本
    title = "TradingView Alert"
    message = body_str
    channel = "trade"
    priority = "normal"
    
    try:
        data = json.loads(body_str)
        if isinstance(data, dict):
            title = data.get("title", title)
            message = data.get("message", body_str)
            channel = data.get("channel", channel)
            priority = data.get("priority", priority)
    except json.JSONDecodeError:
        # 不是 JSON，直接用原始文本作为 message
        pass
    
    # 格式化消息
    emoji = CHANNEL_EMOJI.get(channel, "📈")
    timestamp = datetime.now().strftime("%H:%M:%S")
    priority_mark = "🔴 " if priority == "high" else ""
    
    text = f"""{priority_mark}{emoji} <b>{title}</b>

{message}

<code>[{channel}] {timestamp}</code>"""
    
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="HTML"
        )
        logger.info(f"📈 TradingView webhook: {title}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook 发送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Telegram Bot 轮询处理（用于接收按钮回调）
def run_telegram_polling():
    """在单独线程运行 Telegram 轮询"""
    async def start_polling():
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        logger.info("🤖 Telegram Bot 轮询启动...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_polling())


if __name__ == "__main__":
    # 设置 UTF-8 编码（Windows 兼容）
    import sys
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    if not BOT_TOKEN or not CHAT_ID:
        print("错误: 请先配置 .env 文件")
        print("   复制 .env.example 为 .env 并填写配置")
        exit(1)

    print("=" * 60)
    print("  TG Notify Server v2.0 - 支持电话告警")
    print("=" * 60)
    print(f"  Bot Token: {BOT_TOKEN[:20]}...")
    print(f"  Chat ID: {CHAT_ID}")
    print(f"  端口: {PORT}")
    print(f"  Twilio: {'已配置' if twilio_client else '未配置'}")
    print(f"  电话延迟: {CALL_DELAY_SECONDS} 秒")
    print("-" * 60)
    print(f"  TradingView Webhook:")
    print(f"     http://81.92.219.140/webhook/{WEBHOOK_SECRET}")
    print("=" * 60)
    
    # 启动 Telegram 轮询线程（用于接收按钮回调）
    telegram_thread = threading.Thread(target=run_telegram_polling, daemon=True)
    telegram_thread.start()
    
    # 启动 FastAPI
    uvicorn.run(app, host="0.0.0.0", port=PORT)