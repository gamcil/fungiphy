import React, {
  useState,
  useEffect,
  useMemo
} from 'react';

import {
	Tabs,
	Panel,
	useTabState,
} from '@bumaga/tabs';

import './App.css';
import StrainTable from './StrainTable';
import SelectionTable from './SelectionTable';
import Download from './Download';


async function asyncFetch(uri) {
  let response = await fetch(uri);
  let data = await response.json();
  return data;
}


const cn = (...args) => args.filter(Boolean).join(" ");
const Tab = ({ children }) => {
	const { isActive, onClick } = useTabState();
	return (
		<button className={cn("tab", isActive && "active")} onClick={onClick}>
			{children}
		</button>
	);
}


function App() {

  const [markers, setMarkers] = useState([]);
  const [strains, setStrains] = useState([]);
  const [setting, setSetting] = useState({});

	const [expandedStrains, setExpandedStrains] = useState([]);
  const [selectedMarkers, setSelectedMarkers] = useState([]);
  const [selectedStrains, setSelectedStrains] = useState({});

	const [showFastaModal, setShowFastaModal] = useState(false);
	const [fastaModalRecords, setFastaModalRecords] = useState({});

  // Selected strains should drive the default settings state, however do not
  // overwrite previously set 'true' values.
  useEffect(() => {
    const newSetting = setting;
    Object.keys(selectedStrains).forEach(rowId => {
      if (!newSetting.hasOwnProperty(rowId)) {
        newSetting[rowId] = {
          bold: false,
          strain: false,
          outgroup: false,
        };
      }
    });
    setSetting(newSetting);
  }, [setting, selectedStrains]);


	// Fetch strains and marker types from fungphy API upon page load. No items
	// being in the useEffect dependency array should mean this is only called
	// once.
  useEffect(() => {
    asyncFetch("/strains").then(data => setStrains(data.strains));
    asyncFetch("/markers").then(data => setMarkers(data.markers));
  }, []);

  const data = useMemo(() => strains, [strains]);

	const canVisualise = () => {
		return selectedMarkers.length > 15;
	}

  return (
		<div className="page">

			<div className="header">
				<h2 id="h2-header">fungphy</h2>
				<span>Multi-locus phylogeny with fungal barcodes</span>
			</div>

			<div className="selection">
				<Tabs>
					<div className="tab-list">
						<Tab>Strain table</Tab>
						<Tab>Upload custom strains</Tab>
						<Tab>Upload a tree</Tab>
					</div>

					<Panel>
						<div className="strain-table-wrapper">
							<StrainTable
								data={data}
								markers={markers}
								selectedStrains={selectedStrains}
								expandedStrains={expandedStrains}
								setExpandedStrains={setExpandedStrains}
								setSelectedStrains={setSelectedStrains}
								setSelectedMarkers={setSelectedMarkers}
							/>
						</div>
					</Panel>
					<Panel>User strain uploads...</Panel>
					<Panel>User tree uploads...</Panel>
				</Tabs>
			</div>          

			<div className="sidebar">
				<h4>Selected strains</h4>
				<SelectionTable
					data={data}
					setting={setting}
					setSetting={setSetting}
					selectedMarkers={selectedMarkers}
					selectedStrains={selectedStrains}
					setSelectedStrains={setSelectedStrains}
				/>
				<h4>Selected markers</h4>
				<div className="selected-markers">
					<ul className="selected-marker-list">
						{selectedMarkers.map(m => (
							<li>{m} <button/></li>
						))}
					</ul>
				</div>
				<h4>Download</h4>
				<Download data={data}
					selectedMarkers={selectedMarkers}
					selectedStrains={selectedStrains}
				/>
				<h4>Visualise</h4>
				<button
					id="visualise"
					disabled={
						Object.keys(selectedStrains).length > 15 ? true : null
					}
				>Visualise!</button>
			</div>
		</div>
  );
}

export default App;
