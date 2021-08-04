#!/usr/bin/env python3

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

__author__ = "Marcus LaFerrera (@mlaferrera)"
__version__ = "v1.5.0"

import asyncio
from collections import defaultdict
import gzip
from io import BytesIO
from itertools import chain
import json
import logging
import os
import re
import tarfile
from typing import AsyncGenerator, DefaultDict, List, Union

import aiohttp
from bs4 import BeautifulSoup
import geoip2.database
from maxminddb import MODE_FD

from .dataclasses import ASN, Netblock


logger = logging.getLogger()


class ASParser:
    AS_ORGS_URL = "https://publicdata.caida.org/datasets/as-organizations"
    AS_PREFIXES_V6_URL = (
        "https://publicdata.caida.org/datasets/routing/routeviews6-prefix2as"
    )
    AS_PREFIXES_V4_URL = (
        "https://publicdata.caida.org/datasets/routing/routeviews-prefix2as"
    )
    MMDB_URL = "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&suffix=tar.gz"
    MMDB_FILENAME = "GeoLite2-City.mmdb"

    def __init__(self, token: str = None) -> None:
        self.token = token or os.getenv("MAXMIND_TOKEN")
        self.asns: DefaultDict = defaultdict()
        self.prefixes_ipv4: List[bytes] = []
        self.prefixes_ipv6: List[bytes] = []
        self.reader: Union[geoip2.database.Reader, None] = None
        if not self.token:
            raise Exception(
                "$MAXMIND_TOKEN must be set. Unable to download the geoip database!"
            )

    @staticmethod
    async def get_url(session, url) -> bytes:
        logger.info(f"Downloading {url}...")
        r = await session.get(url, ssl=True)
        r.raise_for_status()
        return await r.content.read()

    @staticmethod
    def gunzip(content) -> bytes:
        content = BytesIO(content)
        with gzip.open(content, "rb") as data:
            return data.read()

    async def get_prefixes_ipv4(self, session) -> None:
        url = f"{self.AS_PREFIXES_V4_URL}/pfx2as-creation.log"
        content = await self.get_url(session, url)
        last_entry = content.splitlines()[-1]
        uri = last_entry.split()[-1].decode()

        url = f"{self.AS_PREFIXES_V4_URL}/{uri}"
        content = await self.get_url(session, url)
        data = self.gunzip(content)
        self.prefixes_ipv4 = data.splitlines()

    async def get_prefixes_ipv6(self, session) -> None:
        url = f"{self.AS_PREFIXES_V6_URL}/pfx2as-creation.log"
        content = await self.get_url(session, url)
        last_entry = content.splitlines()[-1]
        uri = last_entry.split()[-1].decode()

        url = f"{self.AS_PREFIXES_V6_URL}/{uri}"
        content = await self.get_url(session, url)
        data = self.gunzip(content)
        self.prefixes_ipv6 = data.splitlines()

    async def get_as_orgs(self, session) -> None:
        orgs: DefaultDict = defaultdict()

        attrs = {"href": re.compile(r"\.as-org2info.jsonl.gz")}
        content = await self.get_url(session, self.AS_ORGS_URL)
        soup = BeautifulSoup(content, "html.parser")
        uri = soup.find_all("a", attrs=attrs)[-1].get("href")

        url = f"{self.AS_ORGS_URL}/{uri}"
        content = await self.get_url(session, url)
        as_orgs = self.gunzip(content)

        for line in as_orgs.splitlines():
            entry = json.loads(line)
            if entry["type"] == "Organization":
                orgs[entry["organizationId"]] = entry
            elif entry["type"] == "ASN":
                self.asns[entry["asn"]] = entry

        {
            self.asns[k].update({"org": orgs[v["organizationId"]]})
            for k, v in self.asns.copy().items()
        }

    async def get_maxmind(self, session) -> None:
        url = f"{self.MMDB_URL}&license_key={self.token}"
        content = BytesIO(await self.get_url(session, url))
        with tarfile.open(mode="r:*", fileobj=content) as tar:
            for filename in tar.getnames():
                if filename.endswith(f"/{self.MMDB_FILENAME}"):
                    data = tar.extractfile(filename)
                    if data:
                        db = BytesIO(data.read())
                        db.name = self.MMDB_FILENAME
                        self.reader = geoip2.database.Reader(db, mode=MODE_FD)
        if not self.reader:
            raise Exception(f"Failed to extract {self.MMDB_FILENAME} database!")

    async def parse(self) -> AsyncGenerator:
        logger.info("Parsing ASN and Subnets...")
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                *[
                    self.get_prefixes_ipv4(session),
                    self.get_prefixes_ipv6(session),
                    self.get_as_orgs(session),
                    self.get_maxmind(session),
                ]
            )
        logger.info(
            f"Parsing {len(self.prefixes_ipv4)} ipv4 prefixes "
            + f"and {len(self.prefixes_ipv6)} ipv6 prefixes"
        )
        for entry in chain(self.prefixes_ipv4, self.prefixes_ipv6):
            prefix, prefix_length, asn = entry.split()
            asn = asn.decode().split("_")[0].split(",")[0]
            yield Netblock(
                asn=ASN(**self.asns.get(asn, {"asn": asn})),
                prefix=prefix.decode(),
                prefix_length=prefix_length.decode(),
                georeader=self.reader,
            )
        self.reader.close()
