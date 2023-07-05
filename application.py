from roboflow import Roboflow
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials,firestore
from passlib.hash import sha256_crypt
import jwt

#Roboflow initializing
rf = Roboflow(api_key="DSjv6trREzW6HM4WMOJI")
project = rf.workspace().project("graduation-project-annotations")
model = project.version(13).model

def create_app():
    app = Flask(__name__)

    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    #Firebase initializing
    cred = credentials.Certificate("graduationproject-29892-firebase-adminsdk-zchzh-dd9177f559.json")
    firebase_admin.initialize_app(cred)


    @app.route('/')
    def hello():
        return "Hello Ain Shams!"


    @app.route('/predictImg',methods=['POST','GET'])
    def upload():

        # Access the uploaded image file
        image_file = request.files['image']
        image_file.save('image.jpg')
        print("Saved")
        #Sending image to Roboflow API
        pred = model.predict('image.jpg', confidence=10)
        pred.save()
        pred_json = pred.json()
        print(pred_json)
        if len(pred_json['predictions']) == 0:
            return jsonify({
                "message": "Product can not be detected, try to capture another photo."
            }), 500
        doc_id = pred_json['predictions'][0]['class']
        print(doc_id)

        #Getting product data from Firestore
        db = firestore.client()
        doc_ref = db.collection("products").document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            document_data = doc.to_dict()
            product_name = document_data['name']
            product_price = document_data['price']
            return jsonify({
                "message":"",
                "name":product_name,
                "price":product_price,
                "class":doc_id
            }),200
        else:
            return jsonify({
                "message":"Product can not be detected, try to capture another photo."
            }),500


    @app.route('/register',methods=['POST'])
    def register():
        body = request.json
        phone_num = body['number']
        user_name = body['username']
        password = body['password']

        #Hashing password
        db_password = sha256_crypt.encrypt(password)

        db = firestore.client()
        doc_ref = db.collection("users").document(user_name)
        doc = doc_ref.get()

        #Validating credentials
        if phone_num == "" or user_name == "" or password == "":
            return jsonify({
                "message":"Error adding user"
            }),500
        if doc.exists:
            return jsonify({
                "message":"Username already taken"
            }),500
        if doc_ref.set({
            "username":user_name,
            "password":db_password,
            "phone_number":phone_num
        }):
            return jsonify({"message": "User added successfully"}), 200
        else:
            return jsonify({"message": "Error adding user"}), 500

    @app.route('/login',methods = ['POST'])
    def login():
        db = firestore.client()
        body = request.json
        username = body['username']
        password = body['password']

        if username != "" or password != "":
            doc_ref = db.collection("users").document(username)
            doc = doc_ref.get()
            if doc.exists:
                document_data = doc.to_dict()
                username_read = document_data.get('username')
                password_read = document_data.get('password')
                if password:
                    if username == username_read and sha256_crypt.verify(password,password_read):
                        #Generating JWT Token
                        payload = {
                            "username":username_read,
                        }
                        secret_key = 'hv7$#VZ#3SyWU&Q9B@Yb#7e!DkfZ%*nJ'
                        token = jwt.encode(payload, secret_key, algorithm='HS256')
                        return {
                            "message":"Login Successfully",
                            "token" : token
                        }
                    else:
                        return jsonify({"message": "Invalid username or password"}), 500
        else:
            return jsonify({"message": "Failed to login"}), 500

        return app

