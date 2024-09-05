import json
import requests
import datetime

URL_API = "https://api.mainnet-beta.solana.com"
headers = {"Content-Type": "application/json"}

def format_date(timestamp): # convertit un timestamp en date format europe
    try:
        return datetime.datetime.fromtimestamp(int(timestamp)).strftime('%d/%m/%Y %H:%M:%S') # convertir le timestamp en date JKMMAAAA H:M:S
    except TypeError as E:
        return "timestamp incorrect"
    

def sol_to_eur(montant): # convertir sol a eur 
    url = "https://api.coingecko.com/api/v3/simple/price" # sol a eur, API coigecko c'est gratuit
    params = {
            'ids': 'solana', 
            'vs_currencies': 'eur'
            }
    try:
        response = requests.get(url, params=params)
        return response.json()['solana']['eur'] * montant
    except:
        return 0 # en cas d'erreur retourner 0E. Plantera la conversion
    

def get_solde(wallet):
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet]
    }
    req = requests.post(URL_API, headers=headers, data=json.dumps(data))

    if req.status_code == 200:
        data = req.json().get('result', {})
        solde_sol = data.get('value', 0) / 1_000_000_000
        solde_eur = sol_to_eur(solde_sol)
        return {'SOL': solde_sol, 'EUR': solde_eur} # retourne un dict. accessible avec la méthode GET.
    return 0 # SI erreur, retour = 0


def get_transactions(wallet, limit=10): # retourner les signatures des transactions via adresse. limite fixée a 10 pour éviter les volume
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [wallet, 
                   {"limit": limit}
                    ]
    }

    req = requests.post(URL_API, headers=headers, data=json.dumps(data))
    if req.status_code == 200:
        return req.json().get('result', []) # retourne une liste des id de transac
    return []

def read_transactions(transactions): # lit et reformate les transaction. Entrée = LISTE. Conserve que les transactions conformes a la blockchain. filtre.
    transaction_return = list()
    try:
        for transaction in transactions:   
            if transaction['err'] == None and transaction['confirmationStatus'] == 'finalized':
                block_traite = {'Date' : format_date(transaction['blockTime']),
                                'signature' : transaction['signature'],
                                # 'err': transaction['err'], PAS NÉCESSAIRE DANS LE CODE CAR DÉJÀ FILTRÉ PAR LE CODE
                                # 'confirmationStatus': transaction['confirmationStatus'] PAS NECESSAIRE CAR DÉJÀ FILTRÉ PAR LE CODE
                }
                transaction_return.append(block_traite)

        return transaction_return
           
    except:
        return []
    
def get_transaction_detail(signature): # la signature = l'id de la transaciton, on recupère les détails
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, 
                   {"encoding": "json"}]
    }    
    try:
        req = requests.post(URL_API, headers=headers, data=json.dumps(data))
        
        if req.status_code == 200:
            transaction_details = req.json().get('result', None)
            if transaction_details:
                return transaction_details # return = dictionnaire
    except:
        return []
    

def extract_transaction_detail(transaction): #dictionnaire
    details = {}
    try:
        details['signature'] = transaction['transaction']['signatures'][0]
        instructions = transaction['transaction']['message']['instructions']
        acc_keys = transaction['transaction']['message']['accountKeys']

        token_program = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA" # permet de verifier si le type de transac est wallet a wallet ou token
        token_transfert = any(instruct['programIdIndex'] == acc_keys.index(token_program) for instruct in instructions) # instruction = methode utilisée par sol
        if token_transfert:
            details['type'] = "TOKEN"
        else:
            details['type'] = "WALLET"

        # verification du solde solana avant et après l'oppération
        solde_avant = transaction['meta']['preBalances']
        solde_apres = transaction['meta']['postBalances']

        # calcul du solde
        difference = (solde_apres[0] - solde_avant[0]) / 1_000_000_000 # UNITÉ LAMPORT CONVERTIE EN SOLANA
        if difference < 0:
            details['sol_montant'] = abs(difference)  # Convertit en string avec 9 décimales de précision
            details['eur_montant'] = round(sol_to_eur(abs(difference)),2)
            details['typeSolde'] = "negatif"
        else:
            details['sol_montant'] = abs(difference)  # Convertit en string avec 9 décimales de précision
            details['eur_montant'] = round(sol_to_eur(abs(difference)),2)
            details['typeSolde'] = "positif"



        return details

    except:
        return []

if __name__ == "__main__":
    print(get_solde("CZrDCSrm3HGLEdXg8btkPAx9YNf9YFtAFs8uNbp1GB7U"))#solde du wallet
    #transactions = get_transactions("CZrDCSrm3HGLEdXg8btkPAx9YNf9YFtAFs8uNbp1GB7U") # 10 derniere transac
    data = (get_transaction_detail('47YHRnXwtnSJhpYQgnDFiwG61xbRVwyZHHVJAr3YLCmUYwywidEzcg8WawQQfNd8RJrCYzo6DFfHqMYSR9fgTkWj')) # détail de X transac
    print(extract_transaction_detail(data))