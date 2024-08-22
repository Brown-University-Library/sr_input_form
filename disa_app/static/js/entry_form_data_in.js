
import {LOCAL_SETTINGS} from './entry_form_settings.js';
import {DATA_TEMPLATES} from './entry_form_data_templates.js';

// Convert an array into a form that Tagify understands

function prepareForTagify(data) {

  let tagifiedData;
  if (Array.isArray(data) && data.length > 0) {
    if (data[0].id && data[0].label) {
      tagifiedData = JSON.stringify(data.map(dataItem => {
        return { value: dataItem.label, dbID: dataItem.id }
      }));
    }
  } else if (data.id !== undefined && data.label !== undefined) {
    tagifiedData = JSON.stringify({ 
      value: dataItem.label, 
      dbID: dataItem.id
    });
  } else {
    tagifiedData = '[]';
  }

  //console.log('TAGIFYING FROM ', data, ' TO ', tagifiedData);

  return tagifiedData;
}




// SOURCE
// main routine to prepare data structure from browse.json
// for use by Vue

function preprocessSourceData(data) {

  // Convert date formats so that they can be inserted into
  //  date input element -- DISABLED, putting dates in a text field for now

  function getDateInFormFormat(dbDateString) {
    const date = new Date(dbDateString),
          yyyy = date.getFullYear(),
          mm = (date.getMonth() + 1).toString().padStart(2,'0'),
          dd = date.getDate().toString().padStart(2,'0')
    return `${yyyy}-${mm}-${dd}`;
  }

  // data.formData.doc.fields.date = getDateInFormFormat(data.formData.doc.fields.date);
  data.formData.doc.fields.date = data.formData.doc.fields.date;
  // data.formData.doc.fields.accessDate = getDateInFormFormat(data.formData.doc.fields.accessDate);
  data.formData.doc.fields.accessDate = data.formData.doc.fields.accessDate;

  // Merge incoming data , i.e., browse.json, with data structure template to create a
  //  full data structure

  data.formData.doc.references = data.formData.doc.references.map(
    item => Object.assign({}, DATA_TEMPLATES.ITEM, item)
  );

  data.NEW_USER_TEMPLATE = data.formData.new_user_template.sample_payload; 
  delete data.formData.new_user_template;

  // Add registers for Vue implementation

  data.currentItemId     = -1;
  data.currentReferentId = -1;
  data.currentNameId     = -1;

  // Add accessors for API registry

  data.formData.user_api_info.get_user_info.api_url_forID = function (referentID) {
    return data.formData.user_api_info.get_user_info.api_url.replace('THE-REFERENT-ID', referentID);
  }

  // Trim & move location_stuff to MENU_OPTIONS
  // (location_stuff is where Birkin puts value tables, etc.)

  data.MENU_OPTIONS.formInputDISAColonyState = data.formData.location_stuff.col_state_list.reduce(
    (colStateHash, colStateLoc) => Object.assign(colStateHash, { [colStateLoc.id]: colStateLoc.value }),
    {}
  );

  data.MENU_OPTIONS.formInputDISAColonialContext = data.formData.location_stuff.natl_ctxs_list.reduce(
    (locHash, currLoc) => Object.assign(locHash, { [currLoc.id]: currLoc.value }),
    {}
  );

  data.MENU_OPTIONS.formInputDISATown = data.formData.location_stuff.towns_list.reduce(
    (townHash, currTown) => Object.assign(townHash, { [currTown.id]: currTown.value }),
    {}
  );

  data.MENU_OPTIONS.formInputDISAPlaceInfo = data.formData.location_stuff.addl_loc_list.reduce(
    (addLocHash, currAddLoc) => Object.assign(addLocHash, { [currAddLoc.id]: currAddLoc.value }),
    {}
  );
// Commented out for temporarily overriding for fall `23 data cleaning
// (the record type values will come from entry_form_settings.js instead of the server)
//
//  data.MENU_OPTIONS.formInputDISAItemType = data.formData.location_stuff.rec_types_list.reduce(
//    (recTypeHash, currRecType) => Object.assign(recTypeHash, { [currRecType.id]: currRecType.value }),
//    {}
//  );

// Commented out for temporarily overriding for summer `23 data cleaning
// (the status menu values will come from entry_form_settings.js instead of the server)
//
//data.MENU_OPTIONS.formInputDISAPersonStatus = data.formData.location_stuff.status_list.reduce(
//  (statusHash, currStatus) => Object.assign(statusHash, { [currStatus]: currStatus }),
//  {}
//);

  // more stuff in data.formData.location_stuff dealt with here ...
  // addl_loc_list

  // delete data.formData.location_stuff;

  return data;
}

async function getSourceData() {

  const dataURL = new URL(window.location.toString());
  dataURL.hash = '';
  dataURL.search = '?format=json';

  const response = await fetch(dataURL.href),
        dataJSON = await response.json(),
        dataWithSettings = Object.assign({}, LOCAL_SETTINGS, { formData: dataJSON });
  return preprocessSourceData(dataWithSettings);
}


// ITEM (record)

function preprocessItemData(itemData, oldItemData, relationshipsData, referentData) {

  const itemDate = itemData.rec.date ? new Date(itemData.rec.date) : null;

  // Location info: ID is present only in oldItemData BUT
  //  Type is located only in itemData -- need to combine

  const locationInfo = itemData.rec.locations.map(location1 => {
    
    // Look up this location in itemData in oldItemData

    const location2 = oldItemData.location_info.find(
      loc2 => loc2.location_name === location1.label
    );
    
    // Combine the ID from itemData and label from oldItemData
    //  and prepare for tagify

    const tagifiedValue = prepareForTagify([{
      id: location1.id,
      label: location2.location_name
    }]);

    // Mix in the type from itemData and voila! Easy as pie

    return { 
      value: tagifiedValue, 
      type: location2.location_type 
    };
  });

  const locationDefaults = {
      Locale: { value: '' },
      City: { value: '' },
      'Colony/State': { value: '' }
    },
    locationInfoByType = locationInfo.reduce(
      (locationHash, location) => Object.assign(
        {}, locationHash, { [location.type]: location }
      ), locationDefaults
    );

  if (locationInfoByType[null]) { // Sometimes the API lists Locale data as type 'null' (??)
    locationInfoByType.Locale = Object.assign({},
      locationInfoByType[null],
      { type: 'Locale' }
    );
    delete locationInfoByType[null];
  }

  const processedItemData = {
    // date: itemData.rec.date,
    dateParts: {
      day:   itemDate ? itemDate.getDate()      : undefined,
      month: itemDate ? (itemDate.getMonth() + 1).toString().padStart(2, '0') : -1,
      year:  itemDate ? itemDate.getFullYear()  : undefined
    },
    id: itemData.rec.id,
    location_info: locationInfoByType,
    national_context_id: itemData.rec.national_context,
    reference_type_id: 'IGNORE ME', // itemData.rec.record_type.id,
    // reference_type_name: itemData.rec.record_type.label,
    referents: referentData,
    relationships: relationshipsData,
    // referents: getAdditionalReferentInfo(itemData.entrants),
    groups: itemData.groups.group_data,
    transcription: 'IGNORE ME', // itemData.rec.transcription,
    image_url: itemData.rec.image_url,
    // Citation field IDs (which are integers) need to be prefixed with
    //  a letter for Vue to accept them (I chose 'z' for 'zotero')
    citation_fields: Object.entries(itemData.rec.citation_fields)
        .reduce((acc, [key, value]) => { acc['z' + key] = value; return acc }, {}),
    researcher_notes: itemData.rec.researcher_notes,

    // I have no idea why this works -- without these properties being inside of a
    //  wrapper object, they're not Vue-responsive

    kludge: {
      transcription: itemData.rec.transcription,
      reference_type_id: itemData.rec.record_type.id,
      image_url: itemData.rec.image_url
    },

    FULL_DATA_LOADED: true // Flag
  }

  return processedItemData;
}

// Get item data (including relationships) -- return Promise

async function getItemData(itemId, oldItemData, apiInfo) {

  if (itemId) {

    // data_itemrecord_api_url_root variable set in redesign_citation.html
    const dataURL = `${data_itemrecord_api_url_root}${itemId}/`,
          itemDataPromise = fetch(dataURL).then(response => response.json()),
          referentDataPromise = itemDataPromise.then(itemData => {
            return getReferentsData(
              itemData.entrants.map(referent => referent.id), 
              itemId,
              apiInfo
            );
          }),
          relationshipsDataPromise = getRelationshipsData(itemId);

    // fetch all THREE API endpoints: referent, relationships, AND record
    return Promise.all([referentDataPromise, relationshipsDataPromise, itemDataPromise])
           .then(([referentData, relationshipsData, itemData]) => {
      return preprocessItemData(itemData, oldItemData, relationshipsData, referentData);
    });
  } else {
    return undefined
  }
}


// REFERENT

// Referent data - called by getItemData

async function getReferentsData(referentIDs, itemID, apiDefinition) {
  return Promise.all(referentIDs.map(
    referentID => getReferentData(referentID, itemID, apiDefinition))
  );
}

function preprocessReferentData(referentData) {

  // The API gives us name types as string labels, but borks
  //   the entry upon save if it's anything but a number (ID).

  // Convert name type to number

  const nameTypesEntries = Object.entries(LOCAL_SETTINGS.MENU_OPTIONS.formInputDISAItemPersonNameType);

  referentData.names.forEach(name => {
    const nameTypeAsLabel = name.name_type,
          nameTypeAsID_all = nameTypesEntries.find(n => n[1] === nameTypeAsLabel);
    name.name_type = nameTypeAsID_all ? nameTypeAsID_all[0] : '';
  });

  // Tagify fields -- races, tribes, vocation

  referentData.races     = prepareForTagify(referentData.races);
  referentData.tribes    = prepareForTagify(referentData.tribes);
  referentData.vocations = prepareForTagify(referentData.vocations);
  referentData.status    = prepareForTagify(referentData.enslavements);
  referentData.origins   = prepareForTagify(referentData.origins);

  delete referentData.enslavements;

  referentData.FULL_DATA_LOADED = true;

  return referentData;
}

async function getReferentData(referentId, itemId, apiDefinitions) {

  const apiDefinition = apiDefinitions.get_user_info;
  
  if (referentId) {
    const dataURL = apiDefinition.api_url_forID(referentId),
          response = await fetch(dataURL, { 
            method: apiDefinition.api_method,
            headers: {
              'Content-Type': 'application/json'
            }
          }), // @todo need to handle 404s etc.
          dataJSON = await response.json();
    return preprocessReferentData(dataJSON.ent);
  } else {
    return undefined;
  }
}


// RELATIONSHIP

// Get relationships data

function preprocessRelationshipsData(relationshipData) {
  return relationshipData.store;
}

async function getRelationshipsData(itemId, apiDefinition) {
  const dataURL = `${API_URL_ROOT}sections/${itemId}/relationships/`,
        response = await fetch(dataURL, { 
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        }), // @todo need to handle errors
        dataJSON = await response.json();
  return preprocessRelationshipsData(dataJSON);
}

export { getSourceData, getItemData, getRelationshipsData }
