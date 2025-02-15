FROM python:3.12
RUN useradd user
WORKDIR /app
COPY . .
RUN pip install requests
USER user
ENTRYPOINT ["python", "-u", "main.py"]
