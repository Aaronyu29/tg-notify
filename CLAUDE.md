# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TG Notify is a Telegram notification service with multi-level alerting and phone call escalation. It consists of:
- **Notification Server** (`server.py`) - FastAPI server that sends Telegram messages and makes phone calls via Twilio
- **Client SDK** (`notify_client.py`) -  module for sending notifications from monitoring scripts
- **Real-time Monitor** (`monitor/realtime_monitor_v2.py`) - Cryptocurrency price monitoring system using Binance WebSocket

## Architecture

### Core Components

1. **Server (`server.py`)**
   - FastAPI HTTP server with Telegram Bot integration
   - Handles three priority levels: normal, high, critical
   - Critical alerts trigger phone calls via Twilio if not acknowledged within configurable timeout (default 5 minutes)
   - Uses inline keyboard buttons for alert acknowledgment
   - Runs Telegram bot polling in separate thread for callback handling

2. **Client SDK (`notify_client.py`)**
   - Simple import-based notification API
   - Functions: `notify()`, `notify_critical()`, `call_now()`, convenience wrappers
   - Auto-loads `.env` configuration
   - Communicates with server via HTTP API with API key authentication

3. **Monitor System (`monitor/`)**
   - **`realtime_monitor_v2.py`** - Main monitoring script using WebSocket for real-time price data
   - **`monitor_config.py`** - Configuration file for alert rules (thresholds, time windows, priorities)
   - **`alert_generator.py`** - Rule-based alert generation framework
   - **`coingecko_client.py`** - CoinGecko API client for market cap/FDV data with caching
   - **`logger.py`** - Rotating log system with 24-hour retention
   - **`chinese_converter.py`** - Number-to-Chinese conversion for alerts

### Data Flow

```
Monitor Script → WebSocket (Binance) → Price Analysis → Alert Rules → alert_generator.py → FWAlert Webhook
                                                                    ↓
User Script → notify_client.py → HTTP API → server.py → Telegram Bot → User
                                                       ↓
                                          (if critical + not acknowledged)
                                                       ↓
                                                  Twilio Phone Call
```

## Development Commands

### Setup and Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
# - TG_BOT_TOKEN, TG_CHAT_ID (required)
# - NOTIFY_API_KEY (required, custom secret)
# - TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PHONE_TO (optional, for phone alerts)
# - FWALERT_URL (optional, for monitor alerts)
```

### Running Services

```bash
# Start notification server (runs on port 8000 by default)
python server.py

# Start cryptocurrency monitor (in separate terminal)
cd monitor
python realtime_monitor_v2.py
# Or on Windows: double-click start_monitor.bat

# Test notification client
python notify_client.py
```

### Testing

```bash
# Quick notification test
python test_alert_quick.py

# Comprehensive alert testing
python test_alert.py

# Test Chinese message formatting
python test_chinese_message.py

# Test server health (no auth required)
curl http://localhost:8000/health

# Test notification endpoint
curl -X POST http://localhost:8000/test
```

### Monitor Configuration

Edit `monitor/monitor_config.py` to customize:
- `SAMPLE_INTERVAL` - Price sampling interval in seconds (default: 30)
- `ALERT_COOLDOWN` - Cooldown between alerts for same symbol in seconds (default: 60)
- `ALERT_RULES` - List of alert rules with:
  - `window_minutes` - Time window for price change calculation (supports decimals, e.g., 0.5 = 30 seconds)
  - `threshold` - Percentage change threshold
  - `direction` - "up" or "down"
  - `priority` - "normal", "high", or "critical"

### Logs

```bash
# View monitor logs (24-hour retention)
notepad monitor\logs\monitor.log

# View logs with utility script
python view_logs.py
```

## Key Technical Details

### Alert Priority Levels

- **normal** - Standard Telegram message
- **high** - Telegram message with 🔴 red dot indicator
- **critical** - Telegram message with acknowledgment button + scheduled phone call if not acknowledged

### Monitor System

- Uses Binance WebSocket (`wss://fstream.binance.com/ws/!miniTicker@arr`) for real-time USDT perpetual futures prices
- Maintains rolling price history using `deque` with configurable depth based on largest time window
- Calculates percentage changes over multiple time windows simultaneously
- Implements per-symbol, per-rule cooldown to prevent alert spam
- Displays top N gainers/losers in console output
- Integrates CoinGecko API for market cap and FDV data (with 5-minute cache and rate limiting)

### Message Formatting

- Channel-based emoji mapping (price 💰, wallet 👛, trade 📈, alert 🚨, system ⚙️, info ℹ️)
- HTML formatting for Telegram messages
- Chinese number conversion for alert messages (e.g., "正百分之十五点三二")
- Timestamp included in all messages

### API Authentication

All API endpoints (except `/health` and `/test`) require `X-API-Key` header matching `NOTIFY_API_KEY` from `.env`.

### Phone Call System

- Uses Twilio TwiML for voice synthesis
- Speaks alert message twice in Chinese (`zh-CN`)
- Triggered automatically for critical alerts after timeout
- Can be triggered immediately via `/call` endpoint

## Configuration Files

- `.env` - Environment variables (credentials, API keys, phone numbers)
- `monitor/monitor_config.py` - Alert rules and monitoring parameters
- `monitor/.env` - Monitor-specific environment (FWALERT_URL)

## Important Notes

- Server must be running before using client SDK or monitor
- Monitor requires active internet connection for WebSocket and API calls
- Twilio configuration is optional; system works without phone alerts
- Monitor logs rotate automatically, keeping last 24 hours
- CoinGecko free tier has rate limits (~30 requests/minute); client implements 2-second minimum interval
- Symbol mapping for CoinGecko is maintained in `coingecko_client.py` and cached in `coingecko_symbol_cache.json`

## Development Guidelines

### Configuration File Protection

**CRITICAL: Any modifications to `settings.json` or `.claude/settings.local.json` REQUIRE explicit user approval before making changes.**

- **NEVER** modify these files without asking the user first
- **ALWAYS** explain what changes you plan to make and why
- **WAIT** for explicit confirmation ("yes", "confirm", "proceed") before editing
- This applies to:
  - Adding new settings
  - Modifying existing values
  - Removing settings
  - Reformatting the file

Example workflow:
1. Identify need to change settings
2. Explain proposed changes to user
3. Wait for approval
4. Only then make the changes
