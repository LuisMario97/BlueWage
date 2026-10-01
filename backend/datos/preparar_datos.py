"""Obtiene los CSV completos del repositorio y verifica su integridad."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import shutil
import urllib.request
import zipfile

BASE_GITHUB = 'https://raw.githubusercontent.com/LuisMario97/BlueWage/main/backend/datos/'
ARCHIVOS = {'ENOE_COE1T226.csv', 'ENOE_SDEMT226.csv'}


def sha256_archivo(ruta):
    with Path(ruta).open('rb') as archivo:
        return hashlib.file_digest(archivo, 'sha256').hexdigest()


def preparar_datos(destino, base_url=BASE_GITHUB):
    """Usa archivos existentes si coinciden; no sobrescribe CSV diferentes."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(base_url + 'manifest.json', timeout=60) as respuesta:
        manifest = json.load(respuesta)
    if len(manifest) != 2 or {item['archivo'] for item in manifest} != ARCHIVOS:
        raise ValueError('El manifiesto no contiene las dos tablas esperadas.')
    for item in manifest:
        nombre = item['archivo']
        if item['zip'] != nombre + '.zip':
            raise ValueError('Nombre de ZIP inesperado.')
        salida = destino / nombre
        if salida.exists():
            if sha256_archivo(salida) != item['sha256_csv']:
                raise ValueError(f'{salida} ya existe y no coincide. Revisa ese archivo o elige otra carpeta.')
            print(f'{nombre}: ya disponible y verificado.')
            continue
        with TemporaryDirectory() as temporal:
            zip_local = Path(temporal) / item['zip']
            print(f'Descargando {nombre}…')
            with urllib.request.urlopen(base_url + item['zip'], timeout=120) as respuesta, zip_local.open('wb') as archivo:
                shutil.copyfileobj(respuesta, archivo)
            if sha256_archivo(zip_local) != item['sha256_zip']:
                raise ValueError(f'ZIP incompleto o alterado: {nombre}.')
            csv_local = Path(temporal) / nombre
            with zipfile.ZipFile(zip_local) as zip_datos:
                if zip_datos.namelist() != [nombre]:
                    raise ValueError('El ZIP contiene archivos inesperados.')
                with zip_datos.open(nombre) as entrada, csv_local.open('wb') as archivo:
                    shutil.copyfileobj(entrada, archivo)
            if sha256_archivo(csv_local) != item['sha256_csv']:
                raise ValueError(f'El CSV no coincide: {nombre}.')
            # Escritura exclusiva para no reemplazar datos preexistentes.
            with csv_local.open('rb') as entrada, salida.open('xb') as archivo:
                shutil.copyfileobj(entrada, archivo)
        print(f'{nombre}: listo ({item["filas"]:,} registros).')
    return destino


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino', required=True)
    args = parser.parse_args()
    preparar_datos(args.destino)
