import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
    'extract_flat': False
}

ffmpeg_options = {
    'options': '-vn'
}

queue = []

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def play(ctx, url: str):
    voice = ctx.author.voice
    if not voice:
        await ctx.send("Зайди в голосовой канал, бро.")
        return

    vc = await voice.channel.connect() if not ctx.voice_client else ctx.voice_client
    if vc.is_playing():
        queue.append(url)
        await ctx.send("Трек добавлен в очередь.")
        return

    await stream_song(vc, ctx, url)

async def stream_song(vc, ctx, url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        source = await discord.FFmpegOpusAudio.from_probe(info['url'], **ffmpeg_options)
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(vc, ctx), bot.loop))

    await ctx.send(f"Играет: {info.get('title')}")

async def play_next(vc, ctx):
    if queue:
        next_url = queue.pop(0)
        await stream_song(vc, ctx, next_url)
    else:
        await vc.disconnect()

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Пропущено.")
    else:
        await ctx.send("Ничего не играет.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Остановлено.")
    else:
        await ctx.send("Бот не в голосовом канале.")

@bot.command()
async def queue_list(ctx):
    if queue:
        await ctx.send("Очередь:
" + "
".join(queue))
    else:
        await ctx.send("Очередь пуста.")

bot.run(os.getenv("DISCORD_TOKEN"))