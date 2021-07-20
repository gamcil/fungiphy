import React, {
  useMemo,
  useEffect
} from 'react';

import {
  useTable,
	useGroupBy,
	useExpanded,
  useRowSelect,
  useFilters,
} from 'react-table';

import matchSorter from 'match-sorter';

import IndeterminateCheckbox from './IndeterminateCheckbox';
import MarkerSelector from './MarkerSelector';

const NUC_URL = "https://ncbi.nlm.nih.gov/nuccore"

function compositeClassName(names) {
	const nameList = Object.entries(names).map(
		([key, value]) => value && key
  );
  return nameList.filter(e => !!e).join(" ");
};

function MarkersExistFilter(
	{ column: { filterValue, setFilter, preFilteredRows, id } },
	markers,
	setSelectedMarkers
) {
	const handleChange = values => {
		let selected = values.map(value => value.value);
		setSelectedMarkers(selected);
		setFilter(selected);
	};
	return (
		<MarkerSelector options={markers} onChange={handleChange} />
	);
}

function hasMarkersFilterFn(rows, id, filterValue) {
	if (!filterValue) {
		return rows;
	}
	return rows.filter(row => {
		return (
			filterValue.every(value => row.values.markers.hasOwnProperty(value))
		);
	})

}

function SelectColumnFilter({
  column: { filterValue, setFilter, preFilteredRows, id },
}) {

  // Get possible selection values. Must be memoized.
  const options = useMemo(() => {
    const options = new Set();
    preFilteredRows.forEach(row => {
      options.add(row.values[id])
    });
    return [...options.values()];
  }, [id, preFilteredRows]);

  return (
    <select
      value={filterValue}
      onChange={e => {
        setFilter(e.target.value || undefined);
      }}
    >
      <option value="">All</option>
      {options.map((option, i) => (
        <option key={i} value={option}>
          {option}
        </option>
      ))}
    </select>
  )
}


function FuzzyTextFilter({
  column: {
    filterValue,
    preFilteredRows,
    setFilter
  },
}) {
  const count = preFilteredRows.length;

  return (
    <input
      value={filterValue || ""}
      onChange={e => {
        setFilter(e.target.value || undefined)
      }}
			className="fuzzy-filter"
      placeholder={`Search ${count} records...`}
    />
  );
}


// Find rows where cell value CONTAINS filter value
function containsTextFilterFn(rows, id, filterValue) {
  return rows.filter(row => {
    return row.values[id]
      .toUpperCase()
      .includes(filterValue.toUpperCase());
  });
}

// Find rows where cell value similar to filter value
function fuzzyTextFilterFn(rows, id, filterValue) {
  return matchSorter(rows, filterValue, { keys: [row => row.values[id]] });
}

// Remove filter if string is empty
fuzzyTextFilterFn.autoRemove = value => !value;


function StrainTable({
  data,
  markers,
  selectedStrains,
	expandedStrains,
	setExpandedStrains,
  setSelectedStrains,
  setSelectedMarkers,
}) {

  const columns = useMemo(() => ([
		{Header: "ID", accessor: "id"},
		{Header: "Is type", accessor: "is_ex_type"},
		{Header: "MB#", accessor: "mycobank"},
		{Header: "Genus", accessor: "genus", Filter: SelectColumnFilter, filter: 'select'},
		{
			Header: "Subgenus",
			accessor: "subgenus",
			Filter: SelectColumnFilter,
			filter: 'select',
			Cell: ({ row }) => <span><i>subg</i>. {row.values.subgenus}</span>
		},
		{
			Header: "Section",
			accessor: "section",
			Filter: SelectColumnFilter,
			filter: 'select',
			Cell: ({ row }) => <span><i>sect</i>. {row.values.section}</span>
		},
		{
			Header: "Epithet",
			accessor: "epithet",
			Filter: FuzzyTextFilter,
			filter: 'fuzzyText',
			Cell: ({row}) => {
				if (row.values.is_ex_type) {
					return <span>{row.values.epithet} (type)</span>
				}
				return <span>{row.values.epithet}</span>;
			},
		},
		{
			Header: "Strain names",
			accessor: "strains",
			Filter: FuzzyTextFilter,
			filter: 'containsText',
			Cell: ({ row }) => {
				if (!row.isGrouped) {
					return (
						<ul className="strain-list">
							<li key={row.values.id} className="type">{row.original.holotype}</li>
							{row.values.strains.map(strain => (
								<li className="ex-type">{strain}</li>)
							)}
						</ul>
					);
				};
				return null;
			},
		},
		{
			Header: "Markers",
			accessor: "markers",
			Filter: ({ column }) => {
				return MarkersExistFilter({column}, markers, setSelectedMarkers);
			},
			filter: hasMarkersFilterFn,
			Cell: ({ row }) => {
				if (!row.isGrouped) {
					return (
						<ul className="marker-list">
							{Object.keys(row.values.markers).map(marker => {
								const accession = row.values.markers[marker];
								return (
									<li title={marker}>
										<a href={`${NUC_URL}/${accession}`}>{accession}</a>
									</li>
								);
							})}
						</ul>
					);
				};
				return null;
			}
		},
  ]), [markers, setSelectedMarkers])

  const defaultColumn = useMemo(
    () => ({
      Filter: () => { return null; },
    }), []
  );

  const filterTypes = useMemo(() => (
      { fuzzyText: fuzzyTextFilterFn, containsText: containsTextFilterFn, }
    ), [],
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    prepareRow,
    rows,
    state: {
      selectedRowIds,
			expanded
    },
  } = useTable(
    {
      columns,
      data,
      initialState: {
        // Either initialise selectedRowIds as empty (since selectedStrains in
        // the App object will by empty), or as whatever was previously selected
        // such that we don't lose user selection on route change (i.e. is not
        // reset upon re-render).
        selectedRowIds: {...selectedStrains},
        expanded: expandedStrains,
				// Manually set grouping by Genus, Subgenus and Section columns for
				// tree-like structure
				groupBy: useMemo(() => [
					"genus",
					"subgenus",
					"section",
				], []),
				hiddenColumns: useMemo(() => [
					"genus",
					"subgenus",
					"section",
					"is_ex_type"  // TODO: conditional format rows for type or nontype
				], []),
      },
      filterTypes,
      defaultColumn,
    },
    useFilters,
		useGroupBy,
		useExpanded,
    useRowSelect,
    hooks => {
      hooks.visibleColumns.push((columns, {instance}) => {
				if (!instance.state.groupBy.length) {
					return columns
				}
				
				return [
					{
						id: "taxonomy",
						Header: "Taxonomy",
						Cell: ({row}) => {
							if (row.canExpand) {
								const groupedCell = row.allCells.find(d => d.isGrouped);
								return (
									<span
										{...row.getToggleRowExpandedProps({
											style: { paddingLeft: `${row.depth}rem`, fontWeight: "bold", }
										})}
									>
										{groupedCell.render("Cell")}
										{" "}
										({row.leafRows.length})
									</span>
								);
							}
							return null;
						},
					},
					{
						id: "selection",
						Header: ({ getToggleAllRowsSelectedProps }) => (
							<div>
								<IndeterminateCheckbox {...getToggleAllRowsSelectedProps()} />
						 </div>
						),
						Cell: ({ row }) => (
							<div>
								<IndeterminateCheckbox {...row.getToggleRowSelectedProps()} />
							</div>
						),
					},
					...columns,
				];
			});
		},
  );

  useEffect(() => {
    // Watches for change in selectedRowIds, then propogates it to the App so we
    // can use it in other routes.
    setSelectedStrains(selectedRowIds);
  }, [setSelectedStrains, selectedRowIds]);

	useEffect(() => {
		setExpandedStrains(expanded);
	}, [setExpandedStrains, expanded]);

  return (
    <>
      <table className="strain-table" {...getTableProps()}>
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => {
								const cellClass = `th-${column.id}`;
								return (
									<th className={cellClass} {...column.getHeaderProps({
										className: compositeClassName({
											"taxonomy": column.id === "taxonomy"
										})
									})}>
										{column.render("Header")}
										<div>{column.canFilter ? column.render("Filter") : null}</div>
									</th>
								);
              })}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()}>
                {row.cells.map(cell => {
									if (cell.column.id === "taxonomy") {
										return (
											<th {...cell.getCellProps()}>
												{cell.render("Aggregated")}
											</th>
										);
									};
									const cellClass = `td-${cell.column.id}`;
                  return (
                    <td className={cellClass} {...cell.getCellProps()}>
                      {cell.isPlaceholder ? null : cell.render("Cell")}
                    </td>
                  );
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </>
  )
}

export default StrainTable;
