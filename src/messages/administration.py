import time

import discord

from src import bot
from src.util import embeds, checks
from src.util.data_cruncher import data


@checks.is_mod
async def shame(msg):
    """
    Shame a mentioned User, or multiple ones, if you're that hardcore.
    
    :param msg: The Message invoking the Command 
    :return: A discord.Message Object containing the resulting Feedback from the Bot
    """
    if not len(msg.mentions):
        return await embeds.desc_only(msg.channel, 'No User specified. Shaming not possible.')
    shame_role = discord.utils.find(lambda r: r.name == 'Shame', msg.guild.roles)
    result = ''
    for member in msg.mentions:
        try:
            await member.add_roles(shame_role)
        except discord.Forbidden as err:
            result += f'Failed to add Shame to **{str(member)}: {err}.\n'
        else:
            result += f'Shamed **{member.name}**.\n'
    return await embeds.desc_only(msg.channel, result)


@checks.is_mod
async def kick(msg):
    """
    Kick a mentioned User from the Guild.
    
    The User must be mentioned via @name#1337 so the Bot can obtain the Member object.
    It's also possible to specify an optional Kick Message that will be sent by the Bot via DM to the kicked User.
     
    :param msg: The Message invoking the Command
    :return: A discord.Message Object containing the resulting Feedback from the Bot.
    """
    if not len(msg.mentions):
        return await embeds.desc_only(msg.channel, 'No User specified. Kick not possible.')
    else:
        try:
            if len(msg.content.split()) >= 3:  # if a kick message is specified
                await msg.mentions[0].send(f'**You have been kicked from {msg.guild.name}, reason:** \n'
                                           f'{" ".join(msg.content.split()[2:])}')
            else:
                await msg.mentions[0].send(f'You have been kicked from {msg.guild.name}!')
            await msg.guild.kick(msg.mentions[0])
        except (discord.errors.Forbidden, discord.errors.HTTPException) as err:
            return await embeds.desc_only(msg.channel, f'**Can\'t kick**: {err}.')
        return await embeds.desc_only(msg.channel, 'Gone!')


@checks.is_mod
async def ban(msg):
    """
    Ban a mentioned User from the Guild.

    The User must be mentioned via @name#1337 so the Bot can obtain the Member object.
    It's also possible to specify an optional Ban Message that will be sent by the Bot via DM to the banned User.

    :param msg: The Message invoking the Command
    :return: A discord.Message Object containing the resulting Feedback from the Bot.
    """
    if not len(msg.mentions):
        return await embeds.desc_only(msg.channel, 'No User specified. Ban not possible.')
    else:
        try:
            if len(msg.content.split()) >= 3:  # if a ban message is specified
                await msg.mentions[0].send(f'**You have been banned from {msg.guild.name}, reason:** \n'
                                           f'{" ".join(msg.content.split()[2:])}')
            else:
                await msg.mentions[0].send(f'You have been banned from {msg.guild.name}!')
            await msg.guild.ban(msg.mentions[0])
        except (discord.errors.Forbidden, discord.errors.HTTPException) as err:
            return await embeds.desc_only(msg.channel, f'**Can\’t ban:** {err}.')
        return await embeds.desc_only(msg.channel, 'Gone!')


@checks.is_mod
async def purge(msg):
    """
    Purge a specified amount of Messages.
    
    It's possible to either purge a given amount of Messages, or by also mentioning a User searching for Messages
    of the User in the specified amount of Messages.
    
    :param msg: The Message invoking the Command
    :return: A discord.Message Object containing the response from the Bot. Most likely the amount of purged Messages.
    """
    try:
        amount = int(msg.content.split()[1])
    except (ValueError, IndexError):
        amount = 20
    if len(msg.mentions) == 1:
        purge_this_user = msg.mentions[0]
    try:
        def check_if_wanted_user(m):
            return m.author == purge_this_user

        if 'purge_this_user' in locals():
            deleted = await msg.channel.purge(limit=amount, check=check_if_wanted_user)
        else:
            deleted = await msg.channel.purge(limit=amount)
        resp = f'Purged a total of **{len(deleted)} Messages**' \
               f'{"." if "purge_this_user" not in locals() else f" from **{purge_this_user.name}**."}'
        return await embeds.desc_only(msg.channel, resp)
    except discord.Forbidden:
        return await embeds.desc_only(msg.channel, f'I don\'t have the required Permissions to purge Messages.')
    except discord.HTTPException:
        return await embeds.desc_only(msg.channel, 'Got HTTP Exception trying to delete Messages.')


@checks.is_admin
async def change_activity(msg):
    """
    Change the Activity, or also named "playing state", of the Bot.

    :param msg: The Message invoking the Command 
    :return: A discord.Message Object containing the response of the Bot.
    """
    # TODO: add new config file for global settings like the last activity etc
    try:
        new_activity = msg.content.split()[1:]
    except IndexError:
        return await embeds.desc_only(msg.channel, 'No new Activity specified.')
    else:
        new_game = discord.Game()
        new_game.name = ' '.join(new_activity)
        await bot.client.change_presence(game=new_game)
        return await embeds.desc_only(msg.channel, 'Changed Activity.')


@checks.is_admin
async def set_log_channel(msg):
    """
    Set a Log Channel which is used to inform about various Events. 
    
    :param msg: The Message invoking the Command
    :return: A discord.Message Object containing the Response from the Bot indicating Success or Failure.
    """
    if data.get_log_channel(msg.guild.id) == msg.channel:
        return await embeds.desc_only(msg.channel, 'This already is the Log Channel for this Guild.')
    elif data.set_log_channel(msg.guild.id, msg.channel.id):
        return await embeds.desc_only(msg.channel, 'Log Channel set to **this channel**.')
    else:
        return await embeds.desc_only(msg.channel, 'Failed to set Log channel.')


@checks.is_admin
async def add_mod(msg):
    """
    Add a Moderator for the Guild in which the Message was sent.
    
    Since Bard uses his own Permission Management System, this is necessary to authorize Users to use various Commands.
    Check the usage of the @permission_checks Decorator for knowing which Group can invoke which Command.
    
    :param msg: The Message invoking the Command 
    :return: A discord.Message Object containing the Response from the Bot indicating Success or Failure.
    """
    # issue: if multiple roles in the owner - admin - mod hierarchy are assigned, the topmost must be removed first
    if not len(msg.mentions):  # No User Mentioned
        return await embeds.desc_only(msg.channel, f'No User specified, cannot add Moderator.')
    elif msg.mentions[0].id in data.get_moderators_and_above(msg.guild.id):
        return await embeds.desc_only(msg.channel, f'**{msg.mentions[0].name}** is already a Moderator.')
    else:
        data.add_moderator(msg.guild.id, msg.mentions[0].id)
        print(f'Added {msg.mentions[0].name} (ID: {msg.mentions[0].id}) to Moderators for Guild {msg.guild.name}.')
        return await embeds.desc_only(msg.channel, f'Added **{msg.mentions[0].name}** to Moderators.')


@checks.is_admin
async def remove_mod(msg):
    """
    Remove a Moderator for the Guild in which the Message was sent.
    
    :param msg: The Message invoking the Command 
    :return: A discord.Message Object containing the Response from the Bot indicating Success or Failure.
    """
    if not len(msg.mentions):
        return await embeds.desc_only(msg.channel, 'No User specified, cannot remove Moderator.')
    elif msg.mentions[0].id not in data.get_moderators_and_above(msg.guild.id):
        return await embeds.desc_only(msg.channel, f'**{msg.mentions[0].name}** is not a Moderator.')
    else:
        data.remove_moderator(msg.guild.id, msg.mentions[0].id)
        print(f'Removed {msg.mentions[0].name} (ID: {msg.mentions[0].id}) from Moderators for Guild {msg.guild.name}.')
        return await embeds.desc_only(msg.channel, f'Removed **{msg.mentions[0].name}** from Moderators.')


@checks.is_admin
async def shutdown(msg):
    """
    Shutdown the Bot.
    
    :param msg: The Message invoking the Command. 
    :return: A discord.Message Object informing about the Bot shutting itself down.
    """
    await embeds.desc_only(msg.channel, '*emulates windows xp shutdown sound*')
    await bot.client.close()


@checks.is_admin
async def replace(msg):
    """
    Replace everything the Bot can find and can replace in the Guild containing the first argument with the second.
    
    Do not use this unless you know exactly what you are doing.
    This was designed for April fools.
    
    :param msg: The Message invoking the Command 
    :return: A discord.Message Object informing about the result.
    """
    start = time.time()
    history_limit = 100
    try:
        find = msg.content.split()[1]
        replace_with = msg.content.split()[2]
    except IndexError:
        return await embeds.desc_only(msg.channel, 'You need to specify what to find '
                                                   'and with what you wish to replace it.')

    result = f'**Starting replacement process:**\n Searching `{find}` and replacing it with `{replace_with}`...\n'
    if msg.guild.me.top_role.permissions.manage_guild:
        result += '**Bot has permissions to manage this Guild.**\n'
        result += f'Checking Guild Name: `{msg.guild.name}`\n'
        if find in msg.guild.name:
            await msg.guild.edit(name=msg.guild.name.replace(find, replace_with))
            result += 'Replaced occurrences in Guild Name.\n'
        else:
            result += 'No change in Guild Name.\n'
    else:
        result += '**Bot has no permissions to manage this Guild.**\n'

    if msg.guild.me.top_role.permissions.manage_channels:
        result += '**Bot has permissions to manage the Channels.**\n'
        for channel in msg.guild.text_channels:
            if find in channel.name:
                old_name = channel.name
                await channel.edit(name=channel.name.replace(find, replace_with))
                result += f'Replaced #{old_name} with #{channel.name}.\n'
            if channel.topic is not None and find in channel.topic:
                old_topic = channel.topic
                await channel.edit(topic=channel.topic.replace(find, replace_with))
                result += f'Replaced "{old_topic}" with "{channel.topic}" in #{channel.name}.\n'
    else:
        result += '**Bot has no permissions to manage the Channels.**\n'

    if msg.guild.me.top_role.permissions.manage_roles:
        result += '**Bot has permissions to manage the Roles.**\n'
        for role in msg.guild.roles:
            if find in role.name:
                old_name = role.name
                await role.edit(name=role.name.replace(find, replace_with))
                result += f'Replaced Role "{old_name}" with "{role.name}".\n'
    else:
        result += '**Bot has no permissions to manage the Roles.**\n'

    if msg.guild.me.top_role.permissions.manage_nicknames:
        result += '**Bot has permissions to manage the Nicknames.**\n'
        for member in msg.guild.members:
            if member.nick is not None and find in member.nick:
                old_nick = member.nick
                await member.edit(nick=member.nick.replace(find, replace_with))
                result += f'Replaced {member}\'s nickname "{old_nick}" with "{member.nick}".\n'
    else:
        result += '**Bot has no permissions to manage the Nicknames.**\n'

    result += '**Checking for Bot Messages:**\n'
    result += f'Checking up to {history_limit * len(msg.guild.text_channels)} Messages...\n'
    edited_messages = 0
    for channel in msg.guild.text_channels:
        async for message in channel.history(limit=history_limit):
            if msg.author.id == bot.client.user.id and find in msg.content:
                await message.edit(content=message.content.replace(find, replace_with))
                edited_messages += 1
    result += f'Replaced a total of {edited_messages} occurrences in Bot Messages.\n'

    result += f'**Replacement done.**\n'
    result += f'*Took {str(time.time() - start)[:-13]} seconds.*'
    return await embeds.title_and_desc(msg.channel, '- Replacement Command Results -', result)


@checks.is_owner
async def change_avatar(msg):
    """
    Change the Avatar to a file that the bot finds in the root directory called "av.png".
    
    :param msg: The Message invoking the Command 
    :return: A discord.Message Object containing the Response from the Bot
    """
    try:
        new_avatar = open('av.png', 'rb').read()
    except FileNotFoundError:
        return await embeds.desc_only(msg.channel, 'Could not find a file called `av.png` in the Root directory of Bard'
                                                   '. If you wish to set a new Avatar, please make sure it exists befor'
                                                   'e using this Command.', discord.Color.red())
    await bot.client.user.edit(avatar=new_avatar)
    return await embeds.desc_only(msg.channel, 'Set new Avatar.', discord.Color.green())


@checks.is_owner
async def add_admin(msg):
    """
    Add an Administrator for the Guild in which the Message was sent.

    Since Bard uses his own Permission Management System, this is necessary to authorize Users to use various Commands.
    Check the usage of the @permission_checks Decorator for knowing which Group can invoke which Command.

    :param msg: The Message invoking the Command 
    :return: A discord.Message Object containing the Response from the Bot indicating Success or Failure.
    """
    if not len(msg.mentions):
        return await embeds.desc_only(msg.channel, 'No User specified, cannot add Administrator.')
    elif msg.mentions[0].id in data.get_admins_and_above(msg.guild.id):
        return await embeds.desc_only(msg.channel, f'**{msg.mentions[0].name}** is already an Administrator.')
    else:
        data.add_administrator(msg.guild.id, msg.mentions[0].id)
        print(f'Added {msg.mentions[0].name} (ID: {msg.mentions[0].id} to Administrators for Guild {msg.guild.name}.')
        return await embeds.desc_only(msg.channel, f'Added **{msg.mentions[0].name}** to Administrators.')


@checks.is_owner
async def remove_admin(msg):
    """
    Remove an Administrator for the Guild in which the Message was sent.

    :param msg: The Message invoking the Command 
    :return: A discord.Message Object containing the Response from the Bot indicating Success or Failure.
    """
    if not len(msg.mentions):
        return await embeds.desc_only(msg.channel, 'No User specified, cannot remove Administrator.')
    elif msg.mentions[0].id not in data.get_admins_and_above(msg.guild.id):
        return await embeds.desc_only(msg.channel, f'**{msg.mentions[0].name}** is not an Administrator.')
    else:
        data.remove_administrator(msg.guild.id, msg.mentions[0].id)
        print(f'Removed {msg.mentions[0].name} (ID: {msg.mentions[0].id}) from Administrators '
              f'for Guild {msg.guild.name}.')
        return await embeds.desc_only(msg.channel, f'Removed **{msg.mentions[0].name}** from Administrators.')
