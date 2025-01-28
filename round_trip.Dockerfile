FROM python:3.12
RUN useradd user
WORKDIR /app
COPY round_trip.py main.py
RUN pip install requests
USER user
ENTRYPOINT ["python", "-u", "main.py"]
