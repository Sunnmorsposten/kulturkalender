#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
cd src/newsscraper

echo "Scraping started at: $(date)"

for spider in \
  fiskarlagetspider fiskebatspider hispider rafisklagetspider \
  sjomatnorgespider surofispider kystverketspider pelagiskforeningspider \
  nffovergangerspider bypakkealesundspider politispesialenhetspider
do
    echo "Running $spider …"
    # Run scrapy in the foreground so timeout can really kill it, then keep going
    if ! timeout --foreground --kill-after=10s 120s \
           scrapy crawl "$spider" --loglevel=CRITICAL
    then
        echo "$spider did not finish cleanly (exit $?). Continuing…" >&2
    fi
done

echo "Scraping finished at: $(date)"

