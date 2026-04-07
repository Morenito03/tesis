# Model Installation Scripts

Scripts para facilitar la descarga e instalación de modelos para el servicio Smartwatch LLM.

## Scripts Disponibles

### 1. **install_models.sh / install_models.ps1** (Script Principal)

Script maestro interactivo que guía a través del proceso de instalación de modelos.

**Linux/macOS:**
```bash
bash scripts/install_models.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\install_models.ps1
```

**Características:**
- Menú interactivo para seleccionar método de instalación
- Soporte para Ollama (recomendado) y HuggingFace directo
- Verifica dependencias automáticamente
- Crea archivo `.env` si no existe

### 2. **setup_ollama.sh** (Setup de Ollama)

Instala y configura Ollama con modelos de visión.

```bash
bash scripts/setup_ollama.sh
```

**Características:**
- Detecta sistema operativo e instala Ollama
- Descarga modelos multimodales (phi4, llava, bakllava)
- Inicia el servicio de Ollama
- Selección interactiva de modelos

**Modelos Ollama disponibles:**
- `phi4` - Microsoft Phi-4 (recomendado, ~7B)
- `llava` - LLaVA 1.5 (~7B)
- `llava:13b` - LLaVA 1.5 13B (~13B)
- `bakllava` - BakLLaVA (~7B)

### 3. **download_huggingface_model.py** (Descarga HuggingFace)

Script Python para pre-descargar modelos de HuggingFace y sus pesos.

```bash
# Descargar un modelo específico
uv run python scripts/download_huggingface_model.py --model phi4

# Descargar todos los modelos
uv run python scripts/download_huggingface_model.py --all

# Listar modelos disponibles
uv run python scripts/download_huggingface_model.py --list

# Especificar dispositivo (CPU o CUDA)
uv run python scripts/download_huggingface_model.py --model gemma --device cuda
```

**Modelos HuggingFace disponibles:**
- `phi4` - microsoft/phi-4 (~7B)
- `gemma` - google/gemma-3-2b-vision (~2B)
- `gemma3n` - google/gemma-3n-vision
- `llava` - llava-hf/llava-1.5-7b-hf (~7B)
- `moondream` - vikhyatk/moondream2 (~1.8B)

### 4. **verify_models.py** (Verificar Instalación)

Script para verificar que los modelos estén correctamente instalados y puedan cargarse.

```bash
# Verificar modelos instalados
uv run python scripts/verify_models.py
```

**Características:**
- Verifica si Ollama está corriendo y lista modelos disponibles
- Revisa el cache de HuggingFace para modelos descargados
- Muestra tamaño de cada modelo
- Opción para probar la carga de modelos
- Lee configuración de variables de entorno

## Flujo de Trabajo Recomendado

### Instalación Rápida (Ollama - Recomendado)

```bash
# 1. Ejecutar script de instalación
bash scripts/install_models.sh

# 2. Seleccionar opción 1 (Ollama)

# 3. Configurar en .env
echo "LLM_MODEL_TYPE=ollama" >> .env
echo "LLM_MODEL_NAME=phi4" >> .env

# 4. Iniciar servicio
uv run python main.py fastapi
```

### Instalación HuggingFace (Mayor Control)

```bash
# 1. Descargar modelo específico
uv run python scripts/download_huggingface_model.py --model phi4

# 2. Configurar en .env
echo "LLM_MODEL_TYPE=phi4" >> .env
echo "DEVICE=cpu" >> .env  # o cuda si tienes GPU

# 3. Iniciar servicio
uv run python main.py fastapi
```

## Comparación: Ollama vs HuggingFace

| Característica | Ollama | HuggingFace |
|---------------|---------|-------------|
| **Velocidad** | ⚡ Más rápido (optimizado) | Más lento |
| **Memoria** | 💾 Menor uso (cuantización) | Mayor uso |
| **Instalación** | ✅ Simple (pull model) | Descarga automática |
| **Modelos** | Limitado a catálogo Ollama | Acceso a todo HuggingFace |
| **Control** | Menos control | Control total |
| **GPU** | Automático | Manual (CUDA) |

## Requisitos de Espacio en Disco

### Ollama
- `phi4`: ~4.5 GB (cuantizado)
- `llava`: ~4.7 GB (cuantizado)
- `llava:13b`: ~8 GB (cuantizado)

### HuggingFace (sin cuantizar)
- `phi4`: ~14 GB
- `gemma`: ~5 GB
- `llava`: ~14 GB
- `moondream`: ~4 GB

## Requisitos de Memoria RAM

### Inferencia CPU
- Modelos pequeños (moondream, gemma): 4-8 GB RAM
- Modelos medianos (phi4, llava 7B): 8-16 GB RAM
- Modelos grandes (llava 13B): 16-32 GB RAM

### Inferencia GPU
- Modelos pequeños: 4 GB VRAM
- Modelos medianos: 8-12 GB VRAM
- Modelos grandes: 16+ GB VRAM

## Ubicación de Modelos

### Ollama
```
Linux/macOS: ~/.ollama/models
Windows: C:\Users\<username>\.ollama\models
```

### HuggingFace
```
Linux/macOS: ~/.cache/huggingface/hub
Windows: C:\Users\<username>\.cache\huggingface\hub
```

## Troubleshooting

### Ollama no se conecta
```bash
# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Iniciar Ollama manualmente
ollama serve
```

### Error de memoria con HuggingFace
```bash
# Usar un modelo más pequeño
uv run python scripts/download_huggingface_model.py --model moondream

# O configurar para usar CPU
export DEVICE=cpu
```

### Modelo no descarga
```bash
# Verificar conectividad
curl -I https://huggingface.co

# Descargar manualmente con Python
uv run python scripts/download_huggingface_model.py --model phi4
```

### Windows: Script de PowerShell no se ejecuta
```powershell
# Permitir ejecución de scripts (ejecutar como Administrador)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego ejecutar el script
.\scripts\install_models.ps1
```

## Limpieza de Modelos

### Eliminar modelos Ollama
```bash
# Listar modelos
ollama list

# Eliminar modelo específico
ollama rm phi4
```

### Eliminar cache HuggingFace
```bash
# Linux/macOS
rm -rf ~/.cache/huggingface/hub

# Windows PowerShell
Remove-Item -Recurse -Force $env:USERPROFILE\.cache\huggingface\hub
```

## Verificación de Instalación

### Verificar que los modelos están instalados:

```bash
# Script de verificación
uv run python scripts/verify_models.py
```

Este script mostrará:
- ✓ Modelos Ollama disponibles y sus tamaños
- ✓ Modelos HuggingFace en cache y sus tamaños
- ⚠ Advertencias si faltan modelos
- Opción para probar carga de modelos

### Probar los modelos con el servicio:

```bash
# Con Gradio (recomendado para pruebas visuales)
uv run python main.py gradio
# Abrir http://localhost:7860

# Con cliente de prueba FastAPI
uv run python client/test_fastapi_client.py

# Con cliente de prueba gRPC
uv run python client/test_grpc_client.py path/to/image.png
```

## Variables de Entorno

Configura estas variables en tu archivo `.env`:

```bash
# Tipo de modelo (ollama, phi4, gemma, gemma3n, llava, moondream)
LLM_MODEL_TYPE=ollama

# Nombre del modelo (solo para ollama)
LLM_MODEL_NAME=phi4

# Dispositivo (cpu o cuda) - no aplica para ollama
DEVICE=cpu

# Host de Ollama (solo para ollama)
OLLAMA_HOST=http://localhost:11434

# Puertos de servicios
FASTAPI_PORT=8000
GRPC_PORT=50051
```

## Actualización de Modelos

### Ollama
```bash
# Actualizar un modelo
ollama pull phi4

# Ollama descarga automáticamente la última versión
```

### HuggingFace
```bash
# Limpiar cache y re-descargar
rm -rf ~/.cache/huggingface/hub
uv run python scripts/download_huggingface_model.py --model phi4
```

## Soporte

Para problemas o preguntas:
1. Revisa la sección de Troubleshooting
2. Consulta el archivo CLAUDE.md en la raíz del proyecto
3. Abre un issue en el repositorio del proyecto
