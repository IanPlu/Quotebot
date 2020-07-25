from ewit import EWit

cog = EWit()

# Make sure the test file is empty
with open("quotes.csv", "w") as f:
    f.write("")

test_body = "You know what they say, hide in plain sight if you like Christmas"
test_source = "Louis"
test_comment = "incoherently, on the spirit of the season"

test_body2 = "Yeah BONER!"
test_source2 = "Phillip"

test_body3 = "Oh really? It's Horse of course"

test_stored_quote = "|".join([ test_body, test_source, test_comment ])
test_command_input = [ test_body, "-", test_source + "," ] + test_comment.split(" ")

test_formatted_quote = "\"" + test_body + "\" - " + test_source + ", " + test_comment
test_formatted_quote2 = "\"" + test_body2 + "\" - " + test_source2
test_formatted_quote3 = "\"" + test_body3 + "\""

def test_write_row():
    result = cog.__write_row__(test_body, test_source, test_comment)
    assert result

def test_read_row():
    result = cog.__read_row__(0)
    assert result == test_stored_quote

def test_get_quote_by_number():
    # Write multiple quotes
    cog.__write_row__(test_body2, test_source2, "")
    cog.__write_row__(test_body3, "", "")

    result = cog.get_quote(0)
    assert result == test_formatted_quote

    result = cog.get_quote(1)
    assert result == test_formatted_quote2

    result = cog.get_quote(2)
    assert  result == test_formatted_quote3

def test_get_random_quote():
    result = cog.get_random_quote()
    assert result in [ test_formatted_quote, test_formatted_quote2, test_formatted_quote3 ]

def test_register_quote():
    result = cog.register_quote(test_command_input)
    assert result == "Quote added!"

    result = cog.get_quote(3)
    assert result == test_formatted_quote

