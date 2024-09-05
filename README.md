# Discord Bot

Este es un bot para Discord construido usando `discord.py` y varias extensiones para ofrecer funcionalidades avanzadas.

## Características

- **Administración:** Gestión de usuarios, roles y permisos.
- **Moderación:** Herramientas para moderar chats y manejar reportes.
- **Música:** Reproducción de música en canales de voz.
- **ChatGPT:** Integración con OpenAI's GPT para responder preguntas.
- **Niveles:** Sistema de niveles y experiencia para usuarios.
- **Encuestas:** Creación y manejo de encuestas.
- **Recordatorios:** Configuración de recordatorios personalizados.
- **Juegos:** Comandos relacionados con juegos y entretenimiento.
- **Tickets:** Sistema de tickets para soporte y consultas.
- **Logs:** Registro de eventos importantes del bot.
- **Traducción:** Traducción de mensajes en diferentes idiomas.
- **Bienvenida:** Mensajes personalizados de bienvenida para nuevos miembros.

## Instalación

1. Clona el repositorio:

   ```bash
   git clone https://github.com/h3nr1d3v/SkirkBot.git
   cd SkirkBot

   ```

2. Crea un entorno virtual e instálalo:
   ```python -m venv venv
   source venv/bin/activate   # En Windows usa `venv\Scripts\activate`
   ```
3. Instala las dependencias:
   `pip install -r requirements.txt`

4. Configura el archivo .env en el directorio raíz con tus claves:
   ```
   DISCORD_TOKEN=YOUR_DISCORD_CHANNEL_TOKEN
   OPENAI_API_KEY=YOUR_API_KEY
   ```

Para ejecutar el bot, usa el siguiente comando:
`python main.py`
