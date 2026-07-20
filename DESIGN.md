# Design System — App de Detección de Especies

## 1. Filosofía de color

Referencia del sector: apps de identificación de naturaleza convergen en
**verde como color primario** (nature/vegetación) + **neutro cálido** de fondo
+ **un único acento** reservado para la acción principal (cámara/detectar).
Evitar blancos fríos "clínicos" tipo app de salud/finanzas.

## 2. Referencias de mercado

| App | Primario | Secundario | Acento | Notas |
|---|---|---|---|---|
| iNaturalist | `#74AC00` verde oliva | `#3D5A2C` verde oscuro | — | Neutros negro/blanco roto |
| Seek | `#5AA02C` verde vivo | `#2E86C1` azul | `#E67E22` coral | Gamificado, para público infantil |
| Merlin Bird ID | `#1F6F8B` azul petróleo | `#F2A007` ámbar | — | Se aparta del verde (foco: aves/cielo) |
| PlantNet / Picture This | `#2F7D32` verde bosque | `#A5D6A7` verde claro | `#E91E63` rosa | Acento floral para diferenciar |

## 3. Paleta propuesta

### Colores base

| Rol | Hex | Uso |
|---|---|---|
| Primario | `#3B6D11` | Verde bosque — marca, iconos activos, estados de éxito de identificación |
| Primario claro | `#639922` | Hover / estados activos sobre primario |
| Secundario (tierra) | `#BA7517` | Acento cálido — tarjetas de especie, badges, ilustraciones |
| Acento de acción | `#378ADD` | Botón de cámara / "Detectar" — único uso, no repetir en otros elementos |
| Fondo | `#F1EFE8` | Fondo general, crema cálido |
| Superficie | `#FFFFFF` | Tarjetas, modales |
| Texto primario | `#2C2C2A` | Texto principal (casi negro, no negro puro) |
| Texto secundario | `#5F5E5A` | Subtítulos, metadatos |
| Borde | `#D3D1C7` | Separadores, contornos sutiles |

### Colores semánticos (estados)

| Estado | Hex | Uso |
|---|---|---|
| Éxito / especie identificada | `#3B6D11` | Confirmación de identificación |
| Advertencia / confianza baja | `#EF9F27` | "No estamos seguros, revisa estas opciones" |
| Error / sin coincidencias | `#E24B4A` | Fallo de detección, sin conexión |
| Información | `#378ADD` | Tooltips, datos educativos de la especie |

### Categorías taxonómicas (opcional, para diferenciar tipos de especie)

| Categoría | Hex |
|---|---|
| Plantas | `#3B6D11` verde |
| Aves | `#378ADD` azul |
| Insectos / invertebrados | `#BA7517` tierra |
| Hongos | `#993556` vino |
| Mamíferos | `#5F5E5A` gris cálido |

## 4. Modo oscuro

| Rol | Claro | Oscuro |
|---|---|---|
| Fondo | `#F1EFE8` | `#1A1A19` |
| Superficie | `#FFFFFF` | `#2C2C2A` |
| Primario | `#3B6D11` | `#97C459` (versión clara del verde) |
| Acento | `#378ADD` | `#85B7EB` |
| Texto primario | `#2C2C2A` | `#F1EFE8` |
| Texto secundario | `#5F5E5A` | `#B4B2A9` |

## 5. Tipografía

- **Encabezados**: sans-serif geométrica (ej. Inter, Poppins) — peso 500/600, transmite claridad científica.
- **Cuerpo**: sans-serif neutra de alta legibilidad (ej. Inter, System UI) — peso 400, tamaño base 16px.
- **Nombres científicos**: itálica, para respetar convención binomial (*Panthera onca*).

## 6. Principios de uso

1. El acento de acción (`#378ADD`) se reserva **solo** para el botón principal de captura/detección — nunca decorativo.
2. Máximo 2-3 colores visibles por pantalla; el resto son neutros.
3. Las fotos del usuario (animales/plantas) son el elemento más colorido de la interfaz — el UI debe quedar en segundo plano.
4. Contraste mínimo AA (4.5:1) entre texto y fondo en ambos modos.
5. Un mismo color = un mismo significado en toda la app (no reusar verde para "error" en ninguna pantalla).

## 7. Espaciado y forma

- Radio de esquina: `8px` en controles, `12px` en tarjetas.
- Espaciado base: múltiplos de `4px` (4, 8, 12, 16, 24, 32).
- Iconografía: trazo (outline), no relleno — coherente con estética naturalista/de campo.