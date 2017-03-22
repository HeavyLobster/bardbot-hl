import discord
import os

from src.events import message, members, reactions, ready

print('Loading Bot... ', end='')

# All Events go through here.
client = discord.Client()


@client.event
async def on_ready():
    await ready.on_ready()


@client.event
async def on_resumed():
    pass


@client.event
async def on_message(msg):
    try:
        await message.handle_message(msg)
    except TypeError:
        # Message wasn't sent in a Guild
        pass


@client.event
async def on_message_delete(msg):
    pass


@client.event
async def on_message_edit(before, after):
    await message.handle_message(after)


@client.event
async def on_reaction_add(reaction, user):
    """
    Event Handler for when a Reaction is added to a Message.
    
    Currently, this is used to check whether the currently stored Clickable Custom Reaction Embed was actuated,
    and sends a signal to it to move further if this is the Case.
    
    :param reaction: The Added discord.Reaction 
    :param user: The discord.User adding the Reaction 
    """
    if user.id != client.user.id:
        try:
            if reaction.message.id == reactions.get_custom_reaction_embed().id:
                if reaction.emoji == '\N{BLACK RIGHT-POINTING TRIANGLE}':
                    await reactions.move_custom_reaction_embed(True, user)
                elif reaction.emoji == '\N{BLACK LEFT-POINTING TRIANGLE}':
                    await reactions.move_custom_reaction_embed(False, user)
        except AttributeError:
            pass


@client.event
async def on_reaction_remove(reaction, user):
    pass


@client.event
async def on_reaction_clear(reaction, user):
    pass


@client.event
async def on_channel_create(channel):
    pass


@client.event
async def on_channel_delete(channel):
    pass


@client.event
async def on_channel_update(before, after):
    pass


@client.event
async def on_member_join(member):
    await members.join(member)


@client.event
async def on_member_remove(member):
    pass


@client.event
async def on_member_update(before, after):
    pass


@client.event
async def on_server_join(server):
    pass


@client.event
async def on_server_remove(server):
    pass


@client.event
async def on_server_update(before, after):
    pass


@client.event
async def on_server_role_create(role):
    pass


@client.event
async def on_server_role_delete(role):
    pass


@client.event
async def on_server_role_update(before, after):
    pass


@client.event
async def on_server_emojis_update(before, after):
    pass


@client.event
async def on_server_available(server):
    pass


@client.event
async def on_server_unavailable(server):
    pass


@client.event
async def on_member_ban(member):
    pass


@client.event
async def on_member_unban(server, user):
    pass


def start():
    client.run(os.environ['DISCORD_TOKEN'])
    message.data_cruncher.data.save_all()


print('done.')
print('All Modules Loaded. Establishing Connection to Discord...')
