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

from argparse import ArgumentParser, Namespace
import asyncio
from datetime import datetime
import logging
import os

from asparser import ASParser

try:
    from aiohec import SplunkHEC, SplunkKVStore

    SPLUNK_HEC = True
except ImportError:
    SPLUNK_HEC = False

logger = logging.getLogger()


async def run(args: Namespace) -> None:
    asnparse = ASParser(token=args.maxmind_token)
    if args.host:
        if not SPLUNK_HEC:
                logger.warn(
                    "aiohec module is not installed. Unable to save results to HEC or KVStore"
                )
                exit(1)

        if args.endpoint == "hec":
            async with SplunkHEC(
                splunk_host=args.host,
                token=args.splunk_token or os.getenv("SPLUNK_TOKEN"),
            ) as hec:
                async for result in asnparse.parse():
                    await hec.add_event(result.json())

        elif args.endpoint == "kvstore":
            async with SplunkKVStore(
                host=args.host,
                username=args.username or os.getenv("SPLUNK_USERNAME"),
                password=args.password or os.getenv("SPLUNK_PASS"),
                app=args.app,
                collection=args.collection,
            ) as kvstore:
                async for result in asnparse.parse():
                    await kvstore.add_event(result.dict())

    elif args.outfile:
        logger.info(f"Saving results to {args.outfile}")
        with open(args.outfile, "w") as outfile:
            async for result in asnparse.parse():
                outfile.write(f"{result.json()}\n")
    else:
        async for result in asnparse.parse():
            print(f"{result.json()}\n")


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
        help="Log level for events",
    )
    parser.add_argument(
        "--maxmind-token",
        default=None,
        help="MaxMind API Token",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        dest="outfile",
        default=f"asn.{datetime.now().strftime('%Y%m%d')}.json",
        help="Destination file for JSON results",
    )
    parser.add_argument(
        "-s",
        "--host",
        default=None,
        help="Splunk host",
    )
    parser.add_argument(
        "--splunk-token",
        default=None,
        help="Splunk HEC endpoint token",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Splunk username",
    )
    parser.add_argument("--password", default=None, help="Splunk password")
    parser.add_argument(
        "--app", default="search", help="Splunk app where KVStore is configured"
    )
    parser.add_argument(
        "--collection", default="asparse", help="Splunk KVStore collection name"
    )
    parser.add_argument(
        "--endpoint",
        default="kvstore",
        choices=["kvstore", "hec"],
        help="Splunk endpoint to save results to",
    )

    args = parser.parse_args()
    logger.setLevel(args.log_level)
    logger.addHandler(logging.StreamHandler())
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
