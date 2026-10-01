# Datos para reproducir el entrenamiento

Las dos tablas completas utilizadas por el notebook se incluyen en ZIP separados:

- [ENOE_COE1T226.csv.zip](ENOE_COE1T226.csv.zip)
- [ENOE_SDEMT226.csv.zip](ENOE_SDEMT226.csv.zip)

Son las copias de trabajo de ENOE (INEGI) compartidas por el autor en
[su carpeta de Drive](https://drive.google.com/drive/folders/1f6AdFiOpEDAuoTR9naSJJ5olyRBjUhDb).
Se conservaron los CSV byte por byte, sin recortar registros ni columnas.
Cada ZIP contiene un único CSV. Los nombres de periodo son los utilizados en el
notebook original; esta copia no sustituye el diccionario de datos de INEGI.

## Para el profesor: Google Colab

1. [Abre el notebook del repositorio en Colab](https://colab.research.google.com/github/LuisMario97/BlueWage/blob/main/backend/notebooks/BlueWage_Pipeline_ENOE.ipynb).
2. Ejecuta la primera celda de preparación y autoriza el montaje de tu propio Drive.
3. Se descargan los ZIP desde este repositorio y se verifican sus hashes SHA-256.
4. Los CSV se guardan en `/content/drive/MyDrive/BlueWage/Datos/`.
5. Ejecuta en orden las seis celdas de código originales.

No necesitas acceso al Drive del autor. Los archivos deben haberse publicado en
la rama `main` para que la descarga automática funcione. La celda no reemplaza
archivos existentes diferentes: muestra un error para que puedas revisarlos.
El entrenamiento consume más RAM que la inferencia de la aplicación.

## Descarga manual

En GitHub abre cada ZIP y pulsa **Download raw file**. Descomprímelos y sube los
dos CSV a `BlueWage/Datos` en tu Drive. También puedes descargarlos en Python:

```powershell
python backend/datos/preparar_datos.py --destino C:\ruta\datos
```

El script requiere Python 3.11 o posterior y solo usa la biblioteca estándar.
El notebook reconoce UTF-8 o Latin-1; conserva la codificación original.

## Integridad y despliegue

[manifest.json](manifest.json) registra tamaños, filas, columnas, codificación,
origen de la copia y hashes de los CSV y ZIP. La generación verifica CRC y SHA-256
después de comprimir. Los ZIP evitan el límite de 100 MiB por archivo de GitHub;
los CSV descomprimidos están excluidos mediante `.gitignore`.

Esta carpeta no se copia a la imagen de Render ni al frontend de Vercel.
La aplicación publicada usa solamente el modelo ya entrenado.
