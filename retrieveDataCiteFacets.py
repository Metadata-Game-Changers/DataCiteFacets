import json
import datetime
from posix import CLD_CONTINUED
import pandas as pd
import sys
import argparse
import logging
import requests
import os
import numpy as np
import re
import itertools

def writeHTMLOutput(output:str,                         # output file name
                    df:pd.core.frame.DataFrame,         # dataframe
                    simple:bool                         # flag for simple html
                 ):
    '''
        Write a dataframe to an HTML file
    '''
    #
    # Define html header and footer
    #
    startHTML = '''<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>DataCite Facet Summary</title>
    </head>
    <style>body { font-family: "Calibri" }</style>
    <body>
    <h1>DataCite Facet Summary</h1>
    '''

    endHTML = f'<hr><i>Report created {dateStamp} by <a href="https://github.com/Metadata-Game-Changers/DataCiteFacets">retrieveDataCiteFacets</a> from <a href="https://metadatagamechangers.com">Metadata Game Changers</a></i></body></html>'

    with open(output, 'w') as f:
        f.write(startHTML)
        addHTMLHeader(f)
        html_output = dataframeToHTML(df,simple)
        f.write(html_output)
        f.write(endHTML)


def dataframeToHTML(df:pd.core.frame.DataFrame,
                    simple:bool):
    #
    # Dict used to format columns of the dataframe
    #
    t  = dict(selector="table", props=[('border','1px solid black'),('width','100%')])
    th = dict(selector="th", props=[('border','1px solid black'),('border-collapse','collapse'),('padding','5px'),('font-family','Century Gothic')])
    td = dict(selector="td", props=[('border','1px solid black'),('border-collapse','collapse'),('padding','5px'),('font-family','Century Gothic')])
 
    html_df = df.copy()                     # create a copy of df to be written to HTML to avoid changing the content of df
    html_df.fillna(0, inplace=True)         # replace nan values with 0's

    if simple:              # output simple HTML (no highlights)
        for c in [x for x in html_df.columns if html_df[x].dtype == float]:   # adjust column types (float > int)
            html_df[c] = html_df[c].astype(int)
        return html_df.style.set_table_styles([t,th,td]).hide(axis="index").to_html()
    
    for c in html_df.columns:               # adjust column types
        if c.endswith(('NumberOfRecords','_number','_max','_total')):       # integer columns
            html_df[c] = html_df[c].astype(int)
        if c.endswith(('_HI','_coverage')):
            html_df[c] = html_df[c].astype(float)                           # float column

    float_col_mask = html_df.columns.str.endswith(('_HI','_coverage'))
    int_col_mask   = html_df.columns.str.endswith(('NumberOfRecords','_number','_max','_total'))

    color_col_mask = float_col_mask | int_col_mask

     # define the styles and render
    return html_df.style.set_properties(subset=html_df.columns[color_col_mask], # center the numeric columns
                            **{'text-align':'center'})\
            .set_properties(subset=html_df.columns[~color_col_mask], # left-align the non-numeric columns
                            **{'text-align':'left'})\
            .format(lambda x: '{:,.0f}'.format(x) if x > 1e3 else '{:.0%}'.format(x), # format _HI as %
                            subset=pd.IndexSlice[:,html_df.columns[float_col_mask]])\
            .format(lambda x: '{0:d}'.format(x), subset=pd.IndexSlice[:,html_df.columns[int_col_mask]])\
            .set_table_styles([t,th,td]).hide(axis="index")\
            .apply(colorScale,subset=html_df.columns[float_col_mask])\
            .apply(highlight_max,subset=html_df.columns[int_col_mask]).to_html()


def colorScale(s):
    '''
        Highlight table cells with floating point numbers red (<0.000005), lightGreen (> 0.99999), or yellow
    '''
    return   ['' if not isinstance(v,float) \
        else 'background-color: lightPink' if v < 0.000005 \
        else 'background-color: lightGreen' if v > 0.99999 \
        else 'background-color: yellow' for v in s]
        

def highlight_max(s):
    '''
        This function highlights the maximum value in a column of an HTML table lightGreen.
    '''
    is_max = s == s.max()
    return ['background-color: lightGreen' if v else '' for v in is_max]


def addHTMLHeader(f):
    '''
        Write command line options to html header
    '''
    s = ''

    if args.getRelations:                       # the target retrievals can be controlled by command line arguments:
        s += f"<b>Relations:</b> {' '.join(parameters['relations']['data'])}<br>"             # --affiliations --contributors --relations --resources retrieve all 

    if args.getResources:                       # items in each list, i.e. all relationTypes...
        s += f"<b>Resources:</b> {' '.join(parameters['resources']['data'])}<br>"

    if args.getContributorTypes:
        s += f"<b>Contributor Types:</b> {' '.join(parameters['contributors']['data'])}<br>"

    if args.getYears:
        s += f"<b>Years:</b> {' '.join(parameters['years']['data'])}<br>"

    if args.affiliationList:
        s += f"<b>Affiliations:</b> {', '.join(parameters['affiliations']['data'])}<br>"

    if args.itemList:
        s += f"<b>Item list:</b> {' '.join(args.itemList)}<br>"

    if args.facetList:
        s += f"<b>Facet list:</b> {' '.join(args.facetList)}<br>"
    else:
        s += f"<b>Facet list:</b> {facets}<br>"

    f.write(s)


def connectToDataCiteDatabase():
    '''
       make connection to sqlite database, a file defined as an environment variable
    '''
    database = os.environ['DATACITE_STATISTICS_DATABASE']       # environment defines database location
    con = sqlite3.connect(database)
    cur = con.cursor()
    return(con,cur)


def createCountStringFromListOfDictionaries(l:list,                 # list of property dictionaries ({})
                                            useID:bool              # use repository id instead of name as title
                                            )->str:
    '''
        Make a list of counts from DataCite list of property dictionaries (l)

        The list has the form title1 (count1), title2 (count2), ...
    '''
    s = ''
    
    if useID:                           # use repository id as column title 
        s = ", ".join([d['id'] + ' (' + str(d['count']) + ')' for d in l])
    else:                               # use repository name as column title (default)
        s = ", ".join([d['title'].replace(',',';') + ' (' + str(d['count']) + ')' for d in l])
    
 
    return s


def createDictionaryFromCountString(s: str)-> dict:
    '''
        Convert a count string like Aalto University (69), University of Lapland (8)
        into a dictionary like {'Aalto University':69, 'University of Lapland':8}
    '''
    if not isinstance(s,str):
        return

    d_ = {}
    pc = re.compile('^(?P<value>.*?)\((?P<count>[0-9]+?)\)$')
    
    items = s.replace(' ','').split(',')
    for i in items:
        m = re.match(pc, i)
        if m is None:
            print(f'No match: {i}')
            continue
        md = m.groupdict()
        if md['value'] is not None:
            d_[md['value']] = int(md['count'])
        else:
            d_[md['None']] = int(md['count'])
        
    return d_


def retrieveMetadata(URL:str                            # DataCite API URL
                    )-> requests.models.Response:       # query response

    '''
        retrieve and return DataCite metadata response from URL 
    '''

    lggr.debug(f"Retrieving Metadata: {URL}")

    try:
        response = requests.get(URL)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        lggr.debug(f'Error: {err}')
        return None
    except requests.exceptions.ConnectionError as err:
        lggr.debug(f'Error: {err}')
        return None
    except requests.exceptions.Timeout as err:
        lggr.debug(f'Error: {err}')
        return None
    except requests.exceptions.TooManyRedirects as err:
        lggr.debug(f'Error: {err}')
        return None
    except requests.exceptions.MissingSchema as err:
        lggr.debug(f'Error: {err}')
        return None
    
    lggr.debug(f'Response length: {len(response.text)}')
    return response


def  createFacetsDictionary(facetList: list,                # list of facets e.g. ['states','resourceTypes','created'] see full list below
                            item:str,                       # item (resource, relation, contributorType) being retrieved,
                            dateStamp: str,                 # datestamp (YYYYMMDD_HH) 
                            numberOfRecords:int,            # number of records in query
                            item_json:dict)-> dict:         # json retrieved for item 
    '''
        Read DataCite json response and create a summary dictionary for facets in a list. 
        
        For the facet f, the dictionary includes the query item, the datestamp, the numberOfRecords and
        the following statistics:
            f_number: the number of facet values
            f_max: the maximum facet value
            f_common: the name of the facet with the largest value
            f_total: the total of all of the facet values
            f_HI: the homogeneity index (f_max / f_total)
            f: the facet names and values written as a name (value) string
    '''
    d_list = []
    #
    # initialize facets dictionary
    #
    d_dict = {'Id': '_'.join(item), 'DateTime': dateStamp, 'NumberOfRecords': numberOfRecords}
    
    numberOfFacets = 0
    for f in facetList:    # loop facets
        try:
            numberOfFacets = len(item_json['meta'][f])
        except:
            lggr.debug(f'No {f}')
        finally:
            lggr.debug(f'{numberOfFacets} {f}')
            if numberOfFacets > 0:  # populate dictionary for facet
                d_dict[f + '_number'] = numberOfFacets  # add count for facet
                d_dict[f + '_max'] = max([d['count'] for d in item_json['meta'][f]])        # add max for facet
                d_dict[f + '_common'] = ', '.join([d['id'] for d in item_json['meta'][f] \
                                            if d['count'] == d_dict[f + '_max']])           # value with max count
                d_dict[f + '_total'] = sum([d['count'] for d in item_json['meta'][f]])      # add total for facet
                # d_dict[f + '_HI'] = d_dict[f + '_max'] /  d_dict[f + '_total']            # add HI 
                d_dict[f + '_HI'] = d_dict[f + '_max'] /  numberOfRecords                   # add HI (max/number of records) 20220708
                d_dict[f + '_coverage'] = d_dict[f + '_total'] / numberOfRecords            # %coverage of top 10 for facet
                output = createCountStringFromListOfDictionaries(item_json['meta'][f], args.useIDAsTitle)
                d_dict[f] = output # add count string to dictionary

    return d_dict # return facet dictionary for item

parameters = {
    "relations": {
        "data": ['IsCitedBy', 'Cites', 'IsSupplementTo', 'IsSupplementedBy', 'IsContinuedBy', 'Continues',\
             'IsNewVersionOf', 'IsPreviousVersionOf', 'IsPartOf', 'HasPart', 'IsPublishedIn', 'IsReferencedBy',\
             'References', 'IsDocumentedBy', 'Documents', 'IsCompiledBy', 'Compiles', 'IsVariantFormOf', \
             'IsOriginalFormOf', 'IsIdenticalTo', 'HasMetadata', 'IsMetadataFor', 'Reviews', 'IsReviewedBy', \
             'IsDerivedFrom', 'IsSourceOf', 'Describes', 'IsDescribedBy', 'HasVersion', 'IsVersionOf', 'Requires', \
             'IsRequiredBy', 'Obsoletes', 'IsObsoletedBy'],
        "queryString": 'query=relatedIdentifiers.relationType:',
        "url":  'https://api.datacite.org/dois?&page[size]=1&query=relatedIdentifiers.relationType:' 
    },
    "resources": {
        "data": ['Audiovisual','Book','BookChapter','Collection','ComputationalNotebook','ConferencePaper',\
                 'ConferenceProceeding','DataPaper','Dataset','Dissertation','Event','Image','InteractiveResource',\
                 'Journal','JournalArticle','Model','OutputManagementPlan','PeerReview','PhysicalObject','Preprint',\
                 'Report','Service','Software','Sound','Standard','Text','Workflow','Other'],
        "queryString": 'resource-type-id=',
        "url":  'https://api.datacite.org/dois?&page[size]=1&resource-type-id='
    },
    "contributors": {
        "data": ['ContactPerson','DataCollector','DataCurator','DataManager','Distributor','Editor', 'Funder',
                    'HostingInstitution','Other','Producer','ProjectLeader','ProjectManager','ProjectMember',
                    'RegistrationAgency','RegistrationAuthority','RelatedPerson','ResearchGroup','RightsHolder',
                    'Researcher','Sponsor','Supervisor','WorkPackageLeader'],
        "queryString": 'query=contributors.contributorType:',
        "url": 'https://api.datacite.org/dois?query=contributors.contributorType:'
    },
    "affiliations": {
        "data": [],
        "queryString": 'query=creators.affiliation.name:*',
        "url": 'https://api.datacite.org/dois?query=creators.affiliation.name:*'
    },
    "years": {
        "data": [],
        "queryString": 'registered=',
        "url": 'https://api.datacite.org/dois?registered='
    }
}

facets = ['states','resourceTypes','created','published','registered','providers','clients',
              'affiliations','prefixes','certificates','licenses','schemaVersions','linkChecksStatus',
              'subjects','fieldsOfScience','citations','views','downloads']


commandLine=argparse.ArgumentParser(prog='retrieveDataCiteFacets',
                        description='''Use DataCite API to retrieve metadata records for given relationType, resourceType, 
                                    contributorType, and affiliations from DataCite. Save the retrieved metadata into
                                    json files (--jout) and facet data into csv or html file or database (defined in environment).'''
)
commandLine.add_argument("-al", "--affiliationList", nargs="*", type=str,
                        help='space separated list of affiliations to retrieve (affiliations with spaces in quotes)', default=[]
)
commandLine.add_argument("-il", "--itemList", nargs="*", type=str,
                        help='space separated list of items to retrieve', default=[]
)
commandLine.add_argument("-fl", "--facetList", nargs="*", type=str, default=[],
                        help='''Select space separated list of facets to retrieve from: states resourceTypes created published registered providers clients
                                affiliations prefixes certificates licenses schemaVersions linkChecksStatus
                                subjects fieldsOfScience citations views downloads. Default = all'''
)
commandLine.add_argument('--contributors', dest='getContributorTypes', 
                        default=False, action='store_true',
                        help='''Retrieve facets for all contributorTypes: ContactPerson, DataCollector, DataCurator, 
                                DataManager, Distributor, Editor, Funder, HostingInstitution, Other, Producer, ProjectLeader,
                                ProjectManager, ProjectMember, RegistrationAgency, RegistrationAuthority, RelatedPerson,
                                ResearchGroup, RightsHolder, Researcher, Sponsor, Supervisor, WorkPackageLeader'''
)
commandLine.add_argument('--relations', dest='getRelations', 
                        default=False, action='store_true',
                        help='''Retrieve facets for all relations: IsCitedBy, Cites, IsSupplementTo, IsSupplementedBy, IsContinuedBy, Continues, 
                                IsNewVersionOf, IsPreviousVersionOf, IsPartOf, HasPart, IsPublishedIn, IsReferencedBy, References, IsDocumentedBy, 
                                Documents, IsCompiledBy, Compiles, IsVariantFormOf, IsOriginalFormOf, IsIdenticalTo, HasMetadata, IsMetadataFor, 
                                Reviews, IsReviewedBy, IsDerivedFrom, IsSourceOf, Describes, IsDescribedBy, HasVersion, IsVersionOf, Requires, 
                                IsRequiredBy, Obsoletes, IsObsoletedBy'''
)
commandLine.add_argument('--resources', dest='getResources', 
                        default=False, action='store_true',
                        help='''Retrieve facets for all resource types: Audiovisual, Book, BookChapter, Collection, ComputationalNotebook,
                                ConferencePaper, ConferenceProceeding, DataPaper, Dataset, Dissertation, Event, Image, 
                                InteractiveResource, Journal, JournalArticle, Model, OutputManagementPlan, PeerReview,
                                PhysicalObject, Preprint, Report, Service, Software, Sound, Standard, Text, Workflow, Other'''
)
commandLine.add_argument('--years', dest='getYears', 
                        default=False, action='store_true',
                        help='''Retrieve facets for all years: 2004 to present'''
)
commandLine.add_argument('-minYear', dest='minYear', type=int,
                        default=2004,
                        help='''Minimum year for year queries'''
)
commandLine.add_argument('--showURLs', dest='showURLs', 
                        default=False, action='store_true',
                        help='''Show URLs that will be retrieved but DO NOT retrieve metadata'''
)
commandLine.add_argument('--showtargets', dest='showTargetData', 
                        default=False, action='store_true',
                        help='''Show target lists (e.g. all resourceTypes, relationTypes, contributorTypes)'''
)
commandLine.add_argument('--combineQueries', dest='combineQueries', 
                        default=False, action='store_true',
                        help='Run all query parameter combinations'
)
commandLine.add_argument('--csvout', dest='csvout', 
                        default=False, action='store_true',
                        help='Output results in CSV file'
)
commandLine.add_argument('--dbout', dest='dbout', 
                        default=False, action='store_true',
                        help='Output results in database (requires sqlite3 package)'
)
commandLine.add_argument('--facetdata', dest='facetdata', 
                        default=False, action='store_true',
                        help='Create dataframe from facet data'
)
commandLine.add_argument('--id', dest='useIDAsTitle', 
                        default=False, action='store_true',
                        help='Use repository ID as column name instead of repository name'
)
commandLine.add_argument('--htmlout', dest='htmlout', 
                        default=False, action='store_true',
                        help='Output results in HTML file'
)
commandLine.add_argument('--jout', dest='jout', 
                        default=False, action='store_true',
                        help='Output retrieved metadata in json files'
)
commandLine.add_argument('--pout', dest='pout', 
                        default=False, action='store_true',
                        help='Output facet counts to terminal (requires tabulate package https://pypi.org/project/tabulate/)'
)
commandLine.add_argument('--loglevel', default='info',
                        choices=['debug', 'info', 'warning'],
                        help='Logging level for logging module (https://docs.python.org/3/howto/logging.html#useful-handlers)'
)
commandLine.add_argument('--logto', metavar='FILE',
                    help='Log file (will append to file if exists)'
)
args = commandLine.parse_args() # parse the command line and define variables

if args.logto:
    # Log to file
    logging.basicConfig(
        filename=args.logto, filemode='a',
        format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
        level=args.loglevel.upper(),
        datefmt='%Y-%m-%d %H:%M:%S')
else:
    # Log to stderr
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
        level=args.loglevel.upper(),
        datefmt='%Y-%m-%d %H:%M:%S')

lggr = logging.getLogger('retrieveDataCiteFacets')

current_time = datetime.datetime.now()
dateStamp = f'{current_time.year}{current_time.month:02d}{current_time.day:02d}_{current_time.hour:02d}'

homeDir = os.path.expanduser('~')

lggr.info(f'*********************************** retrieveRelationandResourceCounts {dateStamp}')

urlCount = 0
urlInterval = 1

targets = []                                
                                            
if args.getRelations:                       # the target retrievals can be controlled by command line arguments:
    targets.append('relations')             # --affiliations --contributors --relations --resources retrieve all 
if args.getResources:                       # items in each list, i.e. all relationTypes...
    targets.append('resources')
if args.getContributorTypes:
    targets.append('contributors')
if args.affiliationList:                    # read affiliations from the command line
    targets.append('affiliations')
    parameters['affiliations']['data'] = args.affiliationList       # set affiliation list from -al argument
if args.getYears:
    targets.append('years')                 # create a list of years from args.minYear to present
    parameters['years']['data'] = list(map(str, range(args.minYear,current_time.year + 1))) 

if args.showTargetData:                 # list items for each target
    for t in list(parameters):
        if len(parameters[t]['data']) > 0:
            print(f"\nTarget {t} ({len(parameters[t]['data'])}) items:\n{parameters[t]['data']}")
    print(f'\nFacets ({len(facets)}) items:\n{facets}')
    exit()

for i in args.itemList:                     # targets can also be listed as items on the command line
    for t in list(parameters):              # if only a small number of targets are needed. For example, -il Workflow
        if i in parameters[t]['data']:      # will retrieve data for just Workflow (a resource type)
            targets.append(t)

if len(targets) == 0:
    lggr.warning('No targets specified')
    exit()
else:
    lggr.info(f'Targets: {targets}')

url_parameter_lists = []                                  
parameter_lists = []
url_parameters = []
URL_List = []
param_List = []

if args.combineQueries:
    #
    # In some cases we need facet data from queries that combine multiple parameters, e.g. facets from
    # resourceType = Dataset and affiliation = someUniversity. The combineQueries option can be used to 
    # generate these results. It takes items from args.itemList, finds the targets thay are in, and runs
    # queries for all possible combinations.
    #
    # url_parameter_lists is a list of the url_parameters from each target,
    # e.g [[relation url parameters], [resource url parameters], [years]]. All combinations of items in 
    # these lists are used to create combined queries.
    #
    if len(args.itemList) == 0:
        lggr.warning('itemList must be defined for combinedQueries')
        exit()

    for target in ['relations', 'resources', 'contributors']:
                                                                    # trim the parameter data lists for these targets so 
                                                                    # they only contain items in the itemList
        parameters[target]['data'] = [x for x in parameters[target]['data'] if x in args.itemList]

        if len(parameters[target]['data']) > 0:                     # if there are parameters from the itemList for this target
            parameter_lists.append(parameters[target]['data'])      # append the list of parameters to parameter_lists (a list of lists)
            #
            # convert the remaining parameters into URL parameters, i.e. Dataset (a resource) becomes resource-type-id=Dataset
            # so that it can be included in a URL. url_parameters is a list of these parameters for this target
            #
            url_parameters = [parameters[target]['queryString'] + x for x in parameters[target]['data']]
            url_parameter_lists.append(url_parameters)              # append the list of url parameters to url_parameter_lists (a list of lists)
    
    target = 'affiliations'                                         # if affiliations are specified they are all included
    if len(parameters[target]['data']) > 0:                         # in the combined queries, i.e. no trimming required
        parameter_lists.append(parameters[target]['data'])          # append list of affiliations to parameter_lists (list of lists)
                                                                    # convert affiliations to URL parameters
        url_parameters = [parameters[target]['queryString'] + x.replace(' ','*') + '*' for x in parameters[target]['data']]
        url_parameter_lists.append(url_parameters)                                # append the list of affiliation url parameters to url_parameter_lists (a list of lists)

    target = 'years'                                                # if years are specified they are all included
    if len(parameters[target]['data']) > 0:                         # in the combined queries, i.e. no trimming required
        parameter_lists.append(parameters[target]['data'])          # append list of years to parameter_lists (list of lists)
                                                                    # convert years to URL parameters
        url_parameters = [parameters[target]['queryString'] + x for x in parameters[target]['data']]
        url_parameter_lists.append(url_parameters)                  # append the list of year url parameters to url_parameter_lists (a list of lists)

else:                                                   # simple queries, i.e. no combinations
    for target in set(targets):                         # loop through targets
        lggr.debug(f'target')
        for item in parameters[target]['data']:         # loop items in target data
            if target == 'affiliations':                # add wildcards to affiliation
                url_parameters.append(parameters[target]['queryString'] + item.replace(' ','*') + '*')
            else:
                url_parameters.append(parameters[target]['queryString'] + item)

        parameter_lists.extend(parameters[target]['data'])

    url_parameter_lists = [url_parameters]                       # convert url_parameter_lists to list of lists
    parameter_lists = [parameter_lists]                          # convert parameter_lists to list of lists

for u in list(itertools.product(*url_parameter_lists)):                             # create list of all combinations of items in url_parameter_lists
    URL_List.append('https://api.datacite.org/dois?&page[size]=1&' + '&'.join(u))   # and create urls with &-separated parameters
    
for p in list(itertools.product(*parameter_lists)):                                 # create a list of all combinations of the paramters used in
    #param_List = list(itertools.product(*parameter_lists))
    param_List.append(p)                                                            # each query. These are used to create the names of the query results

lggr.info(f"URL List: {len(URL_List)} items. Parameter List: {len(param_List)}")
#print('\n'.join(URL_List))

d_list = []                                # initialize list of dictionaries

for u,p in zip(URL_List, param_List):     # loop items in target data

    if args.showURLs:                               # display URL and parameters to be retrieved without retrieving data
        lggr.info(f'URL: {u} Parameters:{p}')       # use this to test various command line arguments
        continue

    res = retrieveMetadata(u)             # retrieve metadata from DataCite
    item_json = res.json()

    if args.jout:           # write json to file in directory home/data/DataCite/metadata/
                            # the file name includes item__datestamp
        jsonDirectory = homeDir + '/data/DataCite/metadata/' + '_'.join(p) + '__' + dateStamp + '/json'
        os.makedirs(jsonDirectory, exist_ok = True)
        jsonFile = jsonDirectory + '/' + '_'.join(p) + '.json'
        lggr.info(f'{item} json output to {jsonFile}')
        with open(jsonFile,'w') as outf:
            json.dump(item_json, outf, ensure_ascii=False)

    numberOfRecords = item_json.get('meta').get('total')
    if numberOfRecords == 0:
        continue

    urlCount += 1
    if urlCount % urlInterval == 0:
        lggr.info(f'Count: {urlCount} URL: {u} Parameters: {p} Number of records: {numberOfRecords}')

    if args.facetList:
        facetList = args.facetList
    else:
        facetList = facets

    d_dict = createFacetsDictionary(facetList, p, dateStamp, numberOfRecords, item_json)
    d_list.append(d_dict)

item_df = pd.DataFrame(d_list) # create dataframe

if args.facetdata:                               # create and output facet data
    for facet in args.facetList:
        data_l = []
        for i in item_df.index:
            data_d = {'id':item_df.loc[i,'Id']}
            data_d.update(createDictionaryFromCountString(item_df.loc[i,facet]))
            data_l.append(data_d)
                        
        facet_df = pd.DataFrame(data_l)

        outputFile = 'DataCite_' + '_'.join(set(targets)) + '_' + facet + '__' + dateStamp + '.csv'
        lggr.info(f'facet data output to {outputFile}')
        facet_df.to_csv(outputFile,encoding='utf-8',sep=',',index=False)

        if args.htmlout:                                 # output data to html
            htmlOutputFile = 'DataCite_' + '_'.join(set(targets)) + '_' + facet + '__' + dateStamp + '.html'
            lggr.info(f'facet data output to {htmlOutputFile}')
            writeHTMLOutput(htmlOutputFile,facet_df,True)        

if args.csvout:                                 # output data to csv
    outputFile = 'DataCite_' + '_combined__' + dateStamp + '.csv'
    lggr.info(f'facet count output to {outputFile}')
    item_df.to_csv(outputFile,encoding='utf-8',sep=',',index=False)
    
if args.dbout:                                  # add data to database
    import sqlite3                              # get sqlite3 package
    con, cur = connectToDataCiteDatabase()      # connect to database for output
    databaseTableName = 'relationsAndResources'
    item_df.to_sql(databaseTableName,con,if_exists='append',index=False)

if args.htmlout:                                 # output data to html
    htmlOutputFile = 'DataCite_' + '_'.join(set(targets)) + '__' + dateStamp + '.html'
    lggr.info(f'facet count output to {htmlOutputFile}')
    writeHTMLOutput(htmlOutputFile,item_df,False)

if args.pout:                                       # print facet counts to screen
                                                    # this produces VERY UGLY screen output that may work 
                                                    # for a quick look in some cases.  
    from tabulate import tabulate
    print(tabulate(item_df, headers='keys', tablefmt='github', showindex=False))