import React, {
	useMemo,
} from 'react';


// This table shows the currently selected selectedStrains, as well as options for
// visualisation (bolding, type selectedStrains, etc).
function SelectionTable({
	data,
  selectedStrains,
  setSelectedStrains
}) {

	const removeStrain = (rowId) => {
		setSelectedStrains(old => {
			const newStrains = {...old};
			delete newStrains[rowId];
			return newStrains;
		});
	}

	return (
		<div className="selected-strain-wrapper">
			<table className="selected-strain-table">
				<thead>
					<tr>
						<th>ID</th>
						<th>Name</th>
						<th>Remove</th>
					</tr>
				</thead>
				<tbody>
					{Object.keys(selectedStrains).map(rowId => {
						const row = data[rowId];
						return (
							<tr key={rowId}>
								<td key="id" className="td-selected-strain-id">{row.id}</td>
								<td key="name" className="td-selected-strain-name" title={row.strains.join(", ")}>
									<i>{`${row.genus[0]}. `}{row.epithet}</i>
								</td>
								<td key="remove">
									<button
										className="btn-remove-strain"
										onClick={() => removeStrain(rowId)}
									></button>
								</td>
							</tr>
						);
					})}
				</tbody>
			</table>
		</div>
	);
}

export default SelectionTable;
