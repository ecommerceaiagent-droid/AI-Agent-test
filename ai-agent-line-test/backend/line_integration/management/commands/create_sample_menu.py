import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from line_integration.rich_menu_image import render_sample_menu_png
from line_integration.services import sample_rich_menu

LINE_API = "https://api.line.me"
LINE_DATA_API = "https://api-data.line.me"
MENU_NAME = "Sample pages"


class Command(BaseCommand):
    help = "Create the LINE chat menu with two icons that open the sample pages in LIFF."

    def handle(self, *args, **options) -> None:
        liff_id = settings.LIFF_ID
        token = settings.LINE_CHANNEL_ACCESS_TOKEN
        if not liff_id:
            raise CommandError("Set LIFF_ID before creating the menu.")
        if not token:
            raise CommandError("Set LINE_CHANNEL_ACCESS_TOKEN before creating the menu.")

        menu = sample_rich_menu(liff_id)
        headers = {"Authorization": f"Bearer {token}"}
        self._delete_previous(headers)
        rich_menu_id = self._create(headers, menu)
        self._upload(headers, rich_menu_id, render_sample_menu_png())
        self._set_default(headers, rich_menu_id)
        self.stdout.write(self.style.SUCCESS(f"Rich menu {rich_menu_id} is the default chat menu."))
        for area in menu["areas"]:
            action = area["action"]
            self.stdout.write(f"{action['label']}: {action['uri']}")

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        last_error: requests.RequestException | None = None
        for attempt in range(4):
            try:
                return requests.request(method, url, timeout=30, **kwargs)
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(1 + attempt)
        raise CommandError(f"Could not reach LINE at {url}. {last_error}")

    def _delete_previous(self, headers: dict[str, str]) -> None:
        response = self._request("GET", f"{LINE_API}/v2/bot/richmenu/list", headers=headers)
        self._require(response, "Could not list rich menus.")
        for menu in response.json().get("richmenus", []):
            if menu.get("name") != MENU_NAME:
                continue
            menu_id = menu.get("richMenuId")
            if not isinstance(menu_id, str):
                continue
            deleted = self._request("DELETE", f"{LINE_API}/v2/bot/richmenu/{menu_id}", headers=headers)
            self._require(deleted, f"Could not replace rich menu {menu_id}.")

    def _create(self, headers: dict[str, str], menu: dict) -> str:
        response = self._request(
            "POST",
            f"{LINE_API}/v2/bot/richmenu",
            headers={**headers, "Content-Type": "application/json"},
            json=menu,
        )
        self._require(response, "LINE rejected the rich menu.")
        menu_id = response.json().get("richMenuId")
        if not isinstance(menu_id, str) or not menu_id:
            raise CommandError("LINE did not return a rich menu id.")
        return menu_id

    def _upload(self, headers: dict[str, str], menu_id: str, image: bytes) -> None:
        response = self._request(
            "POST",
            f"{LINE_DATA_API}/v2/bot/richmenu/{menu_id}/content",
            headers={**headers, "Content-Type": "image/png"},
            data=image,
        )
        self._require(response, "LINE rejected the menu image.")

    def _set_default(self, headers: dict[str, str], menu_id: str) -> None:
        response = self._request("POST", f"{LINE_API}/v2/bot/user/all/richmenu/{menu_id}", headers=headers)
        self._require(response, "LINE did not set the menu as the default.")

    def _require(self, response: requests.Response, message: str) -> None:
        if response.ok:
            return
        detail = response.text.strip().replace("\n", " ")[:300]
        raise CommandError(f"{message} LINE returned {response.status_code}. {detail}")
