FROM python:3
# Working directory in the container
WORKDIR /whatever
# Requirements first! for cache performance
COPY requirements.txt .
RUN pip install -r requirements.txt
# Then the source code
COPY src/pyfreeradius/ ./pyfreeradius/
COPY src/settings.py .
COPY src/database.py .
COPY src/dependencies.py .
COPY src/api.py .
# For initial data
COPY docker/freeradius-mysql/initial_data.py .
