import React, {useState} from 'react';


async function downloadSequences({
	data,
	markers,
	strains,
	aligned,
	concatenated,
}) {
	const response = await fetch("/react/sequences", {
		method: "POST",
		headers: {
			"Accept": "application/json",
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			"markers": markers,
			"strains": Object.keys(strains).map(rowId => data[rowId].id),
			"aligned": aligned,
			"concatenated": concatenated,
		}),
	})
	await response
		.blob()
		.then(blob => {
			// Create hidden anchor element that will be used to trigger
			// file download after receiving response from Flask.
			const url = window.URL.createObjectURL(blob)
			const a = document.createElement("a");
			a.style.display = "none";
			a.href = url;
			a.download = "fungiphy.zip";
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
		})
};


function Download({
	data,
	selectedMarkers,
	selectedStrains,
}) {

	const [aligned, setAligned] = useState(false);
	const [concatenated, setConcatenated] = useState(false);

	return (
		<div className="user-actions">
			<div className="user-downloads">
				<table>
					<tbody>
						<tr>
							<td><label for="aligned">Aligned</label></td>
							<td>
								<input
									id="aligned"
									type="checkbox"
									onChange={(e) => setAligned(e.target.checked)}
								/>
							</td>
						</tr>
						<tr>
							<td><label for="concatenated">Concatenated</label></td>
							<td>
								<input
									id="concatenated"
									type="checkbox"
									onChange={(e) => setConcatenated(e.target.checked)}
								/>
							</td>
						</tr>
					</tbody>
				</table>
				<button
					id="download-sequences"
					onClick={() => downloadSequences({
						data: data,
						markers: selectedMarkers,
						strains: selectedStrains,
						aligned: aligned,
						concatenated: concatenated,
					})}
				>Download</button>
			</div>
		</div>
	);
}


export default Download;
