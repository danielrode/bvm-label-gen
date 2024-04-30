
// Author: Daniel Rode
// Init: 28 Nov 2023
// Updated: -


#set page("us-letter")
#set page(
	margin: (
	  	rest: 1cm,
	)
)
#set text(font: "DejaVu Sans Mono")

#let bol_data = yaml("./tmp-bol.yaml")

= BILL OF LADING

#line(length: 100%, stroke: 0.5pt)
#v(10pt)

Order ID(s): #bol_data.order_ids

Pickup Date: `_____________________________`

== Ship From

Colorado Food Enterprises \
3645 Wazee St, Denver, CO 80216

== Deliver To

#for dest in bol_data.destinations [
	- #dest
]

== Currier

Pops Transport

== Cargo

#table(
	columns: (auto, auto, 1fr, auto),
	[*Order \#*], [*Item Code*], [*Description*], [*Quantity*],
	// Display array items as cells
	..for i in bol_data.cargo {
		for j in i {
			([#j],)
		}
	}
)

Approximate Weight: Up to 90 ounces per box

Number of boxes: #bol_data.boxes

== Quality Assurance

Vehicle Internal Temperature: `_________________________`

#v(8pt)
#set text(14pt)

Temp-Taker Signature: `___________________________________` Date: `__________`

#set text(14pt)
#align(bottom)[
Shipper Signature: `_______________________________________` Date: `__________`

#v(8pt)

Currier Signature: `_______________________________________` Date: `__________`
]
