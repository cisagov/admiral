# admiral 👩‍✈️🚢⚓️ #

[![GitHub Build Status](https://github.com/cisagov/admiral/workflows/build/badge.svg)](https://github.com/cisagov/admiral/actions)
[![Coverage Status](https://coveralls.io/repos/github/cisagov/admiral/badge.svg?branch=develop)](https://coveralls.io/github/cisagov/admiral?branch=develop)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/cisagov/admiral.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/cisagov/admiral/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/cisagov/admiral.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/cisagov/admiral/context:python)
[![Known Vulnerabilities](https://snyk.io/test/github/cisagov/admiral/develop/badge.svg)](https://snyk.io/test/github/cisagov/admiral)

This project implements a distributed certificate transparency log harvester.

## Requirements ##

This project requires a [Docker](https://www.docker.com) installation.

## Installation and Execution ##

- Build the docker image:
  - `docker-compose build`
- Change the credentials in the following configuration files:
  - `secrets/admiral.yml`
  - `secrets/redis.conf`
  - `docker-compose.yml`
- Start the composition:
  - `docker-compose up`
  - alternately it can be started in [swarm mode](https://docs.docker.com/engine/swarm/):
  `docker stack deploy admiral --compose-file docker-compose.yml`
- Monitor the system:
  - [http://localhost:5555](http://localhost:5555)
- Optional: Run the code tests
  - `docker-compose -f docker-compose-dev.yml run test`

## Development and Debugging ##

A separate `docker-compose-dev.yml` file is provided to support development and
testing. Using this composition, a container can be started in a few different modes:

To start up an IPython session with a configured Celery app:

`docker-compose -f docker-compose-dev.yml run celery-shell`

To start up a development container with a bash shell:

`docker-compose -f docker-compose-dev.yml run bash`

To run all unit and system tests:

`docker-compose -f docker-compose-dev.yml run test`

Additional arguments can be passed to `pytest` when creating the container:

`docker-compose -f docker-compose-dev.yml run test -vs tests/scan_test.py`

To access a mongo shell:

`docker-compose exec mongo mongo admin -u root -p`

To get a shell in a stopped or crashed container:

`docker run -it --rm --entrypoint=sh admiral`

To protect against inadvertent commit of secrets to the repository:

`git update-index --assume-unchanged secrets/*`

## Monitoring ##

The following web services are started for monitoring the underlying components:

- Celery Flower: [http://localhost:5555](http://localhost:5555)
- Mongo Express: [http://localhost:8081](http://localhost:8083)
- Redis Commander: [http://localhost:8082](http://localhost:8082)

## Contributing ##

We welcome contributions!  Please see [here](CONTRIBUTING.md) for
details.

## License ##

This project is in the worldwide [public domain](LICENSE).

This project is in the public domain within the United States, and
copyright and related rights in the work worldwide are waived through
the [CC0 1.0 Universal public domain
dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0
dedication. By submitting a pull request, you are agreeing to comply
with this waiver of copyright interest.
