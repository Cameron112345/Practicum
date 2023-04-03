FROM python:slim
WORKDIR /app
COPY . .


RUN pip install -r requirements.txt
RUN flask db upgrade

ENV FLASK_APP test
ENV FLASK_DEBUG 1

EXPOSE 5000



CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000"]
