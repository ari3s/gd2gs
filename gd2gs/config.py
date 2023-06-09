""" Config class and operations """
from dataclasses import dataclass

import yaml

import gd2gs.logger as log

BUGZILLA = 'BUGZILLA'
API_KEY = 'API_KEY'
DOMAIN = 'DOMAIN'
URL = 'URL'

JIRA = 'JIRA'
SERVER = 'SERVER'
TOKEN = 'TOKEN'

MAX_RESULTS = 'MAX_RESULTS'
DEFAULT_MAX_RESULTS = 100
QUERY = 'QUERY'

SPREADSHEET_ID = 'SPREADSHEET_ID'
SHEETS = 'SHEETS'
NAME = 'NAME'

HEADER_OFFSET = 'HEADER_OFFSET'
DEFAULT_HEADER_OFFSET = 0
DEFAULT_COLUMNS = 'DEFAULT_COLUMNS'
INIT_DEFAULT_COLUMNS = False
INHERIT_FORMULAS = 'INHERIT_FORMULAS'
INIT_INHERIT_FORMULAS = False
SHEET_COLUMNS = 'SHEET_COLUMNS'
SOURCE = 'SOURCE'
FROM = 'FROM'
GET = 'GET'
CONDITION = 'CONDITION'
KEY = 'KEY'
LINK = 'LINK'
OPTIONAL = 'OPTIONAL'
DELIMITER = 'DELIMITER'
DEFAULT_DELIMITER = ' '

# Debug messages:
READ_CONFIG_FILE = 'read config file'
SHEET = 'sheet'
SPREADSHEET = 'spreadsheet: '

# Error messages - config file:
CONFIG_FILE_MISSING_INPUT = 'input is missing in the config file'
CONFIG_FILE_UNKNOWN_INPUT = 'input is unknown in the config file'

# Error messages - Bugzilla:
CONFIG_FILE_MISSING_BUGZILLA_API_KEY_FILE = 'Bugzilla API key file is not set in the config file'
CONFIG_FILE_MISSING_BUGZILLA_DOMAIN = 'Bugzilla domain is not set in the config file'
CONFIG_FILE_MISSING_BUGZILLA_URL = 'Bugzilla URL is not set in the config file'

# Error messages - Jira:
CONFIG_FILE_MISSING_JIRA_TOKEN = 'Jira access token is not set in the config file'
CONFIG_FILE_MISSING_JIRA_URL = 'Jira server url is not set in the config file'

# Error messages - Google spreadsheet:
CONFIG_FILE_MISSING_KEY = 'missing key in the config file'
CONFIG_FILE_MISSING_QUERY = 'query is not set in the config file for the sheet '
CONFIG_FILE_MISSING_SHEET = 'no sheet is set in the config file'
CONFIG_FILE_MISSING_SPREADSHEET = 'spreadsheet_id is not set in the config file'
CONFIG_FILE_MORE_KEYS = 'more than one key is set in the config file'
CONFIG_FILE_WRONG_SPREADSHEET = 'spreadsheet_id must be a string in the config file'

@dataclass
class Sheet:
    """ Sheet data class """
    header_offset: int = DEFAULT_HEADER_OFFSET
    delimiter: str = DEFAULT_DELIMITER
    default_columns: bool = INIT_DEFAULT_COLUMNS
    inherit_formulas: bool = INIT_INHERIT_FORMULAS
    columns: dict = None
    key: str = None

@dataclass
class Column:
    """ Column data class """
    data: str = None
    gets: dict = None
    condition: dict = None
    optional: str = None
    link: str = None
    delimiter: str = DEFAULT_DELIMITER

class Config:   # pylint: disable=too-many-instance-attributes
    """ Config parameters """

    def __init__(self, config_file_name):
        """ Get config data from the config file """
        log.debug(READ_CONFIG_FILE)
        try:
            with open(config_file_name, encoding='utf8') as config_file:
                config_data = yaml.safe_load(config_file)
        except OSError as exception:
            log.fatal_error(exception)
        self.source = get_input(config_data, CONFIG_FILE_MISSING_INPUT)
        if self.source == BUGZILLA:
            self.config_bugzilla(config_data)
        elif self.source == JIRA:
            self.config_jira(config_data)
        else:
            log.error(self.source + ' ' + CONFIG_FILE_UNKNOWN_INPUT)
        self.config_gsheet(config_data)
        log.check_error()

    def config_bugzilla(self, config_data):
        """ Configure Bugzilla params """
        self.bugzilla_domain = get_config(config_data[BUGZILLA], DOMAIN, \
                CONFIG_FILE_MISSING_BUGZILLA_DOMAIN)
        self.bugzilla_url = get_config(config_data[BUGZILLA], URL, \
                CONFIG_FILE_MISSING_BUGZILLA_URL)
        self.bugzilla_api_key = get_config(config_data[BUGZILLA], API_KEY, \
                CONFIG_FILE_MISSING_BUGZILLA_API_KEY_FILE)

    def config_jira(self, config_data):
        """ Configure Jira params """
        self.jira_server = get_config(config_data[JIRA], SERVER, CONFIG_FILE_MISSING_JIRA_URL)
        self.jira_token = get_config(config_data[JIRA], TOKEN, CONFIG_FILE_MISSING_JIRA_TOKEN)
        self.jira_max_results = int(get_config_with_default(config_data[JIRA], \
                MAX_RESULTS, DEFAULT_MAX_RESULTS))

    def config_gsheet(self, config_data):
        """ Configure Google spreadsheet params """
        self.spreadsheet_id = get_config(config_data, SPREADSHEET_ID,
                                         CONFIG_FILE_MISSING_SPREADSHEET)
        if not isinstance(self.spreadsheet_id, str):
            log.fatal_error(CONFIG_FILE_WRONG_SPREADSHEET)

        spreadsheet = get_sheet_config(config_data, None)
        log.debug(SPREADSHEET + str(spreadsheet))
        if SHEETS in config_data:
            self.sheets = []
            self.sheet = {}
            self.queries = {}
            for sheet_item in config_data[SHEETS]:
                name = sheet_item[NAME]
                self.sheets.append(name)
                query = get_config(sheet_item, QUERY, CONFIG_FILE_MISSING_QUERY + sheet_item[NAME])
                self.queries[name] = query
                self.sheet[name] = get_sheet_config(sheet_item, spreadsheet)
                log.debug(SHEET + ' ' + name + ': ' + str(self.sheet[name]))
                if not self.sheet[name].key:
                    log.error(CONFIG_FILE_MISSING_KEY + ' (' + SHEET + ': ' + name + ')')
        else:
            log.error(CONFIG_FILE_MISSING_SHEET)

def get_sheet_config(config_data, spreadsheet):
    """ Get Google sheet params """
    key = None
    columns = {}
    if spreadsheet:
        header_offset = spreadsheet.header_offset
        delimiter = spreadsheet.delimiter
        default_columns = spreadsheet.default_columns
        inherit_formulas = spreadsheet.inherit_formulas
        key = spreadsheet.key
        for column in spreadsheet.columns:
            columns[column] = spreadsheet.columns[column]
    else:    # global parameters
        header_offset = DEFAULT_HEADER_OFFSET
        delimiter = DEFAULT_DELIMITER
        default_columns = INIT_DEFAULT_COLUMNS
        inherit_formulas = INIT_INHERIT_FORMULAS
    if HEADER_OFFSET in config_data:
        header_offset = int(config_data[HEADER_OFFSET])
    if DELIMITER in config_data:
        delimiter = config_data[DELIMITER]
    if DEFAULT_COLUMNS in config_data:
        default_columns = config_data[DEFAULT_COLUMNS]
    if INHERIT_FORMULAS in config_data:
        inherit_formulas = config_data[INHERIT_FORMULAS]
    if SHEET_COLUMNS in config_data:
        for column, data in config_data[SHEET_COLUMNS].items():
            columns[column] = Column()
            key = get_column_config(key, column, columns[column], data, delimiter)
    if spreadsheet and not columns:
        delimiter = spreadsheet.delimiter
        columns = spreadsheet.columns
        key = spreadsheet.key
    return Sheet(header_offset, delimiter, default_columns, inherit_formulas, columns, key)

def get_column_config(key, column, col, c_data, delimiter):
    """ Get column configuration """
    if isinstance(c_data, dict):
        if KEY in c_data:
            if key:
                log.error(CONFIG_FILE_MORE_KEYS)
            key = column
        col.delimiter = c_data[DELIMITER] \
               if DELIMITER in c_data else delimiter
        if LINK in c_data:
            col.link = c_data[LINK]
        if OPTIONAL in c_data:
            col.optional = c_data[OPTIONAL]
        get_source_config(col, c_data)
    else:
        col.data = c_data
    return key

def get_source_config(col, c_data):
    """ Get configuration of source data handling """
    if isinstance(c_data[SOURCE], dict):
        col.delimiter2 = c_data[SOURCE][DELIMITER] \
                if DELIMITER in c_data[SOURCE] else col.delimiter
        if FROM in c_data[SOURCE]:
            col.data = c_data[SOURCE][FROM]
        if GET in c_data[SOURCE]:
            col.gets = c_data[SOURCE][GET]
        if CONDITION in c_data[SOURCE]:
            col.condition = c_data[SOURCE][CONDITION]
        if LINK in c_data[SOURCE]:
            col.link = c_data[SOURCE][LINK]
        if OPTIONAL in c_data[SOURCE]:
            col.optional = c_data[SOURCE][OPTIONAL]
    else:
        col.data = c_data[SOURCE]

def get_config(config_data, param, error_message):
    """ Get param present in the config file """
    if param not in config_data:
        log.error(error_message)
    try:
        value_str = str(config_data[param])
    except KeyError:
        log.check_error()
    log.debug(param + ': ' + value_str)
    return config_data[param]

def get_config_with_default(config_data, param, default_value):
    """ Get param from the config file. If not present, setup default value. """
    if param in config_data:
        value = config_data[param]
        default_info = ''
    else:
        value = default_value
        default_info = ' (default value)'
    log.debug(param + ': ' + str(value) + default_info)
    return value

def get_input(config_data, error_message):
    """ Get input present in the config file """
    param = None
    if BUGZILLA in config_data:
        param = BUGZILLA
    elif JIRA in config_data:
        param = JIRA
    else:
        log.error(error_message)
    try:
        value_str = str(config_data[param])
    except KeyError:
        log.check_error()
    log.debug(param + ': ' + value_str)
    return param
