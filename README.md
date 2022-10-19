# API Interop
API Python dédiée à l'analyse des fichiers Interop d'Illumina.
Cette API est basée sur la librairie python [InterOp](http://illumina.github.io/interop/python_binding.html) d'Illumina.  


## 1. Pré-requis
- python >= 3.7
- pip >= 20.0
- [supervisord](http://supervisord.org/)
- un reverse proxy (i.e [NGinX](https://www.nginx.com/))[]([[url](url)](url))

## 2. Installation
Dans un répertoire de votre choix :  
  * Créer et activer un environnement virtuel python 
  ```
  mkdir my_virtual_env
  python -m venv nf_pyqua_venv my_virtual_env/
  source my_virtual_env/bin/activate
  ```  

  * Installer le dépôt  
  ```
  pip install git+https://gitlab.univ-rouen.fr/ngs-u1245/application-bioinformatique/interop-api.git
  ```

  * Compléter le fichier bin/gunicorn_start

  * Configurer gunicorn pour fonctionner avec supervisord
    * Créer un répertoire de log, i.e 
    ```
    mkdir INTEROP/API/PATH/logs
    ```
    * Créer et ouvrir un fichier interop_api.ini dans /etc/supervisord.d/
    ```
    vim /etc/supervisord.d/interop_api.ini
    ```
    * Copier et compléter les commandes suivantes
    ```
    [program:interop_API]
    command = INTEROP/API/PATH/bin/gunicorn_start
    user = YOUR_USERNAME
    stdout_logfile = INTEROP/API/PATH/logs/gunicorn_supervisor.log
    redirect_stderr = true
    environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8
    ```
    * Mettre à jour supervisord et lancer le process interop_API
    ```
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl restart interop_API
    ```
    * Vérifier que le process tourne
    ```
    sudo supervisorctl status
    ```
  
  * Configurer le serveur web / reverse-proxy, i.e NGinX
    * Créer le repertoire du socket qui permettra à gunicorn de communiquer avec NGinX
    ```
    mkdir INTEROP/API/PATH/run
    ```
    * Créer le fichier de configuration dans les sites disponibles
    ```
    vim /etc/nginx/sites-available/interop-api
    ```
    * Copier et adapter la configuration suivante, puis enregistrer
    ```
    upstream hello_app_server {
      server unix:INTEROP/API/PATH/run/gunicorn.sock fail_timeout=0;
    }

    server {
    listen 80;
    server_name interop_api YOUR.URL.NAME;

    access_log INTEROP/API/PATH/logs/nginx-access.log;
    error_log INTEROP/API/PATH/logs/nginx-error.log;

    location / {
        include prox_params;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    ```
    * Rendre disponible la configuration et redémarrer NGinX
    ```
    sudo ln -s /etc/nginx/sites-available/interop-api /etc/nginx/sites-enabled
    sudo systemctl restart nginx
    ```
