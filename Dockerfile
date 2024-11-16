# Verwende ein Basis-Image mit Python
FROM python:3.11.10

# Setze das Arbeitsverzeichnis
WORKDIR /app

# Kopiere die Anforderungen und installiere sie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Codes
COPY . .

# Exponiere den Streamlit-Port
EXPOSE 8501

# Starte die Anwendung
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# build docker: "docker build -t test_dockerfile ."
# run docker with streamlit and persitent file savings: "docker run --rm -p 8501:8501 -v /:/ test_dockerfile" + "http://localhost:8501"
# stop dockerfile: "docker stop test_dockerfile"