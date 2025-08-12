# Own KI Server by allama local installed and UI by docker

## Install docker 

    colima start --arch aarch64 --cpu 4 --memory 4 --disk 80 --vm-type=vz


## Test ob ollama verfügbar
    curl http://10.0.1.120:11434/api/tags


## Backup
    docker cp ollama-webui:/app/backend/data/webui.db ./backup/webui.db
    docker cp ollama-webui:/app/backend/data/vector_db/chroma.sqlite3 ./backup/chroma.sqlite3


## Generate Self Certificate

mkcert macstudio macstudionas b8d439ec68266ac2f5404b61d152668c1.asuscomm.com 10.0.1.120 localhost

mv macstudio+4-key.pem webui.key
mv macstudio+4.pem webui.crt
