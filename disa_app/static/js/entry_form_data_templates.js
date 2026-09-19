

// These are the definitions of 'blank' data structures
// They're necessary in part because Vue likes to have all
//  the properties defined upon creation, which doesn't mix well
//  with incremental enhancement (which is the way that the API works).
// Also, they're useful when creating a blank entry to create a 
//  new record


const ITEM_TEMPLATE = {
  dateParts: {
    day:undefined,
    month:-1,
    year:undefined
  },
  id: '',
  location_info: {
    Locale:{
      id: undefined,
      name: undefined,
      type: 'Locale'
    },
    City:{
      id: undefined,
      name: undefined,
      type: 'City'
    },
    'Colony/State':{
      id: undefined,
      name: undefined,
      type: 'Colony/State'
    }
  },
  national_context_id: '',
  reference_type_id: 'IGNORE ME',
  referents:[],
  relationships:[],
  researcher_notes: '',
  groups:[],
  transcription: 'IGNORE ME',
  citation_fields: {},
  // image_url: '',
  kludge:{
    transcription: '',
    reference_type_id: '13',
    image_url: ''
  },
  FULL_DATA_LOADED:false
};

const REFERENT_TEMPLATE = {
  age_text: undefined,
  age_integer: null,
  age_category: undefined,
  id: 'new',
  names:[
    {
      first:'',
      id:'name',
      last:'',
      name_type:'8' // Needs to have a value or breaks
    }
  ],
  occupation_text: undefined,
  origins:'[]', // Tagify
  races:'[]', // Tagify
  race_text: undefined,
  record_id: undefined,
  roles:'[]', // Tagify
  sex:'',
  titles:[],
  tribes:'[]', // Tagify
  vocations:'[]', // Tagify
  FULL_DATA_LOADED: true
};

// Make a copy of the given template

function copyTemplate(template) {
  return JSON.parse(
    JSON.stringify(template)
  )
}

// Interface - create copies of template data structures

const DATA_TEMPLATES = {
  get ITEM() {
    return copyTemplate(ITEM_TEMPLATE)
  },
  get REFERENT() {
    return copyTemplate(REFERENT_TEMPLATE)
  }
}

export { DATA_TEMPLATES }

