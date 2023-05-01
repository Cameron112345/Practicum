# Practicum

This is a tool that is used for creating archives of the MVNU website.
It is a web application that allows users to create and view separate archive versions.

Technologies used for this tool include:
* Python
* Flask
* Apache
* NoSQL
* Docker
* Asynchronous Programming
* Multithreading
* Web Scraping


## For Regular Users:
Be sure to contact your adminstrator to retrieve your login information. You may need to provide an email address.

## For Adminstrators:
To run this tool simply fork this repository, and run:
```docker compose up```
on any machine that Docker and Docker Compose are installed on.
To add an inital user on the system, first enter the Docker CLI of the FlaskApp container.
Run These commands:
```
flask shell
user = User(username="<username>", email="<email>", isAdmin=True)
user.set_password("<password>")
db.session.add(user)
db.session.commit()
exit()
```
You can now log in on the app using these credentials, and use the users tab to create more users.
