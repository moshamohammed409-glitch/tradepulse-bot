import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8791427947:AAGCEUPqmYMRo60hTMYEqyJCedL9c3sxQqs"

logging.basicConfig(level=logging.INFO)

COINS = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
         "ADAUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]

def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=5).json()
        price = float(r['lastPrice'])
        change = float(r['priceChangePercent'])
        volume = float(r['quoteVolume'])
        return price, change, volume
    except:
        return None, None, None

def get_rsi(symbol, interval="4h", period=14):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        candles = requests.get(url, timeout=5).json()
        closes = [float(c[4]) for c in candles]
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 سكانر السوق", callback_data="scanner")],
        [InlineKeyboardButton("📈 تحليل BTC", callback_data="analyze_BTCUSDT")],
        [InlineKeyboardButton("📈 تحليل ETH", callback_data="analyze_ETHUSDT")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *TradePulse — بوت التحليل المؤسسي*\n\nاختر ما تريد:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "scanner":
        await query.edit_message_text("⏳ جاري فحص السوق...")
        msg = "📡 *سكانر السوق — RSI 4H*\n\n"
        for coin in COINS:
            price, change, vol = get_price(coin)
            rsi = get_rsi(coin)
            if price is None:
                continue
            arrow = "🟢" if change > 0 else "🔴"
            signal = ""
            if rsi and rsi < 35:
                signal = "⚡ تشبع بيع"
            elif rsi and rsi > 70:
                signal = "⚠️ تشبع شراء"
            name = coin.replace("USDT","")
            msg += f"{arrow} *{name}*: ${price:,.4f} ({change:+.2f}%)\n"
            msg += f"   RSI: {rsi} {signal}\n\n"
        keyboard = [[InlineKeyboardButton("🔄 تحديث", callback_data="scanner"),
                     InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]
        await query.edit_message_text(msg, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "home":
        keyboard = [
            [InlineKeyboardButton("📊 سكانر السوق", callback_data="scanner")],
            [InlineKeyboardButton("📈 تحليل BTC", callback_data="analyze_BTCUSDT")],
            [InlineKeyboardButton("📈 تحليل ETH", callback_data="analyze_ETHUSDT")],
        ]
        await query.edit_message_text("🤖 *TradePulse*\n\nاختر ما تريد:",
                                       reply_markup=InlineKeyboardMarkup(keyboard),
                                       parse_mode="Markdown")

    elif data.startswith("analyze_"):
        symbol = data.replace("analyze_", "")
        await query.edit_message_text("⏳ جاري التحليل...")
        price, change, vol = get_price(symbol)
        rsi_4h = get_rsi(symbol, "4h")
        rsi_1h = get_rsi(symbol, "1h")
        rsi_1d = get_rsi(symbol, "1d")
        name = symbol.replace("USDT","")

        trend = "🟢 صاعد" if change > 0 else "🔴 هابط"
        rsi_signal = ""
        if rsi_4h:
            if rsi_4h < 35: rsi_signal = "⚡ تشبع بيع"
            elif rsi_4h > 70: rsi_signal = "⚠️ تشبع شراء"
            else: rsi_signal = "➡️ محايد"

        msg = f"""📊 *تحليل {name}/USDT*

💵 السعر: `${price:,.4f}`
📉 التغير 24H: `{change:+.2f}%`
📦 الحجم: `${vol:,.0f}`

📈 *RSI متعدد الأطر:*
• 1H: `{rsi_1h}`
• 4H: `{rsi_4h}` — {rsi_signal}
• 1D: `{rsi_1d}`

🔄 الاتجاه: {trend}

⚠️ _هذا تحليل تقني مبسط وليس نصيحة استثمارية_"""

        keyboard = [[InlineKeyboardButton("🔄 تحديث", callback_data=data),
                     InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]
        await query.edit_message_text(msg, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ البوت شغال!")
    app.run_polling()

if __name__ == "__main__":
    main()
