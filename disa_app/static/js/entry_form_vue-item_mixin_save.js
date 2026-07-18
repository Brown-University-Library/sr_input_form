
// This module collects all the functionality related to saving to the server

// Referents - save

async function saveReferentData_post(referentId, itemId, apiDefinition, requestBody) {

  const fetchOptions = {
          method: apiDefinition.api_method,
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': TOKEN
          },
          body: requestBody
        };

  console.log(`SAVE REFERENT FETCH OPTIONS - posting to ${apiDefinition.api_url}`, 
              fetchOptions);

  if (true) { // TURN OFF/ON REFERENT SAVING
    const response = await fetch(apiDefinition.api_url, fetchOptions);
    console.log('SAVE REFERENT RESPONSE', response);
    const dataJSON = await response.text();
    console.log('SAVE REFERENT RESPONSE JSON', dataJSON);
  }

  // @todo Return value??
};



async function createNewReferentOnServer(currentItemId) {

  // If this is a new referent, then create on server;

  console.log('CREATE REFERENT - INIT');

  // Empty starter data structure

  const requestBody = {
    name:{
      id:'name',
      first:'',
      last:''
    },
    id:'new',
    record_id: currentItemId.toString(),
    roles:[]
  }

  const fetchOptions = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': TOKEN
    },
    body: JSON.stringify(requestBody)
  };

  console.log(`CREATE REFERENT FETCH OPTIONS - posting to ${API_URL_ROOT}entrants/new/`, 
              fetchOptions);

  if (true) { // TURN OFF/ON REFERENT CREATION
    const response = await fetch(`${API_URL_ROOT}entrants/new/`, fetchOptions);
    console.log('CREATE REFERENT RESPONSE', response);
    const dataJSON = await response.json();
    console.log('CREATE REFERENT RESPONSE JSON', dataJSON);
    return dataJSON;
  }
}

// Create a new (blank) referent on server and gather the IDs in the response;
//  update form data

async function addNewReferentToForm(form) {
  if (form.currentReferent && form.currentReferent.FULL_DATA_LOADED) {
      createNewReferentOnServer(form.currentItemId).then(newReferentData => {
        form.currentReferent.id = newReferentData.id;
        form.currentReferentId = newReferentData.id;
        form.currentReferent.names[0].id = newReferentData.name_id;
        form.currentNameId = newReferentData.name_id;
      })
  }
}

// Saves the data for the current referent in 
//  the current record to the server

async function saveReferentDataToServer() {

  console.log('SAVE REFERENT - VUE INSTANCE DATA', this.currentReferent);

  if (this.currentReferent && this.currentReferent.FULL_DATA_LOADED) {

    // Convert from Tagify to DB-ready data structure

    function convertFromTagify(tagifyString) {

      let dataStructure;

      try {
        dataStructure = JSON.parse(tagifyString || '[]').map(
          tagData => { return { id: tagData.dbID, name: tagData.value } }
        );
      } catch (error) {
        dataStructure = [];
      }

      return dataStructure;
    }

    // Map data in Vue to what's expected by the API

    const requestBody = JSON.stringify({
      id: this.currentReferentId.toString(),
      record_id: this.currentItemId.toString(),
      age: this.currentReferent.age_text || '',
      age_text: this.currentReferent.age_text || '',
      age_number: parseFloat(this.currentReferent.age_number) || null,
      age_category: this.currentReferent.age_category || null,
      names: this.currentReferent.names.map(
        name => Object.assign({ }, name, { id: name.id.toString() })
      ),
      occupation_text: this.currentReferent.occupation_text || '',
      origins: convertFromTagify(this.currentReferent.origins),
      races: convertFromTagify(this.currentReferent.races),
      race_text: this.currentReferent.race_text || '',
      roles: [], // @todo ?? this.currentReferent.roles,
      sex: this.currentReferent.sex,
      statuses: convertFromTagify(this.currentReferent.status),
      titles: this.currentReferent.titles.map(
        title => {
          title.name = title.label.valueOf();
          return title 
        }
      ),
      tribes: convertFromTagify(this.currentReferent.tribes),
      vocations: convertFromTagify(this.currentReferent.vocations)
    });

    console.log('SAVE REFERENT - REQUEST', requestBody);
    this.saveStatus = this.SAVE_STATUS.SAVE_IN_PROGRESS;

    saveReferentData_post(
      this.currentReferentId, 
      this.currentItemId,
      this.saveCurrentReferentAPI,
      requestBody
    ).then(
      () => { this.saveStatus = this.SAVE_STATUS.SUCCESS }
    );
  }
}

async function deleteReferentOnServer(referent) {
  const url = `${API_URL_ROOT}entrants/${referent.id}/`,
        fetchOptions = {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': TOKEN
          }
        };

  const response = await fetch(url, fetchOptions);

  if (response.ok) {
    // @todo - trigger data backup?
    return true;
  } else {
    throw Error(response.statusText);
  }
}

// Group: create, save, delete

async function createGroupOnServer(newGroupOptions) {
  console.log(`CREATING NEW GROUP ON SERVER`);
  const url = `${API_URL_ROOT}reference_group/new/`,
        fetchOptions = {
          body: JSON.stringify(newGroupOptions),
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': TOKEN
          }
        };

  const response = await fetch(url, fetchOptions);

  if (response.ok) {
    const dataJSON = await response.json();
    return dataJSON.response.group_data;
  } else {
    throw Error(response.statusText);
  }
}

async function saveGroupDataToServer() {

  if (this.currentGroup) {

    console.log(`SAVING GROUP ${this.currentGroup.uuid.slice(0,5)} TO SERVER`);

    this.saveStatus = this.SAVE_STATUS.SAVE_IN_PROGRESS;
    const url = `${API_URL_ROOT}reference_group/${this.currentGroup.uuid}/`,
          payload = {
            count: parseInt(this.currentGroup.count),
            count_estimated: this.currentGroup.count_estimated,
            description: this.currentGroup.description,
            reference_id: this.currentGroup.reference_id
          },
          fetchOptions = {
            body: JSON.stringify(payload),
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': TOKEN
            }
          };
  
    console.log({ url, payload, fetchOptions });
  
    const response = await fetch(url, fetchOptions);
  
    if (response.ok) {
      this.saveStatus = this.SAVE_STATUS.SUCCESS;
      const dataJSON = await response.json();
      return dataJSON.response.group_data;
    } else {
      this.saveStatus = this.SAVE_STATUS.ERROR;
      throw Error(response.statusText);
    }
  }
}

async function deleteGroupOnServer(group) {
  console.log(`DELETING GROUP ${group.uuid} ON SERVER`);
  const url = `${API_URL_ROOT}reference_group/${group.uuid}/`,
        fetchOptions = {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': TOKEN
          }
        };

  const response = await fetch(url, fetchOptions);

  if (!response.ok) {
    throw Error(response.statusText);
  }
}

// Item: create, save, delete

// createItemOnServer() CURRENTLY NOT USED: saveItemDataToServer() is overloaded to allow
//  for new items. Not a good solution

async function createItemOnServer() {

  /* NOTE: THIS MAY NOT BE USEFUL
           Maybe we just need to create a new entry, it will save automatically,
           (using saveItemDatatoServer()) and then we just reload the 
           data into the local copy OR rename 'new' to whatever */

  const requestBody = {
    locations:[],
    date:'',
    transcription:'',
    record_type:{},
    national_context: 3,
    citation_id: 8, // this.formData.doc.id,
    image_url:'',
    researcher_notes:''
  };

  const url = `${API_URL_ROOT}records/new/`,
        fetchOptions = {
          method: 'POST', // apiDefinition.api_method,
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': TOKEN
          },
          body: JSON.stringify(requestBody)
        };

  console.log('CREATE ITEM', fetchOptions);

  const response = await fetch(url, fetchOptions);
  if (response.ok) {
    const dataJSON = await response.json();
    // this.currentItem.relationships = dataJSON.store;
    // this.saveStatus = this.SAVE_STATUS.SUCCESS;
    console.log('RESPONSE', {response, dataJSON}) ;
  } else {
    // this.saveStatus = this.SAVE_STATUS.ERROR;
    throw Error(response.statusText);
  }
}

async function saveItemDataToServer() {

  console.log(`CALLING ROUTINE TO SUBMIT ITEM DATA - item id ${this.currentItemId}`);
  console.log(' FULL DATA LOADED? ' + this.currentItem.FULL_DATA_LOADED);

  if (this.currentItem && this.currentItem.FULL_DATA_LOADED) {

    this.saveStatus = this.SAVE_STATUS.SAVE_IN_PROGRESS;

    const isNewItem = (this.currentItemId === 'new');

    // Only save current Item (without Referent data)

    // const { referents, ...currentItemDataNoReferents } = this.currentItem;
    // const currentItemCopy = JSON.parse(JSON.stringify(currentItemDataNoReferents));


    // THIS WHOLE LOCATION THING IS WAY TOO COMPLICATED FOR WHAT IT DOES

    const NEW_LOCATION_ID = -1;

    const locations = [],
          makeLocationObj = (tagifyValue) => {

            if (tagifyValue) {

              const tagsData = JSON.parse(tagifyValue),
                    tagData = Array.isArray(tagsData) && tagsData[0]
                      ? tagsData[0]
                      : tagsData;
              // @TODO need to look up if this value already exists and get ID
              // (maybe they typed in the text but didn't select the suggest)
              return {
                id: tagData.dbID || NEW_LOCATION_ID,
                label: tagData.value,
                value: tagData.value
              }
            } else {
              return undefined;
            }
          };

    // YIKES!
    // @todo Currently this.currentItem.location_info[<X>]
    //  is an object with only one property: value
    // Instead, have the Tagify string just sit right off of
    //  e.g. this.currentItem.location_info['Colony/State']

    if (this.currentItem.location_info['Colony/State']) {
      const colStateObj = makeLocationObj(
        this.currentItem.location_info['Colony/State'].value
      );
      if (colStateObj) {
        locations.push(colStateObj);
        if (this.currentItem.location_info['City']) {
          const cityObj = makeLocationObj(
            this.currentItem.location_info['City'].value
          );
          if (cityObj) {
            locations.push(cityObj);
            if (this.currentItem.location_info['Locale']) {
              const localeObj = makeLocationObj(
                this.currentItem.location_info['Locale'].value
              );
              if (localeObj) {
                locations.push(localeObj);
              }
            }
          }
        }
      }
    }

    // Prep item date for API

    let date;

    if (this.currentItem.dateParts.year) {
      const month = this.currentItem.dateParts.month !== -1
          ? this.currentItem.dateParts.month
          : '01',
        day = this.currentItem.dateParts.day
          ? this.currentItem.dateParts.day.toString().padStart(2, '0')
          : '01',
        year = this.currentItem.dateParts.year;
      date = `${month}/${day}/${year}`;
    } else {
      date = null;
    }

    // Compile request JSON

    const requestBody = {
      locations,
      date,
      transcription: this.currentItem.kludge.transcription
                      .replace(/ (style|class|id)="[^"]*"/gi, '')
                      .replace(/&nbsp;/gi, ' '),
      record_type: {
        id: this.currentItem.kludge.reference_type_id,
        value: this.MENU_OPTIONS.formInputDISAItemType[this.currentItem.kludge.reference_type_id],
        label: this.MENU_OPTIONS.formInputDISAItemType[this.currentItem.kludge.reference_type_id]
      },
      national_context: this.currentItem.national_context_id,
      citation_id: this.formData.doc.id,
      image_url: this.currentItem.kludge.image_url,
      // Citation fields for the Record: compile into a hash between 
      //  Zotero field ID (without leading 'z') and value;
      //  Only add if not empty
      record_citation_fields: Object.entries(this.currentItem.citation_fields)
        .filter(([k, v]) => v !== '')
        .reduce((acc, [k, v]) => { acc[k.substring(1)] = v; return acc }, {}),
      researcher_notes: this.currentItem.researcher_notes,
    };

    const httpMethod = isNewItem ? 'POST' : 'PUT';

    const url = `${API_URL_ROOT}records/${this.currentItemId}/`,
          fetchOptions = {
            method: httpMethod,
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': TOKEN
            },
            body: JSON.stringify(requestBody)
          };

    console.log(`SAVE ITEM FETCH OPTIONS - ${httpMethod}ing to ${url}`, fetchOptions);

    if (false) { return }  // DEBUG: Skip send if true

    this.saveStatus = this.SAVE_STATUS.SAVE_IN_PROGRESS;

    // If it's a new item and is in the process of
    //  initializing on the DB, then don't proceed with save
    // If it's a new item and is NOT initializing,
    //  then set the initializing flag to block future saving
    //  until we hear back from the DB that it's initialized

    if (isNewItem) {
      if (this.isInitializing) { 
        return;
      } else {
        this.isInitializing = true;
      }
    }

    const response = await fetch(url, fetchOptions);

    if (response.ok) {

      const dataJSON = await response.json();
      // this.currentItem.relationships = dataJSON.store;
      this.saveStatus = this.SAVE_STATUS.SUCCESS;
      console.log('RESPONSE', {response, dataJSON});

      // If this is a new item, grab server-generated Item ID
      //  and update relevant fields

      if (isNewItem) {
        const itemIdMatch = dataJSON.redirect.match('/editor/records/([^/]+)/');
        if (itemIdMatch && itemIdMatch[1]) {
          // @todo, sometime - if we go with UUIDs, then the ID will be a string
          const newItemDatabaseId = parseInt(itemIdMatch[1]);
          console.log(`NEW ITEM ID: ${newItemDatabaseId}`);
          console.log(`CURRENT ITEM `, this.currentItem);
          this.formData.doc.references.find(r => r.id === 'new').id = newItemDatabaseId;
          this.currentItemId = newItemDatabaseId;
          this.isInitializing = false;
        }
      }

      // Using response data, update tagify fields by Vue ref ID
      // (calls updateFromServer() method on disa-tag component)

      const tagUpdateList = [
        ['colonyStateInput', dataJSON.rec.locations[0]],
        ['townInput', dataJSON.rec.locations[1]],
        ['localeInput', dataJSON.rec.locations[2]]
      ].filter(x => x[1] !== undefined);

      tagUpdateList.forEach(([refID, tagData]) => {
        this.$refs[refID].updateFromServer(tagData);
      });

    } else { // response NOT ok
      this.saveStatus = this.SAVE_STATUS.ERROR;
      throw Error(response.statusText);
    }
  }
}

async function deleteItemOnServer(item) {
  console.log(`DELETING ITEM ON SERVER ID ${item.id}`);
  const url = `${API_URL_ROOT}reference/${item.id}/`,
        fetchOptions = {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': TOKEN
          }
        };

  const response = await fetch(url, fetchOptions);

  if (response.ok) {
    return true;
  } else {
    throw Error(response.statusText);
  }
}


// Relationships
// Note that relationships cannot be edited -- only created and deleted

async function createRelationshipOnServer(relationshipData) {
  
  console.log(`SAVING NEW RELATIONSHIP TO SERVER`, relationshipData);

  const requestBody = {
          sbj: parseInt(relationshipData.subject),
          rel: parseInt(relationshipData.relationshipType),
          obj: parseInt(relationshipData.object),
          section: parseInt(relationshipData.itemId)
        },

        url = `${API_URL_ROOT}relationships/`,
        fetchOptions = {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': TOKEN
          },
          body: JSON.stringify(requestBody)
        };
  // console.log({requestBody, url, fetchOptions});

  console.log('SAVE RELATIONSHIP FETCHOPTIONS', fetchOptions);

  if (true) { // TURN OFF/ON RELATIONSHIP SAVING
    const response = await fetch(url, fetchOptions);
    console.log('SAVE RELATIONSHIP RESPONSE', response);

    if (response.ok) {

      // Save new relationship data to relationship store 

      const dataJSON = await response.json();
      console.log('SAVE RELATIONSHIP RESPONSE JSON', dataJSON.store);
      return dataJSON.store;
    } else {
      console.log(`Error creating a new relationship`, { fetchOptions, response });
    }
  }
}

async function deleteRelationshipOnServer(relationship) {
  console.log(`DELETING RELATIONSHIP ON SERVER ID: ${relationship.id}`);
  const url = `${API_URL_ROOT}relationships/${relationship.id}/record_${this.currentItemId}/`,
        fetchOptions = {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': TOKEN
          }
        };
  
  console.log(`DELETE relationship request sent to: ${url}`);

  const response = await fetch(url, fetchOptions);

  if (response.ok) {
    const dataJSON = await response.json();
    return dataJSON.store;
  } else {
    this.saveStatus = this.SAVE_STATUS.ERROR;
    throw Error(response.statusText);
  }
  
  // @todo - also delete inverse relationship?
}

// Vue Mixin

const saveFunctionsMixin = {

  computed: {

    // Computed properties that are watched to trigger saves
    // @TODO CHECK THIS - I SMELL TROUBLE

    watchMeToTriggerGroupSave: function () {
      return JSON.stringify(this.currentGroup);
    }
  },

  watch: {

    // If current referent ID changes, check if it's for a new Referent;
    //  if so, call addNewReferentToForm()

    currentReferentId: {
      handler: function (refId) {
        if (refId === 'new') {
          addNewReferentToForm(this);
        }
      },
      deep: true
    },

    watchMeToTriggerGroupSave: {
      handler: saveGroupDataToServer
    }
  },

  methods: {
    saveReferentDataToServer,
    deleteReferentOnServer,
    createRelationshipOnServer,
    deleteRelationshipOnServer,
    createGroupOnServer,
    deleteGroupOnServer,
    createItemOnServer,
    deleteItemOnServer,
    saveItemDataToServer
  }
}

export { saveFunctionsMixin }

/*

Proper error handling -- from
https://www.tjvantoll.com/2015/09/13/fetch-and-errors/

function handleErrors(response) {
    if (!response.ok) {
        throw Error(response.statusText);
    }
    return response;
}
fetch("http://httpstat.us/500")
    .then(handleErrors)
    .then(response => console.log("ok") )
    .catch(error => console.log(error) );


*/
