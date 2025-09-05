# Own KI Server by allama local installed and UI by docker

## Install ollama

Github:
    https://github.com/ollama/ollama

Ollama muss lokal auf dem MAC laufen! Via Docker läuft zwr auch, aber dann ist es extrem langsam. Wieso? Weil dann die GPUs vom M1 nicht zum Einsatz kommen.
Mitlerweile ist die Version 0.11.8 drausen. Die funktioniert wieder. Sie hat einige OSS Performance Fixes drinnen. Wichtig ist, dass es via LaunchDeamon gestartet wird.

    wget https://github.com/ollama/ollama/releases/download/v0.11.8/ollama-darwin.tgz

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
    curl http://<Server-IP>:11434/api/tags



## Install Open WebUI
Sicherstellen das Docker und Docker-Compose installiert wurden. Dann kann der Service gestartet werden.

    docker-compose up -d
