from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from storage_manager.auth import authorize, disconnect
from storage_manager.config import AppConfig, application_dir, load_config
from storage_manager.errors import AppError, OperationCancelled, WrongAccountError
from storage_manager.gmail_client import GmailClient
from storage_manager.logging_setup import configure_logging
from storage_manager.models import DeleteResult, ScanResult, format_bytes


BG = "#f3f6fb"
CARD = "#ffffff"
TEXT = "#202124"
MUTED = "#5f6368"
PRIMARY = "#49587e"
PRIMARY_ACTIVE = "#5b6c96"
BUTTON_DISABLED = "#b9bec9"
GREEN = "#137333"


class ClassicButton(tk.Button):
    """Botão clássico no mesmo padrão visual usado pelo Robo-INSS."""

    def __init__(self, parent, *, text: str, command, state: str = "normal"):
        super().__init__(
            parent,
            text=text,
            command=command,
            state=state,
            font=("Segoe UI", 10, "bold"),
            bg=BUTTON_DISABLED if state == "disabled" else PRIMARY,
            fg="white",
            disabledforeground="#f3f4f6",
            activebackground=PRIMARY_ACTIVE,
            activeforeground="white",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=8,
            cursor="arrow" if state == "disabled" else "hand2",
        )

    def configure(self, cnf=None, **kwargs):
        if isinstance(cnf, dict):
            kwargs.update(cnf)
            cnf = None
        state = kwargs.get("state")
        if state is not None:
            disabled = str(state) == "disabled"
            kwargs.setdefault("bg", BUTTON_DISABLED if disabled else PRIMARY)
            kwargs.setdefault("cursor", "arrow" if disabled else "hand2")
        return super().configure(cnf, **kwargs)

    config = configure


class StyledCheckbutton(tk.Frame):
    """Caixa de confirmação plana, legível e coerente com a paleta do app."""

    def __init__(self, parent, *, text: str, variable: tk.BooleanVar, command):
        super().__init__(parent, background=CARD, borderwidth=0, highlightthickness=0)
        self.variable = variable
        self.command = command
        self.hovered = False
        self.box = tk.Canvas(
            self,
            width=20,
            height=20,
            background=CARD,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
        )
        self.box.pack(side="left")
        self.label = tk.Label(
            self,
            text=text,
            background=CARD,
            foreground=TEXT,
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        self.label.pack(side="left", padx=(6, 0))
        for widget in (self.box, self.label):
            widget.bind("<Button-1>", self._toggle)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
        self.box.bind("<space>", self._toggle)
        self.box.bind("<Return>", self._toggle)
        self.variable.trace_add("write", lambda *_args: self._draw())
        self._draw()

    def _rounded_fill(self, x1: int, y1: int, x2: int, y2: int, radius: int, color: str) -> None:
        self.box.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=color, outline=color)
        self.box.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=color, outline=color)
        self.box.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=color, outline=color)
        self.box.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=color, outline=color)
        self.box.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=color, outline=color)
        self.box.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=color, outline=color)

    def _draw(self) -> None:
        self.box.delete("all")
        border = PRIMARY_ACTIVE if self.hovered else PRIMARY
        self._rounded_fill(2, 2, 18, 18, 4, border)
        if self.variable.get():
            self.box.create_line(
                6,
                10,
                9,
                13,
                15,
                7,
                fill="white",
                width=2,
                capstyle="round",
                joinstyle="round",
            )
        else:
            self._rounded_fill(4, 4, 16, 16, 2, CARD)

    def _toggle(self, _event=None) -> str:
        self.variable.set(not self.variable.get())
        self.command()
        self.box.focus_set()
        return "break"

    def _on_enter(self, _event) -> None:
        self.hovered = True
        self._draw()

    def _on_leave(self, _event) -> None:
        self.hovered = False
        self._draw()


class StorageManagerApp:
    def __init__(self, root: tk.Tk, config: AppConfig):
        self.root = root
        self.config = config
        self.logger = configure_logging()
        self.gmail: GmailClient | None = None
        self.scan: ScanResult | None = None
        self.cancel_event = threading.Event()
        self.events: queue.Queue[tuple] = queue.Queue()
        self.busy = False

        self.root.title(config.app_name)
        self._window_icon: tk.PhotoImage | None = None
        icon_path = application_dir() / "assets" / "app_icon.png"
        try:
            self._window_icon = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self._window_icon)
        except tk.TclError:
            self.logger.warning("Ícone da janela não encontrado ou inválido: %s", icon_path)
        self.root.geometry("860x620")
        self.root.minsize(860, 620)
        self.root.configure(bg=BG)
        self._configure_styles()
        self._build()
        self.root.after(100, self._drain_events)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 20, "bold"))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure(
            "Treeview",
            rowheight=29,
            font=("Segoe UI", 9),
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
        )
        style.map("Treeview", background=[("selected", PRIMARY)], foreground=[("selected", "white")])
        style.configure(
            "Treeview.Heading",
            background=PRIMARY,
            foreground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", PRIMARY_ACTIVE)])

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text=self.config.app_name,
            background=BG,
            foreground=TEXT,
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            outer,
            text="Remova e-mails para liberar espaço na sua conta Fuper.",
            background=BG,
            foreground=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 10))

        account_card = ttk.Frame(outer, style="Card.TFrame", padding=12)
        account_card.pack(fill="x", pady=(0, 8))
        self.account_var = tk.StringVar(value="Conta Google não conectada")
        tk.Label(
            account_card,
            textvariable=self.account_var,
            background=CARD,
            foreground=TEXT,
            font=("Segoe UI", 10),
        ).pack(side="left")
        self.connect_button = ClassicButton(
            account_card,
            text="Conectar conta Google",
            command=self._connect,
        )
        self.connect_button.pack(side="right")
        self.disconnect_button = ClassicButton(
            account_card,
            text="Desconectar",
            command=self._disconnect,
        )
        self.disconnect_button.pack(side="right", padx=(0, 8))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 7))
        self.analyze_button = ClassicButton(
            actions,
            text="Analisar e-mails",
            command=self._analyze,
            state="disabled",
        )
        self.analyze_button.pack(side="left")
        self.cancel_button = ClassicButton(
            actions,
            text="Cancelar",
            command=self._cancel,
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=8)
        self.status_var = tk.StringVar(value="Conecte uma conta autorizada da Fuper para começar.")
        tk.Label(
            actions,
            textvariable=self.status_var,
            background=BG,
            foreground=MUTED,
            font=("Segoe UI", 10),
        ).pack(side="left", padx=12)

        result_card = ttk.Frame(outer, style="Card.TFrame", padding=12)
        self.summary_var = tk.StringVar(value="Nenhuma análise realizada")
        tk.Label(
            result_card,
            textvariable=self.summary_var,
            background=CARD,
            foreground=TEXT,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 7))

        table_frame = ttk.Frame(result_card, style="Card.TFrame")
        table_frame.pack(fill="x")
        self.table = ttk.Treeview(table_frame, columns=("subject", "date", "size"), show="headings", height=7)
        self.table.heading("subject", text="Assunto")
        self.table.heading("date", text="Data")
        self.table.heading("size", text="Tamanho estimado")
        self.table.column("subject", width=430, anchor="w")
        self.table.column("date", width=230, anchor="w")
        self.table.column("size", width=120, anchor="e")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        confirm_card = ttk.Frame(outer, style="Card.TFrame", padding=10)
        self.awareness_var = tk.BooleanVar(value=False)
        self.awareness_check = StyledCheckbutton(
            confirm_card,
            text="Estou ciente de que esses e-mails não poderão ser recuperados",
            variable=self.awareness_var,
            command=self._update_delete_state,
        )
        self.awareness_check.pack(anchor="w")

        bottom = ttk.Frame(outer)
        self.delete_button = ClassicButton(
            bottom,
            text="Excluir permanentemente",
            command=self._confirm_delete,
            state="disabled",
        )
        self.delete_button.pack(side="right")

        # Reserva primeiro os controles inferiores para que nunca sejam
        # empurrados para fora da janela quando ela for redimensionada.
        bottom.pack(side="bottom", fill="x", pady=(8, 0))
        confirm_card.pack(side="bottom", fill="x", pady=(8, 0))
        result_card.pack(fill="both", expand=True)

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.connect_button.configure(state="disabled" if busy else "normal")
        self.disconnect_button.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        self.analyze_button.configure(state="disabled" if busy or not self.gmail else "normal")
        if busy:
            self.delete_button.configure(state="disabled")

    def _run_worker(self, function) -> None:
        self.cancel_event = threading.Event()
        self._set_busy(True)

        def worker():
            try:
                function()
            except Exception as exc:
                self.events.put(("error", exc))
            finally:
                self.events.put(("idle",))

        threading.Thread(target=worker, daemon=True).start()

    def _progress_callback(self, current: int, total: int, text: str) -> None:
        self.events.put(("progress", current, total, text))

    def _connect(self) -> None:
        def work():
            gmail = GmailClient(authorize(), self.logger)
            account = gmail.verify_account(self.config.expected_account)
            self.events.put(("connected", gmail, account))

        self.status_var.set("Aguardando autorização do Google...")
        self._run_worker(work)

    def _disconnect(self) -> None:
        if self.busy:
            return
        disconnect()
        self.gmail = None
        self.scan = None
        self.account_var.set("Conta Google não conectada")
        self.status_var.set("Conta desconectada.")
        self.analyze_button.configure(state="disabled")
        self._clear_result()

    def _analyze(self) -> None:
        if not self.gmail:
            return
        self._clear_result()

        def work():
            result = self.gmail.scan_sender(
                self.config.gmail_query,
                self.config.preview_limit,
                self.cancel_event,
                self._progress_callback,
            )
            self.events.put(("scan", result))

        self._run_worker(work)

    def _clear_result(self) -> None:
        self.scan = None
        for row in self.table.get_children():
            self.table.delete(row)
        self.summary_var.set("Nenhuma análise realizada")
        self.awareness_var.set(False)
        self.delete_button.configure(state="disabled")

    def _show_scan(self, result: ScanResult) -> None:
        self.scan = result
        self.summary_var.set(
            f"{result.count} e-mail(s) encontrado(s) • aproximadamente {format_bytes(result.total_bytes)}"
        )
        for preview in result.previews:
            self.table.insert("", "end", values=(preview.subject, preview.date, format_bytes(preview.size_bytes)))
        if result.count > len(result.previews):
            self.status_var.set(
                f"Análise concluída. Exibindo {len(result.previews)} de {result.count} resultados."
            )
        else:
            self.status_var.set("Análise concluída. Revise os resultados antes de continuar.")
        self._update_delete_state()

    def _update_delete_state(self) -> None:
        enabled = (
            not self.busy
            and self.scan is not None
            and self.scan.count > 0
            and self.awareness_var.get()
        )
        self.delete_button.configure(state="normal" if enabled else "disabled")

    def _confirm_delete(self) -> None:
        if not self.gmail or not self.scan or not self.scan.count:
            return
        confirmed = messagebox.askyesno(
            "Confirmar exclusão permanente",
            f"Excluir permanentemente {self.scan.count} e-mail(s) de\n"
            f"{self.config.target_sender}?\n\n"
            f"Tamanho estimado: {format_bytes(self.scan.total_bytes)}\n\n"
            "Esta ação não poderá ser desfeita.",
            icon="warning",
        )
        if not confirmed:
            return

        frozen_scan = self.scan

        def work():
            result = self.gmail.permanently_delete(
                frozen_scan,
                self.config.delete_batch_size,
                self.cancel_event,
                self._progress_callback,
            )
            self.events.put(("deleted", result))

        self._run_worker(work)

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.status_var.set("Cancelamento solicitado; aguardando o lote atual terminar...")

    def _show_delete_result(self, result: DeleteResult) -> None:
        messagebox.showinfo(
            "Exclusão concluída",
            f"Excluídos permanentemente: {result.deleted}\n"
            f"Falhas: {result.failed}\n"
            f"Tamanho estimado: {format_bytes(result.estimated_bytes)}\n\n"
            "O indicador de armazenamento do Google pode levar algum tempo para atualizar.",
        )
        self._clear_result()
        self.status_var.set("Processo concluído. Faça uma nova análise para confirmar.")

    def _show_error(self, error: Exception) -> None:
        if isinstance(error, OperationCancelled):
            messagebox.showinfo("Operação cancelada", str(error))
            self.status_var.set(str(error))
            return
        if isinstance(error, WrongAccountError):
            disconnect()
            self.gmail = None
            self.account_var.set("Conta Google não conectada")
        text = str(error) if isinstance(error, AppError) else f"{type(error).__name__}: {error}"
        self.logger.exception("Erro na interface: %s", type(error).__name__)
        messagebox.showerror("Não foi possível concluir", text)
        self.status_var.set("Não foi possível concluir. Verifique a mensagem e tente novamente.")

    def _drain_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "connected":
                    self.gmail = event[1]
                    self.account_var.set(f"Conta conectada: {event[2]}")
                    self.status_var.set(
                        "Conta validada. Se o Google solicitar após 7 dias, conecte-a novamente."
                    )
                elif kind == "progress":
                    _current, _total, text = event[1:]
                    self.status_var.set(text)
                elif kind == "scan":
                    self._show_scan(event[1])
                elif kind == "deleted":
                    self._show_delete_result(event[1])
                elif kind == "error":
                    self._show_error(event[1])
                elif kind == "idle":
                    self._set_busy(False)
                    self._update_delete_state()
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)


def run() -> None:
    root = tk.Tk()
    try:
        config = load_config()
    except AppError as exc:
        root.withdraw()
        messagebox.showerror("Configuração inválida", str(exc))
        root.destroy()
        return
    StorageManagerApp(root, config)
    root.mainloop()
