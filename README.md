# API Interop
API Python dédiée à l'analyse des fichiers Interop d'Illumina.
Cette API est basée sur la librairie python [InterOp](http://illumina.github.io/interop/python_binding.html) d'Illumina.  


## 1. Pré-requis
- python >= 3.7
- pip >= 20.0
- supervisord

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
  pip install git+https://gitlab.univ-rouen.fr/ngs-u1245/application-bioinformatique/nf_pyqua.git
  ```

  * OU Installation alternative
    * Cloner le dépôt
    ```
    git clone -- recursive https://gitlab.univ-rouen.fr/ngs-u1245/application-bioinformatique/nf_pyqua.git
    ```

    * Installer Agoge (to be improved)
    ```
    pip install nf_pyqua/agoge/
    ```

    * Installer PyQua
    ```
    pip install nf_pyqua/
    ```
## 3. Utilisation
