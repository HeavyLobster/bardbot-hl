import re

from src.events import reactions
from src.util import config_holder
from src.util import embeds

print('Loading Message Event Handler...')

data = config_holder.ConfigHolder()


async def handle_message(msg):
    if not msg.content.startswith(tuple(data.get_config('messages', 'prefixes').values())):
        return

    elif msg.content.startswith(data.get_prefix('currency')):
        await currency_cmd(msg)

    elif msg.content.startswith(data.get_prefix('custom_reactions')):
        await custom_reaction_cmd(msg)

    elif msg.content.startswith(data.get_prefix('hugemoji')):
        await hugemoji_cmd(msg)

    return msg.content


async def currency_cmd(msg):
    pass


embed = None


async def custom_reaction_cmd(msg):
    msg.content = msg.content[1:]
    if msg.content.startswith('add') and msg.content[4:7] != 'add':  # the famous !add add
        try:
            if len(msg.content.split()[2:]) <= 1:
                await embeds.desc_only(msg.channel, 'Too little content for a Custom Reaction!')
                return
            data.add_custom_reaction(msg.guild.id, msg.content.split()[1],
                                     ' '.join(msg.content.split()[2:]), msg.author.name)
        except IndexError:
            pass
            return
        await embeds.desc_only(msg.channel, f'Added new Reaction called {msg.content.split()[1]}.')
        await msg.delete()

    elif msg.content.startswith('listall'):
        custom_reactions = data.get_all_custom_reactions_on_guild(msg.guild.id)
        if custom_reactions is None:
            await embeds.desc_only(msg.channel, 'Sorry, no Quotes were found for this Server.')
        else:
            await reactions.create_custom_reaction_embed(f'- All Custom Reactions on {msg.guild.name} - ',
                                                         custom_reactions, msg.channel,
                                                         'https://cdn.discordapp.com/attachments/172251363110027264/'
                                                         '284429672748548096/finebard_by_kuglu-da3ul5m.png')
        msg.delete()

    else:
        reaction = data.get_custom_reaction(msg.guild.id, msg.content.split()[0])
        if reaction[0].startswith('http'):  # Properly Embed Links to GIF, Images etc.
            await embeds.img_with_footer(msg.channel, reaction[0], f'Added by {reaction[1]}', reaction[2])
        else:
            await embeds.desc_with_footer(msg.channel, reaction[0], f'Added by {reaction[1]}', reaction[2])
        await msg.delete()


async def hugemoji_cmd(msg):
    # Match Emoji ID with RegEx
    emoji_id = re.search('[0-9]+', msg.content)
    # Make sure it also works when there's a number in the ID!
    try:
        if len(emoji_id.group(0)) == 1:
            emoji_id = re.search('[0-9]+', msg.content[msg.content.find(emoji_id.group(0)) + 1:])
    except AttributeError:
        await embeds.desc_only(msg.channel, 'Sorry, something went wrong.')
    else:
        await embeds.img_only(msg.channel, f'https://cdn.discordapp.com/emojis/{emoji_id.group(0)}.png')
    await msg.delete()
