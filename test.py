import requests
import re

def decode_secret_message(url):
    # Download the document
    response = requests.get(url)
    content = response.text

    # Find all the character positions from the table
    chars = {}
    max_x = 0
    max_y = 0

    # Look for table rows with x | character | y format
    lines = content.split('\n')
    for line in lines:
        # Match lines like "27 | █ | 0 |"
        match = re.search(r'(\d+)\s*\|\s*([█░])\s*\|\s*(\d+)', line)
        if match:
            x = int(match.group(1))
            char = match.group(2)
            y = int(match.group(3))
            
            chars[(x, y)] = char
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y

    # Make the grid and print it
    for y in range(max_y + 1):
        line = ""
        for x in range(max_x + 1):
            if (x, y) in chars:
                line += chars[(x, y)]
            else:
                line += " "
        print(line)