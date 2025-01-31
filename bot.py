import discord
from discord.ext import commands
import yt_dlp
import asyncio
import json

"""
* El 'ctx' es el context. Al context bàsicament ve el canal on s'ha llançat la comanda, l'autor de la comanda, el nom del servidor, etc...
"""

# Read the token
with open("config.json", "r") as file:
    config = json.load(file)

TOKEN = config["DISCORD_TOKEN"]

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=">", intents=intents)

# Music queues
queues = {}

def get_queue(guild_id):
    """Obtiene la cola de reproducción de un servidor"""
    return queues.setdefault(guild_id, [])

def add_to_queue(guild_id, url):
    """Añade una canción a la cola"""
    get_queue(guild_id).append(url)

async def play_next(ctx):
    """Reproduce la siguiente canción en la cola"""
    queue = get_queue(ctx.guild.id)
    if queue:
        url = queue.pop(0)
        await play_music(ctx, url)

async def play_music(ctx, url):
    """Función principal para reproducir música"""
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # If the bot is not connected into any voicechannel, it joins the author's channel
    if not voice_client: 
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()

    ydl_opts = {'format': 'bestaudio'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False) # Extraiem informació només de la URL i no ho descarreguem
        audio_url = info['url']

    ffmpeg_options = {'options': '-vn'} # Amb '-vn' no processem el video, només l'audio
    # Amb això 'discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)' convertim un arxiu d'audio (en aquest cas la direcció es una URL que apunta a youtube) a algo que es pugui reproduir a discord.
    # ho fem amb les especificacions de que no s'ha de descarregar
    voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

    await ctx.send(f"Reproduint: {info['title']}")

@bot.command()
async def join(ctx):
    """Comando para que el bot se una a un canal de voz"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("*V* Conectado al canal de voz")
    else:
        await ctx.send("*X* Debes estar en un canal de voz")

@bot.command()
async def play(ctx, url: str):
    """Comando para reproducir música"""
    add_to_queue(ctx.guild.id, url)
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    # Si el bot no esta connectat a cap canal o, si està connectat pero no reproduint cap canço, llavors es reprodueix la següent.
    if not voice_client or not voice_client.is_playing(): 
        await play_next(ctx)
    else:
        await ctx.send("🎵 Canción añadida a la cola")

@bot.command()
async def stop(ctx):
    """Detiene la reproducción y desconecta el bot"""
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("🛑 Desconectado del canal de voz")
    else:
        await ctx.send("❌ No estoy en un canal de voz")

@bot.command()
async def skip(ctx):
    """Salta la canción actual y reproduce la siguiente en la cola"""
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await play_next(ctx)
        await ctx.send("⏭️ Saltando a la siguiente canción")
    else:
        await ctx.send("❌ No hay canciones en reproducción")

@bot.command()
async def queue(ctx):

    actual_queue = get_queue(ctx.guild.id)
    if len(actual_queue) == 0:
        await ctx.send("Llista buida")
    else:
        await ctx.send(actual_queue)

    """
    if len(actual_queue) == 0:
        ctx.send("Cua buida.")
    else:
        show_queue = []
        for link in actual_queue:
            ydl_opts = {'format': 'bestaudio'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            show_queue.append(info['title'])
        await ctx.send(show_queue)
    """

try:
    bot.run(TOKEN)
except Exception as error:
    print("TENIM UN ERROR:", error)

