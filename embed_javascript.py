#!/usr/bin/env python3

embedding = ""
hex_digits = "0123456789ABCDEF"
with open("index.js", "rb") as f:
    for byte in f.read():
        embedding += "\\x" + hex_digits[byte>>4] + hex_digits[byte&0xF]

new_content = ""
with open("__init__.py", "r") as f:
    for line in f.readlines():
        if line.startswith('EMBEDDED_JAVASCRIPT_FILE_BYTES = b"'):
            new_content += 'EMBEDDED_JAVASCRIPT_FILE_BYTES = b"' + embedding + '"'
        else:
            new_content += line

with open("__init__.py", "w") as f:
    f.write(new_content)
