import React, {useState, useRef} from 'react';


const Fasta = (markers, preRef) => {

	if (!markers) {
		return null;
	}

	const formRecord = (marker) => {
		const organism = `[organism=${marker.genus} ${marker.epithet}]`
		const strain = `[strain=${marker.strains[0]}]`;
		return (
			<>
				<b>
					{`>${marker.strain_id} ${organism} ${strain}`}
				</b>
				<br />
				{marker.sequence}
			</>
		);
	}

	return (
	 <pre ref={preRef}>
		 {markers.map(marker => (
			 <> {formRecord(marker)} </>
		 ))}
	 </pre>
	);
}

/* Expects an object containing FASTA records keyed on type, as returned by
 * the /react/sequences endpoint.
*/
function FastaModal({ handleClose, show, records }) {
	const [activeTab, setActiveTab] = useState("");

	const preRef = useRef();
	const [copySuccess, setCopySuccess] = useState("");

	if (!records) {
		return null;
	}

	const markers = Object.keys(records);
	const visibleClass = show ? "display-block" : "display-none";

	const copyFasta = (e) => {
		e.preventDefault();
		preRef.current.focus();
		console.log(preRef);
		document.execCommand("copy");
		e.target.focus();
		setCopySuccess("Copied!");
	}

	return (
		<div className={`modal-bg ${visibleClass}`}>
			<div className={`modal ${visibleClass}`}>
				<ul className="marker-type-tablist">
					{markers.map(marker => {
						const active = (
							(activeTab && marker === activeTab)
							|| (!activeTab && marker === markers[0])
								? "active"
								: ""
						);
						return (
							<li
								className={`marker-type-tab ${active}`}
								onClick={e => {
									console.log(e.target);
									setActiveTab(e.target.textContent)
								}}
							>{marker}</li>
						);
					})}
				</ul>	
				<div className="marker-fasta">
					{activeTab
						? Fasta(records[activeTab], preRef)
						: Fasta(records[markers[0]], preRef)
					}
				</div>
				<div className="buttons">
					<button onClick={copyFasta}>Copy Sequences</button>
					{copySuccess}
					<button onClick={handleClose}>Close</button>
				</div>
			</div>
		</div>
	);
}


export default FastaModal;
