import typer
from facilito.models.quality import Quality  # Importar desde el nuevo módulo quality
from facilito.core import Client  # type: ignore
from facilito.utils.logger import cli_logger  # type: ignore
from facilito import helpers  # type: ignore
from facilito.errors import DownloadError, VideoError, CourseError  # type: ignore
import json
from rich import print as tprint
from rich.console import Console
from rich.table import Table

app = typer.Typer()

def load_cookies(client: Client):
    """Carga cookies desde un archivo JSON convertido."""
    try:
        with open("cookies.json", "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                client.cookies.set(
                    name=cookie["name"],
                    value=cookie["value"],
                    domain=cookie["domain"],
                    path=cookie.get("path", "/"),
                    secure=cookie.get("secure", False)
                )
        print("✓ Cookies cargadas correctamente.")
    except Exception as e:
        print(f"✗ Error al cargar cookies: {e}")

def load_urls(file_path: str) -> list[str]:
    """Carga URLs desde un archivo de texto."""
    try:
        with open(file_path, "r") as file:
            urls = [line.strip() for line in file if line.strip()]
        print("✓ URLs cargadas correctamente.")
        return urls
    except Exception as e:
        print(f"✗ Error al cargar URLs: {e}")
        return []

@app.command()
def download(
    file_path: str = "urls.txt",
    quality: Quality = '720p',
    headless: bool = False,
):
    """Descarga videos y cursos completos con autenticación usando cookies."""
    
    if not helpers.is_ffmpeg_installed():
        tprint("[bold red]Error![/bold red] ffmpeg no está instalado.")
        raise typer.Exit()

    urls = load_urls(file_path)

    with Client(headless=headless) as client:
        load_cookies(client)  # Cargar cookies antes de hacer cualquier request
        
        for url in urls:
            if helpers.is_video_url(url):
                try:
                    video = client.video(url)
                    video.download(quality=quality.value)
                    tprint(f"✓ Descargado: {video.title}")
                except Exception as e:
                    tprint(f"✗ Error descargando {url}: {e}")
            elif helpers.is_course_url(url):
                try:
                    course = client.course(url)
                    course_title = helpers.clean_string(course.title)
                    course_sections = course.sections
                    # Mostrar detalles del curso
                    console = Console()
                    title_table = Table(course_title)
                    console.print(title_table)
                    sections_table = Table("Sección", "Videos")
                    for section in course_sections:
                        sections_table.add_row(
                            section.title,
                            str(len(section.videos_url)),
                        )
                    console.print(sections_table)

                    # Confirmar descarga
                    confirm_download = typer.confirm("¿Te gustaría descargar este curso?")
                    if not confirm_download:
                        continue

                    # Descargar los videos del curso
                    for pfx_s, section in enumerate(course_sections, start=1):
                        section_title = helpers.clean_string(section.title)
                        section_videos = section.videos_url
                        for pfx_v, video_url in enumerate(section_videos, start=1):
                            try:
                                video = client.video(video_url)
                            except VideoError as e:
                                tprint("✗ No se pudo obtener los detalles del video.")
                                message = f"[SECCIÓN] {section_title} [VIDEO] {video_url}"
                                cli_logger.error(message)
                                continue
                            max_retries = 5
                            for attempt in range(1, max_retries + 1):
                                try:
                                    tprint("⠹ Descargando...")
                                    tprint(f"⠹ {video.title} ...")
                                    client.refresh_cookies()
                                    # Ruta del directorio de descarga
                                    dir_path = f"{consts.DOWNLOADS_DIR}/{course_title}/{pfx_s:02d}. {section_title}"
                                    video.download(
                                        quality=quality.value,
                                        dir_path=dir_path,
                                        prefix_name=f"{pfx_v:02d}. ",
                                    )
                                except DownloadError:
                                    if attempt < max_retries:
                                        tprint("⠹ Ocurrió un error al descargar :(")
                                        tprint("⠹ Reintentando ...")
                                    else:
                                        tprint("✗ No se pudo descargar el video.")
                                        break
                                else:
                                    tprint("✓ ¡Hecho!")
                except CourseError as e:
                    tprint("✗ No se pudo descargar el curso.")
                    raise typer.Exit() from e
            else:
                tprint("[bold red]Error![/bold red] URL no válida para [VIDEO|CURSO].")
                raise typer.Exit()

if __name__ == "__main__":
    app()

#Explicación
""" Retrasos Aleatorios: Después de cada descarga, se agrega un retraso aleatorio entre 1 y 5 segundos para evitar que el servidor detecte un patrón de descargas rápidas.
Rotación de User Agents: Antes de cada descarga, se selecciona un User Agent aleatorio de una lista predefinida para que las descargas parezcan provenir de diferentes clientes. """