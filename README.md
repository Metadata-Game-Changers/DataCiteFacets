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
