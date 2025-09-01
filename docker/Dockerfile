FROM python:3.12-alpine as builder

# Global dependencies
RUN apk add --no-cache gcc musl-dev

# Dependencies for postgresql
RUN apk add --no-cache postgresql-libs postgresql-dev

WORKDIR /app

# Create venv
RUN python3 -m venv venv

# Install dependencies
COPY requirements.txt .
RUN . venv/bin/activate && \
  python3 -m ensurepip --upgrade && \
  python3 -m pip install -r requirements.txt

FROM python:3.12-alpine

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app /app
ENV PATH="/app/venv/bin:$PATH"

COPY src /app/src

# Copy initial_data.py to the root of the app for easier execution
COPY src/initial_data.py /app/

CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
