# Notebook de entrenamiento

Se incluye `BlueWage_Pipeline_ENOE.ipynb`, descargado el 1 de octubre de 2026 de
la carpeta compartida por el autor. Sus seis celdas de código y sus resultados
originales se conservan; se agregó una celda inicial para preparar los CSV desde
GitHub. No se ha vuelto a entrenar el modelo.

- [Abrir la versión del repositorio en Colab](https://colab.research.google.com/github/LuisMario97/BlueWage/blob/main/backend/notebooks/BlueWage_Pipeline_ENOE.ipynb)
- [Notebook original en Colab](https://colab.research.google.com/drive/1HftYWrOFnSYRmSEQ15bGWxDOuUjyjUrU)
- [Carpeta de origen y datos](https://drive.google.com/drive/folders/1ZnAkNnYdCyg9kPQv6j5cY8fgnnqbOnQk)
- Modelo usado por la aplicación: `../models/bluewage_pipeline_cuantil.joblib`.

Para ejecutar en Colab, abre la versión del repositorio y ejecuta primero la
celda «Preparación de datos desde GitHub». Autoriza el montaje de tu propio Drive;
descargará y verificará los CSV en `BlueWage/Datos`.
Revisa CARPETA y PERIODO en la primera celda si tus rutas cambian. Ejecuta las
celdas en orden: carga y unión, limpieza, EDA, generación sintética, entrenamiento
cuantílico y exportación. La última celda guarda el joblib en Colab y en Drive.
Los CSV completos se incluyen como ZIP en [../datos](../datos/README.md).
Los enlaces funcionarán después de subir los nuevos archivos a GitHub.

El notebook instala rangos de versiones; ejecutarlo en otro entorno puede
producir un artefacto diferente. Las versiones directas del backend validado se
documentan en `../requirements-production.txt`. Las métricas del notebook son
sobre datos sintéticos, no una evaluación independiente de salarios reales.

SHA-256 de los archivos incorporados:

```text
Notebook original: ecf760676971e8cc50baa58727252d967d1c8435f60fb25eac23db2a26227483
Notebook con preparación: d983ad833d1facd4e5b3b7f257665112a1b6c3aa76fe3aebf2c47534d908db98
Modelo:   99934d1cb62d1f922a7ebb0decb4b68f2819d4816c38654966a698bf5c3bc32e
```

El modelo se reubicó sin cambiar sus bytes. Se revisó el notebook en busca de
claves incrustadas; no se detectaron. Los notebooks y el prototipo histórico
no se incluyen en la imagen de producción de Render.
