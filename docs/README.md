# Wiki de neoSkill

`docs/wiki/` contiene el contenido de la [wiki de GitHub](https://github.com/SanTacrZ/neoSkill/wiki), versionado junto al código.

| Página | Contenido |
| --- | --- |
| [wiki/Home.md](wiki/Home.md) | Índice y arranque rápido |
| [wiki/Instalación.md](wiki/Instalación.md) | Requisitos y primer arranque |
| [wiki/Arquitectura.md](wiki/Arquitectura.md) | Módulos y decisiones de diseño |
| [wiki/API-REST.md](wiki/API-REST.md) | Endpoints con ejemplos |
| [wiki/Flujo-de-la-sesión.md](wiki/Flujo-de-la-sesión.md) | Ciclo pregunta → panelista → IA → votación |
| [wiki/Integración-de-IA.md](wiki/Integración-de-IA.md) | Cómo conectar OpenAI u otro proveedor |
| [wiki/Pruebas.md](wiki/Pruebas.md) | Suite de pytest |

## Publicar en la wiki de GitHub

La wiki del repo requiere habilitarse una sola vez:

1. Abre <https://github.com/SanTacrZ/neoSkill/settings> y en **Features** marca **Wikis**
   (o entra a la pestaña *Wiki* y crea la primera página).
2. Ejecuta desde la raíz del proyecto:

   ```bash
   ./scripts/publish-wiki.sh
   ```

   El script clona `neoSkill.wiki.git`, copia `docs/wiki/*.md` y hace push.
3. Queda visible en <https://github.com/SanTacrZ/neoSkill/wiki>.

Mientras tanto, las páginas se leen directamente desde `docs/wiki/`.
