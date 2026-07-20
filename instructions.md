# Guía de ejecución — Strepitus Silvae

## Requisitos

- Windows con Anaconda o Miniconda.
- Una cuenta y clave de OpenAI con acceso al modelo requerido para el reto.
- Conexión a internet para OpenAI, iNaturalist, GBIF, Open-Meteo, OpenStreetMap/Overpass y las fichas públicas de Wikimedia/Wikidata.

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

La interfaz permite elegir estos modelos GPT-5.6:

- `gpt-5.6-sol`: máxima capacidad; recomendado para análisis ecológico complejo.
- `gpt-5.6-terra`: equilibrio entre capacidad y costo.
- `gpt-5.6-luna`: alto volumen y costo reducido.

El valor por defecto es `gpt-5.6-sol`. También puedes fijarlo desde el entorno:

```powershell
$env:OPENAI_MODEL="gpt-5.6-terra"
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

En la pestaña **Audio**, usa *Nota de campo humana* para una observación hablada y *Vocalización de ave (BirdNET beta)* para un canto. La primera ejecución de BirdNET puede tardar mientras descarga sus modelos locales. La pestaña **Video** extrae 12 fotogramas y los analiza como evidencia visual multiespecie; los videos no se envían como una modalidad nativa a GPT-5.6.

Una confianza `medio` o `bajo` activa una consulta de validación a iNaturalist. Todo resultado es una hipótesis asistida por IA: una persona capacitada debe revisarlo antes de usarlo en decisiones científicas o de conservación.

## 7. Consultar el contexto del sitio

1. Selecciona un punto en **Contexto del evento** o escribe latitud y longitud.
2. En **Especies cercanas**, elige radio, grupo y fuente para consultar iNaturalist y/o GBIF.
3. En **Perfil ambiental**, pulsa **Actualizar perfil ambiental**. Verás el mapa local 2D, elevación, clima, cobertura disponible, infraestructura mapeada y el resumen acotado de registros GBIF cercanos.
4. En **Explorador Wiki**, abre la subpestaña de cada taxón detectado. El estado de conservación aparece primero, seguido de imagen y resumen de Wikipedia, enlaces públicos y la ficha taxonómica. El botón **Generar ilustración de hábitat** llama a GPT Image solo cuando lo pulsas; la imagen generada no es evidencia observacional.

Los datos GBIF, Wikipedia, Wikidata e IUCN son referencias externas: no cambian la confianza de la evidencia ni sustituyen revisión humana.

## Verificar la instalación

```powershell
python -m unittest discover -s tests -v
```

## Solución de problemas

| Problema | Solución |
| --- | --- |
| `conda` no se reconoce | Usa Anaconda Prompt o agrega Conda al PATH. |
| Falta `OPENAI_API_KEY` | Ejecuta de nuevo el comando del paso 4 en la misma terminal. |
| Error de modelo | Confirma que tu cuenta tenga acceso a Sol, Terra o Luna; también puedes definir `OPENAI_MODEL` con uno de sus IDs. |
| No hay conexión con iNaturalist | El análisis puede completarse; la validación externa mostrará un mensaje de error. |
| No aparece información en la ficha de especie | Verifica la conexión a Wikimedia/Wikidata. Si no existe una página en Wikipedia en español, la app conserva enlaces de búsqueda sin afectar la detección. |
| La ficha Wiki no muestra imagen o resumen | Confirma la conexión a Wikipedia/Wikidata. La detección y exportación siguen disponibles. |
