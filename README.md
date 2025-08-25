# Meine KI Tools auf dem M1 Studio

## ollama
In diesem Projekt befindet sich die Anleitung um ollama lokal auf dem Mac zu installieren und Docker configurationen für WebUI und Proxy.
Der Proxy (nginx) wird auch für das dalle (image erzeugung via ki) verwendet.

## dalle
Dies ist der Wrapper Server in Python, der Requests für z.B. DALL.E 3 entgegen nimmt. Es wären aber auch andere Modelle möglich.
Der Wrapper beinhaltet den Token für DALL.E im .env Datei, die jedoch manuell erstellt werden muss und nicht im GIT vorhanden ist.
