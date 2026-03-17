

import os
import sys
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button, DataTable, Footer, Header,
    Input, Label, RichLog, Static,
)

# ── DB layer ─────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from db.database import (  # noqa: E402
    add_room,
    get_all_rooms,
    get_bookings_for_room,
    get_room_by_id,
    remove_room,
    save_deletion_report,
    update_room_capacity,
)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


# =============================================================================
# Modal: Add Room
# =============================================================================
class AddRoomModal(ModalScreen):
    DEFAULT_CSS = """
    AddRoomModal { align: center middle; }
    #add-box {
        background: $surface; border: thick $success;
        padding: 1 2; width: 60; height: auto;
    }
    #add-title { text-style: bold; color: $success; margin-bottom: 1; }
    .add-lbl   { margin-top: 1; }
    #add-err   { color: $error; height: 1; }
    #add-btns  { margin-top: 2; }
    """

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self.db_path = db_path

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="add-box"):
            yield Static("➕  Add New Room", id="add-title")
            yield Label("Room Name:", classes="add-lbl")
            yield Input(placeholder="e.g. Conference Room B", id="inp-name")
            yield Label("Capacity:", classes="add-lbl")
            yield Input(placeholder="e.g. 8", id="inp-cap")
            yield Label("Amenities (optional):", classes="add-lbl")
            yield Input(
                placeholder="e.g. Projector, Whiteboard", id="inp-amen"
            )
            yield Static("", id="add-err")
            with Horizontal(id="add-btns"):
                yield Button("Add Room", variant="success", id="btn-add")
                yield Button("Cancel",   variant="default",  id="btn-cancel")

    @on(Button.Pressed, "#btn-add")
    def do_add(self) -> None:
        name = self.query_one("#inp-name", Input).value.strip()
        cap_str = self.query_one("#inp-cap", Input).value.strip()
        amenities = self.query_one("#inp-amen", Input).value.strip()
        err = self.query_one("#add-err", Static)
        try:
            capacity = int(cap_str)
        except ValueError:
            err.update("Capacity must be a whole number.")
            return
        try:
            new_id = add_room(self.db_path, name, capacity, amenities)
            self.dismiss((True, new_id))
        except ValueError as exc:
            err.update(str(exc))

    @on(Button.Pressed, "#btn-cancel")
    def do_cancel(self) -> None:
        self.dismiss((False, None))


# =============================================================================
# Modal: Confirm Delete
# =============================================================================
class ConfirmDeleteModal(ModalScreen):
    DEFAULT_CSS = """
    ConfirmDeleteModal { align: center middle; }
    #del-box {
        background: $surface; border: thick $error;
        padding: 1 2; width: 62; height: auto; max-height: 28;
    }
    #del-title  { text-style: bold; color: $error; margin-bottom: 1; }
    #del-btns   { margin-top: 1; }
    """

    def __init__(self, room: dict, bookings: list, db_path: str) -> None:
        super().__init__()
        self.room = room
        self.bookings = bookings
        self.db_path = db_path

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        affected = (
            ", ".join(b["username"] for b in self.bookings)
            if self.bookings else "none"
        )
        with Container(id="del-box"):
            yield Static(
                f"⚠  Delete Room: {self.room['room_name']}", id="del-title"
            )
            yield Static(
                f"This will cancel "
                f"{len(self.bookings)} active reservation(s)."
            )
            yield Static(f"Affected users: {affected}")
            yield Static("")
            yield Static("A report will be saved to reports/")
            with Horizontal(id="del-btns"):
                yield Button(
                    "Confirm Delete", variant="error", id="btn-confirm"
                )
                yield Button("Cancel", variant="default", id="btn-cancel")

    @on(Button.Pressed, "#btn-confirm")
    def do_delete(self) -> None:
        try:
            cancelled = remove_room(self.db_path, self.room["id"])
            report_path = save_deletion_report(
                REPORTS_DIR,
                self.room["room_name"],
                self.room["id"],
                cancelled,
            )
            self.dismiss((True, cancelled, report_path))
        except Exception as exc:
            self.dismiss((False, [], str(exc)))

    @on(Button.Pressed, "#btn-cancel")
    def do_cancel(self) -> None:
        self.dismiss((False, [], ""))


# =============================================================================
# Modal: Change Capacity
# =============================================================================
class ChangeCapacityModal(ModalScreen):
    DEFAULT_CSS = """
    ChangeCapacityModal { align: center middle; }
    #cap-box {
        background: $surface; border: thick $warning;
        padding: 1 2; width: 52; height: auto;
    }
    #cap-title { text-style: bold; color: $warning; margin-bottom: 1; }
    #cap-err   { color: $error; height: 1; }
    #cap-btns  { margin-top: 2; }
    """

    def __init__(self, room: dict, db_path: str) -> None:
        super().__init__()
        self.room = room
        self.db_path = db_path

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="cap-box"):
            yield Static(
                f"✏  Change Capacity: {self.room['room_name']}", id="cap-title"
            )
            yield Label(f"Current capacity: {self.room['capacity']}")
            yield Label("New capacity:")
            yield Input(placeholder="Enter new capacity", id="cap-inp")
            yield Static("", id="cap-err")
            with Horizontal(id="cap-btns"):
                yield Button("Update", variant="warning", id="btn-update")
                yield Button("Cancel", variant="default", id="btn-cancel")

    @on(Button.Pressed, "#btn-update")
    def do_update(self) -> None:
        cap_str = self.query_one("#cap-inp", Input).value.strip()
        err = self.query_one("#cap-err", Static)
        try:
            new_cap = int(cap_str)
        except ValueError:
            err.update("Capacity must be a whole number.")
            return
        try:
            update_room_capacity(self.db_path, self.room["id"], new_cap)
            self.dismiss((True, new_cap))
        except ValueError as exc:
            err.update(str(exc))

    @on(Button.Pressed, "#btn-cancel")
    def do_cancel(self) -> None:
        self.dismiss((False, None))


# =============================================================================
# Main App
# =============================================================================
class RoomAdminApp(App):
    """Sprint 4 — Room Admin TUI."""

    TITLE = "Room Admin Panel"
    SUB_TITLE = "Sprint 4 · Meeting Room Database Manager"

    CSS = """
    Screen { background: $background; }
    #layout { height: 1fr; }
    #left  { width: 56%; border-right: solid $primary; padding: 0 1; }
    #right { width: 44%; padding: 0 1; }
    #pane-title {
        text-style: bold underline; color: $primary; margin-bottom: 1;
    }
    #log-title  {
        text-style: bold underline; color: $accent;  margin-bottom: 1;
    }
    #rooms-table { height: 1fr; }
    #action-bar  { height: auto; margin-top: 1; }
    #action-bar Button { margin-right: 1; }
    #activity-log { height: 1fr; border: solid $panel; }
    #status { height: 3; background: $panel; padding: 0 1;
              content-align: left middle; }
    """

    BINDINGS = [
        Binding("a", "add_room",        "Add Room"),
        Binding("d", "delete_room",     "Delete Room"),
        Binding("c", "change_capacity", "Change Capacity"),
        Binding("r", "refresh",         "Refresh"),
        Binding("q", "quit",            "Quit"),
    ]

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self.db_path = db_path

    # ── layout ───────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="layout"):
            with Vertical(id="left"):
                yield Static("📋  Available Rooms", id="pane-title")
                yield DataTable(
                    id="rooms-table",
                    cursor_type="row",
                    zebra_stripes=True,
                )
                with Horizontal(id="action-bar"):
                    yield Button(
                        "➕ Add",             variant="success", id="btn-add"
                    )
                    yield Button(
                        "🗑  Remove",          variant="error",   id="btn-del"
                    )
                    yield Button(
                        "✏  Capacity",        variant="warning", id="btn-cap"
                    )
                    yield Button(
                        "🔄 Refresh",         variant="default", id="btn-ref"
                    )
            with Vertical(id="right"):
                yield Static("📝  Activity Log", id="log-title")
                yield RichLog(
                    id="activity-log", highlight=True, markup=True
                )
        yield Static(
            "Select a row · A=Add  D=Delete  C=Capacity  R=Refresh  Q=Quit",
            id="status",
        )
        yield Footer()

    def on_mount(self) -> None:
        tbl = self.query_one("#rooms-table", DataTable)
        tbl.add_columns(
            "ID", "Name", "Capacity", "Active", "Bookings"
        )
        self._reload()
        self._log(f"[bold green]Room Admin started.[/]  DB: {self.db_path}")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _reload(self) -> None:
        tbl = self.query_one("#rooms-table", DataTable)
        tbl.clear()
        for r in get_all_rooms(self.db_path):
            bkgs = get_bookings_for_room(self.db_path, r["id"])
            tbl.add_row(
                str(r["id"]),
                r["room_name"],
                str(r["capacity"]),
                "✅" if r["is_active"] else "❌",
                str(len(bkgs)),
                key=str(r["id"]),
            )

    def _log(self, msg: str) -> None:
        self.query_one(RichLog).write(msg)

    def _selected_room(self) -> Optional[dict]:
        tbl = self.query_one("#rooms-table", DataTable)
        if tbl.cursor_row < 0:
            return None
        row_data = tbl.get_row_at(tbl.cursor_row)
        return get_room_by_id(self.db_path, int(row_data[0]))

    # ── actions ───────────────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        self._reload()
        self._log("[cyan]Table refreshed.[/]")

    def action_add_room(self) -> None:
        def on_close(result):
            ok, new_id = result
            if ok:
                self._log(f"[green]✅ Room added (ID {new_id}).[/]")
                self._reload()
            else:
                self._log("[dim]Add cancelled.[/]")
        self.push_screen(AddRoomModal(self.db_path), on_close)

    def action_delete_room(self) -> None:
        room = self._selected_room()
        if not room:
            self._log("[yellow]⚠ Select a room first.[/]")
            return
        bookings = get_bookings_for_room(self.db_path, room["id"])

        def on_close(result):
            ok, cancelled, info = result
            if ok:
                names = ", ".join(cancelled) if cancelled else "none"
                self._log(
                    f"[red]🗑 '{room['room_name']}' deleted. "
                    f"Cancelled for: {names}[/]"
                )
                self._log(f"[dim]Report: {info}[/]")
                self._reload()
            elif info:
                self._log(f"[red]Error: {info}[/]")
            else:
                self._log("[dim]Delete cancelled.[/]")

        self.push_screen(
            ConfirmDeleteModal(room, bookings, self.db_path), on_close
        )

    def action_change_capacity(self) -> None:
        room = self._selected_room()
        if not room:
            self._log("[yellow]⚠ Select a room first.[/]")
            return

        def on_close(result):
            ok, new_cap = result
            if ok:
                self._log(
                    f"[blue]✏ '{room['room_name']}' capacity "
                    f"{room['capacity']} → {new_cap}[/]"
                )
                self._reload()
            else:
                self._log("[dim]Capacity change cancelled.[/]")

        self.push_screen(ChangeCapacityModal(room, self.db_path), on_close)

    # ── button wiring ─────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-add")
    def _btn_add(self) -> None:
        self.action_add_room()

    @on(Button.Pressed, "#btn-del")
    def _btn_del(self) -> None:
        self.action_delete_room()

    @on(Button.Pressed, "#btn-cap")
    def _btn_cap(self) -> None:
        self.action_change_capacity()

    @on(Button.Pressed, "#btn-ref")
    def _btn_ref(self) -> None:
        self.action_refresh()


# =============================================================================
# Entry point
# =============================================================================

def main() -> None:
    db_path = sys.argv[1] if len(sys.argv) > 1 else "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"ERROR: database not found: {db_path}")
        print("Run:  python create_test_db.py  to create a sample DB.")
        sys.exit(1)
    RoomAdminApp(db_path=db_path).run()


if __name__ == "__main__":
    main()
