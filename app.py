import pandas as pd
from sklearn.cluster import KMeans
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load and preprocess data
data = pd.read_csv("anna_canteen.csv")
data = data.drop("S.No", axis=1)
kmeans = KMeans(n_clusters=5, random_state=42)
pincodes = data[['PinCode']]
pincodes['Cluster'] = kmeans.fit_predict(pincodes[["PinCode"]])
data_with_cluster = pd.merge(data, pincodes, on="PinCode")

def nearby_canteen(zipcode):
    if len(str(zipcode)) != 6:
        return {'error': 'Please enter a valid 6-digit pincode.'}

    if zipcode in data_with_cluster["PinCode"].values:
        return data_with_cluster[data_with_cluster['PinCode'] == zipcode].to_dict(orient='records')
    else:
        pincode_cluster = pincodes[pincodes['PinCode'] == zipcode]["Cluster"].values
        if len(pincode_cluster) > 0:
            nearby_canteens = data_with_cluster[data_with_cluster["Cluster"] == pincode_cluster[0]]
            return nearby_canteens.to_dict(orient='records')
        else:
            # Find the nearest canteen if no match found
            data_with_cluster['Distance'] = abs(data_with_cluster["PinCode"] - zipcode)
            nearest_canteen = data_with_cluster.loc[data_with_cluster["Distance"].idxmin()]
            return nearest_canteen.to_dict()

@app.route('/nearby-canteen', methods=['POST'])
def check_nearby_canteen():
    data = request.json
    zipcode = data.get('zipcode')

    if not zipcode:
        return jsonify({'error': 'zipcode is required'}), 400

    result = nearby_canteen(zipcode)
    
    return jsonify(result)

@app.route('/ping')
def ping():
    return '<h1>Welcome to the Nearby Canteen Checker</h1>'

if __name__ == '__main__':
    app.run(debug=True)
