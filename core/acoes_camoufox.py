import random
import time
from playwright.sync_api import Page


def delay(min_s: float = 0.5, max_s: float = 1.2) -> None:
    """Pausa aleatória entre ações para simular ritmo humano."""
    time.sleep(random.uniform(min_s, max_s))


def mover_mouse(page: Page, locator=None) -> None:
    """
    Move o mouse organicamente.
    Se um locator for passado, move até ele com offset aleatório.
    Caso contrário, faz movimentos aleatórios pela tela.
    """
    try:
        if locator:
            box = locator.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2 + random.randint(-10, 10)
                y = box["y"] + box["height"] / 2 + random.randint(-8, 8)
                page.mouse.move(x, y, steps=random.randint(8, 18))
                delay(0.1, 0.3)
        else:
            vp = page.viewport_size or {"width": 1366, "height": 768}
            for _ in range(random.randint(2, 4)):
                page.mouse.move(
                    random.randint(100, vp["width"] - 100),
                    random.randint(100, vp["height"] - 100),
                    steps=random.randint(10, 20),
                )
                delay(0.2, 0.5)
    except Exception:
        pass


def simular_leitura(page: Page, segundos: float) -> None:
    """
    Mescla scroll, movimentos de mouse e pausas para simular
    que o usuário está lendo o conteúdo antes de agir.
    """
    fim = time.time() + segundos
    while time.time() < fim:
        acao = random.choice(["scroll", "mouse", "pause"])
        if acao == "scroll":
            page.mouse.wheel(0, random.randint(60, 200) * random.choice([1, -1]))
            delay(0.8, 2.0)
        elif acao == "mouse":
            mover_mouse(page)
            delay(0.5, 1.5)
        else:
            delay(1.0, 2.5)


def clicar(page: Page, locator) -> bool:
    """
    Move o mouse até o elemento organicamente e clica com
    delay variável simulando pressão humana no botão.
    """
    try:
        locator.wait_for(state="visible", timeout=10000)
        mover_mouse(page, locator)
        delay(0.2, 0.5)
        locator.click(delay=random.randint(40, 120))
        return True
    except Exception as e:
        print(f"Erro ao clicar: {e}")
        return False


def digitar(page: Page, locator, texto: str) -> bool:
    """
    Clica no campo e digita caractere por caractere com
    variação de tempo realística entre as teclas.
    """
    try:
        locator.wait_for(state="visible", timeout=10000)
        mover_mouse(page, locator)
        locator.click(delay=random.randint(40, 100))
        delay(0.3, 0.6)
        locator.fill("")
        delay(0.2, 0.4)
        for char in texto:
            locator.press_sequentially(char)
            time.sleep(random.uniform(0.08, 0.22))
        return True
    except Exception as e:
        print(f"Erro ao digitar: {e}")
        return False