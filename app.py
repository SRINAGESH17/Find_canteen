import pandas as pd
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load the data and perform clustering when the app starts
data = pd.read_csv("anna_canteen.csv")
pincodes = data[['PinCode']]
kmeans = KMeans(n_clusters=5)  # Specify the number of clusters
pincodes['Cluster'] = kmeans.fit_predict(pincodes[["PinCode"]])
data_with_cluster = pd.merge(data, pincodes, on="PinCode")


data1 = pd.read_csv("Pincode_30052019.csv",encoding="ISO-8859-1")
data1 = data1.drop_duplicates(subset=["Pincode"])

pincode_dict = data1.set_index('Pincode')[['Office Name', 'StateName', 'District', 'Division Name']].to_dict(orient='index')

pincode_values = data1[['Pincode']].values

knn_model = NearestNeighbors(n_neighbors=1).fit(pincode_values)




def nearby_canteen(zipcode):
    if len(str(zipcode)) != 6:
        return "Please enter the right pincode."

    if zipcode in data_with_cluster["PinCode"].values:
        return data_with_cluster[data_with_cluster['PinCode'] == zipcode].to_dict(orient='records')
    else:
        pincode_cluster = pincodes[pincodes['PinCode'] == zipcode]["Cluster"].values
        if len(pincode_cluster) > 0:
            nearby_canteens = data_with_cluster[data_with_cluster["Cluster"] == pincode_cluster[0]]
            return nearby_canteens.to_dict(orient='records')
        else:
            print("No canteen found. Finding Nearest available canteen.")
            data_with_cluster['Distance'] = abs(data_with_cluster["PinCode"] - zipcode)
            nearest_canteen = data_with_cluster.loc[data_with_cluster['Distance'].idxmin()]
            return nearest_canteen.to_dict()



@app.route('/get_post_office', methods=['GET'])
def get_post_office_info():
    pincode = request.args.get('pincode', type=int)
    if pincode is None:
        return jsonify({"error": "Please provide a pincode"}), 400

    if pincode in pincode_dict:
        result = {
            "pincode": pincode,
            "post_office": pincode_dict[pincode]['Office Name'],
            'District': pincode_dict[pincode]['District'],
            'Division': pincode_dict[pincode]['Division Name'] ,
            'State': pincode_dict[pincode]['StateName'],
            "message": "Pincode found"
        }
    else:
        try:
            _, indices = knn_model.kneighbors([[pincode]])
            nearest_pincode = int(data.iloc[indices[0][0]]['Pincode'])
            result = {
                "message": "Pincode not found. Nearest serviceable pincode provided.",
                "nearest_pincode": nearest_pincode,
                "post_office": pincode_dict[nearest_pincode]['Office Name'],
                'District': pincode_dict[pincode]['District'],
                'Division': pincode_dict[pincode]['Division Name'],
                "state": pincode_dict[nearest_pincode]['State']
            }
        except:
            result = {
                "message": "Pincode not found. No serviceable pincode found."
            }
    try:
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/nearby-canteen', methods=['GET'])
def get_nearby_canteen():
    # Get the zipcode from the query parameters
    zipcode = request.args.get('zipcode', type=int)

    if not zipcode:
        return jsonify({"error": "Invalid or missing zipcode"}), 400

    nearby_canten = nearby_canteen(zipcode)

    if isinstance(nearby_canten, str):  # If the response is an error message
        return jsonify({"message": nearby_canten}), 400
    
    # Extract district name for further processing
    district_name = nearby_canten[0].get("District Name", "Unknown District") if isinstance(nearby_canten, list) else "Unknown District"

    # Here you would call your external function, e.g., handle_district_catalog
    # returan handle_district_catalog(recipient_id, district_name)

    return jsonify(nearby_canten), 200

if __name__ == '__main__':
    app.run(debug=True)
