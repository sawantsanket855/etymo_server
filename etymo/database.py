from django.db import connection
import jwt
from django.core.mail import EmailMultiAlternatives
import random
from datetime import datetime, timezone
import secrets
from psycopg2 import Binary
from django.conf import settings
from datetime import datetime, timedelta

def login(email,password,loginType):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                           create table IF NOT EXISTS tbl_login_data(col_username TEXT,col_email TEXT UNIQUE,col_password TEXT,col_login_type TEXT DEFAULT 'Agent');
                           select col_email from tbl_login_data where col_email = '{email}' and col_password = '{password}' and col_login_type='{loginType}';""")
            rows=cursor.fetchone()
            if rows:
                print(f'data for jwt {rows}')
                payload = {
                       "email": rows[0],
                       "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS),
                       "iat": datetime.now(timezone.utc),
                     }
                print(payload)

                token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
                print(token)
                return ('correct credentials',token)
            else:
                return ('invalid credentials','')
    
    except Exception as e:
        print(e)
        return ('server error',e)
    
def register(username,email,password):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                           create table IF NOT EXISTS tbl_login_data(col_username TEXT,col_email TEXT UNIQUE,col_password TEXT,col_login_type TEXT DEFAULT 'Agent');
                           CREATE TABLE IF NOT EXISTS tbl_agent_data(col_email TEXT REFERENCES tbl_login_data(col_email)ON DELETE CASCADE,col_balance INT DEFAULT 0);
                           insert into tbl_login_data (col_username,col_email,col_password) values('{username}','{email}','{password}');
                           insert into tbl_agent_data(col_email) values('{email}')
                           """)
            rows=cursor.rowcount
            print(rows)
            return 'registered'
            
    except Exception as e:
        return 'email already exist'


def generate_otp():
    otp=random.randint(1000,9999)
    return otp

def sendOTP(email):
    otp=generate_otp()

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                            select * from tbl_login_data where col_email = '{email}' 
                            """)
            rows=cursor.rowcount
            if(rows):
                cursor.execute(f'''CREATE TABLE IF NOT EXISTS tbl_otp(
                               col_email_id TEXT,
                               col_otp INT,
                               col_gen_time TIMESTAMPTZ DEFAULT NOW(),
                               col_isused BOOLEAN DEFAULT FALSE);
                               insert into tbl_otp(col_email_id,col_otp) values('{email}','{otp}');''')
            else:
                return 'email not registerd'
    except Exception as e:
        return 'error'
    
    try:
        print('start otp sending')
        subject = "Welcome to GST Web Portal !"
        from_email = "sanketsawant4123@gmail.com"
        to = [email]
        text_content = "OTP."
        html_content = f"<p><b>{otp}</b> This is your otp for login. Please don't share it with others</p>"

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        return 'error'
    return "otp sent"


def verifyOTP(email,otp):
    if not otp.isnumeric():
        return 'incorrect otp'
    try:
        with connection.cursor() as cursor:
            # cursor.execute(f"select * from tbl_otp where col_email_id='{email}' AND col_gen_time > NOW() - INTERVAL '5 minutes' ORDER BY col_gen_time DESC LIMIT 5")
            cursor.execute(f"select * from tbl_otp where col_email_id='{email}' ORDER BY col_gen_time DESC LIMIT 1")
            rows=cursor.fetchall()
            if(rows):
                data=rows[0]
                diff=datetime.now(timezone.utc)-data[2]
                if(diff.total_seconds()<300 and not data[3]):
                    print('otp gen',data[1])
                    if(data[1]==int(otp)):
                        print('correct otp')
                        try:
                            cursor.execute(f"update tbl_otp SET col_isused = True WHERE col_email_id ='{email}' AND col_otp='{data[1]}';")
                            print('otp status updated')
                        except Exception as e:
                            print(e)
                            return 'server error'
                    else:
                        return 'incorrect otp'
                else:
                    return 'otp expired'
            else:
                return 'otp not sent'
            return 'correct otp'
    except Exception as e:
        print(e)
        return 'error'
    
def sendPasswordResetEmail(email):
    username=None    
    reset_token=createResetPasswordToken(email)
    # reset_link=f"https://effulgent-torte-d90e0a.netlify.app/resetpassword/{email}/{reset_token}/"
    reset_link=f"http://localhost:3000/resetpassword/{email}/{reset_token}/"
    try:
        with connection.cursor() as cursor:
            print(email)
            cursor.execute(f"""
                           create table IF NOT EXISTS tbl_login_data(col_username TEXT,col_email TEXT UNIQUE,col_password TEXT);
                           select col_username from tbl_login_data where col_email ='{email}'""")
            rows=cursor.fetchall()
            username=rows[0][0]
            print(f'username is {username}')
        subject = "Reset Password"
        from_email="sanketsawant4123@gmail.com"
        to=[email]
        text_content='Reset Password'
        html_content= f"<p>Hello {username},<br> We received a request to reset your password for your GST webportal account.<br>Click the link below to set a new password: <br><a href='{reset_link}'>reset_link</a><br>This link will expire in 15 minutes. If you did not request a password reset, you can safely ignore this email.</p>"
        msg= EmailMultiAlternatives(subject,text_content,from_email,to)
        msg.attach_alternative(html_content,"text/html")
        msg.send()
        return 'reset password email sent'
    except Exception as e:
         print(e)
         return 'server error'

def createResetPasswordToken(email):
    reset_token=secrets.token_urlsafe(32)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS tbl_reset_token(
                               col_email_id TEXT,
                               col_reset_token TEXT,
                               col_gen_time TIMESTAMPTZ DEFAULT NOW(),
                               col_isused BOOLEAN DEFAULT FALSE);
                               insert into tbl_reset_token(col_email_id,col_reset_token) values('{email}','{reset_token}');''') 
            return reset_token

    except Exception as e:
        print(f'error: {e}')
        return 0
    
def updatePassword(email,reset_token,password):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT col_email_id FROM tbl_reset_token where col_email_id='{email}' and col_reset_token='{reset_token}' and col_gen_time > NOW() - INTERVAL '15 minutes' and col_isused=False;")
            rows=cursor.fetchall()
            if rows:
                cursor.execute(f'''update tbl_login_data set col_password='{password}' where col_email='{email}';
                                   update tbl_reset_token set col_isused = TRUE where col_email_id='{email}' and col_reset_token='{reset_token}'
                               ''')
                return 'password changed'
            else:
                return 'token expired'
    except Exception as e:
        print(e)
        return 'error'

        
def submit_request(name,type_,email,mobile,description,documents,token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        with connection.cursor() as cursor:
            cursor.execute(f"""
                           CREATE TABLE IF NOT EXISTS tbl_transactions(col_id SERIAL PRIMARY KEY,col_amount INT, col_type TEXT, col_user_email TEXT,col_purpose TEXT,col_reference_id INT, col_created_at TIMESTAMPTZ default NOW());
                            CREATE TABLE IF NOT EXISTS tbl_request(col_id SERIAL PRIMARY KEY, col_name TEXT,col_type TEXT ,col_email TEXT,col_mobile TEXT,col_description TEXT,col_status TEXT default 'Under Review',col_instruction TEXT DEFAULT '' ,col_created_at TIMESTAMPTZ default NOW(),col_assigned_ca_cs_id INT DEFAULT 0, col_agent_email_id TEXT);
                            """)
            cursor.execute(f"""
                           INSERT INTO tbl_request (col_name,col_type,col_email,col_mobile,col_description,col_agent_email_id)  VALUES (%s, %s, %s, %s, %s,%s) RETURNING col_id;
                            """,(name, type_, email, mobile, description,payload['email']) )
            new_id = cursor.fetchone()[0]
            print(new_id)
            cursor.execute(f"""
                           INSERT INTO tbl_transactions(col_type,col_amount, col_user_email,col_purpose,col_reference_id) VALUES('debit',500,'{payload['email']}','request_generation',{new_id});
                           UPDATE tbl_agent_data SET col_balance = CAST(col_balance as INT) - 500 where col_email ='{payload['email']}';
                            """)

            for doc in documents:
                byte_data=doc.read()
                print("Name:",doc.name ) 
                print("Type:", doc.content_type)
                print("Size:", len(byte_data))
            
                cursor.execute(f"""
                                CREATE TABLE IF NOT EXISTS tbl_documents (
                                                        col_id SERIAL PRIMARY KEY,
                                                        col_request_id INT REFERENCES tbl_request(col_id) ON DELETE CASCADE, -- link to request
                                                        col_filename TEXT,
                                                        col_content_type TEXT,
                                                        col_file_data BYTEA,
                                                        col_created_at TIMESTAMPTZ DEFAULT NOW()
                                                    );
                               INSERT INTO tbl_documents (col_request_id,col_filename,col_content_type,col_file_data)  VALUES (%s, %s, %s, %s);
                                """,(new_id,doc.name,doc.content_type,byte_data))
            
            print('submitted')
            return 'submitted'
    except jwt.ExpiredSignatureError:
        return "Token expired, Please login again!"
    except jwt.InvalidTokenError:
        return "Invalid token, Please login again!"
    except Exception as e:
        print(e)
        return 'server error'


def get_request_document(request_id):
    print(request_id)
    try:
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_id ,col_filename, col_content_type from tbl_documents where col_request_id={request_id}
                """)
            data=cursor.fetchall()
            print(f'documents got {data}')
            return data
    except Exception as e:
        print(e)
        return []

def get_request_data(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print(payload['email'])
        email=payload['email']
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_login_type from tbl_login_data where col_email='{email}';
                """)
            data=cursor.fetchone()
            print(data[0])
            if(data[0]=='Admin'):
                cursor.execute("""
                        select * from tbl_request order by col_created_at DESC
                    """)
            else:
                cursor.execute(f"""
                        select * from tbl_request where col_agent_email_id='{email}' order by col_created_at DESC
                    """)
            data=cursor.fetchall()
                # print(data)
            return (data,'success')
    except jwt.ExpiredSignatureError:
        return ([],"Token expired, Please login again!")
    except jwt.InvalidTokenError:
        return ([],"Invalid token, Please login again!")
    except Exception as e:
        print(e)
        return ([],'server error')



def get_ca_cs_data(token):
    print("in get_ca_cs_data")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print(payload['email'])
        email=payload['email']
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_login_type from tbl_login_data where col_email='{email}';
                """)
            data=cursor.fetchone()
            print(data[0])
            if(data[0]=='Admin'):
                cursor.execute("""
                        select * from tbl_ca_cs order by col_created_at DESC
                    """)
                data=cursor.fetchall()
                return (data,'success')
            else:
                return ([],"Unauthorized request")
                
            
                # print(data)
    except jwt.ExpiredSignatureError:
        return ([],"Token expired, Please login again!")
    except jwt.InvalidTokenError:
        return ([],"Invalid token, Please login again!")
    except Exception as e:
        print(e)
        return ([],'server error')



def get_request_document_data(id):
    try:
        print('get_request_document_data')
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_content_type,col_file_data from tbl_documents where col_id={id}
                """)
            data= cursor.fetchone()
            print(data)
            return data
    except Exception as e:
        print(e)



def ca_cs_registartion(data,docs):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS tbl_ca_cs(col_id SERIAL PRIMARY KEY, col_name TEXT,col_role TEXT, col_specialization TEXT ,col_email TEXT,col_mobile TEXT,col_regNumber TEXT,col_workingDays TEXT[], col_created_at TIMESTAMPTZ default NOW(),col_assigned_request INT[] DEFAULT '{}');
                            """)
            cursor.execute(f"""
                           INSERT INTO tbl_ca_cs (col_name,col_role,col_specialization, col_email,col_mobile,col_regNumber,col_workingDays) VALUES (%s, %s, %s, %s, %s ,%s, %s) RETURNING col_id;
                            """,(data['name'],data['role'],data['specialization'], data['email'], data['mobile'], data['regNumber'],['mon','tue','wed']) )
            new_id = cursor.fetchone()[0]
            print(new_id)

            for doc in docs:
                byte_data=doc.read()
                print("Name:",doc.name ) 
                print("Type:", doc.content_type)
                print("Size:", len(byte_data))
            
                cursor.execute(f"""
                                CREATE TABLE IF NOT EXISTS tbl_ca_cs_documents (
                                                        col_id SERIAL PRIMARY KEY,
                                                        col_ca_cs_id INT REFERENCES tbl_request(col_id) ON DELETE CASCADE, -- link to request
                                                        col_filename TEXT,
                                                        col_content_type TEXT,
                                                        col_file_data BYTEA,
                                                        col_created_at TIMESTAMPTZ DEFAULT NOW()
                                                    );
                               INSERT INTO tbl_ca_cs_documents (col_ca_cs_id,col_filename,col_content_type,col_file_data)  VALUES (%s, %s, %s, %s);
                                """,(new_id,doc.name,doc.content_type,byte_data))
            
            print('submitted')
            return 'submitted'
    except Exception as e:
        print(e)
        return 'server error'


def sendStatusUpdateEmail(agentEmail,agentUserName,requestId,requesCustomerName,requestStatus,requestInstruction):
    subject = "Request Status Update"
    from_email="sanketsawant4123@gmail.com"
    to=[agentEmail]
    text_content='Request Status Update'
    html_content= f"<p>Dear {agentUserName},<br> We would like to inform you that the status of your request has been updated. Please find the details below : <br><br>Request ID: {requestId}<br>Customer Name: {requesCustomerName}<br>Current Status: <b>{requestStatus}</b><br>Instruction: {requestInstruction if requestInstruction else 'NONE'}<br><br><br> If you have any questions or need further assistance, please feel free to contact us.<br><br>Thank you!</p>"
    msg= EmailMultiAlternatives(subject,text_content,from_email,to)
    msg.attach_alternative(html_content,"text/html")
    msg.send()    
    print('status update mail sent')

def update_request_status(requestId,requestStatus,requestInstruction):
    try:
        print('in update_request_status')
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                    UPDATE tbl_request SET col_status= %s, col_instruction = %s where col_id = %s RETURNING col_status;
                    SELECT col_agent_email_id,col_id,col_name from tbl_request where col_id = %s;
                 """ ,(requestStatus,requestInstruction,requestId,requestId)  
            )
            row=cursor.fetchone()
            agent_email=row[0]
            request_id=row[1]
            reques_customer_name=row[2]
            print(f'agent email : {agent_email}')

            cursor.execute(
                f"""
                    SELECT col_username from tbl_login_data where col_email= %s;
                 """ ,(agent_email,)  
            )
            row=cursor.fetchone()
            agent_username=row[0]
            print(agent_email,agent_username ,request_id,reques_customer_name,requestStatus,requestInstruction)
            sendStatusUpdateEmail(agentEmail=agent_email,agentUserName=agent_username , requestId=request_id,requesCustomerName=reques_customer_name,requestStatus=requestStatus,requestInstruction=requestInstruction)

    except Exception as e:
        print(e)
        return 'server error'


# def get_ca_cs_data():
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                     select * from tbl_ca_cs;
#                 """)
#             data=cursor.fetchall()
#             print(data)
#             return data
#     except Exception as e:
#         print(e)
#         return []
    
def assign_ca_cs(ca_cs_id,requestId):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    UPDATE tbl_request SET col_assigned_ca_cs_id={ca_cs_id},col_status='Assigned' where col_id ={requestId};
                    UPDATE tbl_ca_cs SET col_assigned_request= array_append(col_assigned_request, {requestId}) where col_id={ca_cs_id}
                      """)
            
    except Exception as e:
        print(e)

def get_verified_request_data():
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                    select * from tbl_request where col_status = 'Verified' order by col_created_at DESC
                """)
            data=cursor.fetchall()
            print(data)
            return data
    except Exception as e:
        print(e)
        return []
    

def submit_payment_request(name,amount,paymentMethod,bankName,accountNumber,ifscCode,upiId,documents,token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        with connection.cursor() as cursor:
            cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS tbl_payment_request(col_id SERIAL PRIMARY KEY, col_name TEXT,col_amount TEXT,col_payment_method TEXT ,col_bank_name TEXT,col_account_number TEXT,col_ifsc_code TEXT, col_upi_id TEXT,col_status TEXT default 'Pending',col_instruction TEXT DEFAULT '' ,col_created_at TIMESTAMPTZ default NOW(),col_agent_email_id TEXT);
                            """)
            cursor.execute(f"""
                           INSERT INTO tbl_payment_request (col_name,col_amount,col_payment_method,col_bank_name,col_account_number,col_ifsc_code,col_upi_id,col_agent_email_id)  VALUES (%s,%s, %s, %s, %s, %s,%s,%s) RETURNING col_id;
                            """,(name,amount, paymentMethod, bankName, accountNumber, ifscCode,upiId,payload['email']) )
            new_id = cursor.fetchone()[0]
            print(new_id)

            for doc in documents:
                byte_data=doc.read()
                print("Name:",doc.name ) 
                print("Type:", doc.content_type)
                print("Size:", len(byte_data))
            
                cursor.execute(f"""
                                CREATE TABLE IF NOT EXISTS tbl_payment_documents (
                                                        col_id SERIAL PRIMARY KEY,
                                                        col_request_id INT REFERENCES tbl_request(col_id) ON DELETE CASCADE, -- link to request
                                                        col_filename TEXT,
                                                        col_content_type TEXT,
                                                        col_file_data BYTEA,
                                                        col_created_at TIMESTAMPTZ DEFAULT NOW()
                                                    );
                               INSERT INTO tbl_payment_documents (col_request_id,col_filename,col_content_type,col_file_data)  VALUES (%s, %s, %s, %s);
                                """,(new_id,doc.name,doc.content_type,byte_data))
            
            print('submitted')
            return 'submitted'
    except jwt.ExpiredSignatureError:
        return "Token expired, Please login again!"
    except jwt.InvalidTokenError:
        return "Invalid token, Please login again!"
    except Exception as e:
        print(e)
        return 'server error'
    

    

def get_payment_request_data(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email=payload['email']
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_login_type from tbl_login_data where col_email='{email}';
                """)
            data=cursor.fetchone()
            print(data[0])
            if(data[0]=='Admin'):
                cursor.execute("""
                        select * from tbl_payment_request order by col_created_at DESC
                    """)
            else:
                cursor.execute(f"""
                        select * from tbl_payment_request where col_agent_email_id='{email}' order by col_created_at DESC
                    """)
            
            data=cursor.fetchall()
            print(data)
            return data
    except jwt.ExpiredSignatureError:
        return "Token expired, Please login again!"
    except jwt.InvalidTokenError:
        return "Invalid token, Please login again!"
    except Exception as e:
        print(e)
        return []
    
# def get_payment_request_document_data(id):
#     try:
#         print('get_payment_request_document_data')
#         with connection.cursor() as cursor:
#             cursor.execute(f"""
#                     select col_content_type,col_file_data from tbl_payment_documents where col_id={id}
#                 """)
#             data= cursor.fetchone()
#             print(data)
#             return data
#     except Exception as e:
#         print(e)


def get_payment_request_document(request_id):
    print(request_id)
    try:
        with connection.cursor() as cursor:
            # cursor.execute("""
            #         select col_id from tbl_request order by col_created_at DESC
            #     """)
            # request_id=cursor.fetchone()[0]
            # print(request_id)
            cursor.execute(f"""
                    select col_id ,col_filename, col_content_type from tbl_payment_documents where col_request_id={request_id}
                """)
            data=cursor.fetchall()
            print(f'documents got {data}')
            return data
    except Exception as e:
        print(e)
        return []


def get_payment_request_document_data(id):
    try:
        print('get_payment_request_document_data')
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_content_type,col_file_data from tbl_payment_documents where col_id={id}
                """)
            data= cursor.fetchone()
            print(data)
            return data
    except Exception as e:
        print(e)


def update_payment_request_status(paymentRequestId,requestInstruction):
    try:
        print('in update_payment_request_status')
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT col_agent_email_id,col_name,col_amount from tbl_payment_request where col_id = %s;
                 """ ,(paymentRequestId,)  
            )
            row=cursor.fetchone()
            agent_email=row[0]
            # agent_email='prashant@gmail.com'
            request_customer_name=row[1]
            amount=row[2]
            print(f'agent email : {agent_email}')

            cursor.execute(
                f"""
                    CREATE TABLE IF NOT EXISTS tbl_transactions(col_id SERIAL PRIMARY KEY,col_amount INT, col_type TEXT, col_user_email TEXT,col_purpose TEXT,col_reference_id INT, col_created_at TIMESTAMPTZ default NOW());
                    INSERT INTO tbl_transactions(col_type,col_amount, col_user_email,col_purpose,col_reference_id) VALUES('credit',{amount},'{agent_email}','payment_verification',{paymentRequestId});
                """
            )

            cursor.execute(
                f"""
                    UPDATE tbl_agent_data SET col_balance = CAST(col_balance as INT) + {amount} where col_email ='{agent_email}';
                    UPDATE tbl_payment_request SET col_status= 'Verified', col_instruction = %s where col_id = %s;
                    SELECT col_username from tbl_login_data where col_email= %s;
                 """ ,(requestInstruction,paymentRequestId,agent_email)  
            )

            
            row=cursor.fetchone()
            agent_username=row[0]
            print(agent_email,agent_username ,paymentRequestId,request_customer_name,requestInstruction)
            # sendStatusUpdateEmail(agentEmail=agent_email,agentUserName=agent_username , requestId=request_id,requesCustomerName=reques_customer_name,requestStatus=requestStatus,requestInstruction=requestInstruction)
            return 'success'
    except Exception as e:
        print(e)
        return 'server error'


def get_ca_cs_document(ca_cs_id):
    print(ca_cs_id)
    try:
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_id ,col_filename, col_content_type from tbl_ca_cs_documents where col_ca_cs_id={ca_cs_id}
                """)
            data=cursor.fetchall()
            print(f'documents got {data}')
            return data
    except Exception as e:
        print(e)
        return []
    
def get_ca_cs_document_data(id):
    print(id)
    try:
        print('get_ca_cs_document_data')
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_content_type,col_file_data from tbl_ca_cs_documents where col_id={id}
                """)
            data= cursor.fetchone()
            print(data)
            return data
    except Exception as e:
        print(e)



def get_agent_balance(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        with connection.cursor() as cursor:
            cursor.execute(f"""
                        select col_balance from tbl_agent_data where col_email = '{payload['email']}'
                        """)
            balance=cursor.fetchone()
            return 'success', balance[0]
    except jwt.ExpiredSignatureError:
        return "Token expired, Please login again!",0
    except jwt.InvalidTokenError:
        return "Invalid token, Please login again!",0
    except Exception as e:
        print(e)
        return 'server error',0
    


def get_transaction_data(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email=payload['email']
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_login_type from tbl_login_data where col_email='{email}';
                """)
            data=cursor.fetchone()
            print(data[0])
            if(data[0]=='Admin'):
                cursor.execute("""
                        select * from tbl_transactions order by col_created_at DESC
                    """)
            else:
                cursor.execute(f"""
                        select * from tbl_transactions where col_user_email='{email}' order by col_created_at DESC
                    """)
            
            data=cursor.fetchall()
            print(data)
            return data
    except jwt.ExpiredSignatureError:
        return "Token expired, Please login again!"
    except jwt.InvalidTokenError:
        return "Invalid token, Please login again!"
    except Exception as e:
        print(e)
        return []