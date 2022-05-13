# DataCite Facets
The [DataCite Metadata Schema](https://schema.datacite.org/meta/kernel-4.4/) has [evolved considerably](https://metadatagamechangers.com/blog/2021/1/11/fair-datacite-metadata-evolution) over more than a decade and now includes a variety of metadata elements, resource types, related resources, and contributor types in millions of metadata records from over 2000 repositories. The DataCite Metadata Working Group has overseen this evolution and works with DataCite members and the DataCite Board to chart the path forward for the metadata schema. Understanding how DataCite metadata is currently being used provides critical background for this group. 

A facet is a metadata element, usually from a controlled list, that provides counts of records in a query result with particular values for the metadata element. The [DataCite JSON Response](https://blog.datacite.org/introducing-datacite-json/) includes data on a variety of facets for each query done using the DataCite API. This tool retrieves those facets for a variety of queries and summarizes the results.

## Usage
```
usage: retrieveDataCiteFacets [-h] [-il [ITEMLIST ...]] [-fl [FACETLIST ...]] [--affiliations] [--contributors] [--relations] [--resources] [--showURLs] [--showtargets] [--csvout] [--dbout] [--jout] [--pout]
                              [--loglevel {debug,info,warning}] [--logto FILE]

Use DataCite API to retrieve metadata records for given relationType, resourceType, contributorType, and affiliations from DataCite. Save the retrieved metadata into json files (--jout) and facet data into csv
file or database (defined in environment).

options:
  -h, --help            show this help message and exit
  -il [ITEMLIST ...], --itemList [ITEMLIST ...]
                        list of items to retrieve
  -fl [FACETLIST ...], --facetList [FACETLIST ...]
                        Select list of facets to retrieve from: states resourceTypes created published registered providers clients affiliations prefixes certificates licenses schemaVersions linkChecksStatus
                        subjects fieldsOfScience citations views downloads. Default = all
  --affiliations        Retrieve facets for Affiliations, e.g.: "Cornell University", "University of Minnesota", "Duke University", "University of Michigan", "Washington University in St. Louis", "Virginia Tech"
  --contributors        Retrieve facets for all contributorTypes: ContactPerson, DataCollector, DataCurator, DataManager, Distributor, Editor, HostingInstitution, Other, Producer, ProjectLeader, ProjectManager,
                        ProjectMember, RegistrationAgency, RegistrationAuthority, RelatedPerson, ResearchGroup, RightsHolder, Researcher, Sponsor, Supervisor, WorkPackageLeader
  --relations           Retrieve facets for all relations: IsCitedBy, Cites, IsSupplementTo, IsSupplementedBy, IsContinuedBy, Continues, IsNewVersionOf, IsPreviousVersionOf, IsPartOf, HasPart, IsPublishedIn,
                        IsReferencedBy, References, IsDocumentedBy, Documents, IsCompiledBy, Compiles, IsVariantFormOf, IsOriginalFormOf, IsIdenticalTo, HasMetadata, IsMetadataFor, Reviews, IsReviewedBy,
                        IsDerivedFrom, IsSourceOf, Describes, IsDescribedBy, HasVersion, IsVersionOf, Requires, IsRequiredBy, Obsoletes, IsObsoletedBy
  --resources           Retrieve facets for all resource types: Audiovisual, Book, BookChapter, Collection, ComputationalNotebook, ConferencePaper, ConferenceProceeding, DataPaper, Dataset, Dissertation, Event,
                        Image, InteractiveResource, Journal, JournalArticle, Model, OutputManagementPlan, PeerReview, PhysicalObject, Preprint, Report, Service, Software, Sound, Standard, Text, Workflow, Other
  --showURLs            Show URLs that will be retrieved but DO NOT retrieve metadata
  --showtargets         Show target lists (e.g. all resourceTypes, relationTypes, contributorTypes)
  --csvout              Output results in CSV file
  --dbout               Output results in database (requires sqlite3 package)
  --jout                Output retrieved metadata in json files
  --pout                Output facet counts to terminal (requires tabulate package https://pypi.org/project/tabulate/)
  --loglevel {debug,info,warning}
                        Logging level for logging module (https://docs.python.org/3/howto/logging.html#useful-handlers)
  --logto FILE          Log file (will append to file if exists)
  ```
  
  ## Targets
RetrieveDataCiteFacets is designed to answer questions about several kinds of *targets*, specifically resourceTypes, relationTypes, contributorTypes, or creator affiliations (a special case). *Targets* are groups of *items* defined by DataCite codelists. To see the *items* included in each *target*, use the --showtargets flag to display all *target items*.  

**retrieveRelationAndResourceCounts --showtargets**

Target: relations  
['IsCitedBy', 'Cites', 'IsSupplementTo', 'IsSupplementedBy', 'IsContinuedBy', 'Continues', 'IsNewVersionOf', 'IsPreviousVersionOf', 'IsPartOf', 'HasPart', 'IsPublishedIn', 'IsReferencedBy', 'References', 'IsDocumentedBy', 'Documents', 'IsCompiledBy', 'Compiles', 'IsVariantFormOf', 'IsOriginalFormOf', 'IsIdenticalTo', 'HasMetadata', 'IsMetadataFor', 'Reviews', 'IsReviewedBy', 'IsDerivedFrom', 'IsSourceOf', 'Describes', 'IsDescribedBy', 'HasVersion', 'IsVersionOf', 'Requires', 'IsRequiredBy', 'Obsoletes', 'IsObsoletedBy']

Target: resources  
['Audiovisual', 'Book', 'BookChapter', 'Collection', 'ComputationalNotebook', 'ConferencePaper', 'ConferenceProceeding', 'DataPaper', 'Dataset', 'Dissertation', 'Event', 'Image', 'InteractiveResource', 'Journal', 'JournalArticle', 'Model', 'OutputManagementPlan', 'PeerReview', 'PhysicalObject', 'Preprint', 'Report', 'Service', 'Software', 'Sound', 'Standard', 'Text', 'Workflow', 'Other']

Target: contributors  
['ContactPerson', 'DataCollector', 'DataCurator', 'DataManager', 'Distributor', 'Editor', 'HostingInstitution', 'Other', 'Producer', 'ProjectLeader', 'ProjectManager', 'ProjectMember', 'RegistrationAgency', 'RegistrationAuthority', 'RelatedPerson', 'ResearchGroup', 'RightsHolder', 'Researcher', 'Sponsor', 'Supervisor', 'WorkPackageLeader']

Target: affiliations  
['Cornell University', 'University of Minnesota', 'Duke University', 'University of Michigan', 'Washington University in St. Louis', 'Virginia Tech']

Facets 
['states', 'resourceTypes', 'created', 'published', 'registered', 'providers', 'clients', 'affiliations', 'prefixes', 'certificates', 'licenses', 'schemaVersions', 'linkChecksStatus', 'subjects', 'fieldsOfScience', 'citations', 'views', 'downloads']

*Note: the affiliations items shown here are an example of an affiliation target that includes several Universities. This list is defined in the code and needs to be modified to include the affiliation strings you need to search for.*

## Selecting items

### Command line options provide shortcuts to select all of the items in a target:
| Flag  | Selection| Flag  | Selection|
|:-------- |:------| :-------- |:------| 
| --affiliations | query all affiliations|--relations | query all relationTypes|
| --contributors | query all contributorTypes |--relations | query all resourceTypes|

### Select items from different targets
Sometimes it is hard to remember what kind of target a particular target is or you might need a small selection of items from several targets to answer some interesting questions. In this case, use the item list (-il) option. For example **retrieveRelationAndResourceCounts -il DataManager InteractiveResource Book** retrieves facet counts for records that have contributorType="Data Manager" or "resourceTypeGeneral="InteractiveResource" or "resourceTypeGeneral="Books".  

*Keep in mind that these three criteria are completely independent, these are all separate queries.*

## Selecting facets
Each DataCite API queries returns data for 18 facets covering many aspects of DataCite usage. Many times this can cause information overload! If you are answering specific questions, you may need only a small number of these facets. For example, if you are only interested in the number of records, the "states" facet is all you need: **retrieveRelationAndResourceCounts -il DataManager InteractiveResource Book -fl states --pout** gives the samll result:  

| Id                  |    DateTime |   NumberOfRecords |   states_number |   states_max | states_common   |   states_total |   states_HI | states            |
|---------------------|-------------|-------------------|-----------------|--------------|-----------------|----------------|-------------|-------------------|
| DataManager         | 20220513_16 |            944221 |               1 |       944221 | findable        |         944221 |           1 | Findable (944221) |
| Book                | 20220513_16 |             15086 |               1 |        15086 | findable        |          15086 |           1 | Findable (15086)  |
| InteractiveResource | 20220513_16 |             31889 |               1 |        31889 | findable        |          31889 |           1 | Findable (31889)  |

Which shows that there are nearly 1 million Data Managers referenced in DataCite metadata. 

_Bonus Question_: There are actually three related contributor types: DataCollector, DataCurator, DataManager. How does usage of these compare?

**retrieveRelationAndResourceCounts -il DataCollector DataCurator DataManager -fl states --pout**.  

| Id            |    DateTime |   NumberOfRecords |   states_number |   states_max | states_common   |   states_total |   states_HI | states            |
|---------------|-------------|-------------------|-----------------|--------------|-----------------|----------------|-------------|-------------------|
| DataCollector | 20220513_17 |            886529 |               1 |       886529 | findable        |         886529 |           1 | Findable (886529) |
| DataCurator   | 20220513_17 |            137177 |               1 |       137177 | findable        |         137177 |           1 | Findable (137177) |
| DataManager   | 20220513_17 |            944238 |               1 |       944238 | findable        |         944238 |           1 | Findable (944238) |
