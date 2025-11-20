#!/usr/bin/env python3
"""
A simple bright-blue themed Tkinter-based food-ordering app for a class bazaar.

Features:
- Show menu items (with categories).
- User selects quantities and adds to cart.
- Place order: order saved to orders.json (only admin can view orders).
- Admin login with password (password hash in config.json).
- Admin can view orders list and change admin password.

Run: python main.py
Requires: Python 3.8+ (no external packages).
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import datetime
import hashlib

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_FILE = os.path.join(APP_DIR, "menu.json")
ORDERS_FILE = os.path.join(APP_DIR, "orders.json")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")


# ---------- Utilities ----------
def ensure_files_exist():
    if not os.path.exists(MENU_FILE):
        sample_menu = [
            {"id": 1, "name": "Nasi Goreng", "category": "Makanan", "price": 12000},
            {"id": 2, "name": "Mie Goreng", "category": "Makanan", "price": 10000},
            {"id": 3, "name": "Bakso", "category": "Makanan", "price": 15000},
            {"id": 4, "name": "Es Teh Manis", "category": "Minuman", "price": 5000},
            {"id": 5, "name": "Jus Jeruk", "category": "Minuman", "price": 8000},
            {"id": 6, "name": "Roti Bakar", "category": "Snack", "price": 7000}
        ]
        with open(MENU_FILE, "w", encoding="utf-8") as f:
            json.dump(sample_menu, f, indent=2, ensure_ascii=False)

    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    if not os.path.exists(CONFIG_FILE):
        # Default password is "admin123" (change after first login!)
        default_pw = "admin123"
        default_hash = hashlib.sha256(default_pw.encode()).hexdigest()
        cfg = {"admin_password_sha256": default_hash}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)


def load_menu():
    with open(MENU_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_orders():
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ---------- Main Application ----------
class BazaarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Pemesanan Makanan - Bazaar Kelas 11 P7")
        self.root.geometry("1000x640")
        self.root.resizable(False, False)

        # Bright blue theme colors
        self.bg_color = "#bfe9ff"  # pale bright blue
        self.primary = "#2b9edb"  # strong blue
        self.accent = "#ffd166"  # warm accent
        self.card = "#ffffff"

        self.root.configure(bg=self.bg_color)

        ensure_files_exist()
        self.menu_items = load_menu()
        self.orders = load_orders()
        self.config = load_config()

        self.cart = {}  # item_id -> qty

        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TButton", background=self.primary, foreground="white", font=("Helvetica", 10, "bold"))
        style.map("TButton", background=[("active", "#1f7fb0")])
        style.configure("TLabel", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card, relief="flat")
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), background=self.primary, foreground="white")
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"), background=self.card)

    def build_ui(self):
        header = tk.Frame(self.root, bg=self.primary, height=60)
        header.pack(fill="x")
        tk.Label(header, text="Bazaar Kelas 11 P7 - Aplikasi Pemesanan", bg=self.primary, fg="white",
                 font=("Helvetica", 18, "bold")).pack(padx=12, pady=10, anchor="w")

        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main_frame, bg=self.bg_color)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(main_frame, bg=self.bg_color, width=340)
        right.pack(side="right", fill="y")

        # Category filter
        categories = sorted({it["category"] for it in self.menu_items})
        categories.insert(0, "Semua")
        cat_frame = tk.Frame(left, bg=self.bg_color)
        cat_frame.pack(fill="x", pady=(0, 8))
        tk.Label(cat_frame, text="Filter Kategori:", bg=self.bg_color).pack(side="left")
        self.cat_var = tk.StringVar(value="Semua")
        cat_box = ttk.Combobox(cat_frame, values=categories, state="readonly", textvariable=self.cat_var, width=20)
        cat_box.pack(side="left", padx=8)
        cat_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_menu_list())

        # Menu list (scrollable)
        menu_card = ttk.Frame(left, style="Card.TFrame", padding=10)
        menu_card.pack(fill="both", expand=True)
        tk.Label(menu_card, text="Daftar Menu", style="Header.TLabel").pack(anchor="w", pady=(0, 6))

        canvas = tk.Canvas(menu_card, bg=self.card, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(menu_card, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        self.menu_inner = tk.Frame(canvas, bg=self.card)
        canvas.create_window((0, 0), window=self.menu_inner, anchor="nw")

        self.menu_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.item_qty_vars = {}  # item_id -> tk.IntVar
        self.refresh_menu_list()

        # Right: cart and order actions
        cart_card = ttk.Frame(right, style="Card.TFrame", padding=10)
        cart_card.pack(fill="both", expand=True)
        tk.Label(cart_card, text="Keranjang", style="Header.TLabel").pack(anchor="w", pady=(0, 6))

        cols = ("Nama", "Jumlah", "Subtotal")
        self.cart_tree = ttk.Treeview(cart_card, columns=cols, show="headings", height=12)
        for c in cols:
            self.cart_tree.heading(c, text=c)
        self.cart_tree.column("Nama", width=140)
        self.cart_tree.column("Jumlah", width=60, anchor="center")
        self.cart_tree.column("Subtotal", width=80, anchor="e")
        self.cart_tree.pack(fill="both", expand=True)

        total_frame = tk.Frame(cart_card, bg=self.card)
        total_frame.pack(fill="x", pady=(8, 0))
        self.total_var = tk.StringVar(value="Total: Rp 0")
        tk.Label(total_frame, textvariable=self.total_var, bg=self.card, font=("Helvetica", 12, "bold")).pack(side="left")

        btn_frame = tk.Frame(cart_card, bg=self.card)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="Tambah ke Keranjang", command=self.add_selected_to_cart).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Bersihkan Keranjang", command=self.clear_cart).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Pesan Sekarang", command=self.place_order).pack(side="left", padx=4)

        # Footer right: admin
        admin_card = tk.Frame(right, bg=self.bg_color)
        admin_card.pack(fill="x", pady=(12, 0))
        ttk.Button(admin_card, text="Admin (Lihat Pesanan)", command=self.open_admin_login).pack(fill="x")
        tk.Label(right, text="(Hanya admin yang bisa melihat daftar pesanan)", bg=self.bg_color, fg="#333",
                 font=("Helvetica", 9)).pack(pady=(6, 0))

    def refresh_menu_list(self):
        # Clear existing
        for w in self.menu_inner.winfo_children():
            w.destroy()

        selected_cat = self.cat_var.get()
        filtered = [it for it in self.menu_items if selected_cat in ("Semua", "", it["category"])]
        for it in filtered:
            frame = tk.Frame(self.menu_inner, bg=self.card, pady=6)
            frame.pack(fill="x", padx=6, pady=4)

            left = tk.Frame(frame, bg=self.card)
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=it["name"], bg=self.card, font=("Helvetica", 11, "bold")).pack(anchor="w")
            tk.Label(left, text=f"{it['category']} · Rp {it['price']:,}", bg=self.card, fg="#555").pack(anchor="w")

            right = tk.Frame(frame, bg=self.card)
            right.pack(side="right")
            var = tk.IntVar(value=0)
            self.item_qty_vars[it["id"]] = var
            qty_spin = ttk.Spinbox(right, from_=0, to=99, width=4, textvariable=var)
            qty_spin.pack()

    def add_selected_to_cart(self):
        added = False
        for it in self.menu_items:
            qty = self.item_qty_vars.get(it["id"], tk.IntVar()).get()
            if qty and qty > 0:
                prev = self.cart.get(it["id"], 0)
                self.cart[it["id"]] = prev + qty
                self.item_qty_vars[it["id"]].set(0)
                added = True
        if not added:
            messagebox.showinfo("Info", "Pilih jumlah item terlebih dahulu.")
            return
        self.refresh_cart_view()

    def refresh_cart_view(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        total = 0
        for item_id, qty in self.cart.items():
            item = next((x for x in self.menu_items if x["id"] == item_id), None)
            if not item:
                continue
            subtotal = item["price"] * qty
            total += subtotal
            self.cart_tree.insert("", "end", values=(item["name"], qty, f"Rp {subtotal:,}"))
        self.total_var.set(f"Total: Rp {total:,}")

    def clear_cart(self):
        self.cart = {}
        self.refresh_cart_view()

    def place_order(self):
        if not self.cart:
            messagebox.showwarning("Peringatan", "Keranjang kosong.")
            return
        # ask for buyer name and optional note
        buyer = simpledialog.askstring("Data Pemesan", "Masukkan nama pemesan:", parent=self.root)
        if not buyer:
            messagebox.showinfo("Batal", "Pemesanan dibatalkan (nama diperlukan).")
            return
        note = simpledialog.askstring("Catatan (opsional)", "Catatan / Meja / No HP (opsional):", parent=self.root)

        order_items = []
        total = 0
        for item_id, qty in self.cart.items():
            item = next((x for x in self.menu_items if x["id"] == item_id), None)
            if not item:
                continue
            order_items.append({"id": item_id, "name": item["name"], "price": item["price"], "qty": qty})
            total += item["price"] * qty

        order = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "buyer": buyer,
            "note": note or "",
            "items": order_items,
            "total": total
        }

        # Append to orders file
        self.orders.append(order)
        save_orders(self.orders)
        messagebox.showinfo("Sukses", f"Pesanan diterima! Total Rp {total:,}")
        self.clear_cart()

    # ---------- Admin ----------
    def open_admin_login(self):
        pw = simpledialog.askstring("Admin Login", "Masukkan password admin:", parent=self.root, show="*")
        if pw is None:
            return
        pw_hash = hash_password(pw)
        if pw_hash == self.config.get("admin_password_sha256", ""):
            self.open_admin_panel()
        else:
            messagebox.showerror("Gagal", "Password salah.")

    def open_admin_panel(self):
        admin_win = tk.Toplevel(self.root)
        admin_win.title("Panel Admin - Daftar Pesanan")
        admin_win.geometry("800x500")
        admin_win.configure(bg=self.bg_color)

        top = tk.Frame(admin_win, bg=self.bg_color)
        top.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Waktu (UTC)", "Pemesan", "Total", "Catatan", "Rincian")
        tree = ttk.Treeview(top, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
        tree.column("Waktu (UTC)", width=160)
        tree.column("Pemesan", width=140)
        tree.column("Total", width=100, anchor="e")
        tree.column("Catatan", width=160)
        tree.column("Rincian", width=160)
        tree.pack(fill="both", expand=True, side="left")

        scrollbar = tk.Scrollbar(top, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        # Populate
        self.orders = load_orders()
        for idx, o in enumerate(self.orders, start=1):
            details = "; ".join(f"{it['name']} x{it['qty']}" for it in o["items"])
            tree.insert("", "end", values=(o["timestamp"], o["buyer"], f"Rp {o['total']:,}", o.get("note", ""), details))

        btns = tk.Frame(admin_win, bg=self.bg_color)
        btns.pack(fill="x", padx=10, pady=6)
        ttk.Button(btns, text="Refresh", command=lambda: self._admin_refresh(tree)).pack(side="left", padx=4)
        ttk.Button(btns, text="Export JSON", command=self._admin_export_json).pack(side="left", padx=4)
        ttk.Button(btns, text="Hapus Semua Pesanan", command=lambda: self._admin_clear_orders(tree)).pack(side="left", padx=4)
        ttk.Button(btns, text="Ganti Password Admin", command=self._admin_change_password).pack(side="right", padx=4)

    def _admin_refresh(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        self.orders = load_orders()
        for o in self.orders:
            details = "; ".join(f"{it['name']} x{it['qty']}" for it in o["items"])
            tree.insert("", "end", values=(o["timestamp"], o["buyer"], f"Rp {o['total']:,}", o.get("note", ""), details))
        messagebox.showinfo("Sukses", "Daftar pesanan diperbarui.")

    def _admin_export_json(self):
        path = os.path.join(APP_DIR, f"orders_export_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(load_orders(), f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Ekspor Selesai", f"File diekspor ke: {path}")

    def _admin_clear_orders(self, tree):
        if not messagebox.askyesno("Konfirmasi", "Hapus semua pesanan? Tindakan ini tidak bisa dibatalkan."):
            return
        self.orders = []
        save_orders(self.orders)
        self._admin_refresh(tree)
        messagebox.showinfo("Sukses", "Semua pesanan telah dihapus.")

    def _admin_change_password(self):
        new_pw = simpledialog.askstring("Ganti Password Admin", "Masukkan password baru:", show="*", parent=self.root)
        if not new_pw:
            messagebox.showinfo("Batal", "Perubahan password dibatalkan.")
            return
        confirm = simpledialog.askstring("Konfirmasi", "Masukkan ulang password baru:", show="*", parent=self.root)
        if new_pw != confirm:
            messagebox.showerror("Gagal", "Password tidak cocok.")
            return
        self.config["admin_password_sha256"] = hash_password(new_pw)
        save_config(self.config)
        messagebox.showinfo("Sukses", "Password admin berhasil diperbarui.")

def main():
    root = tk.Tk()
    app = BazaarApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
