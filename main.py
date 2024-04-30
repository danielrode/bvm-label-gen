#!/usr/bin/env python3
# Author: Daniel Rode
# Dependencies:
#   Python 3.10+
#   fpdf2 (via pip)
#   pyyaml (via pip)
#   qrcode (via pip)
#   typst (via Winget)
# Init: 15 Aug 2023
# Updated: 30 Apr 2024


import os
import sys
import pathlib as pl
import subprocess as sp
from itertools import cycle

import re
import csv
import yaml
import qrcode
from fpdf import FPDF


# Constants
labels_A4_export_path = './export_labels_A4.pdf'
labels_4x3_export_path = './export_labels_4x3.pdf'
bol_export_path = './export_bol.pdf'
return_address = """\
Boulder Valley Meals
3645 Wazee St
Denver, CO 80216"""

meal_code_map = {
    'Chorizo, Egg, Potato and Rice Burrito Bowl': 'BV-BG',
    'Potato, Chorizo and Egg Burrito Bowl': 'BV-BR',
    'Potato, Egg, Sausage, Cheese and Bacon Burrito Bowl': 'BV-BY',
    'Potato, Sausage and Egg Burrito Bowl': 'BV-BO',
    'Texas-Inspired Bacon Wrapped Chicken Breasts': 'BV-GT',
    'Three Cheese Bacon Wrapped Chicken Breasts': 'BV-GC',
}


# Functions
def ceiling_div(numer, denom):
    return -(numer // -denom)

def get_next_label(label_info):
    global boxes
    midX = 14.4
    midY = 11.75
    iter_pos = cycle([
        (margin, margin),
        (midX, margin),
        (margin, midY),
        (midX, midY),
    ])

    for order_id in label_info:
        i = label_info[order_id]
        item_count, name, street, city_state_zip, orderID = i

        # Calculate the number of boxes/labels needed for this order
        labels_needed_count = ceiling_div(item_count, 6)

        for _ in range(labels_needed_count):
            x, y = next(iter_pos)
            recipient = "\n".join([name, street, city_state_zip])
            destinations.add(', '.join([name, street, city_state_zip]))
            boxes += 1
            yield recipient, orderID, x, y

def get_multi_cell_width(str):
    return max([ pdf.get_string_width(i) for i in str.split('\n') ])

def render_A4_label(recipient, orderID, x, y):
    # x,y is the positional anchor point for the label

    l = 11.8  # Label length cm (this is the content right bound)
    d = 8.5  # Label depth cm (this is the content lower bound)

    # Render logo
    pdf.set_xy(x,y)
    pdf.image('./bvm_logo.png', w=5)

    # Render return address
    pdf.set_font(size=14)
    w = get_multi_cell_width(return_address)
    pdf.set_xy(x+l-w,y)
    pdf.multi_cell(text=return_address, w=99)

    # Render recipient address
    pdf.set_xy(x,y+6)
    pdf.set_font(size=16)
    pdf.multi_cell(text=recipient, w=99)

    # Render QR code and order number
    w = 2
    qr = qrcode.make(orderID, border = 0)
    pdf.set_xy(x+l-w-0.1,y+d-w-1)
    pdf.image(qr.get_image(), w=2)

    pdf.set_font(size=16)
    pdf.set_xy(x+l-w-0.1,pdf.get_y()+0.1)
    pdf.cell(w=2, text=f'#{orderID}', align='C')

def gen_A4_labels_pdf():

    # Compile/render labels and save to PDF
    print("Generating A4 labels PDF...")

    global pdf
    global margin

    pdf = FPDF(orientation='landscape', format='letter', unit='cm')
    margin = 1.6
    pdf.set_margin(margin)
    pdf.set_font('Times', style='', size=16)
    # pdf.add_font(
    #     'DejaVuSerif',
    #     fname='/usr/share/fonts/TTF/DejaVuSerifCondensed.ttf'
    # )
    # pdf.set_font('DejaVuSerif', style='', size=16)

    for recipient, orderID, x, y in get_next_label(label_info):
        if (x, y) == (margin, margin):
            pdf.add_page()

        render_A4_label(recipient, orderID, x, y)

    pdf.output(labels_A4_export_path)

def render_4x3_label(recipient, orderID, x = 0.3, y = 0.3):
    # x,y is the positional anchor point for the label

    l = 9.2  # Label length cm (this is the content right bound)
    d = 7  # Label depth cm (this is the content lower bound)

    # Render logo
    pdf.set_xy(x,y)
    pdf.image('./bvm_logo.png', w=4)

    # Render return address
    pdf.set_font(size=14)
    w = get_multi_cell_width(return_address)
    pdf.set_xy(x+l-w,y)
    pdf.multi_cell(text=return_address, w=99)

    # Render recipient address
    pdf.set_xy(x,y+5)
    pdf.set_font(size=12)
    pdf.multi_cell(text=recipient, w=99)

    # Render QR code and order number
    w = 2
    qr = qrcode.make(orderID, border = 0)
    pdf.set_xy(x+l-w-0.1,y+d-w-1)
    pdf.image(qr.get_image(), w=2)

    pdf.set_font(size=12)
    pdf.set_xy(x+l-w-0.1,pdf.get_y()+0.1)
    pdf.cell(w=2, text=f'#{orderID}', align='C')

def gen_4x3_labels_pdf():

    # Compile/render labels and save to PDF
    print("Generating 4x3 labels PDF...")

    global pdf
    global margin

    pdf = FPDF(orientation='portrait', format=(10.16,7.62), unit='cm')
    margin = 0.5
    pdf.set_margin(margin)
    pdf.set_font('Times', style='', size=12)

    for recipient, orderID, x, y in get_next_label(label_info):
        pdf.add_page()

        render_4x3_label(recipient, orderID)

    pdf.output(labels_4x3_export_path)

def gen_bol_pdf():
    # Sum quantity of specific items per order
    cargo = dict()
    for o in orders:
        meal_name = o['Lineitem name']
        order_id = o['Name'].strip('#')
        quantity = int(o['Lineitem quantity'])
        if (meal_name, order_id) not in cargo:
            cargo[(meal_name, order_id)] = quantity
        else:
            cargo[(meal_name, order_id)] += quantity

    # Format cargo list for BOL
    cargo_list = list()
    for meal_name, order_id in cargo:
        quantity = cargo[(meal_name, order_id)]

        # Order ID, Item Code, Item Description, Quantity
        try:
            meal_code = meal_code_map[meal_name]
        except KeyError:
            continue
        cargo_list.append([
            order_id,
            meal_code,
            "Frozen meal: " + meal_name.replace(',', '')[:32],
            str(quantity),
        ])

    # Save BOL info to YAML file for Typst to read and render
    with open('./tmp-bol.yaml', 'w') as f:
        data = {
            'boxes': boxes,
            'cargo': cargo_list,
            'order_ids': ', '.join(set([i[0] for i in cargo_list])),
            'destinations': list(destinations),
        }
        yaml.dump(data, f)

    # Render BOL PDF with Typst
    sp.run(['typst', 'compile', './bol-template.typ', bol_export_path])

def get_newest_file(pth, glob):
    paths = list(pth.glob(glob))
    if len(paths) == 0:
        return None
    newest = paths[0]
    for p in paths:
        newest.stat() < p.stat()
        newest = p

    return newest


# Main

# Init vars
boxes = 0
destinations = set()

# Parse command line arguments
try:
    orders_csv_path = pl.Path(sys.argv[1])
except IndexError:
    orders_csv_path = get_newest_file(
        pl.Path.home() / "downloads", "orders_export*.csv"
    )
    if (orders_csv_path is None) or (not orders_csv_path.is_file()):
        print("Usage: this-script ORDERS_CSV_PATH")
        exit(1)

if not orders_csv_path.is_file():
    print("error: File does not exist:", orders_csv_path)
    exit(1)

# Import order information from orders CSV
with open(orders_csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    orders = list(reader)

label_info = dict()
for i in orders:
    order_id = i['Name'].strip('#')
    if order_id in label_info:
        label_info[order_id][0] += int(i['Lineitem quantity'])
        continue
    
    city_state_zip = f"{i['Shipping City']}, " 
    city_state_zip += f"{i['Shipping Province']} {i['Shipping Zip']}"
    label_info[order_id] = [
        int(i['Lineitem quantity']),  # Num of items in order
        i['Shipping Name'],
        i['Shipping Street'],
        city_state_zip,
        order_id,
    ]        

# CD to dir where this script resides
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Generate labels PDF
gen_A4_labels_pdf()
gen_4x3_labels_pdf()

# Generate BOL PDF
gen_bol_pdf()
