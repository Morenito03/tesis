# Scripts de Instalación - Ejemplos de Uso

Guía rápida con ejemplos prácticos para instalar modelos en el proyecto Smartwatch LLM Service.

## Escenario 1: Instalación Rápida con Ollama (Recomendado)

**Caso de uso**: Quiero empezar rápido con el mejor rendimiento.

```bash
# Paso 1: Ejecutar script de instalación
bash scripts/install_models.sh

# Seleccionar opción 1 (Ollama)
# Seleccionar phi4 (recomendado)

# Paso 2: Verificar instalación
uv run python scripts/verify_models.py

# Paso 3: Configurar .env
cat >> .env << EOF
LLM_MODEL_TYPE=ollama
LLM_MODEL_NAME=phi4
EOF

# Paso 4: Probar
uv run python main.py gradio
```

**Resultado**: Servicio listo en ~5 minutos con inferencia optimizada.

---

## Escenario 2: Instalación HuggingFace para Desarrollo

**Caso de uso**: Quiero experimentar con diferentes modelos y tener control total.

```bash
# Paso 1: Instalar modelo pequeño para pruebas
uv run python scripts/download_huggingface_model.py --model moondream

# Paso 2: Verificar descarga
uv run python scripts/verify_models.py

# Paso 3: Configurar
echo "LLM_MODEL_TYPE=moondream" >> .env
echo "DEVICE=cpu" >> .env

# Paso 4: Probar
uv run python main.py fastapi
# En otra terminal:
uv run python client/test_fastapi_client.py
```

**Resultado**: Modelo pequeño (~2GB) ideal para desarrollo.

---

## Escenario 3: Instalación Múltiple (Flexibilidad Máxima)

**Caso de uso**: Quiero tener varios modelos disponibles para comparar.

```bash
# Paso 1: Instalar Ollama
bash scripts/setup_ollama.sh
# Seleccionar opción 3 (phi4 + llava)

# Paso 2: Instalar algunos modelos HuggingFace
uv run python scripts/download_huggingface_model.py --model moondream
uv run python scripts/download_huggingface_model.py --model gemma

# Paso 3: Verificar todo
uv run python scripts/verify_models.py

# Paso 4: Cambiar entre modelos fácilmente
export LLM_MODEL_TYPE=ollama
export LLM_MODEL_NAME=phi4
uv run python main.py fastapi

# En otra sesión con diferente modelo
export LLM_MODEL_TYPE=moondream
uv run python main.py grpc
```

**Resultado**: Varios modelos listos, cambio rápido entre ellos.

---

## Escenario 4: Solo Verificación (Ya tengo modelos)

**Caso de uso**: Ya instalé modelos anteriormente, solo quiero verificar.

```bash
# Ver qué modelos tengo
uv run python scripts/verify_models.py

# Ver modelos Ollama
ollama list

# Ver cache HuggingFace
ls ~/.cache/huggingface/hub/

# Probar carga de un modelo específico
LLM_MODEL_TYPE=phi4 uv run python scripts/verify_models.py
```

---

## Escenario 5: Windows con PowerShell

**Caso de uso**: Estoy en Windows y quiero instalar todo.

```powershell
# Paso 1: Ejecutar script de instalación
.\scripts\install_models.ps1

# Seleccionar opción 1 (Ollama)
# El script te guiará a descargar Ollama si no lo tienes

# Paso 2: Después de instalar Ollama, ejecutar nuevamente
.\scripts\install_models.ps1

# Paso 3: Verificar
uv run python scripts/verify_models.py

# Paso 4: Iniciar servicio
uv run python main.py gradio
```

---

## Escenario 6: Servidor sin GUI (Solo CPU)

**Caso de uso**: Servidor Linux sin GPU, necesito eficiencia.

```bash
# Opción A: Ollama (recomendado)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull phi4

export LLM_MODEL_TYPE=ollama
export LLM_MODEL_NAME=phi4

# Opción B: HuggingFace modelo pequeño
uv run python scripts/download_huggingface_model.py --model moondream --device cpu

export LLM_MODEL_TYPE=moondream
export DEVICE=cpu

# Iniciar servicio
uv run python main.py fastapi --host 0.0.0.0
```

---

## Escenario 7: Desarrollo con GPU

**Caso de uso**: Tengo GPU NVIDIA y quiero máximo rendimiento con HuggingFace.

```bash
# Verificar CUDA
nvidia-smi

# Instalar modelo con soporte CUDA
uv run python scripts/download_huggingface_model.py --model phi4 --device cuda

# Configurar
cat >> .env << EOF
LLM_MODEL_TYPE=phi4
DEVICE=cuda
EOF

# Verificar (probará carga en GPU)
uv run python scripts/verify_models.py

# Iniciar
uv run python main.py fastapi
```

---

## Escenario 8: Instalación Limpia (Empezar desde cero)

**Caso de uso**: Tuve problemas, quiero reinstalar todo.

```bash
# Paso 1: Limpiar modelos existentes
# Ollama
ollama list | grep phi4 && ollama rm phi4
ollama list | grep llava && ollama rm llava

# HuggingFace
rm -rf ~/.cache/huggingface/hub/models--*

# Paso 2: Reinstalar
bash scripts/install_models.sh

# Paso 3: Verificar instalación limpia
uv run python scripts/verify_models.py
```

---

## Escenario 9: Deploy en Lightning.ai

**Caso de uso**: Quiero deployar en la nube con Lightning.

```bash
# Paso 1: Configurar para Ollama (más eficiente en cloud)
cat > .env << EOF
LLM_MODEL_TYPE=ollama
LLM_MODEL_NAME=phi4
OLLAMA_HOST=http://localhost:11434
EOF

# Paso 2: Verificar localmente
uv run python main.py fastapi

# Paso 3: Deploy
lightning run app lightning_app.py --cloud

# Lightning.ai se encargará de instalar Ollama automáticamente
```

---

## Escenario 10: Testing Rápido sin Instalar Modelos

**Caso de uso**: Quiero probar la arquitectura sin descargar GBs.

```bash
# Usar un modelo tiny de prueba (no recomendado para producción)
export LLM_MODEL_TYPE=moondream  # Modelo más pequeño (~1.8GB)

# Descarga bajo demanda (más lento la primera vez)
uv run python main.py gradio

# El modelo se descargará automáticamente en el primer request
```

---

## Tips Generales

### Ver logs detallados
```bash
# Ver qué está haciendo el script
bash -x scripts/setup_ollama.sh

# Ver logs de Python
uv run python scripts/download_huggingface_model.py --model phi4 2>&1 | tee install.log
```

### Cambiar modelo sobre la marcha
```bash
# Sin editar .env, solo con variables
LLM_MODEL_TYPE=ollama LLM_MODEL_NAME=llava uv run python main.py fastapi
```

### Probar todos los modelos instalados
```bash
# Listar disponibles
uv run python scripts/verify_models.py

# Probar cada uno
for model in phi4 gemma moondream; do
    echo "Testing $model..."
    LLM_MODEL_TYPE=$model uv run python client/test_fastapi_client.py
done
```

### Benchmark de velocidad
```bash
# Comparar Ollama vs HuggingFace
time LLM_MODEL_TYPE=ollama uv run python client/test_fastapi_client.py
time LLM_MODEL_TYPE=phi4 DEVICE=cpu uv run python client/test_fastapi_client.py
```

---

## Problemas Comunes y Soluciones

### "Ollama not found"
```bash
# Instalar según OS
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Descargar de https://ollama.ai/download
```

### "Out of memory"
```bash
# Usar modelo más pequeño
uv run python scripts/download_huggingface_model.py --model moondream

# O usar Ollama (usa menos memoria)
ollama pull phi4
```

### "Model not found"
```bash
# Verificar que esté instalado
uv run python scripts/verify_models.py

# Reinstalar si es necesario
ollama pull phi4  # Para Ollama
uv run python scripts/download_huggingface_model.py --model phi4  # Para HF
```

### "Port already in use"
```bash
# Cambiar puerto en .env
echo "FASTAPI_PORT=8001" >> .env
echo "GRPC_PORT=50052" >> .env
```

---

## Checklist de Instalación Exitosa

- [ ] Dependencias instaladas (`uv sync`)
- [ ] Al menos un modelo descargado (Ollama o HuggingFace)
- [ ] `scripts/verify_models.py` muestra modelos disponibles
- [ ] Archivo `.env` configurado con modelo elegido
- [ ] Protobufs generados (`uv run python main.py generate-protos`)
- [ ] Servicio inicia sin errores (`uv run python main.py fastapi`)
- [ ] Request de prueba funciona (`uv run python client/test_fastapi_client.py`)

Si todos los items están marcados, ¡la instalación fue exitosa! 🎉
