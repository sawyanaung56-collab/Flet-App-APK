import flet as ft

def main(page: ft.Page):
    page.title = "My Flet App"
    page.add(ft.Text("Hello, Flet Android App!"))

ft.app(target=main)