import razorpay
from django.db import connection
import jwt
from django.conf import settings
from etymo.email import sendMail


client = razorpay.Client(auth=("rzp_test_RmS9j2gPUxb05Y", "51Uh6aITDjgkce4ufp74fNY0"))
def razorpay_create_request(token,amount):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        data = { "amount": amount, "currency": "INR", "receipt": "order_rcptid_11" }
        payment = client.order.create(data) # Amount is in currency subunits.
        print(payment['id'])

        with connection.cursor() as cursor:
            cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS tbl_razor_order_id(col_id SERIAL PRIMARY KEY, col_order_id TEXT,col_agent_email TEXT,col_amount INT);
                            """)
            cursor.execute(f"""
                           INSERT INTO tbl_razor_order_id (col_order_id,col_agent_email,col_amount)  VALUES (%s,%s,%s);
                            """,(payment['id'],payload['email'],amount/100) )
            print('submitted order id')
            return ('success',amount,payment['id'])
    except jwt.ExpiredSignatureError:
        return ("Token expired, Please login again!")
    except jwt.InvalidTokenError:
        return ("Invalid token, Please login again!")
    except Exception as e:
        print(e)
        return ('server error')
    
def razorpay_payment_data(payment_id,order_id,signature):
    params = {
    'razorpay_order_id': order_id,
    'razorpay_payment_id': payment_id,
    'razorpay_signature': signature
    }
    try:
        client.utility.verify_payment_signature(params)
        print("Payment Signature Verified ✔ here to add amount in wallet")
        print('in update_payment_request_status')
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        SELECT col_agent_email,col_amount from tbl_razor_order_id where col_order_id = %s;
                     """ ,(order_id,)  
                )
                row=cursor.fetchone()
                agent_email=row[0]
                amount=row[1]
                print(f'agent email : {row[0]}   amount : {row[1]}')
                cursor.execute(
                    f"""
                        CREATE TABLE IF NOT EXISTS tbl_transactions(col_id SERIAL PRIMARY KEY,col_amount INT, col_type TEXT, col_user_email TEXT,col_purpose TEXT,col_reference_id INT, col_created_at TIMESTAMPTZ default NOW());
                        INSERT INTO tbl_transactions(col_type,col_amount, col_user_email,col_purpose,col_reference_id) VALUES('credit',{amount},'{agent_email}','payment_verification',{100});
                    """
                )
                cursor.execute(
                    f"""
                        UPDATE tbl_agent_data SET col_balance = CAST(col_balance as INT) + {amount} where col_email ='{agent_email}';
                     """   
                )
                print ('amount is added in wallet')
                return 'success'
        except Exception as e:
            print('error while updating wallet')
            print(e)
       
    except:
        print("Signature Verification Failed ❌")