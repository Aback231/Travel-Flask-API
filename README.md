## Python Flask Backend API with SQLAlchemy and PostgreSQL Database

### Services

Docker-compose is used to build all the services, and make them comunicate with each other.

`web` service contains flask app with all pip requirements and exported .env variables.

`postgres_db_container` service contains postgres DB server.

`pgadmin4_container` service contains pgadmin4 to view postgres DB visually.

`https://www.mailgun.com/` is used as email service (free domain for testing). After getting free API key, email which receives messages, needs to be approved first.

### Build

To build containers and run: `docker-compose up --build`

By default flask app is running on `http://127.0.0.1:5000`

Tested on: `Arch Linux` and `Ubuntu 21.10`

### Documentation

Postman documentation was publicly pubished: `https://documenter.getpostman.com/view/21319787/Uz5KnaPh`