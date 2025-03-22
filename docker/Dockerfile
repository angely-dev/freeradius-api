FROM python:3
# Working directory in the container
WORKDIR /whatever
# Requirements first! for cache performance
COPY requirements.txt .
RUN pip install -r requirements.txt
# Then the source code
COPY freeradius-api/pyfreeradius/ ./pyfreeradius/
COPY freeradius-api/settings.py .
COPY freeradius-api/database.py .
COPY freeradius-api/dependencies.py .
COPY freeradius-api/schemas.py .
COPY freeradius-api/api.py .
# For initial data
COPY docker/freeradius-mysql/initial_data.py .
