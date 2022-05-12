import json
import datetime
from posix import CLD_CONTINUED
from numpy import append
import pandas as pd
import sys
import argparse
import logging
import requests
import os
from pathlib import Path
import sqlite3

def connectToDataCiteDatabase():
    #
    # make database connection
    #
    database = os.environ['DATACITE_STATISTICS_DATABASE']       # environment defines database location
    con = sqlite3.connect(database)
    cur = con.cursor()
    return(con,cur)


def createCountStringFromListOfDictionaries(l):
    ''' make a list of counts from DataCite list of property dictionaries (l)'''
    s = ''
    s = ", ".join([d['title'].replace(',',';') + ' (' + str(d['count']) + ')' for d in l])
 
    return s


def retrieveMetadata(URL:str):

    ''' retrieve response from URL '''

    lggr.info(f"Retrieving Metadata: {URL}")

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


def createfacetsDataframe(facetList,item, dateStamp, numberOfRecords, item_json):

    d_list = []
    #
    # initialize facets dictionary
    #
    d_dict = {'Id': item, 'DateTime': dateStamp, 'NumberOfRecords': numberOfRecords}
    
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
                d_dict[f + '_HI'] = d_dict[f + '_max'] /  d_dict[f + '_total']              # add total for facet
                output = createCountStringFromListOfDictionaries(item_json['meta'][f])
                d_dict[f] = output # add counts to dictionary

    return d_dict # return facets dictionary for item

parameters = {
    "relations": {
        "data": ['IsCitedBy', 'Cites', 'IsSupplementTo', 'IsSupplementedBy', 'IsContinuedBy', 'Continues',\
             'IsNewVersionOf', 'IsPreviousVersionOf', 'IsPartOf', 'HasPart', 'IsPublishedIn', 'IsReferencedBy',\
             'References', 'IsDocumentedBy', 'Documents', 'IsCompiledBy', 'Compiles', 'IsVariantFormOf', \
             'IsOriginalFormOf', 'IsIdenticalTo', 'HasMetadata', 'IsMetadataFor', 'Reviews', 'IsReviewedBy', \
             'IsDerivedFrom', 'IsSourceOf', 'Describes', 'IsDescribedBy', 'HasVersion', 'IsVersionOf', 'Requires', \
             'IsRequiredBy', 'Obsoletes', 'IsObsoletedBy'],
        "url":  'https://api.datacite.org/dois?&page[size]=1&query=relatedIdentifiers.relationType:'
    },
    "resources": {
        "data": ['Audiovisual','Book','BookChapter','Collection','ComputationalNotebook','ConferencePaper',\
                 'ConferenceProceeding','DataPaper','Dataset','Dissertation','Event','Image','InteractiveResource',\
                 'Journal','JournalArticle','Model','OutputManagementPlan','PeerReview','PhysicalObject','Preprint',\
                 'Report','Service','Software','Sound','Standard','Text','Workflow','Other'],
        "url":  'https://api.datacite.org/dois?&page[size]=1&resource-type-id='
    },
    "contributors": {
        "data": ['ContactPerson','DataCollector','DataCurator','DataManager','Distributor','Editor',
                    'HostingInstitution','Other','Producer','ProjectLeader','ProjectManager','ProjectMember',
                    'RegistrationAgency','RegistrationAuthority','RelatedPerson','ResearchGroup','RightsHolder',
                    'Researcher','Sponsor','Supervisor','WorkPackageLeader'],
        "url": 'https://api.datacite.org/dois?query=contributors.contributorType:'
    },
    "affiliations": {
        "data": ['Cornell University', 'University of Minnesota', 'Duke University', 'University of Michigan', 'Washington University in St. Louis', 'Virginia Tech'],
        "url": 'https://api.datacite.org/dois?query=creators.affiliation.name:*'
    }
}

facets = ['states','resourceTypes','created','published','registered','providers','clients',
              'affiliations','prefixes','certificates','licenses','schemaVersions','linkChecksStatus',
              'subjects','fieldsOfScience','citations','views','downloads']

commandLine=argparse.ArgumentParser(prog='retrieveDataCiteFacets',
                        description='''Use DataCite API to retrieve metadata records for given relationType, resourceType, 
                                    contributorType, and affiliations from DataCite. Save the retrieved metadata into
                                    json files (--outputJson) and facet data into csv file or database (defined in environment).'''
)
commandLine.add_argument("-il", "--itemList", nargs="*", type=str,
                        help='list of items to retrieve', default=[]
)
commandLine.add_argument("-fl", "--facetList", nargs="*", type=str, default=[],
                        help='''Select list of facets to retrieve from: states resourceTypes created published registered providers clients
                                affiliations prefixes certificates licenses schemaVersions linkChecksStatus
                                subjects fieldsOfScience citations views downloads. Default = all'''
)
commandLine.add_argument('--affiliations', dest='getAffiliations', 
                        default=False, action='store_true',
                        help='''Retrieve facets for Affiliations, e.g.: "Cornell University", "University of Minnesota", "Duke University",
                                "University of Michigan", "Washington University in St. Louis", "Virginia Tech"'''
)
commandLine.add_argument('--contributors', dest='getContributorTypes', 
                        default=False, action='store_true',
                        help='''Retrieve facets for all contributorTypes: ContactPerson, DataCollector, DataCurator, 
                                DataManager, Distributor, Editor, HostingInstitution, Other, Producer, ProjectLeader,
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
commandLine.add_argument('--showURLs', dest='showURLs', 
                        default=False, action='store_true',
                        help='''Show URLs that will be retrieved but DO NOT retrieve metadata'''
)
commandLine.add_argument('--jout', dest='outputJson', 
                        default=False, action='store_true',
                        help='Output retrieved metadata in json files'
)
commandLine.add_argument('--dbout', dest='dbout', 
                        default=False, action='store_true',
                        help='Output results in database'
)
commandLine.add_argument('--csvout', dest='csvout', 
                        default=False, action='store_true',
                        help='Output results in CSV file'
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

homeDir = str(Path.home())

lggr.info(f'*********************************** retrieveRelationandResourceCounts {dateStamp}')

itemCount = 0
itemInterval = 1

targets = []                                
                                            
if args.getRelations:                       # the target retrievals can be controlled by command line arguments:
    targets.append('relations')             # --affiliations --contributors --relations --resources retrieve all 
if args.getRelations:                       # items in each list, i.e. all relationTypes...
    targets.append('resources')
if args.getAffiliations:
    targets.append('affiliations')
if args.getContributorTypes:
    targets.append('contributors')

for i in args.itemList:                     # targets can also be listed as items on the command line if only
    for t in list(parameters):              # a small number of targets are needed. For example, -il Workflow
        if i in parameters[t]['data']:      # will retrieve data for just Workflow (a resource type)
            targets.append(t)

if len(targets) == 0:
    lggr.warning('No targets specified')
    exit()
else:
    lggr.info(f'Targets: {targets}')

d_list = []                                         # initialize list of dictionaries

for target in targets:                              # loop through targets
    lggr.debug(f'target')

    for item in parameters[target]['data']:         # loop items in target data

        if len(args.itemList) > 0 and not item in args.itemList:    # skip items not in itemList
            continue

        if target == 'affiliations':                # add wildcards to affiliation
            item = item.replace(' ','*') + '*'

        URL = parameters[target]['url'] + item

        if args.showURLs:                       # display URL to be retrieved without retrieving data
            lggr.info(f'URL: {URL}')
            continue

        res = retrieveMetadata(URL)             # retrieve metadata from DataCite
        item_json = res.json()

        if args.outputJson:     # write json to file
            jsonDirectory = homeDir + '/data/DataCite/metadata/' + item.replace(' ','_') + '__' + dateStamp + '/json'
            os.makedirs(jsonDirectory, exist_ok = True)
            jsonFile = jsonDirectory + '/' + item.replace(' ','_') + '.json'
            with open(jsonFile,'w') as outf:
                json.dump(item_json, outf, ensure_ascii=False)

        numberOfRecords = item_json.get('meta').get('total')
        if numberOfRecords == 0:
            continue

        itemCount += 1
        if itemCount % itemInterval == 0:
            lggr.info(f'Count: {itemCount} target: {target} URL: {URL} Number of records: {numberOfRecords}')

        if args.facetList:
            facetList = args.facetList
        else:
            facetList = facets

        d_dict = createfacetsDataframe(facetList,item, dateStamp, numberOfRecords, item_json)
        d_list.append(d_dict)

item_df = pd.DataFrame(d_list) # create dataframe

if args.dbout:                                  # add data to database
    con, cur = connectToDataCiteDatabase()      # connect to database for output
    item_df.to_sql('relationsAndResources',con,if_exists='append',index=False)

if args.csvout:                                 # output data to csv
    outputFile = 'DataCite_' + '_'.join(targets) + '__' + dateStamp + '.csv'
    item_df.to_csv(outputFile,encoding='utf-8',sep=',',index=False)