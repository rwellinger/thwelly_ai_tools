# Own KI Server by allama local installed and UI by docker

## Install ollama

Github:
    https://github.com/ollama/ollama

Ollama muss lokal auf dem MAC laufen! Via Docker läuft zwr auch, aber dann ist es extrem langsam. Wieso? Weil dann die GPUs vom M1 nicht zum Einsatz kommen.
Das geht nur mit der Nativen Mac Version. Des weiteren nicht via "brew" installieren, wegen Update. Aufpassen, da gab es bei Version 1.11.5 und 1.11.6 ein Problem. Kein Listen mehr vorhanden.

    wget https://github.com/ollama/ollama/releases/download/v0.11.4/ollama-darwin.tgz

Testen und abwarten ob eine nächste Version funktioniert.

### LaunchDeamon
Damit es auf dem MAC automatisch gestartet wird, gibts im LauchDeamon Verzeichnis eine Datei. Diese ins Verzeichnis /Library/LaunchDeamon kopieren


Laden:
    sudo launchctl load com.ollama.serve.plist

Entladen:
    sudo launchctl unload com.ollama.serve.plist



Sofort starten:
    sudo launchctl run com.ollama.serve.plist

Sofort Stop:
    sudo launchctl stop com.ollama.serve.plist

### Test ob ollama verfügbar
    curl http://10.0.1.120:11434/api/tags



## Install Open WebUI

### Install Docker

    colima start --arch aarch64 --cpu 4 --memory 4 --disk 80 --vm-type=vz


### Generate Self Certificate

mkcert macstudio macstudionas 10.0.1.120 localhost

mv macstudio+4-key.pem webui.key
mv macstudio+4.pem webui.crt
