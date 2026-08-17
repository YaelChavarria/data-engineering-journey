# Entorno de desarrollo

## Herramientas

- Windows como sistema operativo principal.
- Python 3.12.
- Git.
- Docker Desktop.
- VS Code.
- `uv` para gestionar entornos y dependencias de Python.
- Jupyter para exploración y notebooks.

## Decisiones

- Usar entornos virtuales por proyecto.
- Mantener los comandos de instalación en la documentación.
- Verificar las herramientas con un script sencillo antes de comenzar una lección.
- Usar WSL2 o cloud cuando una herramienta necesite un entorno Linux o más memoria.

## Restricciones actuales

- El equipo local no tiene GPU NVIDIA.
- La memoria disponible obliga a mantener Docker y los procesos de datos ligeros.
- Las tareas de entrenamiento o procesamiento pesado deben ejecutarse en un entorno cloud controlado por coste.

## Comprobación mínima

```powershell
python --version
git --version
docker --version
uv --version
```

Las versiones exactas se registran en la bitácora de cada proyecto para evitar que esta nota quede obsoleta.
