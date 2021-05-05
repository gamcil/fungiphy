import React, { useMemo } from 'react';
import { Select } from 'react-dropdown-select';


// TODO: change library to react-select
// this one has weirdness with CSS


// Component for filtering of strains by marker in the StrainTable.
// built using Select component from react-dropdown-select
function MarkerSelector({ options, onChange }) {

	// Don't show selected markers to save space
	const contentRenderer = ({ state }) => (
    <div className="marker-selector-items" style={{ cursor: 'pointer' }}>
      {state.values.length} selected
    </div>
  );

	// Render each item with a checkbox
	const itemRenderer = ({ item, methods }) => (
		<div className="marker-selector-item" onClick={() => methods.addItem(item)}>
			<input
				type="checkbox"
				onChange={() => methods.addItem(item)}
				checked={methods.isSelected(item)}
			/>
			{" "}
			{item.label}
		</div>	
	);

	// Dropdown uses portal to document <body> so we don't overflow the table
	// parent container
	return (
		<div className="marker-selector-wrapper">
			<Select
				multi
				className="marker-selector"
				portal={document.body}
				placeholder="Select"
				onChange={onChange}
				contentRenderer={contentRenderer}
				itemRenderer={itemRenderer}
				options={options.map(opt => ({label: opt, value: opt}))}
				values={[]}
			/>
		</div>
	);
}

export default MarkerSelector;
