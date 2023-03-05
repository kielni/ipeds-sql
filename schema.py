import argparse
import os
from typing import List, Dict, Optional

import pandas as pd
from sqlalchemy import create_engine

"""
IPEDS data for use by humans

https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx?gotoReportId=7&fromIpeds=true&

Set database connection string in environmentl default sqlite:///ipeds.db

    `export DB_CONNECTION="sqlite:///ipeds.db"`

Download dictionary (zipped xlsx) and data (zipped csv) files
Run `python schema.py hd2021`
Insert into database (any supported by SQLAlchemy).
Make data easier to use by humans

  - English table names: Directory information in directory table (instead of hd2021)
  - Lowercase column names to make them easier to read
  - Replace numeric codes with text labels; prioritize ease of use over saving
    cheap and abundant memory and disk space

Example: hd2021 Institutional Characteristics	Directory information
  https://nces.ed.gov/ipeds/datacenter/data/HD2021.zip
  https://nces.ed.gov/ipeds/datacenter/data/HD2021_Dict.zip
  
hd2021 ic2021 c2021_a ef2021a ef2021d gr2021 adm2021 is 126M sqlite file; 19M gzipped

instead of

select unitid, instnm, city, stabbr, longitud, latitude, webaddr
from directory
where cyactive=1 and c21szset in (8, 11, 14, 17);

do this

select unitid, instnm, city, stabbr, longitud, latitude, webaddr
from directory
where cyactive='Yes' and c21szset like 'Four-year%highly residential'
"""

"""
Run with dataset names and optional path

    python schema.py hd2021 ic2021 c2021_a ef2021a ef2021d gr2021 adm2021 --path datasets
"""
# readable names for datasets
TABLES = {
    "hd2021": "directory",
    "ic2021": "offering",
    "c2021_a": "completion",
    "ef2021a": "enrollment",
    "ef2021d": "class",
    "gr2021": "graduation",
    "adm2021": "admission"
}


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and remove trailing space form column names"""
    columns: Dict[str, str] = {}
    for col in list(df.columns):
        columns[col] = col.lower().strip()
    return df.rename(columns=columns)


def create_table(file_name: str, table_name: str):
    engine = create_engine(os.environ.get("DB_CONNECTION", "sqlite:///ipeds.db"), echo=False)
    """
    Get variables from varlist sheet of dictionary

    varlist sheet contains name, data type, and title for variables
    varnumber,varname,DataType,Fieldwidth,format,imputationvar,varTitle
    1,UNITID,N,6,Cont,,Unique identification number of the institution
    """
    df = pd.read_excel(f"{file_name}.xlsx", sheet_name="varlist")
    df["varname"] = df["varname"].str.lower()
    # variables that are numeric codes
    codes = df[(df["DataType"] == "N") & (df["format"] == "Disc")]
    codes = codes["varname"]
    data = df[["varnumber", "varname", "varTitle"]]
    data = data.rename(columns={"varnumber": "number", "varname": "name", "varTitle": "title"})
    data = data.set_index("number")
    table = f"{table_name}_dict"
    print(f"inserting {len(data.index)} rows into dictionary table {table}")
    data.to_sql(f"{table}", con=engine, if_exists="replace")

    """
    Frequencies sheet contains name, value, and title for variable values
    varnumber,varname,codevalue,valuelabel,frequency,percent
    10016,STABBR,AL,Alabama,81,1.29
    """
    # sometimes the Frequencies sheet doesn't exist
    try:
        df = pd.read_excel(f"{file_name}.xlsx", sheet_name="Frequencies")
    except ValueError:
        print(f"\tno Frequencies sheet in {file_name}")
        df = pd.DataFrame(columns=["varnumber", "varname", "codevalue", "valuelabel"])
    values = df[["varnumber", "varname", "codevalue", "valuelabel"]]
    values = values.rename(columns={"varnumber": "number", "varname": "name", "codevalue": "value", "valuelabel": "label"})
    values["name"] = values["name"].str.lower()
    """
    data
    """
    table = table_name
    df = pd.read_csv(f"{file_name}.csv")
    df = rename_columns(df).set_index("unitid")
    # de-normalize numeric codes; prioritize ease of use over memory/disk size
    for idx, variable in codes.items():
        lookup = values[values["name"] == variable]
        lookup = lookup[["value", "label"]].set_index("value")
        print(f"\treplacing codes for {variable}; {len(lookup.index)} values")
        lookup.index = pd.to_numeric(lookup.index)
        df = df.join(lookup, on=variable, how="left")
        df = df.drop(columns=variable).rename(columns={"label": variable})
    print(f"inserting {len(df.index)} rows into table {table}")
    df.to_sql(f"{table}", con=engine, if_exists="replace", index_label="unitid")


def main(datasets: List[str], path: Optional[str]):
    if path and not path.endswith("/"):
        path += "/"
    for table in datasets:
        name = TABLES.get(table, table)
        print(f"\ncreating table {table} from dataset {name}")
        create_table(f"{path}{table}", name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("datasets", nargs="+", help="dataset names, without extension (ie hd2021)")
    parser.add_argument("--path", help="path prefix for datasets", default="")
    args = parser.parse_args()
    main(args.datasets, args.path)
