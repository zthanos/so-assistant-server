   #!/bin/sh
   ollama pull deepseek-coder-v2:latest
   exec /bin/sh -c "ollama serve"