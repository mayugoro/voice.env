import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pydub import AudioSegment
import subprocess

# Load BOT_TOKEN dari file .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Fungsi untuk memulai bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirimkan file audio atau video untuk saya konversi.")

# Fungsi untuk mengonversi file menjadi voice chat
async def convert_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = None
    ext = None
    wait_message = None

    # Cek jenis file (audio, voice, document, atau video)
    if update.message.audio:
        file = await update.message.audio.get_file()
        ext = "mp3"
        wait_message = await update.message.reply_text("⏳")
    elif update.message.voice:
        file = await update.message.voice.get_file()
        ext = "ogg"
        wait_message = await update.message.reply_text("⏳")
    elif update.message.document:
        file = await update.message.document.get_file()
        ext = update.message.document.file_name.split(".")[-1].lower()
        if ext == "mp3":
            wait_message = await update.message.reply_text("⏳")
    elif update.message.video:
        file = await update.message.video.get_file()
        ext = "mp4"
        wait_message = await update.message.reply_text("⏳")
    else:
        await update.message.reply_text("Kirim file audio atau video ya.")
        return

    input_path = f"{file.file_id}.{ext}"
    output_path = f"{file.file_id}.ogg"

    # Download file
    await file.download_to_drive(input_path)

    try:
        # Jika video, konversi ke audio dengan ffmpeg
        if ext == "mp4":
            audio_path = f"{file.file_id}.mp3"
            subprocess.run(['ffmpeg', '-i', input_path, audio_path])
            input_path = audio_path

        # Konversi file audio menjadi ogg
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(48000).set_channels(2)
        audio = audio.normalize()
        audio.export(output_path, format="ogg", codec="libopus", bitrate="128k")

        # Kirim voice chat
        with open(output_path, "rb") as voice:
            await update.message.reply_voice(voice=voice)

        # Hapus pesan "⏳" setelah selesai
        if wait_message:
            await wait_message.delete()

    except Exception as e:
        if wait_message:
            await wait_message.delete()
        await update.message.reply_text(f"Terjadi kesalahan saat konversi: {e}")

    finally:
        # Bersihkan file sementara (hapus setelah konversi selesai)
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# Fungsi utama untuk memulai bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL | filters.VIDEO, convert_to_voice))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
