import asyncio
import datetime
from concurrent.futures import TimeoutError

import discord
import random

from src import bot
from src.util import embeds, checks
from src.util.data_cruncher import data


async def get_chance(msg):
    """
    Get the Currency Spawn Chance for the Guild in which the Message was sent.
    
    :param msg: The Message invoking the Command 
    :return: The Response of the Bot
    """
    if msg.channel.id not in data.get_currency_channels(msg.guild.id):
        return await embeds.desc_only(msg.channel, 'Currency Generation is **disabled** in this Channel. '
                                                   'Ask an Administrator to enable it.')
    return await embeds.desc_only(msg.channel, f'Currency Generation for this Server is set to '
                                               f'**{data.get_currency_chance(msg.guild.id)} %**.')


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
    return await embeds.desc_only(msg.channel, f'You (**{msg.author.display_name}**) gave **{amount} Chimes** '
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


async def coin_flip(msg):
    """
    Gain a Chime. Or get nightmares. Hehehehe...
     
    :param msg: The Message invoking the Command 
    :return: The Response of the Bot
    """
    if len(msg.content.split()) < 2:
        return await embeds.desc_only(msg.channel, 'You need to specify an Amount of Chimes to bet for this Command.')
    try:
        amount = int(msg.content.split()[1])
    except ValueError:
        return await embeds.desc_only(msg.channel, 'That is not a valid Amount of Chimes to bet.')
    if amount <= 0:
        return await embeds.desc_only(msg.channel, 'You need to bet at least 1 Chime.')
    diff = data.get_currency_of_user(msg.guild.id, msg.author) - amount
    if diff < 0:
        return await embeds.desc_only(msg.channel, f'You are missing **{diff * (-1)} Chimes** for that!')

    if random.uniform(0, 1) < 0.5:
        data.modify_currency_of_user(msg.guild.id, msg.author, amount)
        return await embeds.desc_with_img(msg.channel,
                                          f'You won **{amount} Chime{"s" if amount > 1 else ""}**!',
                                          'https://cdn.discordapp.com/attachments/17225136311002726'
                                          '4/294523714198831105/chime.png')
    else:
        data.modify_currency_of_user(msg.guild.id, msg.author, -amount)
        cat_eating_chime = random.choice(['http://grza.net/gis/Animals/Cats%20Kittens/Cat%20Evil.jpg',
                                          'http://www.hahastop.com/pictures/Evil_Cat.jpg',
                                          'https://c2.staticflickr.com/2/1357/1208954954_62136d4109.jpg',
                                          'http://img04.deviantart.net/3da2/i/2004/313/1/4/'
                                          'evil_cat__p_by_animals_pictures.jpg',
                                          'http://orig07.deviantart.net/02de/f/2012/294/e/a/'
                                          'evil_cat_by_lena14081990-d5ii594.jpg',
                                          'http://media-cache-ec0.pinimg.com/736x/63/71/7a/63717a8'
                                          '9403358ea4097c7b73c4a1321.jpg',
                                          'http://favim.com/orig/201105/25/cat-evil-kitty-eyes-laser-laser'
                                          '-eyes-lasers-Favim.com-55022.jpg'])
        return await embeds.desc_with_img(msg.channel,
                                          f'A cat ate your **{f"{amount} Chimes" if amount > 1 else "Chime"}**!',
                                          cat_eating_chime)


async def leaderboard(msg):
    """
    Show a Leaderboard showing who has the most Chimes on the Guild.
    
    :param msg: The Message which invoked the Command 
    :return: The Bot's Response
    """
    start_time = datetime.datetime.now()
    loading_message = await embeds.desc_only(msg.channel, '*Building Leaderboard...*')
    leader_board = discord.Embed()
    leader_board.title = f'- Chime Leaderboard for {msg.guild.name}-'
    users = sorted(data.get_currency_guild_users(msg.guild.id).items(), key=lambda x: x[1]['amount'], reverse=True)
    for idx, group in enumerate(users):
        if group[1]['amount'] != 0:
            leader_board.add_field(name=f'#{idx + 1}: {group[1]["name"]}',
                                   value=f'*with {group[1]["amount"]} Chime{"s" if group[1]["amount"] > 1 else ""}*')
    leader_board.set_footer(text=f'Took {str(datetime.datetime.now() - start_time)[6:]}s.')
    return await loading_message.edit(embed=leader_board)


async def trivia(msg):
    """
    Play a Trivia Game.
    
    :param msg: The Message invoking the Command 
    :return: The Response of the Bot 
    """
    initial_join_timeout = 25  # Timeout for each User to join when a game is started
    timeout_after_join = 8  # Timeout after at least one User joined
    minimum_users_for_trivia = 2  # Minimum Users needed to start a Game
    time_per_question = 20  # Time Users have per question
    stop_after_unanswered_rounds = 100  # Stop after this amount of unanswered Questions consecutively
    wrong_answer_penalty = 3  # Time penalty for a wrong answer
    get_this_amount_of_points = 10  # The Amount of Points one User has to get to win
    participating_users = [msg.author]  # Who participates in the Trivia Game

    def did_join_trivia(m):
        """
        Helper Function to check if a User sent a Command to join the Trivia Game.
        
        :param m: The message to check 
        :return: a bool
        """
        return m.channel == msg.channel and (m.content == '>join' or m.content == '>leave')

    async def handle_join_and_leave(m):
        """
        Handler Users Joining and Leaving the Trivia Game, aswell as Quit
        
        :param m: The Message to check for Commands
        :return: False if somebody wants to quit
        """
        if m.content.startswith('>leave') and m.author in participating_users:
            participating_users.remove(m.author)
            await embeds.desc_only(msg.channel, f'✅ You (**{m.author.display_name}**) are no longer '
                                                f'participating in the Trivia Game!', discord.Color.green())
        elif m.content.startswith('>leave'):
            await embeds.desc_only(msg.channel, f'You (**{m.author.display_name}**) are not participating'
                                                f' in the Trivia Game!', discord.Color.red())

        elif m.content == '>join' and m.author in participating_users:
            await embeds.desc_only(msg.channel, f'You (**{m.author.display_name}**) are already '
                                                f'participating!', discord.Color.red())
        elif m.content == '>join':
            participating_users.append(m.author)
            await embeds.desc_only(msg.channel, f'✅ You (**{m.author.display_name}**) joined the **'
                                                f'{topic}** Trivia Game! Total: **{len(participating_users)}**',
                                   discord.Color.green())
        elif m.content in ('>stoptrivia', '>stop', '>stahp', '>quit'):
            await embeds.desc_only(msg.channel, f'**Trivia stopped** upon Request by **{m.author.mention}**.',
                                   discord.Color.red())
            return False
        return True

    async def question_loop(index: int, question: dict, consecutive_rounds: int):
        """
        Handles asking Questions and responding to Answers accordingly.
        
        :param index: The Index of the Question 
        :param question: A dictionary representing the Question and its answers
        :param consecutive_rounds: How many Rounds have been without response consecutively
        :return The consecutive Rounds without an Answer, None if it's time to stop, or False if somebody wants to quit
        """
        if consecutive_rounds >= stop_after_unanswered_rounds:
            return None

        description = question['q']
        for key in question:
            if key in ('1', '2', '3', '4'):
                description += f'\n **{key}:** {question[key]}'

        await embeds.title_and_desc(msg.channel, f'- Trivia Question #{index + 1} -',
                                    description, discord.Color.gold())

        try:
            countdown = time_per_question
            while True:
                some_message = await bot.client.wait_for('message', check=lambda m: m.channel == msg.channel,
                                                         timeout=countdown)
                if some_message.content.lower() == question['a'] \
                        and some_message.author.id in (x.id for x in participating_users):
                    break  # PEP8 is a meme
                else:
                    # somebody wanted to quit
                    if not await handle_join_and_leave(some_message):
                        consecutive_rounds = -1
                        return consecutive_rounds
                    else:
                        countdown -= wrong_answer_penalty

        except TimeoutError:
            await embeds.desc_only(msg.channel, f'Nobody responded it in time. The answer was: **{question["a"]}**',
                                   discord.Color.dark_gold())
            consecutive_rounds += 1
        else:
            await embeds.desc_only(msg.channel, f'**{some_message.author.mention}**, you guessed it!',
                                   discord.Color.green())
            consecutive_rounds = 0

            if str(some_message.author.id) in correct_guessing_people:
                correct_guessing_people[str(some_message.author.id)] += 1
            else:
                correct_guessing_people[str(some_message.author.id)] = 1
        return consecutive_rounds

    async def reward():
        """
        Helper function to reward Users at the end of the Game.
        
        :return: The Message containing the Response 
        """
        reward_chimes = random.randrange(1, 4)
        results = ''
        sorted_correct = sorted(correct_guessing_people.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_correct) < 1:
            return await embeds.title_and_desc(msg.channel,
                                               '- Trivia Game Results -',
                                               'Nobody guessed anything. That\'s... interesting.',
                                               discord.Color.gold())
        for index, pepes_friend in enumerate(sorted_correct):
            print(index)
            if index == 0:
                results += f'**{bot.client.get_user(int(pepes_friend[0])).mention}** won with **{pepes_friend[1]}** ' \
                           f'Points and received **{reward_chimes} Chime{"s" if reward_chimes > 1 else ""}**' \
                           f' for it! :confetti_ball: :sparkler:\n'
                data.modify_currency_of_user(msg.guild.id, bot.client.get_user(int(pepes_friend[0])), reward_chimes)
            else:
                results += f'**#{index + 1}**: {bot.client.get_user(int(pepes_friend[0])).mention} ' \
                           f'with {pepes_friend[1]} points!\n'

        return await embeds.title_and_desc(msg.channel, '- Trivia Game Results -', results, discord.Color.gold())

    # Initial Setup
    if len(msg.content.split()) < 2:
        return await embeds.desc_only(msg.channel, 'You did not specify any topic - here are all available ones:\n'
                                                   f'**{", ".join(data.get_all_trivia_topics())}**.')
    topic = msg.content.split()[1]
    trivia_obj = data.get_trivia(topic)
    if trivia_obj is None:
        return await embeds.desc_only(msg.channel, f'I could not find the Trivia Topic "`{topic}`". '
                                                   'Run `>trivia` to get a List of all available Topics.')

    # descriptive variable names
    is_not_being_time_outed = data.timeout_user_is_not_being_time_outed(msg.author.id)
    if not is_not_being_time_outed:
        return await embeds.desc_only(msg.channel,
                                      'You need to wait **at least 10 Minutes** before using this Command.',
                                      discord.Color.red())
    await embeds.desc_only(msg.channel, f'**{msg.author.display_name}** wants to start a Trivia Game! '
                                        f'Type `>join` to join!', discord.Color.gold())

    # Get Participants
    while True:
        try:
            accept_msg = await bot.client.wait_for('message', check=did_join_trivia, timeout=initial_join_timeout
            if len(participating_users) < 2 else timeout_after_join)
        except TimeoutError:
            break
        else:
            await handle_join_and_leave(accept_msg)

    # Check for Amount of participants
    if len(participating_users) < minimum_users_for_trivia:
        return await embeds.desc_only(msg.channel, f'**Not enough Users joined** - you need **at least '
                                                   f'{minimum_users_for_trivia} Users** to '
                                                   f'start a Trivia Game, but only {len(participating_users)} joined!',
                                      discord.Color.red())

    await embeds.desc_only(msg.channel, f'Starting Trivia Game with **{len(participating_users)} User'
                                        f'{"s" if len(participating_users) > 1 else ""}**...')
    data.timeout_trivia_user(msg.author.id)
    correct_guessing_people = {}
    consecutive_rounds_without_answer = 0
    random.shuffle(trivia_obj['questions'])
    if trivia_obj['mode'] in ('guess', 'numbers'):
        for idx, single_question in enumerate(trivia_obj['questions']):
            consecutive_rounds_without_answer = await question_loop(idx, single_question,
                                                                    consecutive_rounds_without_answer)
            if consecutive_rounds_without_answer is None:
                return await embeds.desc_only(msg.channel, f'I did not receive any Trivia Responses within the past **'
                                                           f'{stop_after_unanswered_rounds} rounds** - time to stop!')

            # Somebody requested Quit - need to check for False and not 0 for because magic
            elif consecutive_rounds_without_answer == -1:
                break

            elif get_this_amount_of_points in correct_guessing_people.values():
                return await reward()
        correct_guessing_people = list(sorted(correct_guessing_people.items(), key=lambda x: x[1], reverse=True))
        return await reward()

    else:
        return await embeds.desc_only(msg.channel, 'Unsupported Trivia Mode.', discord.Color.red())


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


@checks.is_admin
async def set_chance(msg):
    """
    Set the Currency Spawn Chance for the Guild in which the Message was sent.
    
    :param msg: The Message invoking the Command 
    :return: The Response of the Bot 
    """
    if len(msg.content.split()) < 2:
        return await embeds.desc_only(msg.channel, 'You need to specify an Amount to which the Chance should be set!')
    try:
        amount = int(msg.content.split()[1])
    except ValueError:
        return await embeds.desc_only(msg.channel, 'That is not a valid amount.')

    if not 0 <= amount <= 20:
        return await embeds.desc_only(msg.channel, 'Chance must be within 0 and 20%.')
    data.set_currency_chance(msg.guild.id, amount)
    return await embeds.desc_only(msg.channel, f'Set **Chime Spawn Chance** to **{amount} %**!')
