from flask import Flask, render_template, jsonify, request, send_file
import requests
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# Configurações da API
API_USERS = "https://broker-api.mybroker.dev/admin/users"
API_DEPOSITS = "https://broker-api.mybroker.dev/admin/user-transactions?type=DEPOSIT"
HEADERS = {
    "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQWNlc3NvIEFkbWluIiwiZ3JvdXBJZCI6IjAxSlowTk5HR0MyNFZQQzdHR1ZXRU1DUVRZIiwiZW1haWwiOiJnYWJyaWVsaGVybmFuZGVzODIxQGdtYWlsLmNvbSIsInRlbmFudElkIjoiMDFKWjBLWk1KS0VESEE4NVBRSlc1MEZDTVEiLCJpZCI6IjAxSlowUDZLTURXV1lIQk1WNlQ3QlJNNkZWIiwibG9naW5JZCI6IjAxSzQzSjNXTVE0S0NSMEJZQ0NQTloxNTZTIiwiaWF0IjoxNzU2NzYxMjg5LCJleHAiOjE3NTY3ODI4ODksImlzcyI6IkFVVEgtVFJBREUtT1BUSU9OLUFETUlOIn0.OJpzZhOZmjVmVvVsn31RFh4K_aTQFhjyMaNXawFMSWI",
    "x-timestamp": "1756761303266"
}

# Funções para buscar dados da API com paginação
def fetch_users(page=1, page_size=50):
    resp = requests.get(API_USERS, headers=HEADERS, params={"page": page, "pageSize": page_size})
    return resp.json().get('data', [])

def fetch_deposits(page=1, page_size=50):
    resp = requests.get(API_DEPOSITS, headers=HEADERS, params={"page": page, "pageSize": page_size})
    return resp.json().get('data', [])

# Página inicial
@app.route('/')
def index():
    return render_template("index.html")

# API para listar leads com paginação
@app.route('/api/leads')
def api_leads():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 50))

    users = fetch_users(page, page_size)
    deposits = fetch_deposits(1, 1000)  # podemos pegar todos os depósitos para cálculos

    df_users = pd.DataFrame(users)
    df_deposits = pd.DataFrame(deposits)

    deposits_count = df_deposits.groupby('userId').size().to_dict()
    results = []

    for user in users:
        uid = user['id']
        balance = sum([w['balance'] for w in user.get('wallets', [])])
        results.append({
            "name": user['name'],
            "email": user['email'],
            "balance": balance,
            "deposits_count": deposits_count.get(uid, 0)
        })

    return jsonify(results)

# Exportação XLS
@app.route('/api/export')
def export():
    users = fetch_users(1, 1000)
    deposits = fetch_deposits(1, 1000)

    df_users = pd.DataFrame(users)
    df_deposits = pd.DataFrame(deposits)

    report = pd.DataFrame({
        "Nome": df_users['name'],
        "E-mail": df_users['email'],
        "Banca USD": [sum([w['balance'] for w in u.get('wallets', [])]) for u in users],
        "Depósitos": [len(df_deposits[df_deposits['userId']==u['id']]) for u in users]
    })

    report.to_excel("report.xlsx", index=False)
    return send_file("report.xlsx", as_attachment=True)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
