FROM python:3.10-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
ENV JAVA_HOME /usr/lib/jvm/java-1.7-openjdk/jre
RUN apt-get update && apt-get install -y g++ default-jdk
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]