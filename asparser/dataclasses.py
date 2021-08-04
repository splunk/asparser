#  Copyright 2021 Splunk Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
from typing import List, Optional

import geoip2.database
from pydantic import BaseModel

logger = logging.getLogger()


class Org(BaseModel):
    changed: Optional[str]
    country: Optional[str]
    name: Optional[str]
    organizationId: Optional[str]
    source: Optional[str]
    type: Optional[str]


class ASN(BaseModel):
    asn: str
    org: Optional[Org] = Org()
    changed: Optional[str]
    source: Optional[str]
    organizationId: Optional[str]
    opaqueId: Optional[str]


class GeoSubdivision(BaseModel):
    iso_code: Optional[str]
    name: Optional[str]


class Geo(BaseModel):
    accuracy_radius: Optional[int]
    time_zone: Optional[str]
    postal_code: Optional[str]
    subdivisions: List[GeoSubdivision] = []
    city: Optional[str]
    continent: Optional[str]
    country: Optional[str]
    registered_country: Optional[str]
    iso_code: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


class Netblock(BaseModel):
    asn: str
    org: Optional[Org]
    changed: Optional[str]
    source: Optional[str]
    organizationId: Optional[str]
    opaqueId: Optional[str]
    geo: Geo
    prefix: str

    def __init__(
        self,
        asn: ASN,
        prefix: str,
        prefix_length: str,
        georeader: geoip2.database.Reader,
    ):
        try:
            geoinfo = georeader.city(prefix).raw
            geo = Geo(
                accuracy_radius=geoinfo.get("location", {}).get("accuracy_radius"),
                time_zone=geoinfo.get("location", {}).get("time_zone"),
                postal_code=geoinfo.get("postal", {}).get("code"),
                subdivisions=[],
                city=geoinfo.get("city", {}).get("names", {}).get("en"),
                continent=geoinfo.get("continent", {}).get("names", {}).get("en"),
                country=geoinfo.get("country", {}).get("names", {}).get("en"),
                registered_country=geoinfo.get("registered_country", {})
                .get("names", {})
                .get("en"),
                iso_code=geoinfo.get("country", {}).get("iso_code"),
                latitude=geoinfo.get("location", {}).get("latitude"),
                longitude=geoinfo.get("location", {}).get("longitude"),
            )
            for subdivision in geoinfo.get("subdivisions", []):
                geo.subdivisions.append(
                    GeoSubdivision(
                        iso_code=subdivision.get("iso_code"),
                        name=subdivision.get("names", {}).get("en"),
                    )
                )
        except Exception as err:
            geo = Geo()
            logger.debug(err)
        super().__init__(
            asn=asn.asn,
            org=asn.org,
            changed=asn.changed,
            source=asn.source,
            organizationId=asn.organizationId,
            opaqueId=asn.opaqueId,
            geo=geo,
            prefix=f"{prefix}/{prefix_length}",
        )
