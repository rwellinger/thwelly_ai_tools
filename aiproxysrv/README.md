# DALL.E Request Server
Um Images zu generieren kann ollama zusammen mit WebUI nicht verwendet werden. Da geht nur Text. Für Image generierung wird DALL.e verwendet aktuell.
Dies ist aber kostenpflichtig und benötigt daher einen API-KEY. Das ist der Grund für diesen Server Wrapper in Python. Ziel ist es die Anfrage entgegen zunehmen und zusammen
mit dem API-KI auf DALL.e zu senden.

## env
Damit das funktioniert muss ein .env Datei erstellt werden. Da dies den API-KEY enthält ist es nicht im GIT Repo.

Das ist der notwendige Inhalt:

    OPENAI_API_KEY=sk-...
    OPENAI_URL=https://api.openai.com/v1/images/generations
    FLASK_SERVER_PORT=5050
    OPENAI_MODEL=dall-e-3
    FLASK_SERVER_HOST=x.x.x.x

Beachte das der Port im dockerfile nicht aus dem .env gelesen werden kann aber übereinstimmen muss.

## Build und Start
Mit folgendem Command builden und starten:

    docker-compose up --build -d

Stop

    docker-compose down

Wenn mal gebildet, muss es danach für Start/Stop nicht mehr zwingend gebildet werden, wenn keine Änderungen.

## Webclient für Abfrage
Der Webclient befindet sich im ../ollama projekt, weil dort bereits ein nginx als proxy definiert wurde.
