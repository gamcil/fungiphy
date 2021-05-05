const width = 500
const height = 360

let labelsAligned = false
let namesAbbreviated = false
let scaleLength = 0.05
let hideDots = false

function parseNewick(a) {
	/* Parse a Newick format string.
	 * Taken from Newick.js
	*/
	for (var e=[],r={},s=a.split(/\s*(;|\(|\)|,|:)\s*/),t=0;t<s.length;t++) {
		var n=s[t];
		switch(n) {
			case "(":
				var c={};
				r.branchset=[c],e.push(r),r=c;
				break;
			case ",":
				var c={};
				e[e.length-1].branchset.push(c),r=c;
				break;
			case ")":
				r=e.pop();
				break;
			case ":":
				break;
			default:
				var h=s[t-1];")"==h||"("==h||","==h?r.name=n:":"==h&&(r.length=parseFloat(n))
		}}
	if (r.branchset.length === 3) {
		
	}
	return r
}

function serialise(svg) {
	/* Saves the figure to SVG in its current state.
	 * Clones the provided SVG and sets the width/height of the clone to the
	 * bounding box of the original SVG. Thus, downloaded figures will be sized
	 * correctly.
	 * This function returns a new Blob, which can then be downloaded.
	*/
	node = svg.node();
	const xmlns = "http://www.w3.org/2000/xmlns/";
	const xlinkns = "http://www.w3.org/1999/xlink";
	const svgns = "http://www.w3.org/2000/node";
	const bbox = svg.select("g").node().getBBox()

	node = node.cloneNode(true);
	node.setAttribute("width", bbox.width);
	node.setAttribute("height", bbox.height);
	node.setAttributeNS(xmlns, "xmlns", svgns);
	node.setAttributeNS(xmlns, "xmlns:xlink", xlinkns);

	// Adjust x/y of <g> to account for axis/title position.
	// Replaces the transform attribute, so drag/zoom is ignored.
	d3.select(node)
		.select("g")
		.attr("transform", `translate(${Math.abs(bbox.x)}, ${Math.abs(bbox.y)})`)

	const serializer = new window.XMLSerializer;
	const string = serializer.serializeToString(node);
	return new Blob([string], {type: "image/node+xml"});
}

function download(blob, filename) {
	/* Downloads a given blob to filename.
	 * This function appends a new anchor to the document, which points to the
	 * supplied blob. The anchor.click() method is called to trigger the download,
	 * then the anchor is removed.
	*/
	const link = document.createElement("a");
	link.href = URL.createObjectURL(blob);
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
}

function elbow(d) {
	/* Path generator function to draw right angles in the dendrogram. */
	return `M${d.source.y},${d.source.x} V${d.target.x} H${d.target.y}`;
}

function maxLength(d) {
	/* Get longest branch length in hierarchy. */
  return d.data.length + (d.children ? d3.max(d.children, maxLength) : 0);
}

function scaleBranchLengths(data) {
	/* Scale branch lengths in tree. */
	const y = d3.scaleLinear()
		.domain([0, maxLength(data)])
		.range([0, width]);
	data.links().forEach(link => {
		link.target.y = link.source.y + y(link.target.data.length)	
	})
}

const nwk = "((496:0.005057,477:0.006786)98:0.003376,((((469:0.250834,(478:0.064609,476:0.053001)100:0.039468)98:0.037866,((494:0.066681,474:0.041177)100:0.039108,(475:0.043886,482:0.030357)100:0.058288)80:0.009302)100:0.056566,988:0.007194)86:0.001772,481:0.004177)75:0.000001,(962:0.001658,465:0.000001)100:0.005452)98:0.0;"

const ids = {
  "465": {
    "genus": "Aspergillus",
    "epithet": "alliaceus",
    "strainNames": [
      "CBS 536.65",
      "NRRL 315",
      "ATCC 10060",
      "DSM 813",
      "IFO 7538",
      "IMI 51982",
      "IMI 051982ii",
      "QM 1885",
      "WB 315",
      "DTO 034-B3",
      "DTO 046-B1"
    ],
    "isExType": true
  },
  "469": {
    "genus": "Aspergillus",
    "epithet": "avenaceus",
    "strainNames": [
      "CBS 109.46",
      "NRRL 517",
      "ATCC 16861",
      "IMI 16140",
      "LCP 89.2592",
      "LSHBBB 155",
      "QM 6741",
      "WB 517"
    ],
    "isExType": true
  },
  "474": {
    "genus": "Aspergillus",
    "epithet": "coremiiformis",
    "strainNames": [
      "CBS 553.77",
      "NRRL 13603",
      "ATCC 38576",
      "IMI 223069",
      "NRRL 13756"
    ],
    "isExType": true
  },
  "475": {
    "genus": "Aspergillus",
    "epithet": "flavus",
    "strainNames": [
      "CBS 569.65",
      "NRRL 1957",
      "ATCC 16883",
      "IMI 124930",
      "QM 9947",
      "WB 1957"
    ],
    "isExType": true
  },
  "476": {
    "genus": "Aspergillus",
    "epithet": "hancockii",
    "strainNames": [
      "MST FP2241"
    ],
    "isExType": true
  },
  "477": {
    "genus": "Aspergillus",
    "epithet": "lanosus",
    "strainNames": [
      "CBS 650.74",
      "NRRL 3648",
      "IMI 130727",
      "QM 9183",
      "WB 5347"
    ],
    "isExType": true
  },
  "478": {
    "genus": "Aspergillus",
    "epithet": "leporis",
    "strainNames": [
      "CBS 151.66",
      "NRRL 3216",
      "ATCC 16490",
      "NRRL A-14256",
      "NRRL A-15810",
      "QM 8995",
      "RMF99",
      "WB 5188"
    ],
    "isExType": true
  },
  "481": {
    "genus": "Aspergillus",
    "epithet": "neoalliaceus",
    "strainNames": [
      "CBS 143681",
      "DTO 326-D3",
      "CCF 5433",
      "IBT 33110",
      "IBT 33353"
    ],
    "isExType": true
  },
  "482": {
    "genus": "Aspergillus",
    "epithet": "nomius",
    "strainNames": [
      "CBS 260.88",
      "NRRL 13137",
      "ATCC 15546",
      "FRR 3339",
      "IMI 331920",
      "LCP 89.3558",
      "NRRL 6108",
      "NRRL A-13671",
      "NRRL A-13794"
    ],
    "isExType": true
  },
  "494": {
    "genus": "Aspergillus",
    "epithet": "togoensis",
    "strainNames": [
      "CBS 205.75",
      "NRRL 13551",
      "LCP 67.3456 (CBS 272.89 (representative strain))"
    ],
    "isExType": true
  },
  "496": {
    "genus": "Aspergillus",
    "epithet": "vandermerwei",
    "strainNames": [
      "CBS 612.78",
      "DTO 069-D2",
      "DTO 034-B5",
      "NRRL 5108",
      "CCF 5683",
      "IBT 13876"
    ],
    "isExType": true
  },
  "962": {
    "genus": "Aspergillus",
    "epithet": "burnettii",
    "strainNames": [
      "MST FP2249"
    ],
    "isExType": true
  },
  "988": {
    "genus": "Aspergillus",
    "epithet": "magaliesburgensis",
    "strainNames": [
      "PPRI 6165",
      "CMV 007A3"
    ],
    "isExType": true
  }
}

const tree = parseNewick(nwk)
const margins = {
	top: 10,
	bottom: 60,
	left: 10,
	right: 10,
}

const root = d3.hierarchy(tree, d => d.branchset)
	.sum(d => d.branchset ? 0 : 1)
	.sort((a, b) => (a.value - b.value) || d3.ascending(a.data.length, b.data.length))

const cluster = d3.cluster()
	.size([300, 600])
	.separation(() => 1)

cluster(root)
scaleBranchLengths(root)

// Assign unique numeric id to every node in the tree
// + Read internal nodes as support values
root.descendants()
	.forEach((d, i) => {
		d._id = i
		if (d.children) d.support = d.data.name
	})

const plotDiv = d3.select("#plot")
const svg = plotDiv.append("svg")
	.attr("width", 1000)
	.attr("height", 1000)
	.attr("xmlns", "http://www.w3.org/2000/svg")
	.attr("font-family", "sans-serif")
	.attr("font-size", 14)

const g = svg.append("g")
	.attr("transform", "translate(20, 0)")

const y = d3.scaleLinear()
	.domain([0, maxLength(root)])
	.range([0, width]);

const scaleBar = g.append("g")
	.attr("transform", "translate(10, 320)")
scaleBar.append("rect")
	.attr("width", y(scaleLength))
	.attr("height", 1.5)
scaleBar.append("text")
	.text(scaleLength)
	.attr("x", y(scaleLength) / 2)
	.attr("y", 18)
	.attr("text-anchor", "middle")

const extend = g.append("g")
	.attr("fill", "none")
	.attr("stroke", "grey")
	.attr("stroke-dasharray", "2")
const links = g.append("g")
	.attr("fill", "none")
	.attr("stroke", "black")
const support = g.append("g")
const text = g.append("g")
const dots = g.append("g")

const cellEnter = (d, i, n) => {
	/* Populates tooltip with current cell data, and adjusts position to match 
	 * the cell in the heatmap (ignoring <g> transforms).
	*/
	tooltip.html(getTooltipHTML(d))
	let rect = n[i].getBoundingClientRect()
	let bbox = tooltip.node().getBoundingClientRect()
	let xOffset = rect.width / 2 - bbox.width / 2
	let yOffset = rect.height * 1.2
	tooltip
		.style("left", rect.x + xOffset + "px")
		.style("top", rect.y + yOffset + "px")
	tooltip.transition()
		.duration(100)
		.style("opacity", 1)
		.style("pointer-events", "all")
}

function extension(d) {
	if (labelsAligned)
		return `M${d.target.y},${d.target.x} H${width}`
	return `M${d.target.y},${d.target.x} H${d.target.y}`;
}

function getSibling(node) {
  if (!node.parent) return null
  return node.parent.children.find(child => child !== node)
}

function reRoot(node, data) {
	/* Reroot hierarchy on given node.
	 * Essentially copies the ETE toolkit set_outgroup function.
	 */
	if (node === data) return

	let parentOutgroup = node.parent

	// Get subtree root
	let ancestors = node.ancestors()
	let subRoot = ancestors[ancestors.length - 2]
	data.children = data.children.filter(c => c !== subRoot)

	// Create a new node to handle basal trifurcations in unrooted trees.
	// Unrooted trees typically are trifurcating at their root (e.g. RAxML
	// output). So, after removing the (sub)root of our new outgroup from the
	// root's children, check if there is >1 child left. If so, create a new node
	// with zero branch length and the node name from the (sub)root, then add the
	// remaining children in the basal root.
	let downBranch
	if (data.children.length !== 1) {
		downBranch = subRoot.copy()
		downBranch.children = []
		downBranch.length = 0.0
		data.children.forEach(child => {
			downBranch.children.push(child)
			child.parent = downBranch
			data.children = data.children.filter(c => c !== child)
		})
	} else {
		downBranch = data.children[0]
	}

	// Swap children and parents, and transfer branch length/node names.
	let node2
	let nextParent = parentOutgroup
	if (nextParent !== data) {
		let nextChild = nextParent.parent
		let prevParent = null
		let bufferDist = nextParent.data.length
		let bufferSupport = nextParent.support

		while (nextChild !== data) {
			nextParent.children.push(nextChild)	
			nextChild.children = nextChild.children.filter(c => c !== nextParent)

			let bufferDist2 = nextChild.data.length
			let bufferSupport2 = nextChild.support

			nextChild.data.length = bufferDist
			nextChild.support = bufferSupport

			bufferDist = bufferDist2
			bufferSupport = bufferSupport2

			nextParent.parent = prevParent
			prevParent = nextParent

			nextParent = nextChild
			nextChild = nextParent.parent
		}

		nextParent.children.push(downBranch)
		downBranch.parent = nextParent
		nextParent.parent = prevParent

		downBranch.data.length += bufferDist
		downBranch.support = bufferSupport

		node2 = parentOutgroup
		node2.data.length = 0.0

		parentOutgroup.children = parentOutgroup.children.filter(c => c !== node)
	} else {
		node2 = downBranch
	}

	node.parent = data
	node2.parent = data
	data.children = [node, node2]

	let midDist = (node.data.length + node2.data.length) / 2
	node.data.length = midDist
	node2.data.length = midDist
	node2.support = node.support
}

function update(data) {
	/* Updates plot with new data.
	*/
	let t = d3.transition().duration(300)
	let linkId = (d) => `${d.source._id}-${d.target._id}`

	links.selectAll("path")
		.data(data.links(), linkId)
		.join(
			enter => enter.append("path")
				.each(function(d) { d.target.linkNode = this })
				.attr("d", elbow)
				.attr("stroke-width", "1px"),
			update => update.call(
				update => update.transition(t).attr("d", elbow)
			),
		)
		.on("mouseover", e => { d3.select(e.target.linkNode).attr("stroke-width", "5px") })
		.on("mouseleave", e => { d3.select(e.target.linkNode).attr("stroke-width", "1px") })
		.on("click", e => {
			reRoot(e.target, root)
			cluster(root)
			scaleBranchLengths(root)
			update(root)
		})

	extend.selectAll("path")
		.data(data.links().filter(d => !d.target.hasOwnProperty("children")), linkId)
		.join(
			enter => enter.append("path")
				.attr("d", extension)
				.attr("stroke-width", "1px"),
			update => update.call(
				update => update.transition(t).attr("d", extension)
			)
		)

	dots.selectAll("circle")
		.data(data.links(), linkId)
		.join(
			enter => enter.append("circle")
				.each(function(d) { d.target.dotNode = this })
				.attr("r", "4")
        .attr("fill", d => d.source === root ? "green" : "black")
				.attr("cx", d => d.source.y)
				.attr("cy", d => d.source.x)
        .style("opacity", () => hideDots ? 0 : 1)
				.on("mouseover", e => {d3.select(e.target.dotNode).attr("fill", "red")})
				.on("mouseleave", e => {d3.select(e.target.dotNode).attr("fill", "black")})
				.on("click", e => {
					// Swap children on click
					e.source.children = e.source.children.reverse()
					cluster(data)
					scaleBranchLengths(data)
					update(data)
				}),
			update => update.call(
				update => update.transition(t)
					.attr("cx", d => d.source.y)
					.attr("cy", d => d.source.x)
			)
		)

	const labelX = (d) => {
		if (!labelsAligned) return d.y
		let y = d3.scaleLinear()
			.domain([0, maxLength(data)])
			.range([0, width]);
		return y(y.domain()[1])
	}

	// Leaf labels
	const speciesName = (d) => {
		// Generates leaf labels, accounting for abbreviations
		let item = ids[d.data.name]
		let genus = (namesAbbreviated) ? `${item.genus[0]}.` : item.genus
		return `${genus} ${item.epithet}`
	}
	const speciesStrain = (d) => {
		// Gets first strain name of a leaf
		let item = ids[d.data.name]
		return item.strainNames[0]
	}
	const hoverShadowEnter = (_, i, n) => {
		// Adds text shadow on leaf labels and sets cursor
		d3.select(n[i])
			.style("text-shadow", "#FC0 1px 0 10px")
			.attr("cursor", "pointer")
	}
	const hoverShadowLeave = (_, i, n) => {
		// Removes text shadow on leaf labels
		d3.select(n[i]).style("text-shadow", "none")
	}
	const boldSpecies = (_, i, n) => {
		// Toggles bold font weight on leaf labels
		let item = d3.select(n[i].parentElement)
		let prev = item.style("font-weight")
		item.style("font-weight", (prev === "bold") ? "normal" : "bold")
	}
	text.selectAll("text")
		.data(data.leaves(), d => d.data.name)
		.join(
			enter => {
				enter = enter.append("text")
					.attr("dx", "0.5em")
					.attr("dy", "0.31em")
					.attr("x", labelX)
					.attr("y", d => d.x)
				enter.append("tspan")
					.text(speciesName)
					.attr("class", "spName")
					.attr("font-style", "italic")
					.on("mouseenter", hoverShadowEnter)
					.on("mouseleave", hoverShadowLeave)
					.on("click", boldSpecies)
				enter.append("tspan")
					.text(speciesStrain)
					.attr("dx", 3)
					.attr("class", "spStrain")
					.attr("font-style", "normal")
					.on("mouseenter", hoverShadowEnter)
					.on("mouseleave", hoverShadowLeave)
					.on("click", (d, i, n) => {
						// Add radio buttons for each strain name to modal
						let label = d3.select(n[i])
						let current = label.text()
						let strain = ids[d.data.name]
						let radios = strain.strainNames.map((sn, i) => `
							<div class="modalChoice">
							<input type="radio" id="${i}" name="strain" value="${sn}"
								${sn === current ? "checked" : ""}>
							<label for="${i}">${sn}</label></div>
						`).join("")

						// Change label text on input change
						d3.select(".modalList")
							.html(radios)
							.selectAll("input")
							.on("change", function() {
								label.text(this.value)
							})

						// Show modal and bind hiding to cancel button
						let modal = d3.select("#modal")
						let rect = n[i].getBoundingClientRect()
						let bbox = modal.node().getBoundingClientRect()
						let xOffset = rect.width / 2 - bbox.width / 2
						let yOffset = rect.height * 1.2
						modal.style("display", "inline-block")
							.style("left", rect.x + xOffset + "px")
							.style("top", rect.y + yOffset + "px")
						modal.select("#closeModal")
							.on("click", () => modal.style("display", "none"))
					})
				enter.append("tspan")
					.text("T")
					.attr("dx", 1)
					.attr("class", "spType")
					.attr("font-size", 10)
					.attr("dy", -5)
					.style("opacity", d => d.isExType ? 1 : 0)
				return enter
			},
			update => update.call(
				update => update.transition(t)
					.attr("x", labelX)
					.attr("y", d => d.x),
			)
		)

	// Support values
	// Draws based on d3 hierarchy links. Each link is identified by the unique
	// _id attribute on the source/target of the link. The support value taken
	// from the internal node names is drawn near the target node.
	support.selectAll("text")
		.data(
			data.links().filter(d => d.target.hasOwnProperty("children")),
			d => `support-${d.source._id}-${d.target._id}`
		)
		.join(
			enter => enter.append("text")
				.text(d => d.target.support)
				.attr("font-size", 10)
				.attr("x", d => d.target.y)
				.attr("y", d => d.target.x)
				.attr("dx", ".5em")
				.attr("dy", ".3em")
				.attr("text-anchor", "start"),
			update => update.call(
				update => update.transition(t)
					.attr("x", d => d.target.y)
					.attr("y", d => d.target.x)
			)
		)

	d3.select("#alignLabels")
		.on("click", e => {
			labelsAligned = !labelsAligned
			text.selectAll("text")
				.transition(t)
				.attr("x", labelX)
			extend.selectAll("path")
				.transition(t)
				.attr("d", extension)
				.style("opacity", labelsAligned ? "1" : "0")
		})

	d3.select("#abbrevNames")
		.on("click", e => {
			namesAbbreviated = !namesAbbreviated
			text.selectAll(".spName").text(speciesName)
		})

	d3.select("#btn-save-svg")
		.on("click", () => {
			const blob = serialise(svg)
			download(blob, "fungphy.svg")
		})

  d3.select("#btn-hide-dots")
    .on("click", e => {
      hideDots = !hideDots
      dots.style("opacity", hideDots ? 0 : 1) 
    })

  d3.select("#btn-sort-desc")
    .on("click", () => {
      data.sort((a, b) => b.height - a.height || d3.descending(a.data.length, b.data.length))
      console.log(data)
			cluster(data)
			scaleBranchLengths(data)
      update(data)
    })

  d3.select("#btn-sort-asc")
    .on("click", () => {
      data.sort((a, b) => a.height - b.height || d3.ascending(a.data.length, b.data.length))
			cluster(data)
			scaleBranchLengths(data)
      update(data)
    })

	d3.select("#scaleLength")
		.on("change", function() {
			scaleBar.selectAll("rect")
				.attr("width", y(+this.value))
			scaleBar.selectAll("text")
				.text(this.value)
				.attr("x", y(+this.value) / 2)
		})
}

update(root)
