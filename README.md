# Python Flask Backend API with: Nginx as load balancer, SQLAlchemy, Redis and PostgreSQL DB's.

## Services

Docker-compose is used to build all the services, and make them comunicate with each other.

`web` service contains flask app with all pip requirements and exported .env variables.

`redis` service contains redis DB server, for fast JWT Token blacklisting.

`postgres_db_container` service contains postgres DB server.

`pgadmin4_container` service contains pgadmin4 to view postgres DB visually.

https://www.mailgun.com/ is used as email service (free domain for testing). After getting free API key, email which receives messages, needs to be approved first.

## Build

To build containers and flask app's scaled to 2, run: `docker-compose up --build --scale web=2`

By default flask API is running on http://127.0.0.1:80

Endpoint http://127.0.0.1/docker_id, loaded in browser, displays Docker container ID running your request.

Tested on: `Arch Linux` and `Ubuntu 21.10`

## Documentation

Postman documentation was publicly pubished: [Postman publication](https://documenter.getpostman.com/view/21319787/UzBmMnEK)