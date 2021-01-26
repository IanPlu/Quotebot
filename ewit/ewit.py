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

        To have Buddy calm down and send only some of the list, give it an upper and lower bound:
        !list_quotes text 37 270
        (Returns a list of quotes from #37, all the way to #370)
        Specify only a lower bound to get all quotes after that:
        !list_quotes text 50
        (Returns a list of quotes from #50, all the way to the last quote)

        To have Buddy slide into your DMs with the entire raw quote CSV file (no bounds):
        !list_quotes file
        !list_quotes csv
        """
        fmt = None
        min_range = None
        max_range = None

        if len(args) == 0:
            # Just get everything as text
            fmt = "text"
        else:
            if len(args) >= 3:
                try:
                    # Check for range numbers
                    min_range = int(args[1])
                    max_range = int(args[2])
                except Exception as e:
                    # Invalid range, throw error
                    await ctx.send("Invalid range specified. Provide numbers like !list_quotes text 37 270")
                    return

            if isinstance(args[0], str):
                if args[0] == "text":
                    fmt = "text"
                elif args[0] == "file" or args[0] == "csv":
                    fmt = "file"

        # Get all quotes for the provided range, formatted
        if fmt == "text":
            all_quotes = self.__get_all_numbered_quotes__(min_range, max_range)

            # TODO: Break into chunks, based on max DM size
            # Then, queue up sending each chunk to the caller
            msg = "\n".join(all_quotes)

            await ctx.author.send(msg)
        elif fmt == "file":
            # TODO: Upload the file for embedding, DM to the caller
            # if the file is too big, ctx.send an error message
            quotes_file = discord.File(self.__get_quotes_file__())
            await ctx.author.send("Here's all the quotes, in .csv format!", file=quotes_file)
        else:
            await ctx.send("Invalid format specified. Provide either 'text', 'file', or 'csv'.")

    # TODO
    # Get a list of quotes that meet some filter criteria
    # Topic -- just a search of the body
    # Author -- all quotes from that author
    # @commands.command()
    # async def find_quote(self, ctx, *args):
    #     """
    #     Find a quote based on some filter parameters.
    #
    #     To find quotes containing a certain word or phrase, use 'about':
    #     !find_quote about banana
    #     !find quote about "banana bread"
    #
    #     To find quotes from a certain author, use 'from':
    #     !find_quote from Louis
    #
    #     Buddy will DM you with the results.
    #     """
    #
    #     await ctx.send("Not yet implemented.")

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
        msg, author, comment = self.parse_quote_chunks(quote)

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
            return self.format_quote_chunks_as_text(msg, author, comment)

    def parse_quote_chunks(self, raw_quote):
        # Split out the quote for better printing
        chunks = list(filter(None, raw_quote.split('|')))
        msg = None
        author = None
        comment = None

        if len(chunks) > 2:
            comment = chunks[2]
        if len(chunks) > 1:
            author = chunks[1]
        if len(chunks) > 0:
            msg = chunks[0]

        return msg, author, comment

    def format_quote_chunks_as_text(self, msg, author, comment, number=None):
        if number is not None:
            return_message = f"{number}) \"{msg}\""
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
            rows = [row.rstrip("\r\n") for row in csvfile]

            if rownum < len(rows):
                logger.debug("Got row: [ " + " ".join(rows[rownum]) + " ]")
                return rows[rownum]
            else:
                raise Exception("No quote with that number exists")

    def __get_num_rows__(self):
        with open(self.quotes_file, "r", newline='') as csvfile:
            return sum(1 for row in csvfile)

    def __get_all_quotes__(self, number_quotes=False, min_range=None, max_range=None):
        with open(self.quotes_file, "r", newline='') as csvfile:
            min_range = min_range if min_range is not None else 0
            max_range = max_range if max_range is not None else 99999

            rows = [self.format_quote_chunks_as_text(*self.parse_quote_chunks(row.rstrip("\r\n")),
                                                     i if number_quotes else None) for i, row in enumerate(csvfile) if
                    min_range <= i <= max_range]

            return rows

    def __get_all_numbered_quotes__(self, min_range=None, max_range=None):
        rows = self.__get_all_quotes__(True, min_range, max_range)
        return rows

    def __get_quotes_file__(self):
        with open(self.quotes_file, "rb") as csvfile:
            return csvfile
