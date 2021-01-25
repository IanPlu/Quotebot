import csv
import logging
import os.path
from pathlib import Path
import random
import discord
from redbot.core import commands, data_manager

logger = logging.getLogger("ipl.ewit")

QUOTES_FILE_NAME = "quotes.csv"


class EWit(commands.Cog):
    """Ye Almighty Quotebot, Eternal Witness of Your Sinful Sayings"""

    def __init__(self):
        super().__init__()

        # Get the path to the local quote csv file
        base_path = str(data_manager.cog_data_path(self)).replace("\\", "/")
        self.quotes_file = base_path + "/" + QUOTES_FILE_NAME

        # Set up the quotes csv file if it doesn't already exist
        Path(self.quotes_file).touch()
        if not os.path.isfile(self.quotes_file):
            with open(self.quotes_file, "w") as new_csv:
                logger.info("Quotes csv file not found. Creating a new one.")
                # Write quote 0 on init, so real quotes start at 1
                self.register_quote("\"Hi mortals, I'm buddy!\" - Buddy, at the dawn of time")
        logger.info("EWit Online")

    @commands.command()
    async def quote(self, ctx, *args):
        """
        Record the horrible things folks say for blackmail or later laughs.

        To get a random quote:
        !quote

        To get a quote by its ID number:
        !quote 37

        To record a new quote:
        !quote "You know what they say, hide in plain sight if you like Christmas" - Louis
        Make sure to format your quote correctly so it sorts for ~enhanced features~:
        !quote "<quote body>" - <source>, <optional comment...>
        """
        # *args will be a list of:
        # 1. Entire strings in double quotes
        # 2. and/or whitespace separated single words

        # Parse the args
        if len(args) == 0:
            # Give a random quote
            raw_quote = self.get_random_quote(ctx)
            await self.try_send_quote(ctx, raw_quote, "Here's a random quote.")
        else:
            if isinstance(args[0], int) or (isinstance(args[0], str) and args[0].isdigit()):
                # Give a quote by the id number provided
                raw_quote = self.get_quote(ctx, int(args[0]))
                await self.try_send_quote(ctx, raw_quote, "")
            else:
                await ctx.send(self.register_quote(args))

    # TODO
    # - Pagination?
    # - Send the file itself?
    @commands.command()
    async def list_quotes(self, ctx, *args):
        """
        Get a list of some or all quotes.

        To have Buddy slide into your DMs with the full text list, broken up over as many messages as it takes:
        !list_quotes
        !list_quotes text

        To have Buddy slide into your DMs with the raw quote CSV file:
        !list_quotes file
        !list_quotes csv

        To have Buddy calm down and send only some of the list, give it an upper and lower bound:
        !list_quotes text 37 370
        !list_quotes file 69 420
        (Returns a list of quotes from #37, all the way to #370 (inclusive). Obeys the format as well.)
        """
        pass

    # TODO
    # Get a list of quotes that meet some filter criteria
    # Topic -- just a search of the body
    # Author -- all quotes from that author
    @commands.command()
    async def find_quote(self, ctx, *args):
        """
        Find a quote based on some filter parameters.

        To find quotes containing a certain word or phrase, use 'about':
        !find_quote about banana
        !find quote about "banana bread"

        To find quotes from a certain author, use 'from':
        !find_quote from Louis

        Buddy will DM you with the results.
        """
        pass

    # Subcommands
    def get_random_quote(self, ctx):
        return self.get_quote(ctx, random.randint(1, self.__get_num_rows__() - 1))

    # TODO
    # Have it optionally send to a specific channel, so you build a running log of all quotes in THAT channel
    def get_quote(self, ctx, number):
        try:
            return self.__read_row__(number)
        except Exception as e:
            return "No quote with that number. Try !list_quotes, or !find_quote."

    def register_quote(self, text):
        try:
            # Expecting format: [ "The entire quote body", "-" "Source,", "any", "extra", "comment" ]
            quote_body = text[0]
            quote_source = ""
            quote_comment = ""

            if len(text) > 2:
                # If there's a dash to delimit, strip it out
                if text[1] == "-":
                    # Join together the source + any of the comment
                    remainder = " ".join(text[2:])
                else:
                    remainder = text[1:]

                # Then split it along the first comma, if any
                remainder = remainder.split(", ")

                if len(remainder) > 1:
                    quote_source = remainder[0]
                    quote_comment = ", ".join(remainder[1:])
                else:
                    quote_source = remainder[0]

            self.__write_row__(quote_body, quote_source, quote_comment)

            return f"Quote added! This is now quote number {self.__get_num_rows__() - 1}!"
        except Exception as e:
            logger.error("Failed to register quote", e)
            return "Couldn't add that quote, sorry. Check your formatting and try again."

    def try_send_quote(self, ctx, raw_quote, embed_message):
        quote = self.format_quote(ctx, raw_quote)
        if isinstance(quote, discord.Embed):
            return ctx.send(embed_message, embed=quote)
        else:
            return ctx.send(quote)

    def can_embed(self, ctx):
        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            return True
        else:
            return ctx.channel.permissions_for(ctx.me).embed_links

    def format_quote(self, ctx, quote, disable_embed=False):
        """
        Try to pretty-print the provided quote.
        If this has permission to send embeds, will return a fancy discord.Embed object.
        Otherwise, just returns a formatted string.
        """
        # Split out the quote for better printing
        chunks = list(filter(None, quote.split('|')))
        msg = None
        author = None
        comment = None

        if len(chunks) > 2:
            comment = chunks[2]
        if len(chunks) > 1:
            author = chunks[1]
        if len(chunks) > 0:
            msg = chunks[0]

        if msg is None:
            raise Exception("No quote body provided!")

        if not disable_embed and self.can_embed(ctx):
            embed = discord.Embed(color=0x556f79)
            embed.title = f"\"{msg}\""

            if author is not None:
                if comment is not None:
                    embed.set_footer(text=f"{author}, {comment}")
                else:
                    embed.set_footer(text=f"{author}")
            return embed
        else:
            return_message = f"\"{msg}\""
            if author is not None:
                return_message += f" - {author}"
            if comment is not None:
                return_message += f", {comment}"

            return return_message

    # Util methods
    def __write_row__(self, body, source, comment):
        with open(self.quotes_file, "a", newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter='|')
            writer.writerow([body, source, comment])
            logger.debug("Wrote row: [ " + " ".join([body, source, comment]) + " ]")
            return True

    def __read_row__(self, rownum):
        with open(self.quotes_file, "r", newline='') as csvfile:
            rows = [row for row in csvfile]

            if rownum < len(rows):
                logger.debug("Got row: [ " + " ".join(rows[rownum]) + " ]")
                return rows[rownum].rstrip("\r\n")
            else:
                raise Exception("No quote with that number exists")

    def __get_num_rows__(self):
        with open(self.quotes_file, "r", newline='') as csvfile:
            return sum(1 for row in csvfile)
