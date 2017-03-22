import asyncio
from concurrent.futures import TimeoutError
import discord
import random
from src.util.data_cruncher import data
from src.util import embeds, checks
from src import bot


async def get_money(msg):
    """
    Get the amount of money / currency / chimes a User possesses.
    
    :param msg: The Message invoking the Command 
    :return: A Message containing Information about the Money the User has
    """

    if len(msg.mentions) == 1:
        return await embeds.desc_only(msg.channel, f'**{msg.mentions[0].name}** has a '
                                      f'total of **{data.get_currency_of_user(msg.guild.id, msg.mentions[0])} '
                                      f'Chimes**!')
    return await embeds.desc_only(msg.channel, f'You (**{msg.author.name}**) have a total of '
                                  f'**{data.get_currency_of_user(msg.guild.id, msg.author)} Chimes**!')


async def give_money(msg):
    """
    Give money to a mentioned User.
    
    :param msg: The Message invoking the Command 
    :return: A Message containing the response
    """
    if len(msg.mentions) < 1:
        return await embeds.desc_only(msg.channel, 'You need to mention a User for this Command!')
    elif len(msg.mentions) > 1:
        return await embeds.desc_only(msg.channel, 'You can\'t give money to multiple Users!')
    elif len(msg.content.split()) + len(msg.mentions) < 3:
        return await embeds.desc_only(msg.channel, 'You need to specify an Amount for this Command!')
    try:
        amount = int(msg.content.split()[1])
    except ValueError:
        return await embeds.desc_only(msg.channel, 'You need to specify an Amount for this Command!')
    if amount <= 0:
        return await embeds.desc_only(msg.channel, 'That is not a valid Amount to give.')
    author_money = data.get_currency_of_user(msg.guild.id, msg.author)
    if amount > author_money:
        return await embeds.desc_only(msg.channel, f'You are missing **{amount - author_money}** Chimes for that!')
    data.modify_currency_of_user(msg.guild.id, msg.author, -amount)
    data.modify_currency_of_user(msg.guild.id, msg.mentions[0], amount)
    return await embeds.desc_only(msg.channel, f'You ({msg.author.name}) gave **{amount} Chimes** '
                                               f'to {msg.mentions[0].mention}!')


async def generator(msg):
    """
    Generate Currency based on different Parameters and a bit of Magic.
    
    The Bot first runs various checks to make sure it's good to spawn a Chime. 
    It then sends out an Embed informing about the appearance of a Chime.
    If it was not picked up within 10 seconds, the original Message will be deleted.
    
    :param msg: The original Message 
    """

    if msg.channel.id not in data.get_currency_channels(msg.guild.id) or msg.author.id == bot.client.user.id:
        # Currency Generation not enabled, or it was a Message by the Bot!
        return

    if not random.uniform(0, 1) <= data.get_currency_chance(msg.guild.id) / 100:
        return

    # After some Checks, now finally - currency spawned!
    chime_image = random.choice([
         'http://2.bp.blogspot.com/-7s3q3BhdCBw/VPUPKAOTbUI/AAAAAAAAlCs/5vyP_lAN0S4/s1600/bardchime.jpg',
         'http://pm1.narvii.com/5786/089f9a52941e8ded0f54df0978378db42680f6d8_hq.jpg',
         'https://cdn.discordapp.com/attachments/172251363110027264/283612882846089216/unknown.png'
    ])
    pickup_command = random.choice(['>pick', '>collect', '>gimme', '>mine', '>ootay', '>doot', '>slurp', '>canihas',
                                    '>bardo', '>penguin', '>ducky', '>quack', '>darb', '>dong', '>owo', '>whatsthis'])

    data.currency_increment_count(msg.guild.id)
    appearance = await embeds.desc_with_img(msg.channel, f'**A Chime has appeared!** '
                                                         f'Type `{pickup_command}` to collect it!',
                                            chime_image,
                                            f'This is Chime #{data.get_currency_total(msg.guild.id)} for this Guild.')

    def validate_pickup(m):
        """
        A Helper Function to validate the Pickup of a Chime.
        
        :param m: The message to check 
        :return: a bool
        """
        return m.channel == msg.channel and m.content == pickup_command

    try:
        resp = await bot.client.wait_for('message', check=validate_pickup, timeout=10)
    except TimeoutError:
        if appearance is not None:  # ???
            return await appearance.delete()
    else:
        await appearance.delete()
        await resp.delete()
        data.modify_currency_of_user(msg.guild.id, resp.author, 1)
        confirmation = await embeds.desc_only(msg.channel, f'**{resp.author.name}** picked up a Chime!')
        await asyncio.sleep(3)
        await confirmation.delete()


@checks.is_admin
async def add_money(msg):
    """
    Add Chimes to a mentioned User or otherwise to the Author.
    
    :param msg: The Message invoking the Command 
    :return: The Response of the Bot
    """
    if len(msg.content.split()) + len(msg.mentions) < 2:
        return await embeds.desc_only(msg.channel, '**Cannot add Chimes**: No Amount specified.')
    try:
        amount = int(msg.content.split()[1])
    except ValueError:
        return await embeds.desc_only(msg.channel, 'That\'s not a valid Amount.')
    if amount <= 0:
        return await embeds.desc_only(msg.channel, '**Cannot add Chimes**: Do I look like a Math Bot?')
    elif len(msg.mentions) == 1:
        data.modify_currency_of_user(msg.guild.id, msg.mentions[0], amount)
        return await embeds.desc_only(msg.channel, f'Added **{amount} Chimes** to **{msg.mentions[0].name}**.')
    else:
        data.modify_currency_of_user(msg.guild.id, msg.author, amount)
        return await embeds.desc_only(msg.channel, f'Added **{amount} Chimes** to yourself!')


@checks.is_admin
async def remove_money(msg):
    """
    Remove the given amount of Chimes from a User - if mentioned - or otherwise from the Author.
    
    :param msg: The Message invoking the Command
    :return: The Response of the Bot
    """
    if len(msg.content.split()) + len(msg.mentions) < 2:
        return await embeds.desc_only(msg.channel, '**Cannot take Chimes**: No Amount specified.')
    try:
        amount = int(msg.content.split()[1])
    except ValueError:
        return await embeds.desc_only(msg.channel, 'That\'s not a valid Amount.')
    if amount <= 0:
        return await embeds.desc_only(msg.channel, '**Cannot take Chimes**: Do I look like a Math Bot?')
    elif len(msg.mentions) == 1:
        if data.get_currency_of_user(msg.guild.id, msg.mentions[0]) - amount < 0:
            return await embeds.desc_only(msg.channel, f'Cannot take **{amount} Chimes** because {msg.mentions[0].name}'
                                                       f' would then have a negative Amount of Chimes!')
        data.modify_currency_of_user(msg.guild.id, msg.mentions[0], -amount)
        return await embeds.desc_only(msg.channel, f'Took **{amount} Chimes** from **{msg.mentions[0].name}**.')
    else:
        if data.get_currency_of_user(msg.guild.id, msg.author) - amount < 0:
            return await embeds.desc_only(msg.channel, 'Do you want negative Chimes? '
                                                       'Because that\'s how you get negative Chimes.')
        data.modify_currency_of_user(msg.guild.id, msg.author, -amount)
        return await embeds.desc_only(msg.channel, f'Took **{amount} Chimes** from yourself!')


@checks.is_admin
async def toggle_cg(msg):
    """
    Toggle Currency Generation in the Channel in which this Command was invoked.
    
    :param msg: The Message invoking the Command
    :return: A Message indicating what happened
    """
    if not isinstance(msg.channel, discord.abc.GuildChannel):
        return await embeds.desc_only(msg.channel, 'This Command must be used on a Guild.')

    if msg.channel.id in data.get_currency_channels(msg.guild.id):
        data.remove_currency_channel(msg.guild.id, msg.channel.id)
        return await embeds.desc_only(msg.channel, 'Currency Generation is now **disabled** in this Channel.')

    data.add_currency_channel(msg.guild.id, msg.channel.id)
    return await embeds.desc_only(msg.channel, 'Currency Generation is now **enabled** in this Channel.')