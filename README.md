Admino is a django package that provides a REST API for admin endpoints. It allows you to customize django admin panel.


###Problem?

Django admin is good solution for development tests and i/o, but django admin needs to be more customizable and extendable. 

### Solution:

if you want to implement a custom widget or ui for django admin, you may need a REST API to handle records.

Admino added to new api views to django admin genericly. You don't need to change default admin files. 
Every API endpoint will generate your "ModelAdmin" configurations.