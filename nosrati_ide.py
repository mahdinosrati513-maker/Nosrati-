# -*- coding: utf-8 -*-
"""محیط توسعه گرافیکی Nosrati ++ - نسخه اصلاح‌شده"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import subprocess
import sys
import threading
import re

HERE = Path(__file__).resolve().parent
COMP = HERE / "nosrati_compiler.py"

KEYS = [
    "عدد", "اعشاری", "رشته", "درست‌نما", "منطقی", "چاپ", "ورودی",
    "اگر", "وگرنه", "تاوقتی", "برای", "از", "تا", "آنگاه",
    "تابع", "بازگردان", "پایان", "کلاس", "آرایه", "و", "یا", "نه"
]


class IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Nosrati ++ | محیط توسعه فارسی")
        self.root.geometry("1100x720")
        self.path = None

        bar = ttk.Frame(root, padding=6)
        bar.pack(fill="x")
        for label, fn in [
            ("فایل جدید", self.new),
            ("باز کردن", self.open),
            ("ذخیره", self.save),
            ("کامپایل و اجرا", self.run),
        ]:
            ttk.Button(bar, text=label, command=fn).pack(side="right", padx=3)

        pane = ttk.Panedwindow(root, orient="vertical")
        pane.pack(fill="both", expand=True, padx=8, pady=5)

        ef = ttk.Frame(pane)
        pane.add(ef, weight=4)
        self.ed = tk.Text(
            ef, wrap="none", undo=True, font=("Consolas", 14),
            bg="#171923", fg="#e7eaf0", insertbackground="white",
            padx=12, pady=10
        )
        sy = ttk.Scrollbar(ef, orient="vertical", command=self.ed.yview)
        sx = ttk.Scrollbar(ef, orient="horizontal", command=self.ed.xview)
        self.ed.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.ed.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        ef.rowconfigure(0, weight=1)
        ef.columnconfigure(0, weight=1)

        bf = ttk.Frame(pane)
        pane.add(bf, weight=1)
        ttk.Label(bf, text="خروجی و پیام‌های کامپایل").pack(anchor="e")
        self.out = tk.Text(
            bf, height=9, bg="#101318", fg="#d7e0ea",
            font=("Consolas", 11), state="disabled"
        )
        self.out.pack(fill="both", expand=True)

        self.status = tk.StringVar(value="آماده")
        ttk.Label(root, textvariable=self.status, anchor="e").pack(fill="x")

        self.ed.bind("<KeyRelease>", self.highlight)
        root.bind("<Control-s>", lambda e: self.save())
        root.bind("<Control-o>", lambda e: self.open())
        root.bind("<F5>", lambda e: self.run())

        for tag, col in [
            ("kw", "#72b7ff"), ("str", "#b5d99c"),
            ("num", "#e7b66b"), ("com", "#7e8796")
        ]:
            self.ed.tag_configure(tag, foreground=col)

        self.new()

    def new(self):
        self.path = None
        self.ed.delete("1.0", "end")
        self.ed.insert(
            "1.0",
            '# برنامه نمونه Nosrati ++\nعدد سن = ۲۰\nچاپ("سلام دنیا")\n'
        )
        self.status.set("فایل جدید")

    def open(self):
        f = filedialog.askopenfilename(
            filetypes=[("Nosrati ++", "*.npp"), ("همه فایل‌ها", "*.*")]
        )
        if f:
            try:
                self.path = Path(f)
                self.ed.delete("1.0", "end")
                self.ed.insert("1.0", self.path.read_text(encoding="utf-8-sig"))
                self.highlight()
                self.status.set("باز شد: " + self.path.name)
            except Exception as e:
                messagebox.showerror("خطا در باز کردن فایل", str(e))

    def save(self):
        if not self.path:
            f = filedialog.asksaveasfilename(
                defaultextension=".npp",
                filetypes=[("Nosrati ++", "*.npp")]
            )
            if not f:
                return False
            self.path = Path(f)
        try:
            self.path.write_text(
                self.ed.get("1.0", "end-1c"), encoding="utf-8"
            )
            self.status.set("ذخیره شد: " + self.path.name)
            return True
        except Exception as e:
            messagebox.showerror("خطا در ذخیره فایل", str(e))
            return False

    def show(self, s):
        # جلوگیری از خطا در صورت دریافت None از هر مرحله
        if s is None:
            s = ""
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", str(s))
        self.out.configure(state="disabled")

    def run(self):
        if not self.save():
            return
        if not self.path:
            return
        if not COMP.is_file():
            self.show(
                "فایل کامپایلر پیدا نشد:\n"
                + str(COMP)
                + "\nفایل nosrati_compiler.py را کنار nosrati_ide.py قرار دهید."
            )
            return

        self.status.set("در حال کامپایل...")
        self.show("در حال کامپایل و اجرا...")

        source_path = self.path.resolve()

        def job():
            try:
                c = subprocess.run(
                    [sys.executable, str(COMP), str(source_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=str(source_path.parent),
                    check=False
                )

                # stdout/stderr همیشه به رشته امن تبدیل می‌شوند.
                msg = (c.stdout or "") + (c.stderr or "")

                if c.returncode == 0:
                    exe = source_path.with_suffix(
                        ".exe" if sys.platform == "win32" else ""
                    )
                    if not exe.exists():
                        exe = source_path.with_suffix("")

                    if not exe.exists():
                        msg += "\nفایل اجرایی پس از کامپایل پیدا نشد:\n" + str(exe)
                    else:
                        r = subprocess.run(
                            [str(exe)],
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            cwd=str(source_path.parent),
                            timeout=15,
                            check=False
                        )
                        msg += "\n--- خروجی برنامه ---\n"
                        msg += (r.stdout or "")
                        msg += (r.stderr or "")
                        if r.returncode != 0:
                            msg += f"\nکد خروج برنامه: {r.returncode}"

                if not msg.strip():
                    msg = "کامپایل و اجرا پایان یافت؛ خروجی‌ای تولید نشد."

                self.root.after(0, lambda result=msg: self.show(result))
                self.root.after(0, lambda: self.status.set("پایان اجرا"))

            except subprocess.TimeoutExpired:
                self.root.after(
                    0, lambda: self.show("زمان اجرای برنامه بیش از ۱۵ ثانیه شد و متوقف گردید.")
                )
                self.root.after(0, lambda: self.status.set("توقف به علت زمان"))
            except Exception as e:
                error_text = f"خطا هنگام کامپایل یا اجرا:\n{type(e).__name__}: {e}"
                self.root.after(0, lambda result=error_text: self.show(result))
                self.root.after(0, lambda: self.status.set("خطا"))

        threading.Thread(target=job, daemon=True).start()

    def highlight(self, event=None):
        text = self.ed.get("1.0", "end-1c")
        for tag in ("kw", "str", "num", "com"):
            self.ed.tag_remove(tag, "1.0", "end")

        for kw in KEYS:
            pos = "1.0"
            while True:
                p = self.ed.search(kw, pos, stopindex="end")
                if not p:
                    break
                end = f"{p}+{len(kw)}c"
                self.ed.tag_add("kw", p, end)
                pos = end

        for pat, tag in [
            (r'"(?:\\.|[^"\\])*"', "str"),
            (r'\b\d+(?:\.\d+)?\b', "num"),
            (r'#.*$', "com")
        ]:
            for m in re.finditer(pat, text, re.M):
                self.ed.tag_add(
                    tag,
                    f"1.0+{m.start()}c",
                    f"1.0+{m.end()}c"
                )


if __name__ == "__main__":
    root = tk.Tk()
    IDE(root)
    root.mainloop()
