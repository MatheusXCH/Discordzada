import asyncio
import json
import math
import os
import random
import sys
from pprint import pprint


import asyncpraw

# Get the globals from Settings
import codes.paths as path
import discord
import dotenv
import requests
from discord.ext import commands, tasks
from discord.ext.commands import MissingPermissions, has_permissions
from discord.utils import *
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
reddit = asyncpraw.Reddit(
    client_id=os.getenv("PRAW_CLIENT_ID"),
    client_secret=os.getenv("PRAW_CLIENT_SECRET"),
    username=os.getenv("PRAW_USERNAME"),
    password=os.getenv("PRAW_PASSWORD"),
    user_agent=os.getenv("PRAW_USER_AGENT"),
)
CONNECT_STRING = os.environ.get("MONGODB_URI")

PLATFORMS = [
    "STEAM",
    "EPIC GAMES",
    "EPICGAMES",
    "GOG",
    "UPLAY",
    "ORIGIN",
    "PC",
    "UBISOFT",
]
CATEGORIES = ["GAME", "DLC", "OTHER", "ALPHA", "BETA", "ALPHA/BETA"]
ICONS_DICT = {
    "STEAM": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png",
    "EPIC GAMES": "https://cdn2.unrealengine.com/Epic+Games+Node%2Fxlarge_whitetext_blackback_epiclogo_504x512_1529964470588-503x512-ac795e81c54b27aaa2e196456dd307bfe4ca3ca4.jpg",
    "EPICGAMES": "https://cdn2.unrealengine.com/Epic+Games+Node%2Fxlarge_whitetext_blackback_epiclogo_504x512_1529964470588-503x512-ac795e81c54b27aaa2e196456dd307bfe4ca3ca4.jpg",
    "GOG": "https://static.wikia.nocookie.net/this-war-of-mine/images/1/1a/Logo_GoG.png/revision/latest/scale-to-width-down/220?cb=20160711062658",
    "UPLAY": "https://play-lh.googleusercontent.com/f868E2XQBpfl677hykMnZ4_HlKqrOs0fUhuwy0TC9ZI_PQLn99RtBV2kQ7Z50OtQkw=s180-rw",
    "UBISOFT": "https://play-lh.googleusercontent.com/f868E2XQBpfl677hykMnZ4_HlKqrOs0fUhuwy0TC9ZI_PQLn99RtBV2kQ7Z50OtQkw=s180-rw",
    "ORIGIN": "https://cdn2.iconfinder.com/data/icons/gaming-platforms-logo-shapes/250/origin_logo-512.png",
    "PC": "https://pbs.twimg.com/profile_images/300829764/pc-gamer-avatar.jpg",
}


# TODO Adicionar os prints que deverão ser mostrados no console log em casos onde ocorram exceções
class FreeGame(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def error_message(self, ctx: commands.Context, error):
        if isinstance(error, MissingPermissions):
            return f"Desculpe {ctx.author.mention}, você não tem permissão para fazer isso!"

    # WORKING
    @commands.command(name="freegame-channel", hidden=True)
    @has_permissions(administrator=True)
    async def set_channel_id(self, ctx: commands.Context):
        try:
            with MongoClient(CONNECT_STRING) as client:
                collection = client.get_database("discordzada").get_collection("guilds_settings")
                collection.update_one(
                    {"_id": ctx.guild.id},
                    {
                        "$set": {
                            "settings.freegame_channel": {
                                "channel_id": ctx.channel.id,
                                "channel_name": ctx.channel.name,
                            }
                        }
                    },
                )
        except Exception as e:
            await ctx.send(
                "Desculpe, **houve um problema** ao salvar essa informação. Por favor, **tente novamente** em alguns instantes!"
                f"Se o problema persistir, entre em contato com o desenvolvedor em {path.dev_contact}"
            )
            print(
                f"""COMMAND >> 'freegame-channel' ERROR: Não foi possível salvar o canal de FreeGameFindings
                da guilda ID: {ctx.guild.id} no database."""
            )
            print(e)
            return

        await ctx.message.delete()
        msg = await ctx.send(
            f"O canal **{ctx.channel.name}** receberá as mensagens de jogos gratuitos a partir de agora! 😉"
        )
        await asyncio.sleep(5)
        await msg.delete()

    @set_channel_id.error
    async def set_channel_id_error(self, ctx: commands.Context, error):
        await ctx.send(self.error_message(ctx, error))

    # TEST
    @tasks.loop()
    async def freegame_findings(self, channel_id=None):
        """ Confere continuamente as postagens no 'r/FreeGamesFindings', obtendo aquelas que atendem aos filtros
        definidos e enviando-as ao canal selecionado (que corresponde ao ID < channel_id >)

        Parameters
        ----------
        - channel_id : int, optional \\
            [ID do canal para o qual as mensagens devem ser enviadas], by default < self.channel_id >
        """

        def apply_filters(submission):
            """Apply PLATFORMS and CATEGORIES filters on r/FreeGameFingings submissions

            Parameters
            ----------
            - submission : reddit.subreddit.submission \\
                [Subreddit submission object]

            Returns
            -------
            - submission : reddit.subreddit.submission \\
                [The proper submission if its attends the filters]
            """

            for platform in PLATFORMS:
                if platform in submission.title.upper():
                    for category in CATEGORIES:
                        if category in submission.title.upper():
                            return submission

        # Handles the Heroku's server restart to not resend a post
        first_entry_flag = True
        subreddit = await reddit.subreddit("FreeGameFindings")
        post = {"title": "", "url": ""}

        while True:
            try:
                with MongoClient(CONNECT_STRING) as client:
                    collection = client.get_database("discordzada").get_collection("guilds_settings")
                    channel_id_list = [
                        item["settings"]["freegame_channel"]["channel_id"]
                        for item in collection.find({}, {"settings.freegame_channel.channel_id": 1})
                    ]
            except Exception as e:
                print(
                    "TASK >> 'freegame_findings' ERROR: Não foi possível acessar os canais de FreeGameFindings no database."
                )
                print(e)

            # Get newest posts
            newest_list = [apply_filters(submission) async for submission in subreddit.new(limit=10)]
            # Clear 'None' from the list
            newest_list = [item for item in newest_list if item]
            newest = newest_list[0]

            if newest.title != post["title"]:
                post_stack = []

                if first_entry_flag:
                    post["title"] = newest.title
                    post["url"] = newest.url
                    first_entry_flag = False
                else:
                    for submission in newest_list:
                        if submission.title != post["title"]:
                            post_stack.append(submission)
                        else:
                            break

                    while post_stack != []:
                        item = post_stack.pop()
                        post["title"] = item.title
                        post["url"] = item.url
                        icon = "".join(
                            [ICONS_DICT[platform] for platform in PLATFORMS if platform in post["title"].upper()]
                        )

                        embed_post = discord.Embed(title=post["title"], description=post["url"])
                        embed_post.set_thumbnail(url=icon)

                        for channel_id in channel_id_list:
                            text_channel = self.bot.get_channel(id=channel_id)
                            await text_channel.send(embed=embed_post)

            collection.database.client.close()
            # Sleep for 1 hour
            await asyncio.sleep(3600)

    # # # NOTE: NOTE: For now, the functions below are for DEBUG only.
    # # # If decided to maintain those on the final stage, then "has_permissions" decorator must be added

    @commands.command(name="free-game-start", hidden=True)
    @commands.is_owner()
    async def free_game_start(self, ctx: commands.Context):
        """Starts the Free-Game-Findings task

        Parameters
        ----------
        ctx : commands.Context
            [Discord command Context]
        """

        await ctx.message.delete()
        self.freegame_findings.start()
        msg = await ctx.send("**FreeGameFindings is RUNNING!**")
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(name="free-game-stop", hidden=True)
    @commands.is_owner()
    async def free_game_stop(self, ctx: commands.Context):
        """Stops the Free-Game-Findings task

        Parameters
        ----------
        ctx : commands.Context
            [Discord command Context]
        """

        await ctx.message.delete()
        self.freegame_findings.cancel()
        msg = await ctx.send("**FreeGameFindings has been STOPPED!**")
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(name="free-game-restart", hidden=True)
    @commands.is_owner()
    async def free_game_restart(self, ctx: commands.Context):
        """Restarts the Free-Game-Findings task

        Parameters
        ----------
        ctx : commands.Context
            [Discord command Context]
        """

        await ctx.message.delete()
        self.freegame_findings.cancel()
        await asyncio.sleep(3)
        self.freegame_findings.start()
        msg = await ctx.send("**FreeGameFindings has been RESTARTED!**")
        await asyncio.sleep(3)
        await msg.delete()

    @commands.Cog.listener()
    async def on_ready(self):
        self.freegame_findings.start()


def setup(bot):
    bot.add_cog(FreeGame(bot))
