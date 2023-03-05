# IPEDS data for modern engineers

The [Integrated Postsecondary Education Data System (IPEDS)](https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx)
has been providing extensive
datasets on post-secondary education since the 1980s. While it's great to have access
to the data, the delivery format leaves a lot to be desired. A SQL version is available, but
only for a proprietary database program that runs only on a proprietary OS (Microsoft Access).
Computing has advanced; we can prioritize ease of use for humans over saving kilobytes of memory.

This repo includes a Python script to read IPEDS datasets and data dictionary information
into any SQL database supported by SQLAlchemy. As part of this, it attempts to make the
schema easier to understand and use:

  - English table names: for example, a `directory` table for the "Directory information" dataset, instead of `hd2021`
  - Use lowercase column names to make them easier to read (all caps is no longer in fashion)
  - Replace numeric codes with text labels; prioritize ease of use over saving (now) cheap and abundant memory and disk space. For example, `Four-year, small, highly residential` instead of `11`. This enables writing easier to understand queries: `like 'Four-year%highly resdential'` instead of `in (11, 14, 17)`

## usage (DIY)

Download datasets of interest from https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx

  - CSV data from Data file column (ie [HD2021.zip](https://nces.ed.gov/ipeds/datacenter/data/HD2021.zip))
  - Data dictionary spreadsheet from Dictionary column (ie [HD2021_Dict.zip](https://nces.ed.gov/ipeds/datacenter/data/HD2021_Dict.zip))

Unzip all files (ie `hd2021.csv`, `hd2021.xlsx`)

Install requirements ([pandas](https://pandas.pydata.org/) and [SQLAlchemy](https://www.sqlalchemy.org/))

```
pip install -r requirements.txt
```

Create a database: any supported by SQLAlchemy. Set a database connection string in environment (default is `sqlite:///ipeds.db`)

```
export DB_CONNECTION="sqlite:///ipeds.db"
```

Run `schema.py` with dataset(s) to create tables and populate data

```
python -u schema.py hd2021 ic2021 c2021_a ef2021a ef2021d gr2021 adm2021 --path datasets | tee ipeds.log

creating table hd2021 from dataset directory
inserting 74 rows into dictionary table directory_dict
    replacing codes for fips; 59 values
    replacing codes for obereg; 10 values
...
    replacing codes for dfrcuscg; 4 values
inserting 6289 rows into table directory

creating table ic2021 from dataset offering
inserting 115 rows into dictionary table offering_dict
    replacing codes for peo1istr; 2 values
    replacing codes for peo2istr; 2 values
    replacing codes for confno4; 133 values
inserting 6179 rows into table offering
...
```

Query the data

```
select unitid, instnm, city, stabbr, longitud, latitude, webaddr
from directory
where cyactive='Yes' and c21szset like 'Four-year%highly residential'
````

## usage (SQLite database)

Download a [gzipped SQLlite database](ipeds.db.gz), including these datasets:

| survey | description| dataset name | table name|
|--------|------------|--------------|-----------|
| Institutional Characteristics | Directory information | hd2021 | directory |
| Institutional Characteristics | Educational offerings, organization, services and athletic associations | ic2021 | offering |
| Completions | Awards/degrees conferred by program (6-digit CIP code), award level, race/ethnicity, and gender: July 1, 2020 to June 30, 2021 | c2021_a | completion |
| Fall Enrollment | Race/ethnicity, gender, attendance status, and level of student: Fall 2021 | ef2021a | enrollment |
| Fall Enrollment | Total entering class, retention rates, and student-to-faculty ratio: Fall 2021 | ef2021d | class |
| Graduation Rates | Graduation rate data, 150% of normal time to complete - cohort year 2015 (4-year) and cohort year 2018 (2-year) institutions | gr2021 | graduation |
| Admissions and Test Scores | Admission considerations, applications, admissions, enrollees and test scores, fall 2021 | adm2021 | admission |

It's only 19 MB gzipped / 126 MB uncompressed, even after de-normalizing the codes. This will easily fit in memory on any modern device.

## schema

The `schema.py` script creates two tables for each dataset.

A **data** table, containing the survey results from the dataset csv, with lowercased column names and de-normalized values.

Example from `directory` (`hd2021` dataset):

```
sqlite> select * from directory where instnm like 'Brown U%';
  unitid = 217156
  instnm = Brown University
  ialias =
    addr = One Prospect Street
    city = Providence
  stabbr = RI
     zip = 02912
   chfnm = Christina Paxson
chftitle = President
 gentele = 4018631000
     ein = 50258809
    duns = 001785542
   opeid = 340100
 webaddr = www.brown.edu/
adminurl = https://www.brown.edu/admission
 faidurl = https://www.brown.edu/about/administration/financial-aid/
 applurl = https://www.commonapp.org/
npricurl = https://npc.collegeboard.org/app/brown
  veturl = https://www.brown.edu/campus-life/support/veterans-and-commissioning-programs/student-veteran-portal/frequently-asked-questions#gibill
  athurl =
 disaurl = https://www.brown.edu/campus-life/support/accessibility-services/
     act = A
   newid = -2
closedat = -2
f1sysnam = -2
f1syscod = -2
countynm = Providence County
longitud = -71.40385
latitude = 41.82617
    fips = Rhode Island
  obereg = New England (CT, ME, MA, NH, RI, VT)
 opeflag = Participates in Title IV federal financial aid programs
  sector = Private not-for-profit, 4-year or above
 iclevel = Four or more years
 control = Private not-for-profit
 hloffer = Doctor's degree
 ugoffer = Undergraduate degree or certificate offering
 groffer = Graduate degree or certificate offering
hdegofr1 = Doctor's degree - research/scholarship and professional practice
deggrant = Degree-granting
    hbcu = No
hospital = No
 medical = Yes
  tribal = No
  locale = City: Midsize
openpubl = Institution is open to the public
 deathyr = Not applicable
cyactive = Yes
 postsec = Primarily postsecondary institution
 pseflag = Active postsecondary institution
pset4flg = Title IV postsecondary institution
  rptmth = Student charges for full academic year and fall GR/SFA/retention rate cohort
 instcat = Degree-granting, primarily baccalaureate or above
c21basic = Doctoral Universities: Very High Research Activity
 c21ipug = Arts & sciences focus, high graduate coexistence
c21ipgrd = Research Doctoral: Comprehensive programs, with medical/veterinary school
c21ugprf = Four-year, full-time, more selective, lower transfer-in
c21enprf = Majority undergraduate
c21szset = Four-year, medium, highly residential
c18basic = Doctoral Universities: Very High Research Activity
c15basic = Doctoral Universities: Highest Research Activity
 ccbasic = Research Universities (very high research activity)
carnegie = Doctoral/Research Universities--Extensive
landgrnt = Not a Land Grant Institution
instsize = 10,000 - 19,999
f1systyp = Institution is NOT part of a multi-institution or multi-campus organization
    cbsa = Providence-Warwick, RI-MA
cbsatype = Metropolitan Statistical Area
     csa = Boston-Worcester-Providence, MA-RI-NH-CT
   necta = Providence-Warwick, RI-MA
countycd = Providence County, RI
cngdstcd = RI, District 01
 dfrcgid = Doctoral Universities: Highest Research Activity, Private not-for-profit
dfrcuscg = Yes, institution submitted a custom comparison group
```

A **dictionary** table, containing (still unfortunately obscure) column names and descriptions:

Example from `directory` (`hd2021` dataset):

```
select name, title from directory_dict;
unitid      Unique identification number of the institution
instnm      Institution (entity) name
ialias      Institution name alias
addr        Street address or post office box
city        City location of institution
stabbr      State abbreviation
zip         ZIP code
fips        FIPS state code
obereg      Bureau of Economic Analysis (BEA) regions
chfnm       Name of chief administrator
chftitle    Title of chief administrator
gentele     General information telephone number
ein         Employer Identification Number
duns        Dun and Bradstreet numbers
opeid       Office of Postsecondary Education (OPE) ID Numb
opeflag     OPE Title IV eligibility indicator code
webaddr     Institution's internet website address
adminurl    Admissions office web address
faidurl     Financial aid office web address
applurl     Online application web address
npricurl    Net price calculator web address
veturl      Veterans and Military Servicemembers tuition po
athurl      Student-Right-to-Know student athlete graduatio
disaurl     Disability Services Web Address
sector      Sector of institution
iclevel     Level of institution
control     Control of institution
hloffer     Highest level of offering
ugoffer     Undergraduate offering
groffer     Graduate offering
hdegofr1    Highest degree offered
deggrant    Degree-granting status
hbcu        Historically Black College or University
hospital    Institution has hospital
medical     Institution grants a medical degree
tribal      Tribal college
locale      Degree of urbanization (Urban-centric locale)
openpubl    Institution open to the general public
act         Status of institution
newid       UNITID for merged schools
deathyr     Year institution was deleted from IPEDS
closedat    Date institution closed
cyactive    Institution is active in current year
postsec     Primarily postsecondary indicator
pseflag     Postsecondary institution indicator
pset4flg    Postsecondary and Title IV institution indicato
rptmth      Reporting method for student charges, graduatio
instcat     Institutional category
c21basic    Carnegie Classification 2021: Basic
c21ipug     Carnegie Classification 2021: Undergraduate Ins
c21ipgrd    Carnegie Classification 2021: Graduate Instruct
c21ugprf    Carnegie Classification 2021: Undergraduate Pro
c21enprf    Carnegie Classification 2021: Enrollment Profil
c21szset    Carnegie Classification 2021: Size and Setting
c18basic    Carnegie Classification 2018: Basic
c15basic    Carnegie Classification 2015: Basic
ccbasic     Carnegie Classification 2005/2010: Basic
carnegie    Carnegie Classification 2000
landgrnt    Land Grant Institution
instsize    Institution size category
f1systyp    Multi-institution or multi-campus organization
f1sysnam    Name of multi-institution or multi-campus organ
f1syscod    Identification number of multi-institution or m
cbsa        Core Based Statistical Area (CBSA)
cbsatype    CBSA Type Metropolitan or Micropolitan
csa         Combined Statistical Area (CSA)
necta       New England City and Town Area (NECTA)
countycd    Fips County code
countynm    County name
cngdstcd    State and 114TH Congressional District ID
longitud    Longitude location of institution
latitude    Latitude location of institution
dfrcgid     Data Feedback Report comparison group created b
dfrcuscg    Data Feedback Report - Institution submitted a
```

## artifacts

[schema.sql](schema.sql) contains the schema for the datasets listed above.

[dictionary.txt](dictionary.txt) contains the data dictionary (column name and English description) for the datasets listed above.
