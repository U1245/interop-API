# API Interop
API Python dédiée à l'analyse des fichiers Interop d'Illumina.
Cette API est basée sur la librairie python [InterOp](http://illumina.github.io/interop/python_binding.html) d'Illumina.  


## 1. Pré-requis
- python >= 3.7
- pip >= 20.0
- [NGinX](https://www.nginx.com/)

## 2. Installation
Dans un répertoire de votre choix (i.e /PATH/TO/INTEROP):  
  
  * **Cloner le dépôt**  et créer les repertoires de fonctionnements
  ```
  mkdir -p /PATH/TO/INTEROP/logs /PATH/TO/INTEROP/run
  cd /PATH/TO/INTEROP
  git clone https://gitlab.univ-rouen.fr/ngs-u1245/application-bioinformatique/interop-api.git
  ```

  * **Créer et activer un environnement virtuel python**  
  ```
  mkdir my_virtual_env
  python -m venv my_virtual_env/
  source my_virtual_env/bin/activate
  ```  

  * **Installer les dépendances**
  ```
  pip install -r interop-api/requirements.txt
  ```  

  * **Adapter le fichier interop-api/bin/gunicorn_start**
  ```
  vim /PATH/TO/INTEROP/interop-api/bin/gunicorn_start
  ```


  * **Configurer gunicorn** pour fonctionner avec le systemd
    * Créer le fichier interop.service
    ```
    vim /etc/systemd/system/interop.service
    ```
    * Copier et compléter les commandes suivantes
    ```
    [Unit]
    Description=Gunicorn instance to serve the Flask interOP API
    After=network.target
    
    [Service]
    User=USER
    Group=GROUP
    WorkingDirectory=/PATH/TO/INTEROP/interop-api/API
    Environment='PATH=/PATH/TO/INTEROP/interop_venv/bin'
    ExecStart=/PATH/TO/INTEROP/interop-api/bin/gunicorn_start
    
    [Install]
    WantedBy=multi-user.target
    ```
    * **Redémarrer le daemon systeme et lancer le service interOP**
    ```
    sudo systemctl daemon-reload
    sudo systemctl start interop
    sudo systemctl enable interop
    ```
    * Vérifier que le service tourne correctement
    ```
    sudo systemctl status interop
    ```
  
  * **Configurer NGinX** 
    * **Créer le fichier de configuration interop pour NGinX**
    ```
    vim /etc/nginx/conf.d/interop.conf
    ```
    * Copier et adapter la configuration suivante, puis enregistrer
    ```
    server {
        listen 80;
        server_name YOUR_DOMAIN;

        access_log /PATH/TO/INTEROP/logs/nginx-access.log;
        error_log /PATH/TO/INTEROP/logs/nginx-error.log;

        location / {
            include proxy_params;
            proxy_pass http://unix:/PATH/TO/INTEROP/run/gunicorn.sock;
        }
    }
    ```
    * **Redémarrer NGinX**
    ```
    sudo systemctl restart nginx
    ```

    * **Tester une requete sur YOUR_DOMAIN/interop**
