#!/usr/bin/env python3
# Dependencies:
#   typst
#   pypdf
# Init: 15 Aug 2023
# Updated: 21 Aug 2023

import os
import sys
import pathlib as pl
import tempfile as tf
import subprocess as sp

import re
import json
import pypdf
import qrcode

# Variables
orders_list = pl.Path("./tmp/orders.json")
label_template = pl.Path("./label-gen.typ")

# Functions
def typst(path):
    sp.run(['typst', 'compile', path])

def ceiling_div(numer, denom):
    return -(numer // -denom)

# Parse command line arguments
try:
    packing_slips_path = pl.Path(sys.argv[1])
except IndexError:
    print("Usage: gen-labels.py PACKING_SLIPS_PDF_PATH")
    exit(1)

if not packing_slips_path.is_file():
    print("error: File does not exist:", packing_slips_path)
    exit(1)

# Setup workspace
os.makedirs("./tmp", exist_ok=True)

# Extract order information from packing slips
orders = list()
reader = pypdf.PdfReader(packing_slips_path)
for page in reader.pages:
    text = page.extract_text()

    order_id = re.search(r"(?<=^BOULDER VALLEY MEALSOrder #)\d+", text)
    order_id = order_id.group()

    pattern = r"(?<=^SHIP TO\n)[^\n]+\n[^\n]+\n[^\n]+\n"
    match = re.search(pattern, text, re.MULTILINE)
    order_recipient, address1, address2, _ = match.group().split('\n')

    # Generate QR code of order number
    qr_img_path = tf.NamedTemporaryFile(
        dir = './tmp', suffix = '.png', delete = False).name
    qr_img_path = './tmp/' + qr_img_path.split('/')[-1]
    qr = qrcode.make(order_id, border = 0)
    qr.save(qr_img_path)

    # Calculate the number of boxes needed for this order, then add that
    # number of this order's label to be printed
    pattern = \
        r'(?<=\nITEMS QUANTITY\n).+(?=\nThank you for shopping with us!\n)'
    match = re.search(pattern, text, re.MULTILINE|re.DOTALL).group()

    item_count = 0
    pattern = r'[^\d]+ (\d+) of (\d+)$'
    for line in match.split('\n'):
        item_count += int(re.match(pattern, line).groups()[1])

    labels_needed_count = ceiling_div(item_count, 6)
    orders.append([
        labels_needed_count,
        order_recipient, address1, address2,
        order_id, qr_img_path
    ])

# Write extracted order info to file
orders_list.write_text(json.dumps(orders))

# Compile labels to PDF
print("Generating PDF labels...")
typst(label_template)


# TODO
# - do not print labels for packages that are for in-store pickup (my order
# was supposed to be in-store pickup, but it is not)
