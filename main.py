from typing import Optional

import discord
from discord import app_commands
import requests
import wikipediaapi

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options):
        super().__init__(intents=intents, **options)

        # set bot to idle
        self.activity = discord.Activity(type=discord.ActivityType.listening, name='your commands')
        self.status = discord.Status.idle
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)


intents = discord.Intents.all()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')


@client.tree.command()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! {client.latency * 1000:.4f} ms')

@client.tree.command()
async def free_admin(interaction: discord.Interaction):
    await interaction.response.send_message('https://tenor.com/view/maniac-wanted-reaction-meme-spongebob-gif-24138039')

@client.tree.command()
async def set_nick(interaction: discord.Interaction, nickname: Optional[str] = None):
    if interaction.user.id != OWNER.id:
        return await interaction.response.send_message('You are not the owner of this bot.', ephemeral=True)

    await interaction.edit_original_response(f'Changing the nickname of everyone in the guild to {nickname}')

    for member in interaction.guild.members:
        try:
            if nickname:
                await member.edit(nick=nickname)
            else:
                await member.edit(nick=member.name)
        except discord.Forbidden:
            pass


fetch = app_commands.Group(name='fetch', description='Fetches data from the internet.')

@fetch.command()
async def xkcd(interaction: discord.Interaction, comic_number: Optional[int] = None):
    if comic_number is None:
        url = 'https://xkcd.com/info.0.json'
    else:
        url = f'https://xkcd.com/{comic_number}/info.0.json'

    with requests.get(url) as r:
        data = r.json()

    embed = discord.Embed(title=data['safe_title'], description=data['alt'], url=data['img'], color=0x6B8BA4)
    embed.set_image(url=data['img'])
    await interaction.response.send_message(embed=embed)


@fetch.command()
async def wiki(interaction: discord.Interaction, *, topic: str):
    # get the title, summary, url, and image of the first result
    wiki = wikipediaapi.Wikipedia('en')

    page = wiki.page(topic)

    title = page.title
    summary = page.summary[:200] + '...'
    try:
        url = page.fullurl
    except AttributeError:
        url = f'https://en.wikipedia.org/wiki/{title.replace(" ", "_")}'

    with requests.get('https://en.wikipedia.org/w/api.php',
                      params={"action": "query", "format": "json", "prop": "info|pageimages", "inprop": "url",
                              "piprop": "thumbnail", "titles": title}) as r:
        data = r.json()

    try:
        page_id = list(data['query']['pages'].keys())[0]
        image = data['query']['pages'][page_id]['thumbnail']['source']
    except KeyError:
        image = None

    # make the image the thumbnail if there is no image
    if image is None:
        image = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/100px-Wikipedia-logo-v2.svg.png'

    embed = discord.Embed(title=title, description=summary, url=url, color=0xA2A9B1)
    embed.set_image(url=image)
    await interaction.response.send_message(embed=embed)

@fetch.command()
async def animal(interaction: discord.Interaction, topic: str):
    fact_url = f'https://some-random-api.ml/facts/{topic}'
    img_url = f'https://some-random-api.ml/img/{topic}'

    try:
        with requests.get(fact_url) as r:
            data1 = r.json()

        with requests.get(img_url) as r:
            data2 = r.json()

        fact = data1['fact']
        image = data2['link']
    except:
        return await interaction.response.send_message('Invalid topic.', ephemeral=True)

    embed = discord.Embed(title=topic.capitalize(), description=fact, color=0x964B00)
    embed.set_image(url=image)
    await interaction.response.send_message(embed=embed)

@fetch.command()
async def joke(interaction: discord.Interaction):
    with requests.get('https://official-joke-api.appspot.com/random_joke') as r:
        data = r.json()

    setup = data['setup']
    punchline = data['punchline']

    embed = discord.Embed(title='Joke', description=setup, color=0x00FF00)

    # add the punchline but make it hidden
    embed.add_field(name='Punchline', value=punchline, inline=False)
    await interaction.response.send_message(embed=embed)

@fetch.command()
async def quote(interaction: discord.Interaction):
    with requests.get('https://api.quotable.io/random') as r:
        data = r.json()

    quote = data['content']
    author = data['authorSlug']

    embed = discord.Embed(title='Quote', description=quote, color=0xFF0000)
    embed.set_footer(text=author)
    await interaction.response.send_message(embed=embed)

@fetch.command()
async def fact(interaction: discord.Interaction):
    # random useless fact
    with requests.get('https://uselessfacts.jsph.pl/random.json?language=en') as r:
        data = r.json()

    fact = data['text']
    permalink = data['permalink']
    embed = discord.Embed(title='Fact', description=fact, url=permalink, color=0x0000FF)
    await interaction.response.send_message(embed=embed)

client.tree.add_command(fetch)

mod = app_commands.Group(name='mod', description='Moderation commands.')

# role command with add/remove option and role name
@mod.command()
async def role(interaction: discord.Interaction, choice: str, rank: discord.Role, member: discord.Member):
    if interaction.user.id != OWNER.id:
        return await interaction.response.send_message('You are not the owner of this bot.', ephemeral=True)

    match choice:
        case 'add':
            try:
                await member.add_roles(rank)
            except discord.Forbidden:
                return await interaction.response.send_message('I do not have permission to add roles.', ephemeral=True)
            await interaction.response.send_message(f'Added {rank} to {member}')
        case 'remove':
            try:
                await member.remove_roles(rank)
            except discord.Forbidden:
                return await interaction.response.send_message('I do not have permission to remove roles.', ephemeral=True)
            await interaction.response.send_message(f'Removed {rank} from {member}')
        case default:
            await interaction.response.send_message(f'Invalid choice: {choice}', ephemeral=True)

client.tree.add_command(mod)

@client.tree.command()
async def sleep(interaction: discord.Interaction):
    if interaction.user.id != OWNER.id:
        return await interaction.response.send_message('You are not the owner of this bot.', ephemeral=True)

    await interaction.response.send_message('Shutting down...')
    await client.close()

@client.tree.command()
async def poll(interaction: discord.Interaction, poll_question: str, poll_options: str):
    if interaction.user.id != OWNER.id:
        return await interaction.response.send_message('You are not the owner of this bot.', ephemeral=True)

    poll_options = poll_options.split(', ')

    if len(poll_options) > 10:
        return await interaction.response.send_message('You cannot have more than 10 poll options.', ephemeral=True)

    embed = discord.Embed(title=poll_question,
                          description='\n'.join(f'{i}: {option}' for i, option in enumerate(poll_options, 1)))
    msg = await interaction.channel.send(embed=embed)

    for i in range(1, len(poll_options) + 1):
        await msg.add_reaction(f'{i}\N{combining enclosing keycap}')


@client.tree.command()
async def purge(interaction: discord.Interaction, amount: int):
    if interaction.user.id != OWNER.id:
        return await interaction.response.send_message('You are not the owner of this bot.', ephemeral=True)

    msg = await interaction.response.send_message(f'Purging {amount} messages')

    await interaction.channel.purge(limit=amount + 1)


@client.tree.command()
@app_commands.describe(
    first_value='The first value you want to add something to',
    second_value='The value you want to add to the first value',
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')


@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def say(interaction: discord.Interaction, text_to_send: str):
    """Sends a message in the current channel."""
    member = interaction.user
    embed = discord.Embed(title=f'{member} said:', description=text_to_send, color=member.color)
    await interaction.response.send_message(embed=embed)


@client.tree.command()
@app_commands.describe(
    member='The member you want to get the joined date from; defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined {discord.utils.format_dt(member.joined_at)}')

# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')


@client.tree.context_menu(name='Poll Winner')
async def poll_winner(interaction: discord.Interaction, message: discord.Message):
    # only the bot can send the message
    if message.author != client.user:
        return

    # get the reactions
    try:
        reactions = message.reactions
        winner = max(reactions, key=lambda r: r.count)
        winner_name = winner.emoji
    except:
        return await interaction.response.send_message('This message has no reactions.', ephemeral=True)

    # send the winner's name
    await interaction.response.send_message(f'The winner is {winner_name}!')


# This context menu command only works on messages
@client.tree.context_menu(name='Report to Moderators')
async def report_message(interaction: discord.Interaction, message: discord.Message):
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(
        f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
    )

    # Handle report by sending it into a log channel
    log_channel = interaction.guild.get_channel(929917856844480523)  # replace with your channel id

    embed = discord.Embed(title='Reported Message')
    if message.content:
        embed.description = message.content

    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    embed.timestamp = message.created_at

    url_view = discord.ui.View()
    url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))

    await log_channel.send(embed=embed, view=url_view)


client.run('')
