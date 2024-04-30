#set text(
  font: "New Computer Modern",
)
#set page(
  paper: "us-letter",
  margin: (x: 1.6cm, y: 1.6cm),
  columns: 2,
  flipped: true,
)
#set par(
  justify: false,
)

#let label(name, address1, address2, orderID, qr_code_pth) = {
  block(
    [
      #grid(
        columns: (150pt, 180pt),
        rows: (135pt, auto),
        gutter: 3pt,
        image("bvm_logo.png"),
        [#align(right, box(align(left, [
          #set text(size: 12pt)
          Boulder Valley Meals \
          3645 Wazee St \
          Denver, CO 80216
        ])))],
      )
      #grid(
        columns: (270pt, 60pt),
        rows: 65pt,
        gutter: 3pt,
        [
          #set text(size: 20pt)
          #name \
          #set text(size: 16pt)
          #address1 \ #address2
        ],
        align(center+bottom, grid(
          rows: (55pt, 10pt),
          image(qr_code_pth),
          [
            #set text(size: 10pt)
            \##orderID
          ],
        ))
      )
      #v(60pt)
    ],
  )
}

#{
  grid(
    columns: (100%, 100%),
    for (count, name, address1, address2, orderID, qr_code_pth) in json("./tmp/orders.json") {
      let c = 0
      while c < count {
        label(name, address1, address2, orderID, qr_code_pth)
        c = c + 1
      }
    }
  )
}


// Can use packing slips from Shopify to get customer information.
