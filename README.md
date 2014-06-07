Dotabank-web
============

The code behind the Dotabank.com website, open sauced because Smashman wanted it to be. Code isn't the cleanest ever,
and the site is still very much under development, but it performs well enough.

## Dependencies

* Python 2.7+ (Not tested on Python 3). (See requirements.txt for Python dependencies; pip and virtualenv highly recommended 10/10)
* Memcached
* SQL database of some sort

## Running

You will need a database. Set one up with something like this in bash:

```
$ cd /path/to/dotabank-web
$ source bin/activate
$ python
>>> from app import db
>>> db.create_all();
```

Then just run `run.py` to use Werkzeug's own internal wsgi server.

In production you probably want to use a more sophisticated set up, here's our (quickly hacked together) server configs
for nginx and uwsgi:

### nginx
```
server {
        listen 80 default_server;
        listen [::]:80 default_server ipv6only=on;

        access_log /srv/www/dotabank.com/logs/access.log;
        error_log /srv/www/dotabank.com/logs/error.log;

        gzip on;
        gzip_http_version 1.1;
        gzip_vary on;
        gzip_comp_level 6;
        gzip_proxied any;
        gzip_types text/plain text/html text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript application/javascript text/x-js;
        gzip_buffers 16 8k;

        root /srv/www/dotabank.com/public_html;
        try_files $uri $uri/ @dotabank;

        location @dotabank {
                uwsgi_pass      unix:///run/uwsgi/app/dotabank.com/dotabank.com.socket;
                include uwsgi_params;
                uwsgi_param     UWSGI_SCHEME $scheme;
                uwsgi_param     SERVER_SOFTWARE nginx/$nginx_version;
        }

        location /static {
                alias /srv/www/dotabank.com/dotabank-web/app/static;
                autoindex off;
                access_log off;
                expires max;

                try_files $uri $uri/ @dotabank;
        }

        location /ugcfiles {
                root /srv/www/dotabank.com/dotabank-web/ugcfiles;
                expires max;

                try_files $uri @dotabank;
        }

}
```

### uwsgi
```
<uwsgi>
    <plugin>python</plugin>
    <socket>/run/uwsgi/app/dotabank.com/dotabank.com.socket</socket>
    <pythonpath>/srv/www/dotabank.com/dotabank-web/</pythonpath>
    <virtualenv>/srv/www/dotabank.com/dotabank-web/</virtualenv>
    <chdir>/srv/www/dotabank.com/dotabank-web/</chdir>
    <wsgi-file>/srv/www/dotabank.com/dotabank-web/run.py</wsgi-file>
    <callable>application</callable>
    <master />
    <processes>4</processes>

    <vacuum />
    <harakiri>30</harakiri>
</uwsgi>
```

## License

[CC-BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Contribution agreement.

Feel free to contribute to Dotabank. Buuuuuuuuuut you surrender all rights of code to us, or something... basically we
own code you contribute, but anybody can use it as per license.

## Credits

* [Rob Jackson](https://rjackson.me)
* [Ben Williams](http://smash.mn)
* [Bence Nagy](http://underyx.me)
