Instructions for matlab:
1. download matlab app, sign in with email
2. go under sensors > settings > stream to and set this to MATLAB
3. go to sensors > settings > more and give access to sensors
4. open up matlab (you can download it or use the web version, I just used the web version; also make sure to use same email)
5. create a new script in matlab
6. paste the contents of matlab/sensor_data_collection.m from this repo into this new script
7. run it


Instructions for fastapi backend:
1. install uv if you don't have it
```pip install uv```
2. clone this repo
3. ```cd backend```
4. ```uv sync``` to install dependencies
5. ```uv run fastapi dev``` to run the backend
