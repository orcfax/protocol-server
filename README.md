# Custom Protocol

Outline/protocol server for Orcfax Custom Feeds.

## Summary

Demonstrates a sample deployment for a data provider website, e.g. Proof of
Reserve; IoT; or any other data provider/collector service.

Public and private keys are created on initialization and the public key
made available to the application.

> NB. The private key is in memory for the purposes of demo only and would need
to be offline elsewhere with other rotation based protections.

Data is made available via API on-demand or as microdata every 30 seconds. In
a production system, the method of production would be customized.

Data is then archived in a predictable manner as JSONL. The JSONL looks as
follows:

```text
1. {data that can be verified by pkey}
2. {pkey data}
3. {data that can be verified by pkey}
4. {pkey data}
```

Two lines must be read at a time to verify data. Filtering can be done based
on the data time stamp and understood using the public key in the line
immediately following it.

Strategies can be created to monitor the integrity of these archival logs
or make the data available through different terms.

## Install

This is a very simple demo and doesn't have full production qualities. To
install and run:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements/requirements.txt
python main.py
```

To view CLI options:

```bash
python main.py -h
```

To install local dependencies and run basic tests:

```bash
python -m pip install -r requirements/local.txt
pytest
```

## Contact

Reach out to the Orcfax team for more information about how a custom offline
data source can be converted into on-chain data for use in your Plutus
scripts on Cardano.
