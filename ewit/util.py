import json
from redbot.core import data_manager
from ewit import EWit

# One shot utility script to convert old-school json full of quotes to the new format
INPUT_FILE = "quotes.json"
OUTPUT_FILE = "quotes.csv"

START = 0
END = 99999999

# Pull in a quotes file (assuming it's a json file with nothing else but an array of quotes inside)
with open(INPUT_FILE) as f:
    # Quote format is all over the place, so we're not going to try to reparse them in a fancy way
    quotes = [[row] for row in json.load(f)]

# Spin up a dummy version of the cog, so we can easily rewrite everything into it
# Stub out the data manager though!
data_manager.cog_data_path = lambda self: "."
cog = EWit()

# Make sure the output file exists
with open(cog.quotes_file, "w") as f:
    f.write("")

# Start parsing
for i, quote in enumerate(quotes):
    if START <= i <= END:
        cog.register_quote(quote)



