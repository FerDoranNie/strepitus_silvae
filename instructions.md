# Guía de ejecución — Strepitus Silvae

## Requisitos

- Windows con Anaconda o Miniconda.
- Una cuenta y clave de OpenAI con acceso al modelo requerido para el reto.
- Conexión a internet para OpenAI e iNaturalist.

## 1. Abrir una terminal en el proyecto

```powershell
cd C:\Users\fernando.dorantes\local\scripts\proyectos\Strepitus_silvae
```

## 2. Activar el entorno Conda

El proyecto usa el entorno ya creado `strepitus_silvae`:

```powershell
conda activate strepitus_silvae
```

Si `conda` no está disponible en tu terminal, abre **Anaconda Prompt** y ejecuta los mismos comandos desde ahí.

## 3. Instalar o actualizar dependencias

```powershell
python -m pip install -r requirements.txt
```

## 4. Configurar la clave de OpenAI

Para la sesión actual de PowerShell, sin guardar la clave en archivos:

```powershell
$env:OPENAI_API_KEY="pega_tu_clave_aqui"
```

Opcionalmente, configura el modelo de análisis. El valor por defecto de la aplicación es `gpt-5.6`.

```powershell
$env:OPENAI_MODEL="gpt-5.6"
```

Nunca subas claves al repositorio, al README o a capturas de pantalla.

## 5. Ejecutar la aplicación

```powershell
streamlit run app.py
```

Streamlit mostrará una URL local, normalmente `http://localhost:8501`. Ábrela en el navegador.

## 6. Probar el flujo

1. Elige **Cámara trampa** y carga una imagen, o elige **Nota de voz** y graba/carga audio.
2. Completa fecha, coordenadas y localidad si las conoces.
3. Selecciona **Analizar evidencia**.
4. Revisa el resultado antes de descargar JSON o CSV.

Una confianza `medio` o `bajo` activa una consulta de validación a iNaturalist. Todo resultado es una hipótesis asistida por IA: una persona capacitada debe revisarlo antes de usarlo en decisiones científicas o de conservación.

## Verificar la instalación

```powershell
python -m unittest discover -s tests -v
```

## Solución de problemas

| Problema | Solución |
| --- | --- |
| `conda` no se reconoce | Usa Anaconda Prompt o agrega Conda al PATH. |
| Falta `OPENAI_API_KEY` | Ejecuta de nuevo el comando del paso 4 en la misma terminal. |
| Error de modelo | Confirma que tu cuenta tenga acceso a `gpt-5.6` o define `OPENAI_MODEL` con el identificador disponible para tu cuenta. |
| No hay conexión con iNaturalist | El análisis puede completarse; la validación externa mostrará un mensaje de error. |
