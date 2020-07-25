import csv
import logging
import os.path
import random
import sys
from redbot.core import commands
from redbot.core.utils.chat_formatting import (
    escape
)

logger = logging.getLogger("ipl.ewit")

QUOTES_FILE = "quotes.csv"

class EWit(commands.Cog):
    """Ye Almighty Quotebot, Eternal Witness of Your Sinful Sayings"""


    def __init__(self):
        super().__init__()

        # Set up the quotes csv file if it doesn't already exist
        if not os.path.isfile(QUOTES_FILE):
            with open(QUOTES_FILE, "w") as new_csv:
                logger.info("Quotes csv file not found. Creating a new one.")


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
            await ctx.send(self.get_random_quote())
        else:
            if isinstance(args[0], int) or (isinstance(args[0], str) and args[0].isdigit()):
                # Give a quote by the id number provided
                await ctx.send(self.get_quote(int(args[0])))
            else:
                await ctx.send(self.register_quote(args))


    ### Subcommands ###
    def get_random_quote(self):
        return self.get_quote(random.randint(0, self.__get_num_rows__() - 1))


    def get_quote(self, number):
        return self.__read_row__(number)


    def register_quote(self, text):
        try:
            # Expecting format: [ "The entire quote body", "-" "Source,", "any", "extra", "comment" ]
            quote_body = text[0]
            quote_source = ""
            quote_comment = ""

            if len(text) > 2:
                # Join together the source + any of the comment
                remainder = " ".join(text[2:])

                # Then split it along the comma, if any
                remainder.split(",")

                if len(remainder) > 1:
                    quote_source = remainder[0]
                    quote_comment = remainder[1]
                else:
                    quote_source = remainder[0]

            self.__write_row__(quote_body, quote_source, quote_comment)

            return "Quote added!"
        except:
            logger.error("Failed to register quote", sys.exc_info()[0])
            return "Couldn't add that quote, sorry. Check your formatting and try again."


    ### Util methods ###
    def __write_row__(self, body, source, comment):
        with open(QUOTES_FILE, newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([ body, source, comment ])


    def __read_row__(self, rownum):
        with open(QUOTES_FILE, newline='') as csvfile:
            reader = csv.reader(csvfile)
            if rownum < len(reader):
                return reader[rownum]
            else:
                raise Exception("No quote with that number exists")

    def __get_num_rows__(self):
        with open(QUOTES_FILE, newline='') as csvfile:
            return len(csv.reader(csvfile))
