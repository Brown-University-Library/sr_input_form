
export const LOCAL_SETTINGS = {

  AGE_BY_NUMBER_CHECKBOX_ID: "formInputSpecifiedByNumber",
  AGE_BY_NUMBER_DISPLAY_CSS_CLASS: "age-as-number",
  DOC_TYPE_ELEM_ID: "document_type",

  // API endpoints -- NOT BEING USED

  API_ENDPOINT_URL: {},

  // Data structure for showing / hiding citation fields

  FIELDS_BY_DOC_TYPE: {
    // Book
    20: {
      required: ["author", "date", "pages", "place", "publisher", "title"],
      optional: [
        "abstractNote",
        "edition",
        "language",
        "publisher",
        "series",
        "seriesNumber",
        "shortTitle",
        "url",
      ],
    },
    // Book Section
    21: {
      required: ["author", "date", "pages", "place", "publisher", "title"],
      optional: [
        "abstractNote",
        "edition",
        "language",
        "section",
        "series",
        "seriesNumber",
        "shortTitle",
        "url",
      ],
    },
    // Document
    26: {
      required: ["author", "date", "pages", "place", "title"],
      optional: ["abstractNote", "archive", "archiveLocation", "language", "publisher", "url"],
    },
    // Interview
    33: {
      required: ["author", "date", "place", "rights", "title"],
      optional: ["abstractNote", "archive", "archiveLocation", "language", "publisher", "url"],
    },
    // Journal Article
    34: {
      required: ["author", "date", "pages", "publisher", "title"],
      optional: ["abstractNote", "language", "url"],
    },
    // Magazine Article
    36: {
      required: ["author", "date", "pages", "publisher", "title"],
      optional: ["abstractNote", "language", "url"],
    },
    // Manuscript
    37: {
      required: [
        "archive",
        "archiveLocation",
        "author",
        "date",
        "pages",
        "title",
      ],
      optional: ["abstractNote", "language", "place", "publisher", "url"],
    },
    // Newspaper Article
    39: {
      required: ["date", "edition", "place", "publicationTitle", "title"],
      optional: [
        "abstractNote",
        "archive",
        "archiveLocation",
        "author",
        "language",
        "publisher",
        "pages",
        "section",
        "url",
      ],
    },
    // Thesis
    46: {
      required: ["author", "date", "rights", "title"],
      optional: ["abstractNote", "archive", "archiveLocation", "language", "url"],
    },
    // Webpage
    49: {
      required: ["accessDate", "date", "title", "url"],
      optional: ["author", "language"],
    }
  },

  // Save status codes

  SAVE_STATUS: {
    NO_CHANGE: 1, 
    SAVE_IN_PROGRESS: 2, 
    ERROR_BAD_API_ID: 3, 
    SUCCESS: 4
  },

  // What goes in the menus? (can be controlled from server)
  // (note: keys are same as element IDs)

  MENU_OPTIONS: {
    document_type: {
      '-1':'Unspecified / not clear',
      '20':'Book',
      '21':'Book Section',
      '26':'Document',
      '33':'Interview',
      '34':'Journal Article',
      '36':'Magazine Article',
      '37':'Manuscript',
      '39':'Newspaper Article',
      '46':'Thesis',
      '49':'Webpage'
    },
    formInputDISAPersonTribe: { 
      
      // With labels/values as ID ... (weird)

      'Bocotora':'Bocotora',
      'Eastern Pequot':'Eastern Pequot',
      'Mashantucket Pequot':'Mashantucket Pequot',
      'Mohegan':'Mohegan',
      'Narragansett':'Narragansett',
      'Pequot':'Pequot',
      'Wampanoag':'Wampanoag',
      'Woolwa':'Woolwa',
      'Unspecified / not clear':'Unspecified / not clear'
      
      /* WITH DB IDs AS KEYS ... (logical)

      '25':'Unspecified / not clear',
      '2':'Bocotora',
      '4':'Eastern Pequot',
      '5':'Mashantucket Pequot',
      '6':'Mohegan',
      '7':'Narragansett',
      '10':'Pequot',
      '20':'Wampanoag',
      '21':'Woolwa' */
    },
    formInputDISAPersonVocation: {
      1: 'Abolitionism',
      2: 'Agriculture, Husbandry, and Forestry',
      3: 'Arts and Entertainment',
      4: 'Banking, Insurance, and Commerce',
      5: 'Crafts and Trades',
      6: 'Crime',
      7: 'Domestic Service',
      8: 'Fishing, Gathering, and Hunting',
      9: 'Government',
      10: 'Hiring',
      11: 'Industry',
      12: 'Landowning',
      13: 'Legal',
      14: 'Supervision',
      15: 'Manual Labor',
      16: 'Maritime',
      17: 'Marketing, Retail, and Trading',
      18: 'Medical and Funerary',
      19: 'Midwifery and Wet-nursing',
      20: 'Military and Militia',
      21: 'Policing and Corrections',
      22: 'Public Works',
      23: 'Religious',
      24: 'Slave Trade',
      25: 'Teaching',
      26: 'Transportation',
      27: 'Writing and Publishing',
      28: 'Other Occupation'
    },
    // Temporary client-side override for summer `23 data cleaning
    // (the status menu items usually come from the server)
    // See also entry_form_data_in.js
    formInputDISAPersonStatus: {
      'free person':'free person',
      'free person ▸ enslaver or owner':'free person ▸ enslaver or owner',
      'free person ▸ formerly unfree':'free person ▸ formerly unfree',
      'free person ▸ formerly unfree ▸ freedman':'free person ▸ formerly unfree ▸ freedman',
      'free person ▸ formerly unfree ▸ emancipated':'free person ▸ formerly unfree ▸ emancipated',
      'free person ▸ formerly unfree ▸ manumitted':'free person ▸ formerly unfree ▸ manumitted',
      'free person ▸ formerly unfree ▸ self-purchased':'free person ▸ formerly unfree ▸ self-purchased',
      'free person ▸ Indigenous kin':'free person ▸ Indigenous kin',
      'free person ▸ non-slaveholder':'free person ▸ non-slaveholder',
      'free person ▸ prospective unfree':'free person ▸ prospective unfree',
      'unfree person':'unfree person',
      'unfree person ▸ enslaved':'unfree person ▸ enslaved',
      'unfree person ▸ enslaved ▸ diplomatically traded/gifted':'unfree person ▸ enslaved ▸ diplomatically traded/gifted',
      'unfree person ▸ enslaved ▸ judicial enslavement':'unfree person ▸ enslaved ▸ judicial enslavement',
      'unfree person ▸ liminal':'unfree person ▸ liminal',
      'unfree person ▸ liminal ▸ captive':'unfree person ▸ liminal ▸ captive',
      'unfree person ▸ liminal ▸ self-emancipated':'unfree person ▸ liminal ▸ self-emancipated',
      'unfree person ▸ term-limited':'unfree person ▸ term-limited',
      'unfree person ▸ term-limited ▸ apprentice':'unfree person ▸ term-limited ▸ apprentice',
      'unfree person ▸ term-limited ▸ indenture':'unfree person ▸ term-limited ▸ indenture',
    },
    formInputDISAPersonGender: {
      '0': 'Not specified',
      'Male': 'Male',
      'Female': 'Female',
      'Two spirit': 'Two spirit'
    }, /*
    formInputDISAColonialContext: {
      '1':	'British',
      '2':	'American',
      '3':	'French',
      '4':	'Spanish',
      '5':	'Other'
    }, */
    formInputDISAItemPersonNameType: {
      '1': 'Alias',
      '2': 'Baptismal',
      '3': 'English',
      '4': 'European',
      '5': 'Indian',
      '6': 'Nickname',
      '7': 'Given',
      '8': 'Unknown'
    },
    formInputDISAPersonRace: {
      'Not specified':'Not specified',
      'Black':'Black',
      'Indigenous':'Indigenous',
      'Multi-racial':'Multi-racial',
      'White':'White'
      /*
      '23':'Not specified',
      '30':'Black',
      '7':'Indian',
      '35':'Multi-racial',
      '24':'White' */
    },
    formInputDISAPersonAge_category: {
      '78ac411b-be39-41e3-be66-43017e30d105':'Infant',
      '761cc55d-8bf6-4737-a728-30f20c4d66b2':'Child',
      '3a592293-9d21-4cef-968a-fcebfd1c0835':'Youth / Young Adult',
      '91372500-720a-44ae-9a97-2f7e6bab4a28':'Adult',
      'c40e63bd-c119-476a-8195-771780cb7c33':'Older adult',
      'affc059e-1c0b-464c-a7da-37ad66aefd5d':'Elder'
    },  
    // Temporary client-side override for fall `23 data cleaning
    // (the record type items usually come from the server)
    // See also entry_form_data_in.js
    formInputDISAItemType: {
      '1':'Baptism',
      '2':'Runaway',
      '3':'Sale',
      '4':'Capture',
      '5':'Inoculation',
      '6':'Execution',
      '7':'Manumission',
      '8':'Entry',
      '9':'Indenture',
      '10':'Account',
      '11':'Note',
      '12':'Inventory',
      '13':'Unspecified',
      '14':'Reference',
      '15':'Skating across the pond',
      '16':'Criminal charge',
      '17':'Council Minutes',
      '18':'Advertisement for Sale',
      '19':'Petition',
      '20':'Petition to Assembly',
      '22':'Arrest Warrant',
      '23':'Account (Letter)',
      '24':'Writ of Indenture',
      '25':'Town Council Records',
      '26':'Power of Attorney',
      '27':'Child Indenture',
      '28':'Deed of Sale',
      '29':'Burial Record',
      '30':'Notice of capture',
      '31':'Record of Death',
      '32':'Enclosure',
      '33':'Complaint',
      '34':'Report',
      '35':'Return',
      '37':'Decree',
      '38':'Order',
      '39':'Resolve',
      '40':'Council Order',
      '41':'Council Resolve',
      '42':'Petition Resolve',
      '43':'Manumission Application',
      '44':'Petition and Resolve',
      '45':'Petition and Order',
      '47':'Council Vote',
      '48':'Court Case',
      '50':'Proclamation',
      '51':'House Resolution',
      '52':'Will',
      '54':'Deposition',
      '56':'Criminal case abstract',
      '57':'Court records',
      '58':'Record of sale',
      '59':'Testimony',
      '60':'Diary entry',
      '61':'Letter',
      '62':'Newspaper Article',
      '63':'Journal Entry',
      '64':'Agreement',
      '65':'Correspondence',
      '66':'Presentments',
      '67':'Appraisal',
      '68':'Deed of Gift',
      '69':'Hire of Indian',
      '70':'Memorandum',
      '71':'Attestations',
      '72':'Receipt',
      '73':'Conference',
      '74':'Treaty',
      '75':'Narrative',
      '76':'Memoir',
      '77':'Abstract',
      '79':'Notice of Runaway'
    },

    // @todo @birkin THESE ARE NOT GOOD - this is only a partial reflection of what's
    //  in the DB (in table 1_roles), but this all needs to be reviewed

    formInputDISARelationship: {
      '1':'enslaved by',
      '2':'owner of',
      '3':'priest for',
      '4':'inoculated by',
      '5':'bought by',
      '6':'sold by',
      '7':'shipped by',
      '8':'delivered by',
      '9':'escaped from',
      '10':'captured',
      '11':'captured by',
      '12':'baptised by',
      '13':'released by',
      '14':'executed by',
      '15':'parent of',
      '16':'spouse of',
      '17':'child of',
      '18':'mother of',
      '19':'father of',
      '20':'buyer of',
      '21':'seller of',
      '22':'indentured by',
      '23':'master of',
      '34':'ran away with',
      '38':'servant of'
    },
    formInputDISAPersonGeoOrigins: {
      // Origins are joined to locations
      // but those are uncontrolled, so there's nothing to
      // suggest here
    }
  }
};
