import asyncio
import calendar
import os
import random
import re
import time

import discord
import dotenv
import emoji
import youtube_dl
from discord import Option
from discord.ext import commands

dotenv.load_dotenv()
token = os.getenv("TOKEN")

urls = [
    "https://youtu.be/_DYAnU3H7RI",
    "https://youtu.be/HFT4mQwat_4",
    "https://youtu.be/ESe5OWELD2I",
    "https://youtu.be/45V-QQe2a8Y",
    "https://youtu.be/uhs75RvA8S0",
    "https://youtu.be/XdvOIQ3_irk",
    "https://youtu.be/1k9MqmB4wO0"
]

assignable_roles = {
    ":video_game:": {
        "name": "Game Designer",
        "id": 500853492982874112,
    }, ":world_map:": {
        "name": "Level/Map Designer",
        "id": 513840484175708160,
    }, ":radio_button:": {
        "name": "UI/UX Designer",
        "id": 514648534939598916,
    }, ":writing_hand:": {
        "name": "Writer",
        "id": 514990466652176384,
    }, ":desktop_computer:": {
        "name": "Programmer",
        "id": 500349141004582922,
    }, ":person_walking:": {
        "name": "Animator",
        "id": 514646088603664384,
    }, ":ice:": {
        "name": "3D Modeler",
        "id": 503300166921748480,
    }, ":artist_palette:": {
        "name": "2D Artist",
        "id": 500842841984073758,
    }, ":musical_note:": {
        "name": "Composer",
        "id": 500853537014546453,
    }, ":speaker_high_volume:": {
        "name": "Audio Engineer",
        "id": 532531272723988490,
    }, ":hammer_and_pick:": {
        "name": "Gamer/Tester",
        "id": 516128704993296385,
    }, ":partying_face:": {
        "name": "Giveaways",
        "id": 1029687775135547453,
    }
}
just_chillin_role = 507517011879002112
giveaways_role = 1029687775135547453

giveaways = {}

music_messages = []
giveaway_messages = []

bot_channel = 776539733660139542
admin_channel = 776539589111840779
giveaways_channel = 776506419150454784
chat_channel = 500124505595838475
welcome_channel = 696414232261951508
music_channel = 684128787180552205

server = 500124505021349911

bot_id = 516792910990016515

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


bot = commands.Bot(intents=discord.Intents.all())


@bot.slash_command(name="help", description="Get help for using the bot.")
async def _help(ctx):
    description = '''
A bot created by <@496392770374860811> for his server.

• Add roles to yourself in <#%s>
• Join the <#684128787180552205> voice chat to listen to lofi beats while programming and studying.
• Look out for giveaways in <#%s>

/links | Lists important links
/help | Displays this message
''' % (welcome_channel, giveaways_channel)

    embed = create_embed(title="CGPrograms Bot Help", description=description, color=discord.Color.green(),
                         image="https://www.cgprograms.com/images/logo.png", url="https://www.cgprograms.com",
                         footer="© CompuGenius Programs. All rights reserved.")
    await ctx.respond(embed=embed)


@bot.slash_command(name="links", description="List important CompuGenius Programs links.")
async def links(ctx):
    description = '''
__CompuGenius Programs__
**Website:** *<https://www.cgprograms.com>*
**Discord:** *<https://discord.gg/4gc5fQf>*
**Twitter:** *<https://twitter.com/CompuGeniusCode>*

__Scifyre League__
**Website:** https://scifyre.cgprograms.com
**Steam:** *<https://store.steampowered.com/app/1313660>*
**Discord:** *<https://discord.gg/pPRdKWUu69>*
**Twitter:** *<https://twitter.com/ScifyreLeague>*
'''

    embed = create_embed(title="CompuGenius Programs", description=description, color=discord.Color.purple(),
                         footer="© CompuGenius Programs. All rights reserved.",
                         image="https://www.cgprograms.com/images/logo.png", url="https://www.cgprograms.com",
                         author="Important CompuGenius Programs Links")

    await ctx.respond(embed=embed)


@bot.slash_command()
async def send_roles(ctx):
    display_roles = []

    for role in assignable_roles:
        display_roles.append("%s    -   %s" % (emoji.emojize(role), assignable_roles[role]["name"]))

    description = '''
Click the reactions below corresponding to the roles you want.

%s
    ''' % '\n'.join(display_roles)

    embed = create_embed(title="Add roles", description=description, color=discord.Color.blurple(),
                         footer="© CompuGenius Programs. All rights reserved.")
    msg = await bot.get_channel(welcome_channel).send(embed=embed)

    for role in assignable_roles:
        await msg.add_reaction(emoji.emojize(role))


async def add_roles(emoji_name, user):
    role_name = assignable_roles[emoji_name]["name"]
    role = discord.utils.get(bot.get_guild(server).roles, name=role_name)
    just_chillin = discord.utils.get(bot.get_guild(server).roles, id=just_chillin_role)

    if role in user.roles:
        await user.send("You already have the %s role." % role.name)
    else:
        await user.add_roles(role, reason="User assigned role to themselves.")
        await user.send("The %s role was successfully assigned to you." % role.name)

    if just_chillin in user.roles and len(user.roles) >= 2:
        await user.remove_roles(just_chillin, reason="User has a self-assigned role.")


async def remove_roles(emoji_name, user):
    role_name = assignable_roles[emoji_name]["name"]
    role = discord.utils.get(bot.get_guild(server).roles, name=role_name)
    just_chillin = discord.utils.get(bot.get_guild(server).roles, id=just_chillin_role)

    await user.remove_roles(role, reason="User removed role from themselves.")
    await user.send("The %s role was successfully removed from you." % role.name)

    if just_chillin not in user.roles and len(user.roles) <= 1:
        await user.add_roles(just_chillin, reason="User has no self-assigned roles.")


@bot.slash_command(name="giveaway", description="Start a giveaway!")
async def giveaway(ctx, prize: Option(str), winners: Option(int, required=True), duration: Option(str, required=True),
                   url: Option(str) = "", image: Option(str) = ""):
    if discord.utils.get(bot.get_guild(server).roles, name="Admin") in ctx.author.roles:
        winners = int(winners)
        if winners > 1:
            description = '''
Click the :tada: to be entered into a giveaway!
There are %d winners!
''' % winners
        elif winners == 1:
            description = '''
Click the :tada: to be entered into a giveaway!
There is %d winner!
''' % winners
        else:
            await ctx.send(content="ERROR! Must have at least 1 winner!")
            return

        days, hours, minutes = [int(x) if x else 0 for x in re.match('(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?',
                                                                     duration).groups()]

        epoch_time = calendar.timegm(time.gmtime())

        duration_in_seconds = (int(days) * 24 * 60 * 60) + (int(hours) * 60 * 60) + (int(minutes) * 60)

        if duration_in_seconds < 60:
            await ctx.send(content="ERROR! Must be at least a minute long!")
            return

        giveaway_ends_in_seconds = epoch_time + duration_in_seconds

        description += "\nGiveaway ends: <t:%s>" % giveaway_ends_in_seconds

        footer = "Best of luck to all the participants!"

        url = url if url else ""
        image = image if image else ""

        if url != "":
            prize = "%s\n[Click to Open Prize Page]" % prize
        author = emoji.emojize(":partying_face: GIVEAWAY :partying_face:")

        embed = create_embed(title=prize, description=description, color=discord.Color.green(), footer=footer,
                             image=image, url=url, author=author)

        await ctx.respond("Giveaway Started Successfully", ephemeral=True)
        message = await ctx.send("<@&%s> (Add or Remove role in <#%s>): New Giveaway!" %
                                 (giveaways_role, welcome_channel), embed=embed)
        await message.add_reaction("🎉")

        giveaway_messages.append(message.id)

        giveaways[prize] = []
        await countdown_giveaway(time_in_seconds=duration_in_seconds, giveaway_message=message, prize=prize, url=url,
                                 winners_amount=winners)
    else:
        await ctx.send(content="You do not have permission to create a giveaway!")


async def countdown_giveaway(time_in_seconds, giveaway_message, prize, url, winners_amount):
    await asyncio.sleep(time_in_seconds)

    winner_ids = []
    giveaway_members = giveaways[prize]
    if winners_amount >= len(giveaway_members):
        for winner in giveaway_members:
            winner_ids.append(winner)
    else:
        for winner in range(winners_amount):
            winner_id = await get_new_winner(giveaway_members, winner_ids)
            winner_ids.append(winner_id)

    winners = []
    for winner_id in winner_ids:
        winners.append("<@%s>" % winner_id)

    description = '''
The giveaway is over!
Congrats to the winners:
%s
''' % ('\n'.join(winners))

    author = emoji.emojize(":alarm_clock: GIVEAWAY OVER :alarm_clock:")

    embed = create_embed(title=prize, description=description, color=discord.Color.red(),
                         footer="Thanks to all who entered and didn't win. Better luck next time!", url=url,
                         author=author)
    await giveaway_message.edit("%s - You won!" % ', '.join(winners), embed=embed)

    giveaway_messages.remove(giveaway_message.id)


async def get_new_winner(giveaway_members, winner_ids):
    winner_id = random.choice(giveaway_members)
    not_new_winner = winner_id in winner_ids
    while not_new_winner:
        return await get_new_winner(giveaway_members, winner_ids)
    return winner_id


async def play():
    player, url = await get_url()

    voice_client = discord.utils.get(bot.voice_clients, guild=bot.get_guild(server))

    if voice_client and not voice_client.is_playing() and voice_client.is_connected():
        for message in music_messages:
            await message.delete()
            music_messages.remove(message)

        async with bot.get_channel(bot_channel).typing():
            voice_client.play(player, after=lambda e: bot.loop.create_task(play()))
        msg = await bot.get_channel(bot_channel).send("**Playing now:** *%s*" % url)
        music_messages.append(msg)


async def get_url():
    url = random.choice(urls)
    try:
        player = await YTDLSource.from_url(url)
        return player, url
    except youtube_dl.utils.DownloadError or youtube_dl.utils.ExtractorError:
        urls.remove(url)
        await bot.get_channel(admin_channel).send("**<@496392770374860811> BAD MUSIC URL:** *%s*" % url)
        return await get_url()


def create_embed(title, description, color, footer, image="", *, url="", author=""):
    embed = discord.Embed(title=title, description=description, url=url, color=color)
    embed.set_footer(text=footer)
    embed.set_thumbnail(url=image)
    embed.url = url
    embed.set_author(name=author)
    return embed


@bot.event
async def on_raw_reaction_add(payload):
    emoji_name = emoji.demojize(payload.emoji.name)
    channel = bot.get_channel(payload.channel_id)
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not user == bot.user:
        message = await channel.fetch_message(payload.message_id)
        if message.id in giveaway_messages:
            if emoji_name == ":party_popper:":
                giveaway_members = giveaways[message.embeds[0].title]
                giveaway_members.append(user.id)

        elif message.channel == bot.get_channel(welcome_channel) and message.author == bot.user:
            if emoji_name in assignable_roles:
                await add_roles(emoji_name, user)


@bot.event
async def on_raw_reaction_remove(payload):
    emoji_name = emoji.demojize(payload.emoji.name)
    channel = bot.get_channel(payload.channel_id)
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not user == bot.user:
        message = await channel.fetch_message(payload.message_id)
        if message.id in giveaway_messages:
            if emoji_name == ":party_popper:":
                giveaway_members = giveaways[message.embeds[0].title]
                giveaway_members.remove(user.id)

        elif message.channel == bot.get_channel(welcome_channel) and message.author == bot.user:
            if emoji_name in assignable_roles:
                await remove_roles(emoji_name, user)


@bot.event
async def on_voice_state_update(member, before, after):
    music_voice_channel = bot.get_channel(music_channel)
    voice_client = discord.utils.get(bot.voice_clients, guild=bot.get_guild(server))
    if member.id != bot_id and after.channel == music_voice_channel and before.channel != music_voice_channel:
        if voice_client is None:
            await music_voice_channel.connect()

        await play()

    if len(music_voice_channel.members) <= 1:
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            for message in music_messages:
                await message.delete()
                music_messages.remove(message)


@bot.event
async def on_member_join(member):
    description = '''
Welcome %s to the %s server!
Please make sure to check out <#%d>.
Enjoy your stay!
''' % (member.mention, bot.get_guild(server).name, welcome_channel)

    embed = create_embed(title="Welcome %s!" % member.display_name, description=description, color=discord.Color.blue(),
                         footer="© CompuGenius Programs. All rights reserved.", image=member.avatar.url)
    await bot.get_channel(chat_channel).send(embed=embed)

    role = discord.utils.get(bot.get_guild(server).roles, id=just_chillin_role)
    await member.add_roles(role, reason="New member joined.")


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="the CompuGenius Programs server. Type /help."))


bot.run(token)
