# 1. Use an official, lightweight Python base image
FROM python:3.10-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory inside the container
WORKDIR /code

# 4. Copy the requirements file and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copy the application code into the container
COPY ./app /code/app
COPY ./.env /code/.env

# 6. Expose the port FastAPI will run on
EXPOSE 8000

# 7. Command to run the application using Uvicorn (production server)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

