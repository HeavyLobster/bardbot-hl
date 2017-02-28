import discord

from src.util import embeds, permission_checks
from src.util.data_cruncher import data


async def _perform_checks(msg: discord.Message):
    status = data.get_role_self_assigning_state(msg.guild.id)
    if status is None:  # No Roles found
        return await embeds.desc_only(msg.channel, 'There are no self-assignable Roles set for this Server.')
    elif not status:  # Self-Assigning Disabled
        return await embeds.desc_only(msg.channel, 'Self-Assigning Roles is currently disabled for this Server.')
    elif len(msg.content.split()) < 2:  # No Role specified
        return await embeds.desc_only(msg.channel, 'No Role specified, can\'t modify.')
    role = _get_role_by_name(' '.join(msg.content.split()[1:]), msg.guild.roles)
    if role is None:
        return await embeds.desc_only(msg.channel, f'Couldn\'t find **\'{" ".join(msg.content.split()[1:])}\'** '
                                                   f'on this Server.')
    return role


def get_comma_separated_roles(msg):
    comma_separated_roles = list()
    msg.content = msg.content[5:]  # Ignore the command part
    for single_role in msg.content.split(', '):
        role_name = single_role.lstrip()
        print('getting ' + role_name)
        single_role = _get_role_by_name(role_name, msg.guild.roles)
        comma_separated_roles.append([single_role, role_name])
    return comma_separated_roles


def _get_role_by_name(name, guild_roles):
    return discord.utils.find(lambda r: r.name == name, guild_roles)


async def assign(msg):
    role = await _perform_checks(msg)
    if not isinstance(role, discord.Role):  # checks didn't pass, it sent a warning instead of the Role
        return role

    if role in msg.author.roles[1:]:
        return await embeds.desc_only(msg.channel, 'You already have that Role assigned.')
    elif role.id not in data.get_self_assignable_roles(msg.guild.id):
        return await embeds.desc_only(msg.channel, 'That Role is not self-assignable.')
    else:
        try:
            await msg.author.add_roles(role)
        except discord.errors.Forbidden as err:
            return await embeds.desc_only(msg.channel, f'Can\'t assign: {err}.')
    return await embeds.desc_only(msg.channel, f'Gave you the **{role.name}** Role!')


async def remove(msg):
    role = await _perform_checks(msg)
    if not isinstance(role, discord.Role):
        return role  # why am I returning this

    try:
        if role in msg.author.roles[1:]:  # first element is always @everyone, so skip it
            await msg.author.remove_roles(role)
        else:
            return await embeds.desc_only(msg.channel, 'You don\'t have that Role assigned.')
    except discord.errors.Forbidden as err:
        return await embeds.desc_only(msg.channel, f'Can\'t remove: {err}.')
    return await embeds.desc_only(msg.channel, f'Removed **{role.name}** from you!')


async def list_self_assignable(msg):
    if not data.get_role_self_assigning_state(msg.guild.id):
        return await embeds.desc_only(msg.channel, 'Self-Assigning Roles is **disabled** for this Server.')
    roles = data.get_self_assignable_roles(msg.guild.id)
    if roles is None:
        return await embeds.desc_only(msg.channel, 'There are no self-assignable Roles for this Server.')
    elif len(roles) >= 1:
        role_names = [discord.utils.find(lambda r: r.id == role_id, msg.guild.roles) for role_id in roles]
        return await embeds.desc_only(msg.channel, f'**There\'s a total of {len(role_names)} self-assignable '
                                                   f'Roles:**\n {", ".join((x.name for x in role_names))}')


@permission_checks.check_if_mod
async def add_self_assignable(msg):
    roles = get_comma_separated_roles(msg)
    updated_roles = []
    for role in roles:
        if role[0] is None:
            await embeds.desc_only(msg.channel, f'Couldn\t find `{role[1]}`.')
        elif role[0].id in data.get_self_assignable_roles(msg.guild.id):
            await embeds.desc_only(msg.channel, f'`{role[1]}` is already self-assignable.')
        elif role[0].position >= msg.guild.me.top_role.position:
            await embeds.desc_only(msg.channel, f'The Role `{role[1]}` stands higher or equal to mine, '
                                                f'can\'t make self-assignable.')
        else:
            data.add_self_assignable_role(msg.guild.id, role[0].id)
            updated_roles.append(role[0].name)
    if len(updated_roles) > 1:
        return await embeds.desc_only(msg.channel, '**The following Roles are now self-assignable:** \n'
                                                   f'{", ".join(updated_roles)}')
    elif len(updated_roles) == 1:
        return await embeds.desc_only(msg.channel, f'Role `{role[0].name}` is now self-assignable.')


@permission_checks.check_if_mod
async def remove_self_assignable(msg):
    role = await _perform_checks(msg)
    if not isinstance(role, discord.Role):
        return role

    data.remove_self_assignable_role(msg.guild.id, role.id)
    return await embeds.desc_only(msg.channel, f'Removed **{role.name}** from self-assignable Roles!')


@permission_checks.check_if_admin
async def switch_self_assignment(msg):
    new_state = data.switch_role_self_assigning_state(msg.guild.id)
    if new_state is None:
        await embeds.desc_only(msg.channel, 'No self-assignable Roles set for this Server.')
    else:
        await embeds.desc_only(msg.channel, f'Self-Assigning Roles is now '
                                            f'**{"enabled" if new_state else "disabled"}**.')