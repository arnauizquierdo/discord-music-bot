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

# Diccionari de cues per a tots els servidors
queues = {}

# Obtenim la cua d'un servidor en concret
def get_queue(guild_id):
    return queues.setdefault(guild_id, []) # Retornem la cua del servidor de queues, i si no existeix creem un element (tipus llista) al diccionari amb l'id del servidor i ho retornem

# Afegim una URL a la cua del servidor que tenim a queues
def add_to_queue(guild_id, url):
    get_queue(guild_id).append(url)


# 1. Creem 'queue' que es la cua del servidor actual
# 2. Mirem si esta buida i creem 'url' quedant-nos amb el primer element de la cua 'queue'
# 3. Amb un await, reproduim aquesta 'url' (canço)
async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if queue:
        url = queue.pop(0)
        await play_music(ctx, url)
    else:
        await stop(ctx)



async def play_music(ctx, url):
    # Obtenim 'voice_client' que es la instancia de veu que fa servir el bot per 'parlar'
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # Si el bot no te instancia de veu (o sigui que no esta connectat a cap canal), es connectarà al canal de la persona que l'ha cridat (al 'autor') 
    if not voice_client: 
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()

    if '/playlist?list=' in url:
        await ctx.send("```No pots reproduir llistes de reproducció```")
        await play_next(ctx)
        return 0

    ydl_opts = {'format': 'bestaudio', 'noplaylist': True, 'cookiefile': config["COOKIES_YOUTUBE"]}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False) # Extraiem informació (format diccionari) només de la URL i no ho descarreguem
            audio_url = info['url']
        except Exception as e:
            await ctx.send(f"```Error obtenint l'àudio: {e}```")
            return 1

    if info.get('extractor') != 'youtube':
        await ctx.send(f"```No pots reproduir '{info['title']}'! Només es poden reproduir cançons de Youtube.```")
        voice_client.pause()
        await play_next(ctx)
        return 0

    #-reconnect_delay_max 5 -reconnect_streamed 1 --> AMB L'OPCIÓ 'before_options': '-reconnect 1' S'HA ACONSEGUIT QUE LES CANÇONS NO ES PARIN A LA MEITAT
    ffmpeg_options = {'options': '-vn', 'before_options': '-reconnect 1'} # Amb '-vn' no processem el video, només l'audio
    # Amb això 'discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)' convertim un arxiu d'audio (en aquest cas la direcció es una URL que apunta a youtube) a algo que es pugui reproduir a discord.
    # ho fem amb les especificacions de que no s'ha de descarregar
    voice_client.play(discord.FFmpegOpusAudio(audio_url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop) if not voice_client.is_paused() else  None)

    await ctx.send(f"```Reproduint: {info['title']}```")

# Comanda perque el bot entri al canal de veu de l'autor del missatge (pot passar que s'hagi quedat en un altre canal de veu reproduint una musica i tu el vulguis en l'actual)
@bot.command()
async def join(ctx):
    
    if ctx.author.voice:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        channel = ctx.author.voice.channel
        
        if not voice_client:
            await channel.connect()
            return 0

        if voice_client.channel == channel: # Si el canal es el mateix
            await ctx.send("```Ja estic al canal " + str(voice_client.channel) + ".```")
            return
        await voice_client.move_to(channel, timeout=4.0)

    else:
        await ctx.send("```Has d'estar en un canal de veu```")

@bot.command()
async def play(ctx, url: str):

    if not ctx.author.voice: # Si l'autor de la crida no esta a cap canal...
        await ctx.send("```Error! Primer has d'estar en un canal de veu.```")
        return 0

    add_to_queue(ctx.guild.id, url)
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    # Si el bot no esta connectat a cap canal o, si està connectat pero no reproduint cap canço, llavors es reprodueix la següent.
    if not voice_client or not voice_client.is_playing(): 
        await play_next(ctx)
    else:
        await ctx.send("```Cançó afegida a la cua.```")

@bot.command()
async def stop(ctx):
    
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        get_queue(ctx.guild.id).clear()
        try:
            await ctx.send("```Sortint del canal de veu " + str(voice_client.channel) + "```")
            await voice_client.disconnect()
        except Exception as e:
            await ctx.send(f"```Error durant la desconnexió: {e}```")
            return 1
    else:
        await ctx.send("```No estic a cap canal de veu```")

@bot.command()
async def skip(ctx):
    #"""Salta la canción actual y reproduce la siguiente en la cola"""
    if len(get_queue(ctx.guild.id)) == 0:
        await ctx.send("```No hi han més cançons a la cua.```")
        return 0
    
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("```Saltant de cançó.```")
        await play_next(ctx)       

bot.remove_command("help")

@bot.command()
async def help(ctx):
    await ctx.send("```\n=====================================\n Bot per reproduïr musica de Youtube\n=====================================\n\nLlistat de comandes:\n\n>play [link]: Escoltar musica (de Youtube).\n\n>stop:  Surt del canal i elimina la cua existent.\n\n>skip:  Reprodueix la següent cançó de la cua.\n\n>queue: Mostra els links de la cua.\n\n>join:  Entra al teu canal de veu i elimina la cua.```")


@bot.command()
async def queue(ctx):

    actual_queue = get_queue(ctx.guild.id)
    if len(actual_queue) == 0:
        await ctx.send("```Llista buida```")
    else:
        llista = "```Cua de cançons:\n\n"
        for i in range(len(actual_queue)):
            llista = llista + str(i+1) + ". " + actual_queue[i] + "\n"
        llista = llista + "```"
        await ctx.send(llista)

try:
    bot.run(TOKEN)
except Exception as error:
    print("TENIM UN ERROR:", error)

