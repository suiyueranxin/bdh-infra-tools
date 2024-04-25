# flask with shellinabox cgi mode
This will be used for infrabox job debugging online by launching cusom docker container with test environments.

# How to start the service
After docker image is build:
```
docker build . -t shellinabox_flask:latest
```

Then run the docker container with port exposed configuration:

```
docker run -d -p 7000-7100:7000-7100 -p 9090:80 -p 4300:4200 -v /bdh_bugs:/bdh_bugs -v :/docker-folder:/docker-folder --privileged shellinabox_flask:latest
```

You can start the shellinabox service in port `9090`.

