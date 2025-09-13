# Reverse Proxy (NGINX)

## Generate Self Certificate

    mkcert macstudio macstudionas 10.0.1.120 localhost

    mv macstudio+3-key.pem webui.key
    mv macstudio+3.pem webui.crt

## Protected Aeria für Prompt

    htpasswd -c ./nginx/.htpasswd username

## Starten
Es muss sichergestellt werden das Docker und Docker-Compose installiert sind und eine Docker Umgebung entsprechend verfügbar ist.

    docker-compose up -d
