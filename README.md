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

One such example: `docker run -d --name oval-db -p 5432:5432 postgres:9.2`

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

If you get an error installing `stravalib`, you might need to update `pip` (either in your virtualenv or system-wide) and then deactivate/reactivate your venv. Any version of pip >= 8.1.2 should work.

Example of the error:

```
  File "<string>", line 16, in <module>

  File "/home/user/oval/venv/build/stravalib/setup.py", line 33, in <module>

    install_reqs = parse_requirements(os.path.join(os.path.dirname(__file__), 'requirements.txt'), session=False)

TypeError: parse_requirements() got an unexpected keyword argument 'session'

```

Example of upgrading pip (using pip) in your virtualenv:
```
. ./venv/bin/activate && pip install -U pip==8.1.2 
```


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

Start by creating the necessary DB tables in your blank DB:
`./manage.py db upgrade`

Then launch the Flask shell and create an admin:
`./manage.py shell`

```
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

## Releasing

### New features
Any new feature or bugfix should have a corresponding GitHub pull request (and hopefully a GitHub Issue). PRs with multiple commits should be squashed prior to merging. One feature/bugfix = one PR = one commit if possible.

### Timestamp Versioning
Releases are labeled based on release date: `vYYYYMMDD`, e.g. `v20170718`. Older releases (v.1.2.7 and prior) were a mix of incremental and semver (much to the dismay of @johnwheffner) and do not follow this convention. Unless otherwise noted, all release dates are based on UTC.

### Cutting a release
Ready to cut a new release? If so, follow these steps:
* Verify all desired changes have been merged into `master`
* Open a PR to merge `master` to `release`
* Once PR is approved and `release` has been updated, create and push a new git [lightweight tag](//git-scm.com/book/en/v2/Git-Basics-Tagging#_lightweight_tags) with the release version number (e.g. vYYYMMDD) based on the current UTC date
* Merge `release` back to `master` to verify `master` is up to date

### Hotfixes
Bugs happen. To create a hotfix (quick patch to address a specific bug), do the following:
* Create a new branch off of `release` (**not** `master`)
* Open a new PR to merge your new hotfix branch into `release`
* Create a new git lwt labeled `vYYYMMDD-hotfix`
* Merge `release` back to `master` to verify `master` is up to date

## Provide feedback!
Any and all feedback would be greatly appreciated.
