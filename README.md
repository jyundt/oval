# The Oval App
## Synposis
The Oval App is a skunkworks project to create a database of all [ACA oval results](http://acaracing.com).  Hopefully it can be a platform for fun data-y stuff with decades worth of race data.

The Oval App uses python (flask) and postgres.  It's prety straightforward and basic.`

## Installation
### Requirements
* git
* Python 2.7 (pip and virtualenv)
* Postgres DB (9.x something should work)
* Linux (but I guess Mac OSX would probably work as well)

### Database setup
For local development, I run my postgres DB in Docker.

One such example: `docker run -d --name oval-db -p 5432:5432 postgres:9`

If you don' want to use docker, that's a-ok, just get a postgres DB that has write access to a database.

Create your database:
`psql  -h YOURDBHOST -U YOURDBUSER -c "create database YOUROVALDBNAME owner YOURDBUSER;"`


### Application setup
#### Download the code
Grabbing everything from [The Oval App](https://github.com/jyundt/oval) is probably the easiest way.
#### Create a virtual environment
`virtualenv venv`
#### Activate virtual environment and install python reqs
`. ./venv/bin/activate`

`pip install -r requirements.txt`
#### Define application variables.
Environmental variables are used to set various application settings.

Example config
```
export DB_HOST="YOURDBHOST"
export DB_PASS="whateveryourdbpasswordis"
export DB_NAME="YOUROVALDBNAME"
export DB_USER="YOURDBUSER"
export GOOGLE_ANALYTICS_ID="yourgoogleanalyticsid
export SECRET_KEY="makesomethingupcrazy"
export MAIL_PASSWORD="SMTPpassword"
export MAIL_USERNAME="SMTPusername"
```
There are some other things (like `STRAVA_API_TOKEN`) that can be added as well. Consult the `config.py` for an exhaustive list.
#### Create initial database
It's probably easiest to get a DB dump from an existing installation, but if you are starting from scratch you can manually create the tables, admin roles and initial super admin.

Start by launching the flask shell:
`./manage.py shell`

```
>>> db.create_all()
>>> from app.models import Role
>>> Role.insert_roles()
>>> from app.models import Admin
>>> firstadmin = Admin(email='YOUREMAIL',username='YOURUSERNAME',password='YOURPASSWORD')
>>> db.session.add(firstadmin)
>>> db.session.commit()
```

## Run a development server
You can use the flask development server for launching a local webserver:
`./manage.py runserver -d -r`

For real deployments, use a real application server (like uwsgi).

## Provide feedback!
Any and all feedback would be greatly appreciated.
