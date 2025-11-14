import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import boto3
from botocore.exceptions import ClientError
import hashlib
import os

dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
table = dynamodb.Table('Users')

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def register_user(username, pw):
    try:
        ans = table.get_item(Key={'username': username})
        if 'Item' in ans:
            messagebox.showerror("A user with this username already exists.")

        hashed_pw = hash_password(pw)
        table.put_item(Item={'username': username, 'pw': hashed_pw})
        messagebox.showinfo(f"User '{username}' registered.")
        return True
    except ClientError as e:
        messagebox.showerror("Server side error", str(e))
        return False
    
def verify_login(username, pw):
    try:
        resp = table.get_item(Key={'username': username})
        if 'Item' not in resp:
            messagebox.showerror("User not found.")
            return False

        stored_hash = resp['Item']['pw']

        if stored_hash == hash_password(pw):
            return True
        else:
            messagebox.showerror("Incorrect pw.")
            return False

    except ClientError as e:
        messagebox.showerror("Server side error", str(e))
        return False

def login(on_success):
    def handle_login():
        user = username_entry.get().strip()
        pw = pw_entry.get().strip()
        if not user or not pw:
            messagebox.showwarning("Enter both a username and password.")
            return
        
        if verify_login(user, pw):
            os.environ["EC_USERNAME"] = user
            root.destroy()
            on_success()
        

    def handle_register():
        user = username_entry.get().strip()
        pw = pw_entry.get().strip()
        if not user or not pw:
            messagebox.showwarning("Enter both a username and password.")
            return
        register_user(user, pw)
        username_entry.delete(0, tk.END)
        pw_entry.delete(0, tk.END)

    root = tk.Tk()
    root.title("Emoji Cam")
    root.geometry("225x230")
    root.resizable(False, False)
    root.configure(bg="white")
    style = ttk.Style(root)
    style.theme_use('clam')

    tk.Label(root, 
             text="Username", 
             bg="white", 
             font=("Arial", 10)
             ).pack(anchor="w", padx=40, pady=(20,0))
    username_entry = tk.Entry(root, width=30)
    username_entry.pack(padx=40, pady=(0, 10))

    tk.Label(root, text="Password", 
             bg="white", 
             font=("Arial", 10)
             ).pack(anchor="w", padx=40)
    pw_entry = tk.Entry(root, width=30, show="*")
    pw_entry.pack(padx=40, pady=(0, 15))

    button_frame = tk.Frame(root, bg="white")
    button_frame.pack(pady=10)

    tk.Button(button_frame, 
              text="Login", 
              bg="Salmon", 
              fg="white",
              width=15, 
              command=handle_login,
              relief="flat"
              ).grid(row=0, column=0)
    tk.Button(button_frame, 
              text="Register", 
              bg="DeepSkyBlue", 
              fg="white",
              width=15, 
              command=handle_register,
              relief="flat"
              ).grid(row=1, column=0, pady=15)

    root.mainloop()