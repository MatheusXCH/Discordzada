import os

import codes.paths as path
import discord
from discord.ext import commands
from discord.utils import *
from google_trans_new import google_translator
from jikanpy import Jikan, exceptions

jikan = Jikan()
translator = google_translator()

# # # Módulo: MyAnimeList
# # - Integra os resultados de busca do MyAnimeList com o Bot, via jikanpy API
# # - Utiliza da API 'google_trans_new' para fazer automaticamente traduções necessárias de 'EN/PT-BR'
# # - Os comandos listados abaixo buscam fornecer informações, em forma de Embed interativos, sobre animes, mangás, suas sinopses e personagens das obras

# # # Utiliza:
# # - Discord.py API (by Rapptz on: https://github.com/Rapptz/discord.py)
# # - JikanPY API (by abhinavk99 on: https://github.com/abhinavk99/jikanpy)
# # - Google_Trans_New API (by lushan88a on: https://github.com/lushan88a/google_trans_new)


class MyAnimeList(commands.Cog):
    """Obtém dados sobre animes, mangás e personagens diretamente do MyAnimeList (MAL)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="anime")
    async def anime(self, ctx: commands.Context, *, anime_title: str = None):
        """!anime <anime_title> => Pesquisa um anime no MAL
        - Retorna os animes encontrados no MyAnimeList que correspondem à busca
        """

        if anime_title is None:
            nothing_passed_embed = discord.Embed(
                description="É preciso passar o nome do anime junto ao comando `!anime`"
            )
            await ctx.send(embed=nothing_passed_embed)
        else:
            search = jikan.search("anime", anime_title, page=1)

            # Trata caso onde não há resultado algum
            if search["results"] == []:
                no_results_embed = discord.Embed(
                    title="OPS!",
                    description="Desculpe, mas parece que a consulta feita não retornou nada!",
                )
                await ctx.send(embed=no_results_embed)
                return

            def anime_pages_layout(i):
                anime = jikan.anime(search["results"][i]["mal_id"])
                embed_anime = discord.Embed(
                    title=str(anime["title"]),
                    colour=discord.Colour(0x04D197),
                    description=f'*{anime["title_english"]}*\n *{anime["premiered"]}*\n *{anime["status"]}*\n *{anime["type"]}*\n *{anime["episodes"]} episódios*',
                    url=anime["url"],
                )

                studios = ", ".join([studio["name"] for studio in anime["studios"]])
                if studios == "":
                    studios = "Unknown"

                genres_list = []
                genres = ""
                label_count = 0
                for genre in anime["genres"]:
                    label_count += 1
                    genres_list.append(genre["name"])
                    if label_count == 3:
                        genres_list.append("line_feed")
                        label_count = 0

                genres = ", ".join(genres_list)
                if genres == "":
                    genres = "Unknown"

                # Tratando os 'Enters'
                genres = genres.replace("line_feed,", "\n")
                # Caso o valor seja múltiplo de 3, apaga o último line_feed
                genres = genres.replace(", line_feed", "\n")

                embed_anime.add_field(name="**Nota: **", value=str(anime["score"]), inline=True)
                embed_anime.add_field(name="**#Rank: **", value=str(anime["rank"]))
                embed_anime.add_field(name="**#Popularidade:**", value=anime["popularity"], inline=True)

                embed_anime.add_field(name="**Estudio:**", value=studios, inline=True)
                embed_anime.add_field(name="**Fonte Original:**", value=anime["source"], inline=True)
                embed_anime.add_field(name="**Gêneros: **", value=genres, inline=False)

                embed_anime.set_footer(text="Clique em 📄 para ver a sinopse")
                embed_anime.set_image(url=str(anime["image_url"]))

                return embed_anime

            page = anime_pages_layout(0)

            message = await ctx.send(embed=page)
            await message.add_reaction("⏪")
            await message.add_reaction("◀")
            await message.add_reaction("▶")
            await message.add_reaction("⏩")
            await message.add_reaction("📄")
            await message.add_reaction("❌")

            def check(reaction, user):
                return user == ctx.author

            i = 0
            reaction = None
            try:
                while True:
                    if str(reaction) == "⏪":
                        i = 0
                        page = anime_pages_layout(i)
                        await message.edit(embed=page)
                    elif str(reaction) == "◀":
                        if i > 0:
                            i -= 1
                            page = anime_pages_layout(i)
                            await message.edit(embed=page)
                    elif str(reaction) == "▶":
                        if i < len(search) - 1:
                            i += 1
                            page = anime_pages_layout(i)
                            await message.edit(embed=page)
                    elif str(reaction) == "⏩":
                        i = len(search) - 1
                        page = anime_pages_layout(len(search) - 1)
                        await message.edit(embed=page)
                    elif str(reaction) == "📄":
                        await ctx.invoke(
                            self.bot.get_command("anime-sin"),
                            anime_sin_title=page.title,
                        )
                    elif str(reaction) == "❌":
                        await message.clear_reactions()
                        await message.delete()
                        return
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                        await message.remove_reaction(reaction, user)
                    except Exception:
                        break
            except Exception:
                error_embed = discord.Embed(
                    title="Erro:",
                    description="Desculpe, o limite de consultas por minuto ao MyAnimeList foi atingido!\nPor favor, aguarde um pouco e tente novamente!",
                )
                await ctx.send(embed=error_embed)
            await message.clear_reactions()

    @commands.command(name="anime-sin")
    async def anime_sin(
        self,
        ctx: commands.Context,
        *,
        anime_sin_title: str = None,
    ):
        """!anime-sin <anime_title> => Pesquisa a sinopse de um anime no MAL
        - Retorna as sinopses dos animes encontrados no MyAnimeList que correspondem à busca
        """

        if anime_sin_title is None:
            nothing_passed_embed = discord.Embed(
                description="É preciso passar o nome do anime junto ao comando `!anime-sin`"
            )
            await ctx.send(embed=nothing_passed_embed)
        else:
            search = jikan.search("anime", anime_sin_title, page=1)

            # Trata caso onde não há resultado algum
            if search["results"] == []:
                no_results_embed = discord.Embed(
                    title="OPS!",
                    description="Desculpe, mas parece que a consulta feita não retornou nada!",
                )
                await ctx.send(embed=no_results_embed)
                return

            anime = jikan.anime(search["results"][0]["mal_id"])
            embed_anime_sin = discord.Embed(
                title=str(anime["title"]),
                colour=discord.Colour(0x04D197),
                description=translator.translate(anime["synopsis"], lang_src="en", lang_tgt="pt"),
                url=anime["url"],
            )
            await ctx.send(content=None, embed=embed_anime_sin)

    @commands.command(name="manga")
    async def manga(self, ctx: commands.Context, *, manga_title: str = None):
        """!manga <manga_title> => Pesquisa um mangá no MAL
        - Retorna os mangás encontrados no MyAnimeList que correspondem à busca
        """

        if manga_title is None:
            nothing_passed_embed = discord.Embed(
                description="É preciso passar o nome do mangá junto ao comando `!manga`"
            )
            await ctx.send(embed=nothing_passed_embed)
        else:
            search = jikan.search("manga", manga_title, page=1)

            # Trata caso onde não há resultado algum
            if search["results"] == []:
                no_results_embed = discord.Embed(
                    title="OPS!",
                    description="Desculpe, mas parece que a consulta feita não retornou nada!",
                )
                await ctx.send(embed=no_results_embed)
                return

            def manga_pages_layout(i):
                manga = jikan.manga(search["results"][i]["mal_id"])

                embed_manga = discord.Embed(
                    title=manga["title"],
                    colour=discord.Colour(0xFC7B03),
                    description=f'*{manga["title_english"]}*\n*{manga["status"]}*\n *{manga["type"]}*\n *{manga["chapters"]} capítulos*\n *{manga["volumes"]} volumes*',
                    url=manga["url"],
                )
                # Pegando todos os autores e revistas que publicam o mangá, caso mais de um

                author = "; ".join([author["name"] for author in manga["authors"]])
                if author == "":
                    author = "Unknown"

                magazine = "; ".join([magazine["name"] for magazine in manga["serializations"]])
                if magazine == "":
                    magazine = "Unknown"

                genres_list = []
                genres = ""
                label_count = 0
                for genre in manga["genres"]:
                    label_count += 1
                    genres_list.append(genre["name"])
                    if label_count == 3:
                        genres_list.append("line_feed")
                        label_count = 0
                genres = ", ".join(genres_list)

                if genres == "":
                    genres = "Unknown"
                # Tratando os 'Enters'
                genres = genres.replace("line_feed,", "\n")
                # Caso o valor seja múltiplo de 3, apaga o último line_feed
                genres = genres.replace(", line_feed", "\n")

                embed_manga.add_field(name="**Nota: **", value=str(manga["score"]), inline=True)
                embed_manga.add_field(name="**#Rank: **", value=str(manga["rank"]))
                embed_manga.add_field(name="**#Popularidade:**", value=manga["popularity"], inline=True)

                embed_manga.add_field(name="**Autor:**", value=author, inline=True)
                embed_manga.add_field(name="**Revista:**", value=magazine, inline=False)
                embed_manga.add_field(name="**Gêneros:**", value=genres, inline=False)

                embed_manga.set_footer(text="Clique em 📄 para ver a sinopse")
                embed_manga.set_image(url=str(manga["image_url"]))

                return embed_manga

            page = manga_pages_layout(0)

            message = await ctx.send(embed=page)
            await message.add_reaction("⏪")
            await message.add_reaction("◀")
            await message.add_reaction("▶")
            await message.add_reaction("⏩")
            await message.add_reaction("📄")
            await message.add_reaction("❌")

            def check(reaction, user):
                return user == ctx.author

            i = 0
            reaction = None

            try:
                while True:
                    if str(reaction) == "⏪":
                        i = 0
                        page = manga_pages_layout(i)
                        await message.edit(embed=page)
                    elif str(reaction) == "◀":
                        if i > 0:
                            i -= 1
                            page = manga_pages_layout(i)
                            await message.edit(embed=page)
                    elif str(reaction) == "▶":
                        if i < len(search) - 1:
                            i += 1
                            page = manga_pages_layout(i)
                            await message.edit(embed=page)
                    elif str(reaction) == "⏩":
                        i = len(search) - 1
                        page = manga_pages_layout(len(search) - 1)
                        await message.edit(embed=page)
                    elif str(reaction) == "📄":
                        await ctx.invoke(
                            self.bot.get_command("manga-sin"),
                            manga_sin_title=page.title,
                        )
                    elif str(reaction) == "❌":
                        await message.clear_reactions()
                        await message.delete()
                        return
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                        await message.remove_reaction(reaction, user)
                    except Exception:
                        break
            except Exception:
                error_embed = discord.Embed(
                    title="Erro:",
                    description="Desculpe, o limite de consultas por minuto ao MyAnimeList foi atingido!\nPor favor, aguarde um pouco e tente novamente!",
                )
                await ctx.send(embed=error_embed)
            await message.clear_reactions()

    @commands.command(name="manga-sin")
    async def manga_sin(
        self,
        ctx: commands.Context,
        *,
        manga_sin_title: str = None,
    ):
        """!manga-sin <manga_title> => Pesquisa a sinopse de um mangá no MAL
        - Retorna as sinopses dos mangás encontrados no MyAnimeList que correspondem à busca
        """

        if manga_sin_title is None:
            nothing_passed_embed = discord.Embed(
                description="É preciso passar o nome do mangá junto ao comando `!manga-sin`"
            )
            await ctx.send(embed=nothing_passed_embed)
        else:
            search = jikan.search("manga", manga_sin_title, page=1)

            # Trata caso onde não há resultado algum
            if search["results"] == []:
                no_results_embed = discord.Embed(
                    title="OPS!",
                    description="Desculpe, mas parece que a consulta feita não retornou nada!",
                )
                await ctx.send(embed=no_results_embed)
                return

            manga = jikan.manga(search["results"][0]["mal_id"])

            embed_sin = discord.Embed(
                title=str(manga["title"]),
                colour=discord.Colour(0xFC7B03),
                description=translator.translate(manga["synopsis"], lang_src="en", lang_tgt="pt"),
                url=manga["url"],
            )
            await ctx.send(content=None, embed=embed_sin)

    # # Limitações:
    # Devido a forma como o MAL busca por personagens, ao passar o nome incompleto a API nem sempre retorna o resultado mais popular
    # Diante disso, buscando amenizar a situação, essa função busca os 10 primeiros resultados e retorna o mais popular deles
    # Ainda assim, nem sempre é garantido que o resultado mais popular de todo o MAL estará entre os 10 primeiros
    @commands.command(name="mal-char")
    async def mal_char(self, ctx: commands.Context, *, char_name: str = None):
        """!mal-char <character_name> => Pesquisa um personagem no MAL
        - Retorna personagem de anime mais famoso de acordo com a busca requisitada
        - OBS: Essa função nem sempre retorna o personagem mais popular, devido a uma limitação da busca do MAL
        """

        if char_name is None:
            nothing_passed_embed = discord.Embed(
                description="É preciso passar o nome do personagem junto ao comando `!mal-char`"
            )
            await ctx.send(embed=nothing_passed_embed)
        else:

            try:
                search = jikan.search("character", char_name, page=1)
                members_favorites_list = []
                size_of_search = 0

                if len(search["results"]) < 10:
                    size_of_search = len(search["results"])
                else:
                    size_of_search = 10

                for i in range(size_of_search):
                    character_aux = jikan.character(search["results"][i]["mal_id"])
                    members_favorites_list.append(character_aux["member_favorites"])

                index = members_favorites_list.index(max(members_favorites_list))
                members_favorites_list.clear()
                character = jikan.character(search["results"][index]["mal_id"])
            except exceptions.APIException:
                char_error_embed = discord.Embed(
                    title="Erro",
                    description="Hmm... Não consegui encontrar este personagem no MyAnimeList!\nEspere alguns segundos e tente novamente!",
                )
                await ctx.send(embed=char_error_embed)
                return

            voice = "; ".join([dub["name"] for dub in character["voice_actors"] if dub["language"] == "Japanese"])
            if voice == "":
                voice = "Unknown"

            # Tratando possíveis erros na descrição
            # Esses erros podem acontecer pois os itens "animeography" e "mangaography" podem ser listas vazias
            descrição = ""
            try:
                descrição += f'**Anime:** *{character["animeography"][0]["name"]}* \n'
            except Exception:
                descrição += "None \n"
            try:
                descrição += f'**Mangá/Light Novel:** *{character["mangaography"][0]["name"]}* \n'
            except Exception:
                descrição += "None \n"
            try:
                descrição += f"**Dublador:** *{voice}* \n"
            except Exception:
                descrição += "None \n"

            page = discord.Embed(
                title=str(character["name"]),
                colour=discord.Colour(0xC9002C),
                description=descrição,
                url=character["url"],
            )

            page.set_image(url=str(character["image_url"]))

            await ctx.send(content=None, embed=page)

    # TODO Fazer um comando para pesquisar pelos TOP anime ou mangá


def setup(bot):
    bot.add_cog(MyAnimeList(bot))
