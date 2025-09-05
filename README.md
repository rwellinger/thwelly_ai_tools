# Meine KI Tools auf dem M1 Studio

<img src="python_ai_services.png" alt="Python AI Services" width="204" height="204">

## Allgemein
Damit es funktioniert müssen gewisse Verzeichnisse und .env Dateien erstellt werden, die ich aus
Sicherheitsgründen nicht eingecheckt habe.

## revproxy
Der Reverse Proxy ist ein ngnix wo der Zugriff für webui auf ollama und ein UI für die
Bild- und Song- Generierung zu verfügung stellt. Er macht vor allem die Umleitung von HTTP <-> HTTPS

## ollama & webui
In diesem Projekt befindet sich die Anleitung um ollama lokal auf dem Mac zu installieren und
das erstellen des Open WebUI Docker containers.


## aiproxy
Der AI Proxy ist ein Server geschrieben in python. Er hat aktuell zwei API's implementiert:

* Image Generierung via DALL.E
* Musik Song Generierung via MUREKA

### Image Generierung
Funktioniert sehr gut und via Web das via Reverse Proxy zu verfügung gestellt wird.

### Song Generierung
Funktioniert aktuell nur via AIProxy API. Das Implementieren der Webseite ist nicht ganz so einfach
weil der Prozess asynchron ist. Ich bin dran.

### Grösste Challange
Die grösste Herausforderung ist dabei Song Generierung. Da dieser Prozess länger dauern kann muss man es asyncrhon
implementieren. Dabei habe ich Redis und Celery verwendet um einen unabhängigen Worker benutzen zu können.

Das Problem wo ich habe ist, dass ich bis jetzt keinen Weg finden könnte dies besser zu strukturieren. Sprich
Controller, Business Logik und Main so wie Tools zu separieren. Jedesmal verliert Celery und Redis die Verknüpfung
und funktioniert nicht mehr. Die verschachtlung von diesen zwei Tools ist gross. Eine Bessere Lösung sehe ich jedoch
aktuell gerade nicht.


## Dependencies

### Install Docker
Auf dem Mac habe ich die besten erfahrungen mit colima gemacht. Das lässt sich via "brew" isntallieren.

    colima start --arch aarch64 --cpu 4 --memory 4 --disk 80 --vm-type=vz

### Netzwerk Abhängigkeit
Damit die einzelnen Services miteinander über die verteilten Konfigurationen ansprechen können ist das erstellen
einer Netzwerk Resource notwendig.

    docker network create webui-network

### API KEYs
Damit DALL.E und MUREKA APIs funktionieren muss ein API Key generiert werden.

>⚠️ **Wichtig!** 
>Diese Services sind NICHT opensource oder etwa gratis!
