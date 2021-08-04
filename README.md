# asparser

A module to collect and normalize ASN datasets and enrich with Geolocation results.

Results may be returned to STDOUT, saved to a localfile, inserted into a Splunk 
Index via the HTTP Event Collector Endpoint (HEC), or inserted into a Splunk 
KVStore Collection.

##  Installation

    git clone https://github.com/splunk/asparser
    cd asparser
    python3 -m pip install -r requirements.txt .

## Usage

    usage: asparser [-h] [--log-level {DEBUG,INFO,WARN,ERROR,CRITICAL}]
                    [--maxmind-token MAXMIND_TOKEN] [-o OUTFILE] [-s HOST]
                    [--splunk-token SPLUNK_TOKEN] [--username USERNAME]
                    [--password PASSWORD] [--app APP] [--collection COLLECTION]
                    [--endpoint {kvstore,hec}]

    optional arguments:
      -h, --help            show this help message and exit
      --log-level {DEBUG,INFO,WARN,ERROR,CRITICAL}
                            Log level for events
      --maxmind-token MAXMIND_TOKEN
                            MaxMind API Token
      -o OUTFILE, --outfile OUTFILE
                            Destination file for JSON results
      -s HOST, --host HOST  Splunk host
      --splunk-token SPLUNK_TOKEN
                            Splunk HEC endpoint token
      --username USERNAME   Splunk username
      --password PASSWORD   Splunk password
      --app APP             Splunk app where KVStore is configured
      --collection COLLECTION
                            Splunk KVStore collection name
      --endpoint {kvstore,hec}
                            Splunk endpoint to save results to


## Examples

Save results to a Splunk KVStore:

    export MAXMIND_TOKEN=1234567
    export SPLUNK_HOST=127.0.0.1
    export SPLUNK_APP=search
    export SPLUNK_USER=admin
    export SPLUNK_PASS=abc123
    asparser --splunk-type kvstore 


Save results to a Splunk index via HEC:

    export MAXMIND_TOKEN=1234567
    export SPLUNK_HOST=127.0.0.1
    export SPLUNK_TOKEN=1234-abcd-efgh
    asparser --splunk-type hec 


Save results to a local file on disk:

    export MAXMIND_TOKEN=1234567
    asparser -o asparser-results.json


## Example Output

    {
      "asn": "13335",
      "org": {
        "changed": "20210111",
        "country": "US",
        "name": "Cloudflare, Inc.",
        "organizationId": "CLOUD14-ARIN",
        "source": "ARIN",
        "type": "Organization"
      },
      "changed": "20170217",
      "source": "ARIN",
      "organizationId": "CLOUD14-ARIN",
      "opaqueId": "28408e4f0567c2545afefd9cbce183bc_ARIN",
      "geo": {
        "accuracy_radius": 1000,
        "time_zone": "Australia/Sydney",
        "postal_code": null,
        "subdivisions": [],
        "city": null,
        "continent": "Oceania",
        "country": "Australia",
        "registered_country": "Australia",
        "iso_code": "AU",
        "latitude": -33.494,
        "longitude": 143.2104
      },
      "prefix": "1.0.0.0/24"
    }


## Support

This software is released as-is. Splunk provides no warranty and no support on this software.

## License

Copyright 2021 Splunk Inc.
 
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
 
http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
