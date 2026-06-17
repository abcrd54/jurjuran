import os
import asyncio
import logging
import httpx
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_IDS = os.getenv("TELEGRAM_ADMIN_IDS", "").split(",")

user_state = {}


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Buat Video", callback_data="create")],
        [InlineKeyboardButton("📋 Template", callback_data="templates"),
         InlineKeyboardButton("📐 Aspect Ratio", callback_data="ratios")],
        [InlineKeyboardButton("🎤 Voice", callback_data="voices"),
         InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎬 *Shopee Video Generator Bot*\n\n"
        "Buat video promosi produk Shopee otomatis!\n\n"
        "Kirim link Shopee untuk mulai, atau gunakan tombol di bawah.",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Cara Penggunaan*\n\n"
        "1️⃣ Kirim link produk Shopee\n"
        "2️⃣ Pilih template (promo/review/unboxing/minimal)\n"
        "3️⃣ Pilih aspect ratio (9:16/1:1/16:9)\n"
        "4️⃣ Pilih suara (male/female)\n"
        "5️⃣ Tunggu proses selesai (1-2 menit)\n"
        "6️⃣ Video dikirim langsung!\n\n"
        "🎵 *Upload Musik*: Kirim file MP3 sebagai musik custom\n\n"
        "📌 *Commands*\n"
        "/start - Menu utama\n"
        "/help - Bantuan\n"
        "/status - Cek status proses\n"
        "/cancel - Batalkan proses"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "create":
        await query.edit_message_text(
            "Kirim link produk Shopee sekarang!\n\n"
            "Contoh: `https://s.shopee.co.id/xxx`",
            parse_mode="Markdown",
        )
        user_state[query.from_user.id] = {"step": "waiting_url"}

    elif query.data == "templates":
        text = (
            "📋 *Template Tersedia*\n\n"
            "1. *Promo* - Zoom dinamis, warna vivid\n"
            "2. *Review* - Zoom halus, warna natural\n"
            "3. *Unboxing* - Zoom cepat, warna vivid+\n"
            "4. *Minimal* - Zoom sangat halus, warna soft"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "ratios":
        text = (
            "📐 *Aspect Ratio*\n\n"
            "• `9:16` - Vertikal (Reels/TikTok/Shorts)\n"
            "• `1:1` - Kotak (Instagram Feed)\n"
            "• `16:9` - Landscape (YouTube)"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "voices":
        text = (
            "🎤 *Voice Options*\n\n"
            "• *ArdiNeural* - Suara pria Indonesia\n"
            "• *GadisNeural* - Suara wanita Indonesia"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "help":
        await help_cmd(update, context)

    elif query.data.startswith("tpl_"):
        template = query.data.replace("tpl_", "")
        uid = query.from_user.id
        if uid in user_state:
            user_state[uid]["template"] = template
            await _ask_ratio(query, uid)

    elif query.data.startswith("ratio_"):
        ratio = query.data.replace("ratio_", "")
        uid = query.from_user.id
        if uid in user_state:
            user_state[uid]["ratio"] = ratio
            await _ask_voice(query, uid)

    elif query.data.startswith("voice_"):
        voice = query.data.replace("voice_", "")
        uid = query.from_user.id
        if uid in user_state:
            user_state[uid]["voice"] = voice
            await _start_generation(query, uid, context)


async def _ask_ratio(query, uid):
    keyboard = [
        [InlineKeyboardButton("9:16 Vertikal", callback_data="ratio_9:16"),
         InlineKeyboardButton("1:1 Kotak", callback_data="ratio_1:1")],
        [InlineKeyboardButton("16:9 Landscape", callback_data="ratio_16:9")],
    ]
    await query.edit_message_text(
        "Pilih aspect ratio:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _ask_voice(query, uid):
    keyboard = [
        [InlineKeyboardButton("🎤 ArdiNeural (Pria)", callback_data="voice_id-ID-ArdiNeural"),
         InlineKeyboardButton("🎤 GadisNeural (Wanita)", callback_data="voice_id-ID-GadisNeural")],
    ]
    await query.edit_message_text(
        "Pilih suara dubbing:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _start_generation(query, uid, context):
    state = user_state.get(uid, {})
    url = state.get("url")
    template = state.get("template", "promo")
    ratio = state.get("ratio", "9:16")
    voice = state.get("voice", "id-ID-ArdiNeural")
    music_path = state.get("music_path")

    await query.edit_message_text(
        f"⏳ *Memproses video...*\n\n"
        f"🔗 Link: `{url[:50]}...`\n"
        f"📋 Template: {template}\n"
        f"📐 Ratio: {ratio}\n"
        f"🎤 Voice: {voice.split('-')[-1]}\n\n"
        f"Proses ini butuh 1-2 menit. Sabar ya!",
        parse_mode="Markdown",
    )

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            files = {}
            if music_path and Path(music_path).exists():
                files["music"] = (
                    Path(music_path).name,
                    open(music_path, "rb"),
                    "audio/mpeg",
                )

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🔄 Memproses video... Mohon tunggu 1-2 menit.",
            )

            resp = await client.post(
                f"{BACKEND_URL}/api/generate",
                data={
                    "shopee_url": url,
                    "voice": voice,
                    "template": template,
                    "aspect_ratio": ratio,
                },
                files=files if files else None,
            )

        if resp.status_code == 200:
            video_path = Path(f"temp/tg_{uid}_{datetime.now().strftime('%H%M%S')}.mp4")
            video_path.parent.mkdir(exist_ok=True)
            video_path.write_bytes(resp.content)
            size_mb = len(resp.content) / 1024 / 1024

            if size_mb > 50:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"⚠️ Video terlalu besar ({size_mb:.1f} MB). Telegram limit 50MB.\n\nVideo tersimpan di server.",
                )
            else:
                with open(video_path, "rb") as video_file:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=video_file,
                        caption=f"✅ Video selesai!\n\n📋 Template: {template}\n📐 Ratio: {ratio}\n💾 Size: {size_mb:.1f} MB",
                        read_timeout=120,
                        write_timeout=120,
                    )
            video_path.unlink(missing_ok=True)
        else:
            error = resp.text[:200]
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Gagal membuat video:\n`{error}`",
                parse_mode="Markdown",
            )

    except Exception as e:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ Error: {str(e)[:200]}",
        )

    finally:
        if music_path and Path(music_path).exists():
            Path(music_path).unlink(missing_ok=True)
        user_state.pop(uid, None)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    if "shopee" in text.lower() or "shp.ee" in text.lower():
        user_state[uid] = {"url": text, "step": "choose_template"}

        keyboard = [
            [InlineKeyboardButton("🎬 Promo", callback_data="tpl_promo"),
             InlineKeyboardButton("📝 Review", callback_data="tpl_review")],
            [InlineKeyboardButton("📦 Unboxing", callback_data="tpl_unboxing"),
             InlineKeyboardButton("✨ Minimal", callback_data="tpl_minimal")],
        ]
        await update.message.reply_text(
            f"✅ Link terdeteksi!\n\n`{text[:80]}`\n\nPilih template:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.message.reply_text(
            "Kirim link produk Shopee untuk membuat video!\n\n"
            "Contoh: `https://s.shopee.co.id/xxx`",
            parse_mode="Markdown",
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    doc = update.message.document

    if doc and doc.file_name.lower().endswith(".mp3"):
        file = await context.bot.get_file(doc.file_id)
        music_path = Path(f"uploads/tg_music_{uid}_{doc.file_name}")
        music_path.parent.mkdir(exist_ok=True)
        await file.download_to_drive(music_path)

        if uid in user_state:
            user_state[uid]["music_path"] = str(music_path)
            await update.message.reply_text(
                f"🎵 Musik berhasil diupload: `{doc.file_name}`\n\n"
                "Kirim link Shopee untuk mulai membuat video!",
                parse_mode="Markdown",
            )
        else:
            user_state[uid] = {"music_path": str(music_path)}
            await update.message.reply_text(
                f"🎵 Musik berhasil diupload: `{doc.file_name}`\n\n"
                "Sekarang kirim link produk Shopee!",
                parse_mode="Markdown",
            )
    else:
        await update.message.reply_text("Kirim file MP3 untuk musik custom!")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    state = user_state.get(uid)
    if state:
        await update.message.reply_text(
            f"📊 *Status Proses*\n\n"
            f"URL: `{state.get('url', '-')}`\n"
            f"Template: {state.get('template', '-')}\n"
            f"Ratio: {state.get('ratio', '-')}\n"
            f"Step: {state.get('step', '-')}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("Tidak ada proses yang berjalan.")


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    state = user_state.pop(uid, None)
    if state:
        music = state.get("music_path")
        if music and Path(music).exists():
            Path(music).unlink(missing_ok=True)
        await update.message.reply_text("✅ Proses dibatalkan.")
    else:
        await update.message.reply_text("Tidak ada proses yang perlu dibatalkan.")


def main():
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN belum di-set di .env file!")
        print("Buat bot di https://t.me/BotFather, lalu masukkan token ke .env")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
